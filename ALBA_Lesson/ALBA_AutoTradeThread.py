import os.path

from PyQt5.QtCore import *  # 쓰레드 함수를 불러온다.
from ALBA_Kiwoom import Kiwoom
from ALBA_Types import *
from PyQt5.QtWidgets import *
from datetime import datetime

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

        # 중복 요청 막는 용도
        self.buy_ordered_items = []
        self.sell_ordered_items = []

        # 등록된 실시간 요청 데이터 전부 해지하기
        self.kiwoom.ocx.dynamicCall("SetRealRemove(QString, QString)", ["ALL", "ALL"])

        # 실시간 데이터 받기
        self.kiwoom.ocx.OnReceiveRealData.connect(self.receive_realdata)

        # 체결 결과 받기
        self.kiwoom.ocx.OnReceiveChejanData.connect(self.receive_chejandata)

        # 주문 취소한 종목
        self.cancel_buy_order = []
        self.cancel_sell_order = []

        # 선정된 종목 실시간 요청으로 등록하기
        screen_no = 5000

        # 요청!
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

    # 실시간으로 서버에서 데이터를 준다.
    def receive_realdata(self, code, realtype, realdata):
        if realtype == "장시작시간":
            fid = self.realType.REALTYPE[realtype]['장운영구분']

            value = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)

            if value == '0':
                print("장 시작 전")
            elif value == '3':
                print("장 시작")
            elif value == '2':
                print("장 종료, 동시호가")
            elif value == '4':
                print("장 마감")

        # 주식 체결은 반드시 1개의 틱 정보가 변할때만 넘어온다.
        # 같은 가격에서 계속 거래가 발생하면 오지 않는다.
        elif realtype == "주식체결":
            if code not in self.kiwoom.autoTradeData:
                self.kiwoom.autoTradeData.update({code: {}})

            fid1 = self.realType.REALTYPE[realtype]['체결시간']     # 체결시간은 string으로 나온다.
            data1 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid1)

            fid2 = self.realType.REALTYPE[realtype]['현재가']      # 현재가는 +/-로 나온다.
            data2 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid2)

            fid3 = self.realType.REALTYPE[realtype]['전일대비'] # 전일 대비 오르거나 내린 가격
            data3 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid3)

            fid4 = self.realType.REALTYPE[realtype]['등락율']  # 전일 대비 오르거나 내린 퍼센티지
            data4 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid4)

            fid5 = self.realType.REALTYPE[realtype]['(최우선)매도호가']    # 매도쪽에 첫번째 부분(시장가)
            # 최우선 매도호가에 매수를 넣게 되면 시장가와 동일하게 바로 매수된다.
            data5 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid5)

            fid6 = self.realType.REALTYPE[realtype]['(최우선)매수호가']  # 매수쪽에 첫번재 부분(시장가)
            data6 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid6)
            data6 = abs(int(data6))

            fid7 = self.realType.REALTYPE[realtype]['거래량']  # 틱봉의 현재 거래량 (아주 작은 단위)
            data7 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid7)
            data7 = abs(int(data7))

            fid8 = self.realType.REALTYPE[realtype]['누적거래량']
            data8 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid8)
            data8 = abs(int(data8))

            fid9 = self.realType.REALTYPE[realtype]['고가']  # 오늘자 재일 높은 가격
            data9 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid9)
            data9 = abs(int(data9))

            fid10 = self.realType.REALTYPE[realtype]['시가']  # 시가
            data10 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid10)
            data10 = abs(int(data10))

            fid11 = self.realType.REALTYPE[realtype]['저가']  # 전체 제일 낮은 가격
            data11 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid11)
            data11 = abs(int(data11))

            fid12 = self.realType.REALTYPE[realtype]['거래회전율']  # 누적 거래회전율
            data12 = self.kiwoom.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid12)
            data12 = abs(float(data12))

            # 포트폴리오 종목 코드마다 실시간 데이터를 입력 및 업데이트
            self.kiwoom.autoTradeData[code].update({"채결시간": data1})  # 아래 내용을 업데이트
            self.kiwoom.autoTradeData[code].update({"현재가": data2})
            self.kiwoom.autoTradeData[code].update({"전일대비": data3})
            self.kiwoom.autoTradeData[code].update({"등락율": data4})
            self.kiwoom.autoTradeData[code].update({"(최우선)매도호가": data5})
            self.kiwoom.autoTradeData[code].update({"(최우선)매수호가": data6})
            self.kiwoom.autoTradeData[code].update({"거래량": data7})
            self.kiwoom.autoTradeData[code].update({"누적거래량": data8})
            self.kiwoom.autoTradeData[code].update({"고가": data9})
            self.kiwoom.autoTradeData[code].update({"시가": data10})
            self.kiwoom.autoTradeData[code].update({"저가": data11})
            self.kiwoom.autoTradeData[code].update({"거래회전율": data12})

            # 1. 매수 알고리즘 가동
            if self.kiwoom.autoTradeData["현재가"] <= self.kiwoom.autoTradeData["매수가"]:
                if code not in self.buy_ordered_items:
                    print("매수시작 %s : %s" % (code, self.kiwoom.autoTradeData[code]["종목명"]))

                    self.buy_ordered_items.append(code)
                    # 1.사용자구분명, 2.화면번호, 3.계좌번호, 4.주문유형(1.신규매수, 2.신규매도, 3.매수취소, 4.매도취소, 5.매수정정, 6.매도정정)
                    # 5. 종목코드, 6. 주문수량, 7.주문가격, 8.거래구분, 9.원주문번호 (신규주문에는 공백 입력, 정정/취소시 입력)
                    result = self.kiwoom.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
                                                           , "신규매수"
                                                           , self.kiwoom.autoTradeData[code]['주문용스크린번호']
                                                           , self.account_id
                                                           , 1
                                                           , code
                                                           , self.kiwoom.autoTradeData[code]['매수수량']
                                                           , self.kiwoom.autoTradeData[code]['현재가']
                                                           , self.realType.SENDTYPE['거래구분']['지정가']
                                                           , "")

                    f = open("TradeLog.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\n" % ("매수주문정보", self.kiwoom.autoTradeData[code]["종목명"], data2, data1))
                    f.close()
                    
                    if result == 0:
                        print("현재가로 주문 전달 성공")
                    else:
                        print("현재가로 주문 전달 실패")

            # 2. 매도 알고리즘 가동
            # 2-1. 익절
            if self.kiwoom.autoTradeData[code]['현재가'] >= self.kiwoom.autoTradeData[code]['익절가']:
                if code not in self.sell_ordered_items:
                    print("익절 시작 %s : %s" % (code, self.kiwoom.autoTradeData[code]["종목명"]) )

                    self.sell_ordered_items.append(code)
                    result = self.kiwoom.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
                                                           , "신규익절"
                                                           , self.kiwoom.autoTradeData[code]['주문용스크린번호']
                                                           , self.account_id
                                                           , 2
                                                           , code
                                                           , self.kiwoom.autoTradeData[code]['매수수량']
                                                           , self.kiwoom.autoTradeData[code]['현재가']
                                                           , self.realType.SENDTYPE['거래구분']['지정가']
                                                           , "")

                    f = open("TradeLog.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\n" % ("익절주문정보", self.kiwoom.autoTradeData[code]["종목명"], data2, data1))
                    f.close()

                    if result == 0:
                        print("익절가로 주문 전달 성공")
                    else:
                        print("익절가로 주문 전달 실패")

            # 2-2. 손절
            if self.kiwoom.autoTradeData[code]['현재가'] <= self.kiwoom.autoTradeData[code]['손절가']:
                if code not in self.sell_ordered_items:
                    print("손절 시작 %s : %s" % (code, self.kiwoom.autoTradeData[code]["종목명"]) )

                    self.sell_ordered_items.append(code)
                    result = self.kiwoom.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
                                                           , "신규손절"
                                                           , self.kiwoom.autoTradeData[code]['주문용스크린번호']
                                                           , self.account_id
                                                           , 2
                                                           , code
                                                           , self.kiwoom.autoTradeData[code]['매수수량']
                                                           , self.kiwoom.autoTradeData[code]['현재가']
                                                           , self.realType.SENDTYPE['거래구분']['지정가']
                                                           , "")

                    f = open("TradeLog.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\n" % ("손절주문정보", self.kiwoom.autoTradeData[code]["종목명"], data2, data1))
                    f.close()

                    if result == 0:
                        print("손절가로 주문 전달 성공")
                    else:
                        print("손절가로 주문 전달 실패")

            # 3. 미체결 잔고 매수/매도 취소
            not_buy_list = list(self.kiwoom.not_chegual_data)

            for order_no in not_buy_list:
                code = self.kiwoom.not_chegual_data[order_no]['종목코드']
                order_price = self.kiwoom.not_chegual_data[order_no]['주문가격']
                not_chegual_num = self.kiwoom.not_chegual_data[order_no]['미체결수량']
                order_gubun = self.kiwoom.not_chegual_data[order_no]['주문구분']
                
                # 매수에 대한 취소 주문 : 매수주문가격이 현재가보다 작을 경우
                if order_gubun == '매수' and not_chegual_num > 0 and order_price < self.kiwoom.autoTradeData[code]["현재가"]:
                    order_success = self.kiwoom.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
                                                                , ["매수취소"
                                                                    , self.kiwoom.autoTradeData[code]['주문용스크린번호']
                                                                    , self.account_id
                                                                   , 3
                                                                   , code
                                                                   , 0
                                                                   , 0
                                                                   , self.realType.SENDTYPE['거래구분']['지정가']
                                                                   , order_no])
                    
                    if order_success == 0:
                        # 체결 잔고에서 del을 했기 때문에 여기서 하지 않는다.
                        print("%s : %s 매수취소 전달 성공" % (code, self.kiwoom.autoTradeData[code]['종목명']))

                        # 차후 재매수를 위해 필요하다.
                        self.cancel_buy_order.append(code)
                    else:
                        print("%s : %s 매수취소 전달 실패" % (code, self.kiwoom.autoTradeData[code]['종목명']))

                    f = open("CancelOrderLog.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\n" % ('매수취소', self.kiwoom.autoTradeData[code]['종목명'], not_chegual_num, self.kiwoom.autoTradeData[code]['체결시간']))
                    f.close()

                # 미체결 수량이 없을 경우 미체결리스트에서 삭제한다.
                elif not_chegual_num == 0:
                    del self.kiwoom.not_chegual_data[order_no]

                # 매도에 대한 취소 주문 : 매도주문가격이 현재가보다 클 경우
                if order_gubun == '매도' and not_chegual_num > 0 and order_price > self.kiwoom.autoTradeData[code]["현재가"]:
                    order_success = self.kiwoom.ocx.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
                        , ["매도취소"
                            , self.kiwoom.autoTradeData[code]['주문용스크린번호']
                            , self.account_id
                            , 4
                            , code
                            , 0
                            , 0
                            , self.realType.SENDTYPE['거래구분']['지정가']
                            , order_no])

                    if order_success == 0:
                        # 체결 잔고에서 del을 했기 때문에 여기서 하지 않는다.
                        print("%s : %s 매도취소 전달 성공" % (code, self.kiwoom.autoTradeData[code]['종목명']))

                        # 차후 재매도를 위해 필요하다.
                        self.cancel_sell_order.append(code)
                    else:
                        print("%s : %s 매도취소 전달 실패" % (code, self.kiwoom.autoTradeData[code]['종목명']))

                    f = open("CancelOrderLog.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\n" % ('매도취소', self.kiwoom.autoTradeData[code]['종목명'], not_chegual_num,
                                                  self.kiwoom.autoTradeData[code]['체결시간']))
                    f.close()

                # 미체결 수량이 없을 경우 미체결리스트에서 삭제한다.
                elif not_chegual_num == 0:
                    del self.kiwoom.not_chegual_data[order_no]

            # 4. 재매수 알고리즘 : 현재가가 매수 되지 못하였을 경우를 대비하여 재매수 알고리즘 가동
            if code in self.cancel_buy_order:
                if self.kiwoom.autoTradeData[code]['현재가'] <= self.kiwoom.autoTradeData[code]['매수가']:
                    print("재매수 시작 %s : %s" % (code, self.kiwoom.autoTradeData[code]['종목명']))

                    order_success = self.kiwoom.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
                                                           , "신규매수"
                                                           , self.kiwoom.autoTradeData[code]['주문용스크린번호']
                                                           , self.account_id
                                                           , 1
                                                           , code
                                                           , self.kiwoom.autoTradeData[code]['매수수량']
                                                           , self.kiwoom.autoTradeData[code]['현재가']
                                                           , self.realType.SENDTYPE['거래구분']['지정가']
                                                           , "")
                    
                    f = open("TradeLog.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\n" % ("재매수정보", self.kiwoom.autoTradeData[code]['종목명'], data2, self.kiwoom.autoTradeData[code]['체결시간']))
                    f.close()

                    if order_success == 0:
                        print("재매수 주문 전달 성공 %s : %s" % (code, self.kiwoom.autoTradeData[code]['종목명']))
                    else:
                        print("재매수 주문 전달 실패 %s : %s" % (code, self.kiwoom.autoTradeData[code]['종목명']))

                    self.cancel_buy_order.remove(code)
                    # del self.cancel_buy_order[self.cancel_buy_order.index(code)]


            # 5. 재매도 알고리즘 :

    # 체결 정보를 받는다.
    # 주문 접수, 체결통보, 잔고통보를 수신한다.
    def receive_chejandata(self, gubun, item_count, fid_list):
        # (주문접수, 체결통보) = 0, (잔고변경) = 1
        if gubun == "0":
            print("매수/매도 진행 중, 미체결 잔고 업데이트")
        else:
            print("미체결 잔고 해결로 실제 잔고 업데이트")

        print("Fid List : %s" % (str(fid_list)))

        # 주문전송 후 미체결 되었을 때
        if int(gubun) == 0:
            account_id = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            # [A203042] 이런식으로 오기 때문에 앞의 알파벳을 잘라줘야 한다.
            code = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])
            item_name = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명']).strip()

            # 원주문번호가 없으면 0000000이다.
            origin_order_no = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['원주문번호'])

            order_no = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호'])
            
            # 접수/확인/체결 정보
            order_status = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])
            order_num = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량']))
            order_price = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격']))
            not_chegual_num = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['미체결수량']))
            order_gubun: str = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])

            # 부호가 나오기 때문에 잡아주어야 한다.
            order_gubun = order_gubun.lstrip('+').lstrip('-').strip()
            chegual_time: str = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문/체결시간'])
            chegual_price = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결가'])

            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)

            chegual_num = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결량'])

            if chegual_num == '':
                chegual_num = 0
            else:
                chegual_num = int(chegual_num)


            current_price = abs(int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['현재가'])))
            first_sell_price = abs(int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매도호가'])))
            first_buy_price = abs(int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매수호가'])))

            if order_no not in self.kiwoom.not_chegual_data.keys():
                self.kiwoom.not_chegual_data.update({order_no: {}})

            self.kiwoom.not_chegual_data[order_no].update({"종목코드": code})
            self.kiwoom.not_chegual_data[order_no].update({"종목명": item_name})
            self.kiwoom.not_chegual_data[order_no].update({"주문번호": order_no})
            self.kiwoom.not_chegual_data[order_no].update({"주문상태": order_status})
            self.kiwoom.not_chegual_data[order_no].update({"주문수량": order_num})
            self.kiwoom.not_chegual_data[order_no].update({"주문가격": order_price})
            self.kiwoom.not_chegual_data[order_no].update({"주문구분": order_gubun})
            self.kiwoom.not_chegual_data[order_no].update({"미체결수량": not_chegual_num})
            self.kiwoom.not_chegual_data[order_no].update({"체결량": chegual_num})
            self.kiwoom.not_chegual_data[order_no].update({"원주문번호": origin_order_no})
            self.kiwoom.not_chegual_data[order_no].update({"주문/체결시간": chegual_time})
            self.kiwoom.not_chegual_data[order_no].update({"체결가": chegual_price})
            self.kiwoom.not_chegual_data[order_no].update({"현재가": current_price})
            self.kiwoom.not_chegual_data[order_no].update({"(최우선)매도호가": first_sell_price})
            self.kiwoom.not_chegual_data[order_no].update({"(최우선)매수호가": first_buy_price})

            row_count = len(self.kiwoom.not_chegual_data)
            self.gui.chegualTable: QTableWidget
            self.gui.chegualTable.setRowCount(row_count)

            for index in range(row_count):
                self.gui.chegualTable.setItem(index, 0, QTableWidgetItem(str(code)))
                self.gui.chegualTable.setItem(index, 1, QTableWidgetItem(str(item_name)))
                self.gui.chegualTable.setItem(index, 2, QTableWidgetItem(str(format(order_no))))
                self.gui.chegualTable.setItem(index, 3, QTableWidgetItem(str(format(order_status))))
                self.gui.chegualTable.setItem(index, 4, QTableWidgetItem(str(format(order_num, ","))))
                self.gui.chegualTable.setItem(index, 5, QTableWidgetItem(str(format(order_price, ","))))
                self.gui.chegualTable.setItem(index, 6, QTableWidgetItem(str(format(not_chegual_num, ","))))
                
            print("미체결잔고 종목 추가: %s, 수량: %s" % (self.kiwoom.not_chegual_data[order_no]['종목명'], self.kiwoom.not_chegual_data[order_no]['미체결수량']))

        # 잔고 변경
        elif int(gubun) == 1:
            account_no = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
            code = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드'])[1:] # [A203042]
            item_name = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명']).strip()
            current_price = abs(int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])))
            item_num = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량']))
            can_order_num = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량']))
            buy_price = abs(int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])))
            total_buy_price = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가']))
            order_gubun = self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분'])
            order_gubun = self.realType.REALTYPE['매도수구분'][order_gubun]

            first_sell_price = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가']))
            first_buy_price = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가']))
            deposit = int(self.kiwoom.ocx.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['예수금']))

            if code not in self.kiwoom.jango_data.keys():
                self.kiwoom.jango_data.update({code: {}})
            self.kiwoom.jango_data[code].update({"현재가": current_price})
            self.kiwoom.jango_data[code].update({"종목코드": code})
            self.kiwoom.jango_data[code].update({"종목명": item_name})
            self.kiwoom.jango_data[code].update({"보유수량": item_num})
            self.kiwoom.jango_data[code].update({"주문가능수량": can_order_num})
            self.kiwoom.jango_data[code].update({"매입단가": buy_price})
            self.kiwoom.jango_data[code].update({"총매입가": total_buy_price})
            self.kiwoom.jango_data[code].update({"매도매수구분": order_gubun})
            self.kiwoom.jango_data[code].update({"(최우선)매도호가": first_sell_price})
            self.kiwoom.jango_data[code].update({"(최우선)매수호가": first_buy_price})

            # 더 이상 종목에 대한 보유수량이 없을 경우 계좌잔고에서 삭제한다.
            if code in self.kiwoom.accPortfolio.keys() and item_num == 0:
                del self.kiwoom.accPortfolio[code]