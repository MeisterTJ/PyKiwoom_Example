from PyQt5.QtCore import *       # eventloop, thread를 사용할 수 있는 함수 가져옴
from ALBA_Kiwoom import Kiwoom
from PyQt5.QtWidgets import *
from PyQt5.QtTest import *      # 시간 관련 함수
from datetime import datetime, timedelta   # 특정 일자를 조회

class Thread2(QThread):
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.kiwoom = Kiwoom()