import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtWidgets, QtGui
import qdarkstyle
from Test_Kiwoom import *
from Test_Utility import *
from Test_UI import Ui_MainWindow


#form_class = uic.loadUiType("test.ui")[0]
ui_auto_complete("test.ui", "Test_UI.py")

class Test_Main():
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.setUI()

    def setUI(self):
        self.ui = Ui_MainWindow()
        self.window = QtWidgets.QMainWindow()
        self.ui.setupUi(self.window)
        self.ui.btn_searchbycodename.clicked.connect(self.onclicked_search_by_codename)
        self.ui.btn_opw00001.clicked.connect(self.onclicked_opw00001)
        self.ui.btn_opw00018.clicked.connect(self.onclicked_opw00018)
        self.ui.btn_opt10075.clicked.connect(self.onclicked_opt10075)

        self.window.show()


        # 다크 테마 적용
        self.window.setStyleSheet(qdarkstyle.load_stylesheet_pyside2())


    # 예수금 얻어오기
    def onclicked_opw00001(self):
        self.kiwoom.get_deposit()

    def onclicked_opw00018(self):
        self.kiwoom.get_balance()

    def onclicked_opt10075(self):
        self.kiwoom.get_order()

    def onclicked_search_by_codename(self):
        Model = QtGui.QStandardItemModel(self.ui.list_codename)
        for key, value in self.kiwoom.name_to_code.items():
            if self.ui.input_codename.text() in key:
                Model.appendRow(QtGui.QStandardItem("%s : %s" % (value, key)))

        self.ui.list_codename.setModel(Model)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Test_Main()
    sys.exit(app.exec_())
