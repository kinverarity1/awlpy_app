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

from wellcadformats import arraydata

from awlpy_app.log_document import LogDocument

from awlpy_app.sonic_log import SonicLog


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        undo_stack = QUndoStack(self)
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # https://www.pythonguis.com/tutorials/pyside-actions-toolbars-menus/

        menu = self.menuBar()

        toolbar = QToolBar("Main toolbar")
        self.addToolBar(toolbar)

        new_log_document_action = QAction("&New log document", self)
        new_log_document_action.setStatusTip("New log document")
        new_log_document_action.triggered.connect(self.create_new_log_document)
        new_log_document_action.setShortcut(QKeySequence("Ctrl+N"))
        
        load_sonic_log_action = QAction("Open sonic &log", self)
        load_sonic_log_action.setStatusTip("Open sonic log")
        load_sonic_log_action.triggered.connect(self.load_sonic_log)
        load_sonic_log_action.setShortcut(QKeySequence("Ctrl+L"))
        toolbar.addAction(load_sonic_log_action)
        if self.tab_widget.count() == 0:
            load_sonic_log_action.setDisabled(True)
        self.load_sonic_log_action = load_sonic_log_action

        undo_action = undo_stack.createUndoAction(self, "Undo")
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action = undo_stack.createRedoAction(self, "Redo")
        redo_action.setShortcuts(QKeySequence.Redo)
        
        file_menu = menu.addMenu("&File")
        file_menu.addAction(new_log_document_action)
        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        # log_menu = menu.addMenu("&Log")
        # log_menu.addAction(load_sonic_log_action)

        self.setStatusBar(QStatusBar(self))

        settings = QSettings()
        if settings.value("main_window/geometry"):
            self.restoreGeometry(settings.value("main_window/geometry"))
        if settings.value("main_window/window_state"):
            self.restoreState(settings.value("main_window/window_state"))

    def closeEvent(self, event):
        settings = QSettings()
        settings.setValue("main_window/geometry", self.saveGeometry())
        settings.setValue("main_window/window_state", self.saveState())
        super(MainWindow, self).closeEvent(event)

    def create_new_log_document(self):
        document = LogDocument(mw=self)
        self.tab_widget.addTab(document, document.name)
        self.load_sonic_log_action.setEnabled(True)
    
    def load_sonic_log(self):
        folder = str(QSettings().value("sonic_log/last_opened_file", "."))

        files = QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select one or more sonic log files to open",
            dir=folder,
            filter="WellCAD ASCII file (*.waf)"
        )
        paths = []
        filenames, file_types = files
        for filename in filenames:
            paths.append(Path(filename))

        for path in paths:
            QSettings().setValue("sonic_log/last_opened_file", path.parent)
            self.load_sonic_log_file(path)

    def load_sonic_log_file(self, filename):
        log = SonicLog(filename)
        self.tab_widget.currentWidget().add_log(log)


def main():
    logging.basicConfig(level=logging.DEBUG)
    pg.setConfigOptions(imageAxisOrder='row-major')
    app = QApplication([])
    app.setOrganizationName("awlpy_app") 
    app.setApplicationName("awlpy_app")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    