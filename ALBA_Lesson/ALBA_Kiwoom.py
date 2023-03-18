from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5Singleton import Singleton


# Kiwoom 클래스는 싱글톤 클래스이다.
class Kiwoom(QWidget, metaclass=Singleton):     # QMainWindow : PyQt5에서 윈도우 생성시 필요한 함수
    def __init__(self, parent=None, **kwargs):  # Main class의 self를 초기화 한다.
        print("로그인 프로그램을 실행합니다.")
        super().__init__(parent, **kwargs)
        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')  # CLSID

        # 전체 공유 데이터
        self.All_Stock_Code = {}    # 코스피, 코스닥 전체 코드 리스트
        self.accPortfolio = {}  # 계좌에 들어있는 종목의 코드, 수익률 등등 입력
        self.autoTradeData = {}

        self.not_chegual_data = {}  # 미체결 정보
        self.jango_data = {}  # 잔고 데이터 정보
        self.kospi = 0.0
        self.kosdaq = 0.0
