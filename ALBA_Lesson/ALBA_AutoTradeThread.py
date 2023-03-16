import os.path

from PyQt5.QtCore import *  # 쓰레드 함수를 불러온다.
from ALBA_Kiwoom import Kiwoom
from ALBA_Types import *
from PyQt5.QtWidgets import *


class AutoTradeThread(QThread):
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.kiwoom = Kiwoom()  # 멤버로 Kiwoom 클래스 생성
        self.account_id = self.gui.accComboBox.currentText()

        # txt로부터 아이템들 읽어와서 딕셔너리에 등록
        self.load_items_from_txt()
        # 필요한 FID 번호들
        self.realType = RealType()

        # 등록된 실시간 요청 데이터 전부 해지하기
        self.kiwoom.ocx.dynamicCall("SetRealRemove(QString, QString)", ["ALL", "ALL"])

        # 선정된 종목 실시간 요청으로 등록하기
        screen_no = 5000

        for code in self.kiwoom.autoTradeData.keys():
            fid = self.realType.REALTYPE['주식체결']['체결시간']
            # 체결시간만 fid로 해서 요청해도 기타 모든 데이터들을 받을 수 있다.
            self.kiwoom.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, code, fid, "1")
            screen_no += 1

    def load_items_from_txt(self):
        if not os.path.exists("TradeItems.txt"):
            return

        f = open("TradeItems.txt", "r", encoding="utf8")
        lines = f.readlines()   # 여러 종목이 저장되어 있다면 모든 항목을 가져온다.
        screen = 4000

        for line in lines:
            if line == "":
                continue

            splits = line.split("\t")
            code = splits[0]
            name = splits[1]
            current_price = splits[2]
            credit_ratio = splits[3]
            buy_price = splits[4]
            buy_num = splits[5]
            profit_price = splits[6]
            loss_price = splits[7].split("\n")[0]

            self.kiwoom.autoTradeData.update({code: {"종목명": name}})
            self.kiwoom.autoTradeData[code].update({"현재가": int(current_price)})
            self.kiwoom.autoTradeData[code].update({"신용비율": credit_ratio})
            self.kiwoom.autoTradeData[code].update({"매수가": int(buy_price)})
            self.kiwoom.autoTradeData[code].update({"매수수량": int(buy_num)})
            self.kiwoom.autoTradeData[code].update({"익절가": int(profit_price)})
            self.kiwoom.autoTradeData[code].update({"손절가": int(loss_price)})
            self.kiwoom.autoTradeData[code].update({"주문용스크린번호": screen})
            screen += 1

        f.close()
