import glob
import sys
import os
from pathlib import Path
import logging

import numpy as np
import pandas as pd

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import pyqtgraph as pg
from pyqtgraph.dockarea import Dock

from wellcadformats import arraydata


logger = logging.getLogger(__name__)

class SonicLog(Dock):
    def __init__(self, waf_fn):
        self.filename = Path(waf_fn)
        super(SonicLog, self).__init__(self.filename.stem, closable=True)

        self.waf = arraydata.WAF(waf_fn)
        self.waf.depths *= 0.3048
        self.waf.data *= -1
        logger.debug(f"WAF data: {self.waf.data.shape}")
        logger.debug(f"WAF times: {self.waf.times.shape}")
        logger.debug(f"WAF depths: {self.waf.depths.shape}")
        self.waf_fn = waf_fn
        self.vdl = VDL(self.waf)
        
        self.time_plot_panel = QWidget()
        time_plot_panel_layout = QVBoxLayout()
        self.time_plot_panel.setLayout(time_plot_panel_layout)
        self.time_plot = pg.PlotWidget()
        tpp_layout_controls = QHBoxLayout()
        tpp_controls = QWidget()
        tpp_controls.setLayout(tpp_layout_controls)
        self.time_plot_label = QLabel()
        self.time_plot_statistic = QComboBox()
        self.time_plot_statistic.addItems(FixedWindow._statistic_values)
        tpp_layout_controls.addWidget(self.time_plot_label)
        tpp_layout_controls.addWidget(self.time_plot_statistic)
        
        time_plot_panel_layout.addWidget(self.time_plot)
        time_plot_panel_layout.addWidget(tpp_controls)

        self.vertical_plot_panel = QWidget()
        layout1 = QVBoxLayout()
        self.vertical_plot_panel.setLayout(layout1)
        self.vertical_plot = pg.PlotWidget()
        self.export_button = QPushButton("Export CSV")
        layout1.addWidget(self.vertical_plot)
        layout1.addWidget(self.export_button)

        self.topbottom_splitter = QSplitter()
        self.leftright_splitter = QSplitter()
        self.topbottom_splitter.setOrientation(Qt.Vertical)
        self.leftright_splitter.setOrientation(Qt.Horizontal)
        
        # layout = QHBoxLayout()
        # layout.addWidget(self.leftright_splitter)
        # self.setLayout(layout)
        self.addWidget(self.leftright_splitter)
        
        self.leftright_splitter.addWidget(self.vertical_plot_panel)
        self.leftright_splitter.addWidget(self.topbottom_splitter)

        self.topbottom_splitter.addWidget(self.vdl)
        self.topbottom_splitter.addWidget(self.time_plot_panel)
        
        self.rois = []
        self.add_roi(DepthSlice(self.vdl, self.time_plot))
        self.add_roi(FixedWindow(200, 50, self.vdl, self.vertical_plot, self.time_plot, window_label=self.time_plot_label, window_statistic_select=self.time_plot_statistic))
        self.export_button.clicked.connect(self.export)

        self.vdl.set_vampl(500)

    def add_roi(self, roi):
        roi.show()
        self.rois.append(roi)

    def set_vampl(self, value):
        value = abs(value) * 2
        self.time_plot.getPlotItem().setYRange(value * -1, value, padding=0)

    def export(self):
        fixed_window = self.rois[1]  # very hard-coded thingy
        t0 = fixed_window.t0
        width = fixed_window.width
        fn = str(self.waf_fn).replace(
            ".waf", 
            f"_{fixed_window.t0:.0f}+{fixed_window.width:.0f}us_{fixed_window.statistic}.csv"
        )
        depths, times, values = fixed_window.data()
        depths, times, values = resample([depths, times], [depths, values])
        keys = [
            "Depth",
            "Time (%.0f-%.0f us)" % (t0, t0 + width),
            "Amplitude (%.0f-%.0f us)" % (t0, t0 + width)
            ]
        data = {
            "Depth": depths,
            "Time (%.0f-%.0f us)" % (t0, t0 + width): times,
            "Amplitude (%.0f-%.0f us)" % (t0, t0 + width): values,
            }
        pd.DataFrame(data, columns=keys).to_csv(fn, index=False)



def resample(*pairs):
    new_pairs = []
    for pair in pairs:
        i = np.argsort(pair[0])
        p0 = pair[0][i]
        p1 = pair[1][i]
        new_pairs.append((p0, p1))
    print(new_pairs)
    index_array = np.asarray(new_pairs[0][0])
    min_gradients = [np.min(index_array)]
    for pair in new_pairs[1:]:
        index_array = np.append(index_array, pair[0])
        min_gradients.append(np.min(np.gradient(pair[0])))
    print(min_gradients)
    index_reg = np.arange(np.min(index_array), np.max(index_array), np.min(min_gradients) / 5.)
    data_regs = []
    for index_array, data in new_pairs:
        data_reg = np.interp(index_reg, index_array, data, left=np.nan, right=np.nan)
        data_regs.append(data_reg)
    return [index_reg] + data_regs




class DepthSlice(object):
    def __init__(self, vdl, time_plot, depth=None):
        self.vdl = vdl
        self.time_plot = time_plot
        if depth is None:
            depth = np.mean(vdl.waf.depths)
            logger.info("Selecting mean depth of {depth:.2f}")
        self.depth = depth
        self.vdl_line = pg.InfiniteLine(depth, angle=0, movable=True, bounds=(vdl.waf.depths[0], vdl.waf.depths[-1]))
        self.trace_line = pg.PlotDataItem(self.vdl.waf.times, self.trace)
        self.vdl_line.sigPositionChanged.connect(self.update)

    @property
    def trace(self):
        depth, trace = self.vdl.waf.htrace(self.depth)
        return trace
        
    def update(self):
        self.depth = self.vdl_line.value()
        self.trace_line.setData(self.vdl.waf.times, self.trace)
        self.time_plot.setTitle(str(self.depth))

    def show(self):
        self.vdl.addItem(self.vdl_line)
        self.time_plot.addItem(self.trace_line)
        
    def hide(self):
        self.vdl.removeItem(self.vdl_line)
        self.time_plot.removeItem(self.trace_line)



