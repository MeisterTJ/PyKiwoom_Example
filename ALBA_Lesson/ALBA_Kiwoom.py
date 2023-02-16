from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5Singleton import Singleton


class Kiwoom(QWidget, metaclass=Singleton):     # QMainWindow : PyQt5에서 윈도우 생성시 필요한 함수
    def __init__(self, parent=None, **kwargs):  # Main class의 self를 초기화 한다.

        print("로그인 프로그램을 실행합니다.")
        super().__init__(parent, **kwargs)
        self.kiwoom = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')  # CLSID
