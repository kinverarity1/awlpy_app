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
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea


logger = logging.getLogger(__name__)


class LogDocument(QWidget):
    def __init__(self, mw, parent=None, name="New Log Document"):
        super(LogDocument, self).__init__()
        self.mw = mw
        self.name = name

        self.dock_area = DockArea()
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.dock_area)

    def add_log(self, log):
        self.dock_area.addDock(log)