from PyQt5.QtWidgets import QApplication

from EBook.strategy import *
import sys

app = QApplication(sys.argv)

rsi_strategy = RSIStrategy()
rsi_strategy.start()

app.exec_()
