import sys  # system specific parameters and functions : 파이썬 스크립트 관리
import os   # 파일 저장용

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *  # GUI의 그래픽적 요소를 제어       하단의 terminal 선택, activate py37_32,  pip install pyqt5,   전부다 y
from PyQt5 import uic  # ui 파일을 가져오기위한 함수
import qdarkstyle

#### 부가 기능 수행(일꾼) ################
from ALBA_Kiwoom import Kiwoom
from ALBA_AccountThread import AccountThread    # 계좌평가잔고내역 가져오기
from ALBA_EvaluateWarningThread import EvaluateWarningThread    # 계좌 관리
from ALBA_AutoTradeThread import AutoTradeThread        # 자동매매 쓰레드

# =================== 프로그램 실행 프로그램 =========================#

form_class = uic.loadUiType("UI.ui")[0]  # 만들어 놓은 ui 불러오기


class Login_Machine(QMainWindow, QWidget, form_class):  # QMainWindow : PyQt5에서 윈도우 생성시 필요한 함수

    searchItemTextEdit: QTextEdit
    buyPriceSpinBox: QDoubleSpinBox
    buyNumSpinBox: QDoubleSpinBox
    profitSpinBox: QDoubleSpinBox
    lossSpinBox: QDoubleSpinBox
    addItemBtn: QPushButton
    removeItemBtn: QPushButton
    buylistTable: QTableWidget
    autoTradeBtn: QPushButton
    accComboBox: QComboBox
    saveItemsBtn: QPushButton
    loadItemsBtn: QPushButton
    deleteFileBtn: QPushButton
    chejanTable: QTableWidget

    def __init__(self, *args, **kwargs):  # Main class의 self를 초기화 한다.
        print("Login Machine 실행합니다.")
        super(Login_Machine, self).__init__(*args, **kwargs)
        form_class.__init__(self)               # 상속 받은 from_class를 실행하기 위한 초기값(초기화)
        self.setUI()                    # UI 초기값 셋업 반드시 필요
        self.login_event_loop = QEventLoop()    # QEventLoop()는 block 기능을 가지고 있다.

        # 키움증권 로그인
        self.kiwoom = Kiwoom()
        self.set_signal_slot()  # 키움로그인을 위한 명령어 전송시 받는 공간을 미리 생성한다.
        self.signal_login_commConnect()
        self.kiwoom.ocx.OnReceiveTrData.connect(self.res_tr_data)

    def setUI(self):
        self.setupUi(self)                       # UI 초기값 셋업
        # 다크 테마 적용
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.accLabel1.setText(str("총매입금액"))
        self.accLabel2.setText(str("총평가금액"))
        self.accLabel3.setText(str("추정예탁자산"))
        self.accLabel4.setText(str("총평가손익금액"))
        self.accLabel5.setText(str("총수익률(%)"))
        self.reqAccBtn.clicked.connect(self.runAccountThread)
        self.accManageBtn.clicked.connect(self.runEvaluateWarningThread)
        self.autoTradeBtn.clicked.connect(self.runAutoTradeThread)

        # TEXT 저장, 로드, 삭제
        self.saveItemsBtn.clicked.connect(self.save_items_to_txt)
        self.loadItemsBtn.clicked.connect(self.load_items_from_txt)
        self.deleteFileBtn.clicked.connect(self.delete_txtfile)

        # 우측 정렬
        self.searchItemTextEdit.setAlignment(Qt.AlignRight)
        self.buyPriceSpinBox.setAlignment(Qt.AlignRight)
        self.buyNumSpinBox.setAlignment(Qt.AlignRight)
        self.profitSpinBox.setAlignment(Qt.AlignRight)
        self.lossSpinBox.setAlignment(Qt.AlignRight)

        # 스핀박스 소수점 제거
        self.buyPriceSpinBox.setDecimals(0)
        self.buyNumSpinBox.setDecimals(0)
        self.profitSpinBox.setDecimals(0)
        self.lossSpinBox.setDecimals(0)

        # 종목 선택하기 : 새로운 종목 추가 및 삭제
        self.addItemBtn.clicked.connect(self.search_item)
        self.removeItemBtn.clicked.connect(self.remove_item)
        column_head = ["종목코드", "종목명", "현재가", "신용비율", "매수가", "매수수량", "익절가", "손절가"]
        col_count = len(column_head)
        # 행 갯수
        self.buylistTable.setColumnCount(col_count)
        # 행의 이름 삽입
        self.buylistTable.setHorizontalHeaderLabels(column_head)

        column_head = ["종목코드", "종목명", "주문번호", "주문상태", "주문수량", "주문가격", "미체결수량"]
        col_count = len(column_head)
        self.chejanTable.setColumnCount(col_count)
        self.chejanTable.setHorizontalHeaderLabels(column_head)

    def set_signal_slot(self):
        self.kiwoom.ocx.OnEventConnect.connect(self.login_slot)  # 커넥트 결과를 login_slot 함수로 전달

    # 로그인 처리
    def signal_login_commConnect(self):
        self.kiwoom.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def login_slot(self, errCode):
        if errCode == 0:
            print("로그인 성공")
            self.statusbar.showMessage("로그인 성공")
            self.get_account_info()                     # 로그인시 계좌정보 가져오기

        elif errCode == 100:
            print("사용자 정보교환 실패")
        elif errCode == 101:
            print("서버접속 실패")
        elif errCode == 102:
            print("버전처리 실패")

        self.login_event_loop.exit()                     # 로그인이 완료되면 로그인 창을 닫는다.

    # 계좌번호 가져오기
    def get_account_info(self):
        account_list = self.kiwoom.ocx.dynamicCall("GetLoginInfo(String)", "ACCNO")

        for acc in account_list.split(';'):
            self.accComboBox.addItem(acc)

    def runAccountThread(self):
        print("선택 계좌 정보 가져오기")
        h1 = AccountThread(self)
        h1.start()

    def runEvaluateWarningThread(self):
        print("계좌 관리 쓰레드 시작!")
        h2 = EvaluateWarningThread(self)
        h2.start()

    def runAutoTradeThread(self):
        print("자동 매매 쓰레드 시작!")
        h3 = AutoTradeThread(self)
        h3.start()

    def save_items_to_txt(self):
        codeset = set()  # 중복 방지
        f = open("TradeItems.txt", "a", encoding="utf8")  # "a" = append
        for row in range(self.buylistTable.rowCount()):
            code = self.buylistTable.item(row, 0).text()
            if codeset.__contains__(code) or code == "":
                continue
            else:
                codeset.add(code)
            name = self.buylistTable.item(row, 1).text().strip()
            price = self.buylistTable.item(row, 2).text()
            credit_ratio = self.buylistTable.item(row, 3).text()
            buy_price = self.buylistTable.item(row, 4).text()
            buy_num = self.buylistTable.item(row, 5).text()
            profit_price = self.buylistTable.item(row, 6).text()
            loss_price = self.buylistTable.item(row, 7).text()
            f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (code, name, price, credit_ratio, buy_price, buy_num, profit_price, loss_price))
        f.close()

    def load_items_from_txt(self):
        if not os.path.exists("TradeItems.txt"):
            return

        f = open("TradeItems.txt", "r", encoding="utf8")
        load_items = []
        lines = f.readlines()
        for line in lines:
            if line != "":  # 만약에 line이 비어 있지 않으면 탭으로 구분
                splits = line.split("\t")
                code = splits[0]
                name = splits[1]
                price = splits[2]
                credit_ratio = splits[3]
                buy_price = splits[4]
                buy_num = splits[5]
                profit_price = splits[6]
                loss_price = splits[7]
                load_items.append([code, name, price, credit_ratio, buy_price, buy_num, profit_price, loss_price])

        f.close()

        row_count = len(load_items)
        self.buylistTable.setRowCount(row_count)
        self.buylistTable.setSelectionMode(QAbstractItemView.SingleSelection)

        for index in range(row_count):
            for col in range(0, 8):
                self.buylistTable.setItem(index, col, QTableWidgetItem(str(load_items[index][col])))

    def delete_txtfile(self):
        if os.path.exists("TradeItems.txt"):
            os.remove("TradeItems.txt")

    def search_item(self):
        item_name: str = self.searchItemTextEdit.toPlainText()
        new_code: str = ""
        if item_name != "":
            for code in self.kiwoom.All_Stock_Code.keys():
                # 주식 정보 가져오기
                if item_name == self.kiwoom.All_Stock_Code[code]['종목명']:
                    new_code = code

        self.get_item_info(new_code)

    def remove_item(self):
        index_list = []
        selected_indexes = self.buylistTable.selectedIndexes()
        for model_index in selected_indexes:
            # QPersistentModelIndex는 QModelIndex와 달리
            # 항목에 대한 참조가 모델에서 엑세스 할 수 있는한 계속 유효하도록 보장한다.
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        for index in index_list:
            self.buylistTable.removeRow(index.row())

    # 주식기본정보요청 (opt10001)
    def get_item_info(self, code):
        self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보요청", "opt10001", 0, "100")

    def res_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next):
        # 주식기본정보요청
        if tr_code == "opt10001":
            if rq_name == "주식기본정보요청":
                code = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "종목코드").strip()
                if not code:
                    print("존재하지 않는 종목입니다.")
                    return

                item_name = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0,
                                                   "종목명").strip()
                current_price = abs(int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "현재가")))
                # [      +3000] -> [+3000]  strip으로 공백 없애기
                credit_ratio = (self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "신용비율")).strip()
                row_count = self.buylistTable.rowCount()

                self.buylistTable.setRowCount(row_count + 1)
                self.buylistTable.setItem(row_count, 0, QTableWidgetItem(code))
                self.buylistTable.setItem(row_count, 1, QTableWidgetItem(item_name))
                self.buylistTable.setItem(row_count, 2, QTableWidgetItem(str(current_price)))
                self.buylistTable.setItem(row_count, 3, QTableWidgetItem(credit_ratio))
                self.buylistTable.setItem(row_count, 4, QTableWidgetItem(str(int(self.buyPriceSpinBox.value()))))
                self.buylistTable.setItem(row_count, 5, QTableWidgetItem(str(int(self.buyNumSpinBox.value()))))
                self.buylistTable.setItem(row_count, 6, QTableWidgetItem(str(int(self.profitSpinBox.value()))))
                self.buylistTable.setItem(row_count, 7, QTableWidgetItem(str(int(self.lossSpinBox.value()))))

                # 우측, 수직 가운데 정렬
                for i in range(0, 8):
                    self.buylistTable.item(row_count, i).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)

                self.buylistTable.resizeRowsToContents()
                self.buylistTable.resizeColumnsToContents()




if __name__ == '__main__':                  # import된 것들을 실행시키지 않고 __main__에서 실행하는 것만 실행 시킨다.
                                            # 즉 import된 다른 함수의 코드를 이 화면에서 실행시키지 않겠다는 의미이다.
    app = QApplication(sys.argv)         # PyQt5로 실행할 파일명을 자동으로 설정, PyQt5에서 자동으로 프로그램 실행
    CH = Login_Machine()               # Main 클래스 myApp으로 인스턴스화
    CH.show()                           # myApp에 있는 ui를 실행한다.
    app.exec_()                          # 이벤트 루프
