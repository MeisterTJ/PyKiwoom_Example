from PyQt5.QtCore import *  # eventloop, thread를 사용할 수 있는 함수 가져옴
from ALBA_Kiwoom import Kiwoom
from PyQt5.QtWidgets import *
from PyQt5.QtTest import *  # 시간 관련 함수
from datetime import datetime, timedelta  # 특정 일자를 조회


# opt10045 : 종목별기관매매추이요청
class Thread2(QThread):
    def __init__(self, gui):
        super().__init__(gui)
        self.FluctuationRateData = None
        self.EstimateAvgPriceData = None
        self.foreignTradePerDayData = None
        self.companyTradePerDayData = None
        self.gui = gui
        self.kiwoom = Kiwoom()

        self.Find_Down_Screen = "1200"  # 50개가 넘어가면 스크린 번호를 1201로 바꾸어야 한다.
        self.codeInAll = None  # 계좌에 있는 종목 코드를 임시로 저장하는 객체이다.

        self.kiwoom.ocx.OnReceiveTrData.connect(self.res_tr_data)  # Tr요청시 결과 이벤트를 받을 함수를 연결해준다.
        self.eventLoop = QEventLoop()  # 계좌 조회 이벤트 루프

        # 종목별 기관매매추이 요청 및 위험도 검사
        self.req_company_foreign_sales_by_stock()

        # 결과 GUI에 출력
        column_head = ["종목코드", "종목명", "위험도"]
        col_count = len(column_head)
        row_count = len(self.kiwoom.accPortfolio)
        self.gui.stockWarningTable.setColumnCount(col_count)
        self.gui.stockWarningTable.setRowCount(row_count)
        self.gui.stockWarningTable.setHorizontalHeaderLabels(column_head)

        for index, code in enumerate(self.kiwoom.accPortfolio.keys()):
            self.gui.stockWarningTable.setItem(index, 0, QTableWidgetItem(str(code)))
            self.gui.stockWarningTable.setItem(index, 1, QTableWidgetItem(self.kiwoom.accPortfolio[code]["종목명"]))
            self.gui.stockWarningTable.setItem(index, 2, QTableWidgetItem(self.kiwoom.accPortfolio[code]["위험도"]))

    def req_company_foreign_sales_by_stock(self):
        code_list = []

        for code in self.kiwoom.accPortfolio.keys():
            code_list.append(code)

        print("계좌 종목 개수 %s" % code_list)

        # enumerator 함수를 사용하여 codeList에 있는 코드 번호들에 번호를 부여하여 하나씩 나열시킨다.
        # [1, 12345], [2, 45678]... 라는 형식으로 코드 번호가 들어간다.
        for index, code in enumerate(code_list):
            # 키움 서버에 짧은 시간안에 너무 많은 명령을 전송하면 계좌가 일시 정지한다.
            # 따라서 시간 지연이 필요하다.
            QTest.qWait(1000)

            # 기존에 명령된 스크린에 대한 접속을 끊는 역할을 한다.
            # 하나의 스크린에 50개 이상의 주문이 들어가게 되면 에러가 발생할 수 있으므로
            # 한번 주문마다 이전 주문에 대한 기록을 끊는 것도 효율적이다.
            # 혹은 10~49개의 주문마다 스크린 번호를 바꿔주거나 끊어주는 것도 답이다.
            self.kiwoom.ocx.dynamicCall("DisconnectRealData(QString)", self.Find_Down_Screen)  # 해당 스크린을 끊고 다시 시작

            self.codeInAll = code  # 종목코드 선언 (중간에 코드 정보 받아오기 위해서)
            print("%s / %s : 종목 검사 중 코드이름 : %s." % (index + 1, len(code_list), self.codeInAll))

            date_today = datetime.today().strftime("%Y%m%d")
            date_prev = datetime.today() - timedelta(10)  # 넉넉히 10일전의 데이터를 받아온다.
            date_prev = date_prev.strftime("%Y%m%d")

            # SetInputValue와 CommRqData는 한몸이라 생각하면 편하다.
            self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "시작일자", date_prev)
            self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "종료일자", date_today)
            self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "기관추정단가구분", "1")
            self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "외인추정단가구분", "1")
            self.kiwoom.ocx.dynamicCall("CommRqData(String, String, int, String)", "종목별기관매매추이요청", "opt10045", "0",
                                        self.Find_Down_Screen)
            self.eventLoop.exec_()

    def res_tr_data(self, screenNo: str, rqName: str, trCode: str, recordName: str, prevNext: str):
        if rqName == "종목별기관매매추이요청":
            row_count = self.kiwoom.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trCode,
                                                    rqName)  # 10일치 이상을 하려면 이부분에 10일치 이상 데이터 필요

            self.companyTradePerDayData = []
            self.foreignTradePerDayData = []
            self.EstimateAvgPriceData = []
            self.FluctuationRateData = []

            for index in range(row_count):  #

                company_trade_amount_per_day = (
                    self.kiwoom.ocx.dynamicCall("GetCommData(String, String, int, String)", trCode, rqName, index,
                                                "기관일별순매매수량"))
                company_estimate_avg_price = (
                    self.kiwoom.ocx.dynamicCall("GetCommData(String, String, int, String)", trCode, rqName, 0,
                                                "기관추정평균가"))
                foreign_trade_amount_per_day = (
                    self.k.kiwoom.dynamicCall("GetCommData(String, String, int, String)", trCode, rqName, index,
                                              "외인일별순매매수량"))
                foreign_estimate_avg_price = (
                    self.k.kiwoom.dynamicCall("GetCommData(String, String, int, String)", trCode, rqName, 0,
                                              "외인추정평균가"))
                fluctuation_rate = (
                    self.k.kiwoom.dynamicCall("GetCommData(String, String, int, String)", trCode, rqName, index, "등락율"))
                closing_price = (
                    self.k.kiwoom.dynamicCall("GetCommData(String, String, int, String)", trCode, rqName, index, "종가"))

                self.companyTradePerDayData.append(int(company_trade_amount_per_day.strip()))
                self.foreignTradePerDayData.append(abs(int(foreign_trade_amount_per_day.strip())))
                self.EstimateAvgPriceData.append(abs(int(closing_price.strip())))
                self.EstimateAvgPriceData.append(abs(int(company_estimate_avg_price.strip())))
                self.EstimateAvgPriceData.append(int(foreign_estimate_avg_price.strip()))
                self.FluctuationRateData.append(float(fluctuation_rate.strip()))

            # 위험도 계산 함수 호출
            self.calculate_warning(self.companyTradePerDayData, self.foreignTradePerDayData)
            self.eventLoop.exit()

    # 기관, 외국인 매매 동향으로 계좌위험도 판단 함수를 코딩.
    def calculate_warning(self, companyData, foreignData):
        # 10일치의 데이터중 4일치만 판단하는 간단한 로직
        if companyData[0] < 0 and companyData[1] < 0 and companyData[2] < 0 and companyData[3] < 0 \
                and foreignData[0] < 0 and foreignData[1] < 0 and foreignData[2] < 0 and foreignData[3] < 0:
            self.k.acc_portfolio[self.code_in_all].update({"위험도": "손절"})

        elif companyData[0] < 0 and companyData[1] < 0 and companyData[2] < 0 \
                and foreignData[0] < 0 and foreignData[1] < 0 and foreignData[2] < 0:
            self.k.acc_portfolio[self.code_in_all].update({"위험도": "주의"})

        elif companyData[0] < 0 and companyData[1] < 0 and foreignData[0] < 0 and foreignData[1] < 0:
            self.k.acc_portfolio[self.code_in_all].update({"위험도": "관심"})
        else:
            self.k.acc_portfolio[self.code_in_all].update({"위험도": "낮음"})
