# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1113, 866)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.btn_searchbycodename = QtWidgets.QPushButton(self.centralwidget)
        self.btn_searchbycodename.setGeometry(QtCore.QRect(230, 60, 75, 41))
        self.btn_searchbycodename.setObjectName("btn_searchbycodename")
        self.input_codename = QtWidgets.QLineEdit(self.centralwidget)
        self.input_codename.setGeometry(QtCore.QRect(10, 60, 211, 41))
        self.input_codename.setObjectName("input_codename")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 10, 231, 41))
        self.label.setObjectName("label")
        self.list_codename = QtWidgets.QListView(self.centralwidget)
        self.list_codename.setGeometry(QtCore.QRect(10, 110, 231, 221))
        self.list_codename.setObjectName("list_codename")
        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(310, 60, 581, 131))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.btn_opt10075 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.btn_opt10075.setObjectName("btn_opt10075")
        self.gridLayout.addWidget(self.btn_opt10075, 1, 0, 1, 1)
        self.btn_opw00018 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.btn_opw00018.setObjectName("btn_opw00018")
        self.gridLayout.addWidget(self.btn_opw00018, 0, 0, 1, 1)
        self.btn_opw00001 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.btn_opw00001.setObjectName("btn_opw00001")
        self.gridLayout.addWidget(self.btn_opw00001, 0, 1, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(10, 340, 231, 61))
        self.pushButton.setObjectName("pushButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1113, 38))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.btn_searchbycodename.setText(_translate("MainWindow", "검색"))
        self.label.setText(_translate("MainWindow", "종목 이름으로 검색"))
        self.btn_opt10075.setText(_translate("MainWindow", "주문 내역 요청"))
        self.btn_opw00018.setText(_translate("MainWindow", "평가잔고내역"))
        self.btn_opw00001.setText(_translate("MainWindow", "예수금상세현황요청"))
        self.pushButton.setText(_translate("MainWindow", "보유종목실시간체결정보 수신"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())