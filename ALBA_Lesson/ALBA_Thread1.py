from PyQt5.QtCore import *  # 쓰레드 함수를 불러온다.
from ALBA_Kiwoom import Kiwoom
from PyQt5.QtWidgets import *

# opw00018 계좌평가잔고내역요청
class Thread1(QThread):
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.kiwoom = Kiwoom()  # 멤버로 Kiwoom 클래스 생성
        self.Acc_Screen = 1000  # 스크린은 1~9999까지 총 9999개가 존재하며 1개당 50개의 데이터를 저장할 수 있는 주머니이다.

        self.kiwoom.ocx.OnReceiveTrData.connect(self.resTrData)  # Tr요청시 결과 이벤트를 받을 함수를 연결해준다. 
        self.eventLoop = QEventLoop()  # 계좌 조회 이벤트 루프

        self.getItemList()          # 전체 종목 리스트 가져오기.
        self.reqAccountDetail()

    # 종목 코드 가져오기
    def getItemList(self):
        marketList = ["0", "10"]

        for market in marketList:
            # 12345;67891 이런식으로 결과가 오는데 이것을 ;단위로 자른다.
            codeList = self.kiwoom.ocx.dynamicCall("GetCodeListByMarket(QString)", market).split(";")[:-1]

            # 받아온 종목코드들을 한글로 바꿔준다.
            for code in codeList:
                name = self.kiwoom.ocx.dynamicCall("GetMasterCodeName(QString)", code)
                self.kiwoom.All_Stock_Code.update({code: {"종목명": name}})

    # 계좌 평가 잔고내역 조회
    def reqAccountDetail(self, prevNext: str="0"):
        print("계좌 평가 잔고내역 조회")
        account = self.gui.accComboBox.currentText()  # 콤보박스에서 선택된 계좌 가져오기
        self.account_id = account
        print("선택 계좌는 %s" % self.account_id)

        self.kiwoom.ocx.dynamicCall("SetInputValue(String, String)", "계좌번호", account)
        self.kiwoom.ocx.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.kiwoom.ocx.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.kiwoom.ocx.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        # 1 : 하고싶은 이름, 2: 요청, 3: 30개 이상일 경우 2 입력?, 4: 화면번호
        self.kiwoom.ocx.dynamicCall("CommRqData(String, String, int, String)"
                                    , "계좌평가잔고내역요청", "opw00018", prevNext, self.Acc_Screen)
        self.eventLoop.exec_()

    # TR 결과
    def resTrData(self, screenNo:str, rqName:str, trCode:str, recordName:str, prevNext:str):
        if rqName == "계좌평가잔고내역요청":
            # 싱글데이터 정보 넣기
            totalBuyingPrice = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)"
                                                               , trCode, rqName, 0, "총매입금액"))
            currentTotalPrice = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)"
                                                                , trCode, rqName, 0, "총평가금액"))
            balanceAsset = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)"
                                                           , trCode, rqName, 0, "추정예탁자산"))
            totalEstimateProfit = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)"
                                                                  , trCode, rqName, 0, "총평가손익금액"))
            totalProfieLossRate = float(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)"
                                                                    , trCode, rqName, 0, "총수익률(%)"))

            self.gui.accLabel6.setText(str(totalBuyingPrice))
            self.gui.accLabel7.setText(str(currentTotalPrice))
            self.gui.accLabel8.setText(str(balanceAsset))
            self.gui.accLabel9.setText(str(totalEstimateProfit))
            self.gui.accLabel10.setText(str(totalProfieLossRate))

            # 멀티데이터 정보 넣기
            column_head = ["종목번호", "종목명", "보유수량", "매입가", "현재가", "평가손익", "수익률(%)"]
            colCount = len(column_head)

            # 보유 종목 수를 가져온다.
            rowCount = self.kiwoom.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trCode, rqName)
            self.gui.stockListTable.setColumnCount(colCount)
            self.gui.stockListTable.setRowCount(rowCount)  # 종목 수
            self.gui.stockListTable.setHorizontalHeaderLabels(column_head)  # 행의 이름 삽입

            self.rowCount = rowCount

            print("계좌에 들어있는 종목 수 %s" % rowCount)

            for index in range(rowCount):
                # 종목별 정보를 임시변수에 저장한다.
                itemCode = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "종목번호").strip(" ").strip("A")
                itemName = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "종목명")
                amount = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "보유수량"))
                buyingPrice = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "매입가"))
                currentPrice = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "현재가"))
                estimateProfit = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "평가손익"))
                profitRate = float(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "수익률(%)"))
                totalBuyPrice = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "매입금액").strip())
                possibleQuantity = int(self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index, "매매가능수량").strip())

                # Kiwoom 클래스의 포트폴리오 컨테이너에 정보 갱신
                if itemCode in self.kiwoom.accPortfolio:
                    pass
                else:
                    self.kiwoom.accPortfolio.update({itemCode: {}})

                self.kiwoom.accPortfolio[itemCode].update({"종목명": itemName.strip()})
                self.kiwoom.accPortfolio[itemCode].update({"보유수량": amount})
                self.kiwoom.accPortfolio[itemCode].update({"매입가": buyingPrice})
                self.kiwoom.accPortfolio[itemCode].update({"수익률(%)": profitRate})
                self.kiwoom.accPortfolio[itemCode].update({"현재가": currentPrice})
                self.kiwoom.accPortfolio[itemCode].update({"매입금액": totalBuyPrice})
                self.kiwoom.accPortfolio[itemCode].update({"매매가능수량": possibleQuantity})

                self.gui.stockListTable.setItem(index, 0, QTableWidgetItem(str(itemCode)))
                self.gui.stockListTable.setItem(index, 1, QTableWidgetItem(str(itemName)))
                self.gui.stockListTable.setItem(index, 2, QTableWidgetItem(str(amount)))
                self.gui.stockListTable.setItem(index, 3, QTableWidgetItem(str(buyingPrice)))
                self.gui.stockListTable.setItem(index, 4, QTableWidgetItem(str(currentPrice)))
                self.gui.stockListTable.setItem(index, 5, QTableWidgetItem(str(estimateProfit)))
                self.gui.stockListTable.setItem(index, 6, QTableWidgetItem(str(profitRate)))

            if prevNext == "2":
                self.reqAccountDetail(prevNext="2")         # 다음 페이지가 있으면 전부 검색한다
            else:
                self.eventLoop.exit()  # 끊어 준다.
