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

        # 기관매매추이동향을 위한 변수들
        self.Find_Down_Screen = "1200"  # 50개가 넘어가면 스크린 번호를 1201로 바꾸어야 한다.
        self.codeInAll = None  # 계좌에 있는 종목 코드를 임시로 저장하는 객체이다.

        # 일봉차트를 위한 변수
        self.DayChart_Screen = "1400"
        self.day_chart_data = []  # 받아온 종목의 다양한 값 (현재가/고가/저가 등)을 계산한다.
        self.day_chart_filter = []  # 역배열인지 확인
        self.day_chart_current_price = []  # 미래예측

        self.kiwoom.ocx.OnReceiveTrData.connect(self.res_tr_data)  # Tr요청시 결과 이벤트를 받을 함수를 연결해준다.
        self.eventLoop = QEventLoop()  # 계좌 조회 이벤트 루프

        # 종목별 기관매매추이 요청 및 위험도 검사
        self.req_company_foreign_sales_by_stock()

        # 역배열 평가
        self.req_evaluate_inverse_arrangement()

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
            self.gui.stockWarningTable.setItem(index, 3, QTableWidgetItem(self.kiwoom.accPortfolio[code]["역배열"]))

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

    # 기관, 외국인 매매 동향으로 계좌위험도 판단 함수를 코딩.
    def evaluate_warning(self, companyData, foreignData):
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

    # 역배열 평가 함수
    def req_evaluate_inverse_arrangement(self):
        code_list = []
        for code in self.kiwoom.accPortfolio.keys():
            code_list.append(code)

        print("계좌 종목 개수 %s" % code_list)

        for index, code in enumerate(code_list):
            QTest.qWait(1000)
            self.codeInAll = code

            print("%s 종목 검사 중 코드 : %s" % (index + 1, self.codeInAll))

            self.kiwoom.ocx.dynamicCall("DisconnectRealData(QString)", self.DayChart_Screen)
            self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.kiwoom.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")  # 0: 액면분할 포함X, 1: 액면분할 포함
            self.kiwoom.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", "0",
                                        self.DayChart_Screen)
            self.eventLoop.exec_()

    # tr 결과
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
            self.evaluate_warning(self.companyTradePerDayData, self.foreignTradePerDayData)
            self.eventLoop.exit()

        elif rqName == "주식일봉차트조회":
            code = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, 0, "종목코드")
            code = code.strip()  # 여백 발생 방지
            row_count = self.kiwoom.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trCode, rqName)

            # GetCommDataEx를 쓰면 for문을 쓰지 않고 멀티데이터를 다 받아올 수 있으나 학습 목적으로 for문 사용

            for index in range(row_count):  # 0 ~ 599 : 최대 600일치가 넘어온다.
                data = []
                current_price = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode,
                                                            rqName, index, "현재가")
                trade_amount = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode,
                                                           rqName, index, "거래량")
                trade_total_price = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode,
                                                                rqName, index, "거래대금")
                date = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName, index,
                                                   "일자")  # 접수, 확인, 체결
                start_price = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName,
                                                          index, "시가")
                high_price = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName,
                                                         index, "고가")
                low_price = self.kiwoom.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, rqName,
                                                        index, "저가")

                data.append("")  # 빈칸을 만들어주는 이유는 GetCommDataEx 함수의 반환값과 동일하게 하기 위해서
                data.append(current_price.strip())
                data.append(trade_amount.strip())
                data.append(trade_total_price.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append("")

                self.day_chart_current_price.append(int(current_price.strip()))
                self.day_chart_data.append(data.copy())  # 리스트로 데이터가 들어간다.

            if self.day_chart_data is None or len(self.day_chart_data) < 120:
                self.kiwoom.accPortfolio[self.codeInAll].update({"역배열": "데이터 없음"})
            else:
                total_five_price = []
                total_twenty_price = []

                for k in range(10):
                    # 5일 이평선 정보를 채워넣는다.
                    total_five_price.append(sum(self.day_chart_current_price[k: 5 + k]) / 5)
                for k in range(10):
                    # 20일 이평선 정보를 채워넣는다.
                    total_twenty_price.append(sum(self.day_chart_current_price[k: 20 + k]) / 20)

                add_item = 0

                # 현재가 < 20일 이평선, 5일선 < 20일선일경우 역으로 판단, 8개 이상일 경우 역배열로 판단한다.
                for k in range(10):
                    if float(total_five_price[k]) < float(total_twenty_price[k]) \
                            and float(self.day_chart_current_price[k]) < float(total_twenty_price[k]):
                        add_item += 1
                    else:
                        pass

                if add_item >= 8:
                    self.kiwoom.accPortfolio[self.codeInAll].update({"역배열": "맞음"})
                else:
                    self.kiwoom.accPortfolio[self.codeInAll].update({"역배열": "아님"})

            self.day_chart_data.clear()
            self.day_chart_current_price.clear()
            self.eventLoop.exit()
