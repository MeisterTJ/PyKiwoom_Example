from PyQt5.QtCore import *  # 쓰레드 함수를 불러온다.
from ALBA_Kiwoom import Kiwoom
from PyQt5.QtWidgets import *
from ALBA_Lesson.ALBA_GuiMain import Login_Machine


class AutoTradeThread(QThread):
    def __init__(self, gui: Login_Machine):
        super().__init__(gui)
        self.gui = gui
        self.kiwoom = Kiwoom()  # 멤버로 Kiwoom 클래스 생성
        self.account_id = self.gui.accComboBox.currentText()