class FixedWindow(object):
    _statistic_values = ("max", "min", "max(abs)")

    def __init__(self, t0, width, vdl, vertical_plot, time_plot, window_label=None, window_statistic_select=None):
        self._statistic = "max(abs)"
        window_statistic_select.currentTextChanged.connect(self.set_statistic)
        self.vdl = vdl
        self.vertical_plot = vertical_plot
        self.time_plot = time_plot
        self.window_label = window_label

        self.vdl_roi = pg.LinearRegionItem(values=[t0, t0+width], orientation=pg.LinearRegionItem.Vertical)
        self.time_plot_roi = pg.LinearRegionItem(values=[t0, t0+width], orientation=pg.LinearRegionItem.Vertical)
        depths, times, values = self.data()
        self.statistic_value_curve = pg.PlotDataItem(values, depths)
        self.statistic_time_curve = pg.PlotDataItem(times, depths, pen="r")

        self.vdl_roi.sigRegionChanged.connect(self.moved_vdl_roi)
        self.time_plot_roi.sigRegionChanged.connect(self.moved_time_plot_roi)
        self.vdl_roi.sigRegionChanged.connect(self.update)

        self.update()

    @property
    def t0(self):
        return min(self.vdl_roi.getRegion())

    @property
    def t1(self):
        return max(self.vdl_roi.getRegion())

    @property
    def width(self):
        return self.t1 - self.t0
    
    def set_statistic(self, value):
        self.statistic = value

    @property
    def statistic(self):
        return self._statistic

    @statistic.setter
    def statistic(self, value):
        assert value in self._statistic_values
        self._statistic = value        
        self.update()

    def update(self):
        depths, times, values = self.data()
        
        self.statistic_value_curve.setData(values, depths)
        self.statistic_time_curve.setData(times, depths)

        if self.window_label:
            self.window_label.setText(f"{self.t0:.0f} us - {self.t1:.0f} us ({self.width:.0f} us)")

    def data(self):
        try:
            self.window_waf = self.vdl.waf.extract(
                    trange=self.vdl_roi.getRegion())
        except ValueError:
            return [], [], []
        if self.statistic == "max":
            seek_data = self.window_waf.data
            return_data = self.window_waf.data
            func = np.argmax
        if self.statistic == "min":
            seek_data = self.window_waf.data
            return_data = self.window_waf.data
            func = np.argmin
        if self.statistic == "max(abs)":
            seek_data = np.abs(self.window_waf.data)
            return_data = np.abs(self.window_waf.data)
            func = np.argmax

        time_args = func(seek_data, axis=1)
        times = np.asarray([self.window_waf.times[ti] for ti in time_args])

        values = []
        for i in range(len(time_args)):
            values.append(return_data[i, time_args[i]])
        values = np.asarray(values)

        return self.window_waf.depths, times, values

    def moved_vdl_roi(self):
        self.time_plot_roi.setRegion(self.vdl_roi.getRegion())

    def moved_time_plot_roi(self):
        self.vdl_roi.setRegion(self.time_plot_roi.getRegion())

    def show(self):
        self.vdl.addItem(self.vdl_roi)
        self.time_plot.addItem(self.time_plot_roi)

        self.vertical_plot.addItem(self.statistic_value_curve)
        self.vertical_plot.invertY()

        self.vdl.addItem(self.statistic_time_curve)

    def hide(self):
        self.vdl.removeItem(self.vdl_roi)
        self.time_plot.removeItem(self.time_plot_roi)
        self.vertical_plot.removeItem(self.statistic_value_curve)
        self.vdl.removeItem(self.statistic_time_curve)



class VDL(pg.ImageView):

    sigVamplChanged = Signal(float)

    def __init__(self, waf):
        super(VDL, self).__init__(view=pg.PlotItem())
        self.waf = waf
        self.view.removeItem(self.roi)
        self.view.removeItem(self.normRoi)
        self.ui.roiBtn.hide()
        hist_region = self.getHistogramWidget().item.region
        hist_region.lines[0].sigPositionChanged.connect(self.hist_drag_0_slot)
        hist_region.lines[1].sigPositionChanged.connect(self.hist_drag_1_slot)
        x0 = waf.times[0]
        x1 = waf.times[-1]
        y1 = waf.depths[-1]
        y0 = waf.depths[0]
        # print("VDL WAF data shape = %s" % (waf.data.shape, ))
        xscale = (x1 - x0) / waf.data.shape[1]
        yscale = (y1 - y0) / waf.data.shape[0]
        self.setImage(waf.data, pos=[x0, y0], scale=[xscale, yscale])
        self.view.setAspectLocked(False)

    def hist_drag_0_slot(self):
        hist_region = self.getHistogramWidget().item.region
        value = hist_region.lines[0].value()
        hist_region.lines[1].setValue(value * -1)
        self.sigVamplChanged.emit(abs(value))

    def hist_drag_1_slot(self):
        hist_region = self.getHistogramWidget().item.region
        value = hist_region.lines[1].value()
        hist_region.lines[0].setValue(value * -1)
        self.sigVamplChanged.emit(abs(value))

    def set_vampl(self, value):
        value = abs(value)
        hist = self.getHistogramWidget()
        hist.setLevels(value * -1, value)