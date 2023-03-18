import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
import os
import qdarkstyle

from ALBA_Kiwoom import Kiwoom

condition_window = uic.loadUiType("Condition.ui")[0]

class ConditionWindow(QMainWindow, QWidget, condition_window):
    def __init__(self):
        super(ConditionWindow, self).__init__()
        self.setupUi(self)
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.kiwoom = Kiwoom()

