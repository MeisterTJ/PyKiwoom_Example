ver = "#version 1.3.10"
print(f"simulator_func_mysql Version: {ver}")
import sys
is_64bits = sys.maxsize > 2**32
if is_64bits:
    print('64bit 환경입니다.')
else:
    print('32bit 환경입니다.')

from sqlalchemy import event

import pymysql.cursors

from .logging_pack import *
from . import cf
from pandas import DataFrame
import re
import datetime
from sqlalchemy import create_engine

pymysql.install_as_MySQLdb()


class simulator_func_mysql:
    # ex) 1, 'real', Jackbot1_imi1
    def __init__(self, simul_num, option, db_name):
        self.simul_num = int(simul_num)

        # scraper할 때 start date 가져오기 위해서
        if self.simul_num == -1:
            self.date_setting()

        # option이 reset일 경우 실행
        elif option == 'reset':
            self.op = 'reset'
            self.simul_reset = True
            self.db_name = db_name
            self.variable_setting()
            self.rotate_date()

        # option이 real일 경우 실행(시뮬레이터와 무관)
        elif option == 'real':
            self.op = 'real'
            self.simul_reset = False
            self.db_name = db_name
            self.variable_setting()

        #  option이 continue 일 경우 실행
        elif option == 'continue':
            self.op = 'continue'
            self.simul_reset = False
            self.db_name = db_name
            self.variable_setting()
            self.rotate_date()
        else:
            print("simul_num or option 어느 것도 만족 하지 못함 simul_num : %s ,option : %s !!", simul_num, option)

    # 마지막으로 구동했던 시뮬레이터의 날짜를 가져온다.
    def get_jango_data_last_date(self):
        sql = "SELECT date from jango_data order by date desc limit 1"
        return self.engine_simulator.execute(sql).fetchall()[0][0]

    # 모든 테이블을 삭제 하는 함수
    def delete_table_data(self):
        logger.info('delete_table_data !!!!')
        if self.is_simul_table_exist(self.db_name, "all_item_db"):
            sql = "drop table all_item_db"
            self.engine_simulator.execute(sql)
            # 만약 jango data 컬럼을 수정하게 되면 테이블을 삭제하고 다시 생성이 자동으로 되는데 이때 삭제했으면 delete가 안먹힌다. 그래서 확인 후 delete

        if self.is_simul_table_exist(self.db_name, "jango_data"):
            sql = "drop table jango_data"
            self.engine_simulator.execute(sql)

        if self.is_simul_table_exist(self.db_name, "realtime_daily_buy_list"):
            sql = "drop table realtime_daily_buy_list"
            self.engine_simulator.execute(sql)

    # realtime_daily_buy_list 테이블의 check_item컬럼에 특정 종목의 매수 시간을 넣는 함수
    def update_realtime_daily_buy_list(self, code, min_date):
        sql = "update realtime_daily_buy_list set check_item = '%s' where code = '%s'"
        self.engine_simulator.execute(sql % (min_date, code))

    # 시뮬레이션 옵션 설정 함수
    # 날짜 설정, 데이터베이스 초기화 및 설정도 여기서 한다.
    def variable_setting(self):
        # 아래 if문으로 들어가기 전까지의 변수들은 모든 알고리즘에 공통적으로 적용 되는 설정
        # 오늘 날짜를 설정
        self.date_setting()

        # 시뮬레이팅이 끝나는 날짜.
        self.simul_end_date = self.today
        self.start_min = "0900"

        # 아래 3개는 분별시뮬레이션 옵션
        # (use_min, only_nine_buy 변수만 각각의 알고리즘에 붙여 넣기 해서 사용)
        # 분별 시뮬레이션을 사용하고 싶을 경우 아래 옵션을 True로 변경하여 사용
        self.use_min = False
        # 아침 9시에만 매수를 하고 싶은 경우 True, 9시가 아니어도 매수를 하고 싶은 경우 False(분별 시뮬레이션 적용 가능 / 일별 시뮬레이션은 9시에만 매수, 매도)
        # 일별일 경우에는 중간에 매도를 통해 돈이 생길 경우 9시가 아니어도 매수가 가능하도록 한다.
        self.only_nine_buy = True
        # self.buy_stop옵션은 수정 필요가 없음. self.only_nine_buy 옵션을 True로 하게 되면 시뮬레이터가 9시에 매수 후에 self.buy_stop을 true로 변경해서 당일에는 더이상 매수하지 않도록 설정함
        self.buy_stop = False

        # AI알고리즘 사용 여부 (고급 챕터에서 소개)
        self.use_ai = False  # ai 알고리즘 사용 시 True 사용 안하면 False
        self.ai_filter_num = 1  # ai 알고리즘 선택

        # 실시간 조건 매수 옵션 (고급 챕터에서 소개)
        # self.only_nine_buy 옵션을 반드시 False로 설정해야함
        # self.use_min 옵션이 반드시 True로 설정이 되어야함
        # 실시간 조건 매수 알고리즘 선택 (1,2,3..)
        self.trade_check_num = False

        print("self.simul_num!!! ", self.simul_num)

        # ##!@####################################################################################################################
        # 아래 부터는 알고리즘 별로 별도의 설정을 해주는 부분
        # 1번 알고리즘을 돌리겠다.
        if self.simul_num in (1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
            # 시뮬레이팅 시작 일자(분 별 시뮬레이션의 경우 최근 1년 치 데이터만 있기 때문에 start_date 조정 필요)
            self.simul_start_date = "20190101"

            # ######## 알고리즘 선택 #############
            # 매수 리스트 설정 알고리즘 번호
            self.db_to_realtime_daily_buy_algo_num = 1

            # 매도 리스트 설정 알고리즘 번호
            self.sell_list_num = 1
            ###################################

            # 초기 투자자금
            self.start_invest_price = 10000000

            # 매수 금액
            self.invest_unit = 100000

            # 자산 중 최소로 남겨 둘 금액
            self.limit_money = 3000000

            # 익절 수익률 기준치
            self.sell_point = 10

            # 손절 수익률 기준치
            self.losscut_point = -2

            # 실전/모의 봇 돌릴 때 매수하는 순간 종목의 최신 종가 보다 1% 이상 오른 경우 사지 않도록 하는 설정(변경 가능)
            self.invest_limit_rate = 1.01
            # 실전/모의 봇 돌릴 때 매수하는 순간 종목의 최신 종가 보다 -2% 이하로 떨어진 경우 사지 않도록 하는 설정(변경 가능)
            self.invest_min_limit_rate = 0.98

            if self.simul_num == 4:
                self.db_to_realtime_daily_buy_algo_num = 4
                self.interval_month = 3
                self.invest_unit = 50000

            elif self.simul_num == 5:
                self.db_to_realtime_daily_buy_algo_num = 5
                self.total_transaction_price = 10000000000
                self.interval_month = 3
                self.vol_mul = 3
                self.d1_diff = 2
                # self.use_min= True
                # self.only_nine_buy = False

            elif self.simul_num == 6:
                self.db_to_realtime_daily_buy_algo_num = 6

            # 절대 모멘텀 / 상대 모멘텀
            elif self.simul_num in (7, 8, 9, 10):
                # 매수 리스트 설정 알고리즘 번호(절대모멘텀 code ver)
                self.db_to_realtime_daily_buy_algo_num = 7
                # 매도 리스트 설정 알고리즘 번호(절대모멘텀 code ver)
                self.sell_list_num = 4
                # 시뮬레이팅 시작 일자(분 별 시뮬레이션의 경우 최근 1년 치 데이터만 있기 때문에 start_date 조정 필요)
                self.simul_start_date = "20200101"
                # n일 전 종가 데이터를 가져올지 설정 (ex. 20 -> 장이 열리는 날 기준 20일 이니까 기간으로 보면 약 한 달, 250일->1년)
                self.day_before = 20  # 단위 일
                # n일 전 종가 대비 현재 종가(현재가)가 몇 프로 증가 했을 때 매수, 몇 프로 떨어졌을 때 매도 할 지 설정(0으로 설정 시 단순히 증가 했을 때 매수, 감소 했을 때 매도)
                self.diff_point = 1  # 단위 %
                # 분별 시뮬레이션 옵션
                # self.use_min = True
                # self.only_nine_buy = True

                if self.simul_num == 8:
                    # 매수 리스트 설정 알고리즘 번호 (절대모멘텀 query ver)
                    self.db_to_realtime_daily_buy_algo_num = 8
                    # 매도 리스트 설정 알고리즘 번호 (절대모멘텀 query ver)
                    self.sell_list_num = 5

                elif self.simul_num == 9:
                    # 매수 리스트 설정 알고리즘 번호 (절대모멘텀 query ver)
                    self.db_to_realtime_daily_buy_algo_num = 8
                    # 매도 리스트 설정 알고리즘 번호 (절대모멘텀 query ver + losscut point 추가)
                    self.sell_list_num = 6
                    # 손절 수익률 기준치
                    self.losscut_point = -2

                elif self.simul_num == 10:
                    # 매수 리스트 설정 알고리즘 번호 (상대모멘텀 query ver)
                    self.db_to_realtime_daily_buy_algo_num = 9
                    # 매도 리스트 설정 알고리즘 번호 (절대모멘텀 query ver + losscut point 추가)
                    self.sell_list_num = 5

            elif self.simul_num == 11:
                self.use_ai = True  # ai 알고리즘 사용 시 True 사용 안하면 False
                self.ai_filter_num = 1  # ai 알고리즘 선택

            # 실시간 조건 매수
            elif self.simul_num in (12, 13, 14):
                self.simul_start_date = "20200101"
                self.use_min = True
                # 아침 9시에만 매수를 하고 싶은 경우 True, 9시가 아니어도 매수를 하고 싶은 경우 False(분별 시뮬레이션, trader 적용 가능 / 일별 시뮬레이션은 9시에만 매수, 매도)
                self.only_nine_buy = False
                # 실시간 조건 매수 옵션 (고급 챕터에서 소개) self.only_nine_buy 옵션을 반드시 False로 설정해야함
                self.trade_check_num = 1  # 실시간 조건 매수 알고리즘 선택 (1,2,3..)
                # 특정 거래대금 보다 x배 이상 증가 할 경우 매수
                self.volume_up = 2
                #
                if self.simul_num == 13:
                    self.trade_check_num = 2
                    # 매수하는 순간 종목의 최신 종가 보다 1% 이상 오른 경우 사지 않도록 하는 설정(변경 가능)
                    self.invest_limit_rate = 1.01
                    # 매수하는 순간 종목의 최신 종가 보다 -2% 이하로 떨어진 경우 사지 않도록 하는 설정(변경 가능)
                    self.invest_min_limit_rate = 0.0

                # 래리윌리엄스 변동성 돌파 전략
                elif self.simul_num == 14:
                    self.trade_check_num = 3
                    self.rarry_k = 0.5

        elif self.simul_num == 2:
            # 시뮬레이팅 시작 일자
            self.simul_start_date = "20240101"

            # ######## 알고리즘 선택 #############
            # 매수 리스트 설정 알고리즘 번호
            self.db_to_realtime_daily_buy_algo_num = 1
            # 매도 리스트 설정 알고리즘 번호 : 데드크로스
            self.sell_algo_num = 2
            ###################################
            # 초기 투자자금
            # 주의! start_invest_price 는 모의투자 초기 자본금과 별개. 시뮬레이션에서만 적용.
            # 키움증권 모의투자의 경우 초기에 모의투자 신청 할 때 설정 한 금액으로 자본금이 설정됨
            self.start_invest_price = 10000000
            # 매수 금액
            self.invest_unit = 1000000

            # 자산 중 최소로 남겨 둘 금액
            self.limit_money = 1000000
            # # 익절 수익률 기준치
            self.sell_point = False
            # 손절 수익률 기준치
            self.losscut_point = -2
            # 실전/모의 봇 돌릴 때 매수하는 순간 종목의 최신 종가 보다 1% 이상 오른 경우 사지 않도록 하는 설정(변경 가능)
            self.invest_limit_rate = 1.01
            # 실전/모의 봇 돌릴 때 매수하는 순간 종목의 최신 종가 보다 -2% 이하로 떨어진 경우 사지 않도록 하는 설정(변경 가능)
            self.invest_min_limit_rate = 0.98

        elif self.simul_num == 3:
            # 시뮬레이팅 시작 일자
            self.simul_start_date = "20240101"

            # ######## 알고리즘 선택 #############
            # 매수 리스트 설정 알고리즘 번호
            self.db_to_realtime_daily_buy_algo_num = 3

            # 매도 리스트 설정 알고리즘 번호 : 데드크로스
            self.sell_algo_num = 2

            ###################################

            # 초기 투자자금
            # 주의! start_invest_price 는 모의투자 초기 자본금과 별개. 시뮬레이션에서만 적용.
            # 키움증권 모의투자의 경우 초기에 모의투자 신청 할 때 설정 한 금액으로 자본금이 설정됨
            self.start_invest_price = 10000000

            # 매수 금액
            self.invest_unit = 3000000

            # 자산 중 최소로 남겨 둘 금액
            self.limit_money = 1000000

            # 익절 수익률 기준치
            self.sell_point = 10

            # 손절 수익률 기준치
            self.losscut_point = -2

            # 실전/모의 봇 돌릴 때 매수하는 순간 종목의 최신 종가 보다 1% 이상 오른 경우 사지 않도록 하는 설정(변경 가능)
            self.invest_limit_rate = 1.01
            # 실전/모의 봇 돌릴 때 매수하는 순간 종목의 최신 종가 보다 -2% 이하로 떨어진 경우 사지 않도록 하는 설정(변경 가능)
            self.invest_min_limit_rate = 0.98
        else:
            logger.error(
                f"입력 하신 {self.simul_num}번 알고리즘에 대한 설정이 없습니다. simulator_func_mysql.py 파일의 variable_setting함수에 알고리즘을 설정해주세요. ")
            sys.exit(1)

        #########################################################################################################################
        # db 이름으로 연결
        self.db_name_setting()

        # 'reset'
        if self.op != 'real':
            # database, table 초기화 함수
            self.table_setting()

            # 시뮬레이팅 할 날짜를 가져 오는 함수
            self.get_date_for_simul()

            # 매도를 한 종목들 대상 수익
            self.total_valuation_profit = 0

            # 실제 수익 : 매도를 한 종목들 대상 수익 + 현재 보유 중인 종목들의 수익
            self.sum_valuation_profit = 0

            # 전재산 : 투자금액 + 실제 수익(self.sum_valuation_profit)
            self.total_invest_price = self.start_invest_price

            # 현재 총 투자한 금액
            self.total_purchase_price = 0

            # 현재 투자 가능한 금액(예수금) = (초기자본 + 매도한 종목의 수익) - 현재 총 투자 금액
            self.d2_deposit = self.start_invest_price

            # 일별 정산 함수
            self.check_balance()

            # 매수할때 수수료 한번, 매도할때 전체금액에 세금, 수수료
            self.tax_rate = 0.0025
            self.fees_rate = 0.00015

            # 시뮬레이터를 멈춘 지점 부터 다시 돌리기 위해 사용하는 변수(중요X)
            self.simul_reset_lock = False

    # 데이터베이스와 테이블을 세팅하기 위한 함수
    def table_setting(self):
        print("self.simul_reset" + str(self.simul_reset))

        # 시뮬레이터를 초기화 하고 처음부터 구축하기 위한 로직
        # option이 reset일 경우 True이다.
        if self.simul_reset:
            print("table reset setting !!! ")
            self.init_database()
        # 시뮬레이터를 초기화 하지 않고 마지막으로 끝난 시점 부터 구동하기 위한 로직
        else:
            # self.simul_reset 이 False이고, 시뮬레이터 데이터베이스와, all_item_db 테이블, jango_table이 존재하는 경우 이어서 시뮬레이터 시작
            if self.is_simul_database_exist() and self.is_simul_table_exist(self.db_name,
                                                                            "all_item_db") and self.is_simul_table_exist(
                    self.db_name, "jango_data"):
                self.init_df_jango()
                self.init_df_all_item()
                # 마지막으로 구동했던 시뮬레이터의 날짜를 가져온다.
                self.last_simul_date = self.get_jango_data_last_date()
                print("self.last_simul_date: " + str(self.last_simul_date))
            #    초반에 reset 으로 돌다가 멈춰버린 경우 다시 init 해줘야함
            else:
                print("초반에 reset 으로 돌다가 멈춰버린 경우 다시 init 해줘야함 ! ")
                self.init_database()
                self.simul_reset = True

    # 데이터베이스 초기화 함수
    def init_database(self):
        self.drop_database()
        self.create_database()
        self.init_df_jango()
        self.init_df_all_item()

    # 데이터베이스를 생성하는 함수
    def create_database(self):
        if self.is_simul_database_exist() == False:
            sql = 'CREATE DATABASE %s'
            self.db_conn.cursor().execute(sql % (self.db_name))
            # commit을 하지 않으면 변경 사항은 메모리에만 머무른다.
            self.db_conn.commit()

    # 데이터베이스를 삭제하는 함수
    def drop_database(self):
        # 데이터 베이스가 있을 경우에만 삭제
        if self.is_simul_database_exist():
            print("drop!!!!")
            sql = "drop DATABASE %s"
            self.db_conn.cursor().execute(sql % (self.db_name))
            # commit을 하지 않으면 변경 사항은 메모리에만 머무른다.
            self.db_conn.commit()

    # 데이터베이스의 존재 유무를 파악하는 함수.
    def is_simul_database_exist(self):
        # Information_schema.SCHEMATA 는 표준 SQL 시스템 뷰이다.
        # 현재 데이터베이스 서버에 존재하는 모든 데이터베이스 스키마의 정보를 포함한다.
        # SELECT 1은 특정 조건을 만족하는 행이 있는지만 확인하기 위한 목적으로 데이터를 반환하지 않는다. 만족하면 1을 반환한다.
        sql = "SELECT 1 FROM Information_schema.SCHEMATA WHERE SCHEMA_NAME = '%s'"
        rows = self.engine_daily_buy_list.execute(sql % (self.db_name)).fetchall()
        print("rows : ", rows)
        if len(rows):   # rows : [(1,}]
            return True
        else:  # rows : []
            return False

    # 오늘 날짜를 설정하는 함수
    def date_setting(self):
        self.today = datetime.datetime.today().strftime("%Y%m%d")
        self.today_detail = datetime.datetime.today().strftime("%Y%m%d%H%M")
        self.today_date_form = datetime.datetime.strptime(self.today, "%Y%m%d").date()

    # DB 이름 세팅 함수
    def db_name_setting(self):
        # 여기서 현재 db_name은 0이다.
        self.engine_simulator = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/" + str(
                self.db_name),
            encoding='utf-8')

        # 실전 및 모의 투자가 아닐 경우 : 시뮬레이터
        if self.op != "real":
            # db_name을 setting 한다.
            # db_name은 simulator1 이나 simualtor2 등이 되겠지.
            self.db_name = "simulator" + str(self.simul_num)
            self.engine_simulator = create_engine(
                "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/" + str(
                    self.db_name), encoding='utf-8')

        self.engine_daily_craw = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/daily_craw",
            encoding='utf-8')

        self.engine_craw = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/min_craw",
            encoding='utf-8')
        self.engine_daily_buy_list = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/daily_buy_list",
            encoding='utf-8')

        # before_excute는 SQLAlchemy의 이벤트 중 하나로, 데이터베이스에 SQL 쿼리가 실행되기 전에 호출된다.
        # escape_percentage는 이벤트 발생 시 실행될 함수이다.
        event.listen(self.engine_simulator, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_craw, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_craw, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_buy_list, 'before_execute', escape_percentage, retval=True)

        # 특정 데이터 베이스가 아닌, mysql 에 접속하는 객체
        # SQLAlchemy 라이브러리가 아닌 PyMySQL 라이브러리
        self.db_conn = pymysql.connect(host=cf.db_ip, port=int(cf.db_port), user=cf.db_id, password=cf.db_passwd,
                                       charset='utf8')

    # 매수 함수
    def invest_send_order(self, date, code, code_name, price, yes_close, j):
        # print("invest_send_order!!!")
        # 시작가가 투자하려는 금액 보다 작아야 매수가 가능하기 때문에 아래 조건
        if price < self.invest_unit:
            print(code_name, " 매수!!!!!!!!!!!!!!!")

            # 매수를 하게 되면 all_item_db 테이블에 반영을 한다. (append를 한다.)
            self.db_to_all_item(date, self.df_realtime_daily_buy_list, j,
                                code,
                                code_name, price,
                                yes_close)

            # 매수를 성공적으로 했으면 realtime_daily_buy_list 테이블의 check_item 에 매수 시간을 설정
            self.update_realtime_daily_buy_list(code, date)

            # 일별, 분별 정산 함수
            self.check_balance()

    # code명으로 code_name을 가져오는 함수
    def get_name_by_code(self, code):
        sql = "select code_name from stock_item_all where code = '%s'"
        code_name = self.engine_daily_buy_list.execute(sql % (code)).fetchall()
        print(code_name)
        if code_name:
            return code_name[0][0]
        else:
            return False

    # 실제 매수하는 함수, min_date : 시와 분까지 포함된 날짜
    def auto_trade_stock_realtime(self, min_date, date_rows_today, date_rows_yesterday):
        print("auto_trade_stock_realtime 함수에 들어왔다!!")
        # self.df_realtime_daily_buy_list 에 있는 모든 종목들을 매수한다
        for j in range(self.len_df_realtime_daily_buy_list):
            if self.jango_check():
                # 종목 코드를 가져온다.
                code = str(self.df_realtime_daily_buy_list.loc[j, 'code']).rjust(6, "0")

                # 종목명을 가져온다.
                code_name = self.df_realtime_daily_buy_list.loc[j, 'code_name']

                # (촬영 후 추가 코드) 매수 들어가기전에 db에 테이블이 존재하는지 확인
                # 분별 시뮬레이팅 인 경우
                if self.use_min:
                    # print("code_name!!", code_name)
                    # min_craw db에 종목이 없으면 매수 하지 않는다.
                    if not self.is_min_craw_table_exist(code_name):
                        continue
                # 일별 시뮬레이팅 인 경우
                else:
                    # daily_craw db에 종목이 없으면 매수 하지 않는다.
                    if not self.is_daily_craw_table_exist(code_name):
                        continue

                # 아래 if else 구문은 영상 촬영 후 수정 하였습니다. open_price 를 가져오는 것을 분별/일별 시뮬레이션 구분하여 설정하였습니다.
                # 분별 시뮬레이션이 아닌 일별 시뮬레이션의 경우
                if not self.use_min:
                    # 매수 당일 시작가를 가져온다.
                    price = self.get_now_open_price_by_date(code, date_rows_today)
                # 분별 시뮬레이션의 경우
                else:
                    # 매수 시점의 가격을 가져온다.
                    price = self.get_now_close_price_by_min(code_name, min_date)

                # 어제 종가를 가져온다.
                yes_close = self.get_yes_close_price_by_date(code, date_rows_yesterday)

                # False는 데이터가 없는것
                if code_name == False or price == 0 or price == False:
                    continue

                # 촬영 후 아래 if 문 추가 (향후 실시간 조건 매수 시 사용) ###################
                if self.use_min and not self.only_nine_buy and self.trade_check_num:
                    # 시작가
                    open = self.get_now_open_price_by_date(code, date_rows_today)
                    # 당일 누적 거래량
                    sum_volume = self.get_now_volume_by_min(code_name, min_date)

                    # open, sum_volume 값이 존재 할 경우
                    if open and sum_volume:
                        # 매수 할 종목에 대한 dataframe row와, 시작가, 현재가, 분별 누적 거래량 정보를 전달
                        if not self.trade_check(self.df_realtime_daily_buy_list.loc[j], open, price, sum_volume):
                            # 실시간 매수 조건에 맞지 않는 경우 pass
                            continue
                ################################################################

                # 매수 주문에 들어간다.
                self.invest_send_order(min_date, code, code_name, price, yes_close, j)
            else:
                break

    # 최근 daily_buy_list의 날짜 테이블에서 code에 해당 하는 row만 가져오는 함수
    def get_daily_buy_list_by_code(self, code, date):
        # print("get_daily_buy_list_by_code 함수에 들어왔습니다!")

        sql = "select * from `" + date + "` where code = '%s'"

        daily_buy_list = self.engine_daily_buy_list.execute(sql % (code)).fetchall()

        df_daily_buy_list = DataFrame(daily_buy_list,
                                      columns=['index', 'index2', 'date', 'check_item',
                                               'code', 'code_name', 'd1_diff_rate', 'close', 'open',
                                               'high', 'low',
                                               'volume',
                                               'clo5', 'clo10', 'clo20', 'clo40', 'clo60', 'clo80',
                                               'clo100', 'clo120',
                                               "clo5_diff_rate", "clo10_diff_rate", "clo20_diff_rate",
                                               "clo40_diff_rate", "clo60_diff_rate",
                                               "clo80_diff_rate", "clo100_diff_rate",
                                               "clo120_diff_rate",
                                               'yes_clo5', 'yes_clo10', 'yes_clo20', 'yes_clo40',
                                               'yes_clo60',
                                               'yes_clo80',
                                               'yes_clo100', 'yes_clo120',
                                               'vol5', 'vol10', 'vol20', 'vol40', 'vol60', 'vol80',
                                               'vol100', 'vol120'])
        return df_daily_buy_list

    # realtime_daily_buy_list 테이블의 매수 리스트를 가져오는 함수
    def get_realtime_daily_buy_list(self):
        print("get_realtime_daily_buy_list 함수에 들어왔습니다!")

        # 이 부분은 촬영 후 코드를 간소화 했습니다. 조건문 모두 없앴습니다.
        # check_item = 매수 했을 시 날짜가 찍혀 있다. 매수 하지 않았을 때는 0
        sql = "select * from realtime_daily_buy_list where check_item = '%s' order by volume"

        realtime_daily_buy_list = self.engine_simulator.execute(sql % (0)).fetchall()

        self.df_realtime_daily_buy_list = DataFrame(realtime_daily_buy_list,
                                                    columns=['index', 'index2', 'index3', 'date', 'check_item',
                                                             'code', 'code_name', 'd1_diff_rate', 'close', 'open',
                                                             'high', 'low',
                                                             'volume',
                                                             'clo5', 'clo10', 'clo20', 'clo40', 'clo60', 'clo80',
                                                             'clo100', 'clo120',
                                                             "clo5_diff_rate", "clo10_diff_rate", "clo20_diff_rate",
                                                             "clo40_diff_rate", "clo60_diff_rate",
                                                             "clo80_diff_rate", "clo100_diff_rate",
                                                             "clo120_diff_rate",
                                                             'yes_clo5', 'yes_clo10', 'yes_clo20', 'yes_clo40',
                                                             'yes_clo60',
                                                             'yes_clo80',
                                                             'yes_clo100', 'yes_clo120',
                                                             'vol5', 'vol10', 'vol20', 'vol40', 'vol60', 'vol80',
                                                             'vol100', 'vol120'])

        self.len_df_realtime_daily_buy_list = len(self.df_realtime_daily_buy_list)

    # 가장 최근의 daily_buy_list에 담겨 있는 날짜 테이블 이름을 가져오는 함수
    def get_recent_daily_buy_list_date(self):
        sql = "select TABLE_NAME from information_schema.tables where table_schema = 'daily_buy_list' and TABLE_NAME like '%s' order by table_name desc limit 1"
        row = self.engine_daily_buy_list.execute(sql % ("20%%")).fetchall()

        if len(row) == 0:
            return False
        return row[0][0]

    # 실시간 주가 분석 알고리즘 함수 (느낌표 골뱅이 추가하면 검색 시 편합니다) (고급클래스에서 소개)
    def trade_check(self, df_row, open_price, current_price, current_sum_volume):
        '''
        :param df_row: 매수 종목 리스트(realtime_daily_buy_list)
        :param current_price: (현재가)
        :param current_sum_volume: (현재 누적 거래량)
        :return: True (매수), False(매수 X)
        '''
        code_name = df_row['code_name']
        yes_vol20 = df_row['vol20']
        yes_close = df_row['close']
        yes_high = df_row['high']
        yes_low = df_row['low']
        yes_volume = df_row['volume']

        # 실시간 거래 대금 체크 알고리즘
        if self.trade_check_num == 1:
            # 어제 거래 대금
            yes_total_tr_price = yes_close * yes_volume
            # 현재 거래 대금
            current_total_tr_price = current_price * current_sum_volume 
            # 어제 종가 보다 현재가가 증가했고, 거래 대금이 어제 거래대금에 비해서 x배 올라갔을 때 매수
            if current_price > yes_close and current_total_tr_price > yes_total_tr_price * self.volume_up:
                return True
            else:
                return False

        elif self.trade_check_num == 2:
            # 매수 가격 최저 범위
            min_buy_limit = int(yes_close) * self.invest_min_limit_rate
            # 매수 가격 최고 범위
            max_buy_limit = int(yes_close) * self.invest_limit_rate
            # 현재가가 매수 가격 최저 범위와 매수 가격 최고 범위 안에 들어와 있다면 매수 한다.
            if min_buy_limit < current_price < max_buy_limit:
                return True
            else:
                return False

        # 래리 윌리엄스 변동성 돌파 알고리즘(매수)
        elif self.trade_check_num == 3:
            # 변동폭(_range): 전일 고가(yes_high)에서 전일 저가(yes_low)를 뺀 가격
            # 매수시점 : 현재가 > 시작가 + (변동폭 * k)  [k는 0~1 사이 수]
            _range = yes_high - yes_low
            if open_price + _range * self.rarry_k < current_price:
                return True
            else:
                return False

        else:
            logger.debug("trade_check 함수에 self.trade_check_num = {} 에 맞는 알고리즘이 없습니다. ".format(self.trade_check_num))
            exit(1)

    # 여기서 sql문의 date는 반드시 어제 일자여야 한다. -> 어제 일자 기준 반영된 데이터로 종목을 선정해야함.
    # #!@####################################################################################################################################################################################
    # 매수 할 종목의 리스트를 선정 알고리즘
    # date_rows_yesterday의 날짜를 기반으로 사기로 결정한 종목들을 date_rows_today에 매수한다는 개념.
    def db_to_realtime_daily_buy_list(self, date_rows_today, date_rows_yesterday, i):
        # 5일선 / 20일선 골든크로스 buy
        if self.db_to_realtime_daily_buy_algo_num == 1:
            # orderby는 거래량 많은 순서
            # 목적은 5일선이 20일선을 돌파한 골든 크로스 종목들을 거래량 순서대로 나열하는것 같은데 아래의 쿼리가 잘못된 것 같다.
            # 각 종목들은 kospi, kosdaq, konex 등등이 있다. 코넥스는 봇에서 매도가 잘 안되는 경험이 있다고 했다. 그렇기 때문에 stock_konex 테이블에 있는 종목들은 매수하지 않는다는 뜻이다.
            # 앞의 쿼리를 a로 묶고 뒤의 쿼리를 b로 묶었을때 a의 코드가 b의 코드가 같은 경우가 없을 때 매수를 한다는 뜻이다. b를 sub query라고 한다.
            # sql = "select * from `" + date_rows_yesterday + "` a where yes_clo20 > yes_clo5 and clo5 > clo20 " \
            #                                                 "and NOT exists (select null from stock_konex b where a.code=b.code) " \
            #                                                 "and close < '%s' group by code"
            sql = "select * from `" + date_rows_yesterday + "` a where yes_clo20 > yes_clo5 and clo5 > clo20 " \
                                                            "and NOT exists (select null from stock_konex b where a.code=b.code) " \
                                                            "and close < '%s' order by volume"
            realtime_daily_buy_list = self.engine_daily_buy_list.execute(sql % (self.invest_unit)).fetchall()

        # 5일선 / 40일선 골든크로스 buy
        elif self.db_to_realtime_daily_buy_algo_num == 2:
            # orderby는 거래량 많은 순서
            # 목적은 5일선이 40일선을 돌파한 골든 크로스 종목들을 거래량 순서대로 나열하는것 같은데 아래의 쿼리가 잘못된 것 같다.
            # sql = "select * from `" + date_rows_yesterday + "` a where yes_clo40 > yes_clo5 and clo5 > clo40 " \
            #                                                 "and NOT exists (select null from stock_konex b where a.code=b.code) " \
            #                                                 "and close < '%s' group by code"
            # group by code를 통해서 중복된 코드를 하나로 묶겠다는 의도인데, 하나로 묶을때 나머지 column의 값들을 어떤 것으로 표시해야될지 알 수 없기 때문에 에러가 나게 된다.

            sql = "select * from `" + date_rows_yesterday + "` a where yes_clo40 > yes_clo5 and clo5 > clo40 " \
                                                            "and NOT exists (select null from stock_konex b where a.code=b.code) " \
                                                            "and close < '%s' order by volume"
            realtime_daily_buy_list = self.engine_daily_buy_list.execute(sql % (self.invest_unit)).fetchall()

        # 1일차 대비 1% 이상 상승한 종목들 중 거래량이 많은 순서대로 매수
        elif self.db_to_realtime_daily_buy_algo_num == 3:
            # sql = "select * from `" + date_rows_yesterday + "` a where d1_diff_rate > 1 " \
            #                                                 "and NOT exists (select null from stock_konex b where a.code=b.code) " \
            #                                                 "and close < '%s' group by code"
            sql = "select * from `" + date_rows_yesterday + "` a where d1_diff_rate > 1 " \
                                                            "and NOT exists (select null from stock_konex b where a.code=b.code) " \
                                                            "and close < '%s' order by volume"
            # 아래 명령을 통해 테이블로 부터 데이터를 가져오면 리스트 형태로 realtime_daily_buy_list 에 담긴다.
            realtime_daily_buy_list = self.engine_daily_buy_list.execute(sql % (self.invest_unit)).fetchall()

        # 절대 모멘텀 전략 : 특정일 전의 종가 보다 n% 이상 상승한 종목 매수 (code version)
        elif self.db_to_realtime_daily_buy_algo_num == 7:
            # 아래에서 필터링 된 매수종목을 append 해주기 위해 비어있는 리스트를 만들어준다.
            realtime_daily_buy_list = []
            if i < self.day_before + 1:
                pass
            else:
                sql = "SELECT * FROM `" + date_rows_yesterday + "` a " \
                      "WHERE NOT exists (SELECT null FROM stock_konex b WHERE a.code=b.code) " \
                      "AND close < '%s' "
                # realtime_daily_buy_list_temp 로 일단 위 조건의 종목을을받는다.
                realtime_daily_buy_list_temp = self.engine_daily_buy_list.execute(sql % (self.invest_unit)).fetchall()
                for row in realtime_daily_buy_list_temp:
                    # 종목코드
                    code = row[4]
                    # 어제 종가
                    yes_close = row[7]
                    # date_rows_yesterday 가 self.date_rows[i-1] 값이다.
                    # 어제 일자 기준 n 일전 날짜
                    date_before = self.date_rows[i - 1 - self.day_before][0]
                    # 어제 일자 기준 n 일전 종가
                    date_before_close = self.get_now_close_price_by_date(code, date_before)
                    # n 일전 종가가 0이 아니고 값이 있을 경우
                    if date_before_close != 0 and date_before_close != False:
                        # 모멘텀 계산 : n일전 종가 대비 수익률
                        diff_point_calc = (yes_close - date_before_close) / date_before_close * 100
                        # 모멘텀(수익률)이 self.diff_point 보다 높을 경우 realtime_daily_buy_list에 append
                        # 모멘텀이 오르는 주식은 더 오른다에 기초하기 때문에 높이 오른 주식을 매수한다.
                        if diff_point_calc > self.diff_point:
                            realtime_daily_buy_list.append(row)

        # 절대 모멘텀 전략 : 특정일 전의 종가 보다 n% 이상 상승한 종목 매수 (query vesrion)
        elif self.db_to_realtime_daily_buy_algo_num == 8:
            if i < self.day_before + 1:
                realtime_daily_buy_list = []
                pass
            else:
                # date_before와 date_rows_yesterday는 BEFORE_DAY와 YES_DAY라는 alias로 참조가 된다.
                # 별칭을 사용하여 쿼리의 가독성을 높이고, 테이블 이름을 줄일 수 있다.
                date_before = self.date_rows[i - 1 - self.day_before][0]
                sql = "SELECT YES_DAY.* " \
                      "FROM `" + date_before + "` BEFORE_DAY, `" + date_rows_yesterday + "` YES_DAY "\
                    "WHERE BEFORE_DAY.code = YES_DAY.code "\
                    "AND (YES_DAY.close - BEFORE_DAY.close) / BEFORE_DAY.close * 100 > '%s' " \
                    "AND NOT exists (SELECT null FROM stock_konex b WHERE YES_DAY.code=b.code)" \
                    "AND YES_DAY.close < '%s'"
                realtime_daily_buy_list = self.engine_daily_buy_list.execute(
                    sql % (self.diff_point, self.invest_unit)).fetchall()
        # 상대 모멘텀 전략 : 특정일 전의 종가 보다 n% 이상 상승한 종목 중 가장 많이 상승한 종목 순으로 매수 (내림차순) (query version)
        # 절대 모멘텀과 다른 점은 ORDER BY 하나가 추가된 것이다. 모멘텀 순으로 정렬을 해준다.
        # 100을 곱하는 이유는 수익률을 백분율로 표현하기 위해서이다.
        elif self.db_to_realtime_daily_buy_algo_num == 9:
            if i < self.day_before + 1:
                realtime_daily_buy_list = []
                pass
            else:
                date_before = self.date_rows[i - 1 - self.day_before][0]
                sql = "SELECT YES_DAY.* " \
                      "FROM `" + date_before + "` BEFORE_DAY, `" + date_rows_yesterday + "` YES_DAY " \
                    "WHERE BEFORE_DAY.code = YES_DAY.code " \
                    "AND (YES_DAY.close - BEFORE_DAY.close) / BEFORE_DAY.close * 100 > '%s' " \
                    "AND NOT exists (SELECT null FROM stock_konex b WHERE YES_DAY.code=b.code)" \
                    "AND YES_DAY.close < '%s'" \
                    "ORDER BY (YES_DAY.close - BEFORE_DAY.close) / BEFORE_DAY.close * 100 DESC"       
                realtime_daily_buy_list = self.engine_daily_buy_list.execute(
                    sql % (self.diff_point, self.invest_unit)).fetchall()

        ######################################################################################################################################################################################
        else:
            print(f"{self.simul_num}번 알고리즘에 대한 self.db_to_realtime_daily_buy_algo_num 설정이 비었습니다. variable_setting 함수에서 self.db_to_realtime_daily_buy_algo_num 을 확인해주세요.")
            sys.exit(1)

        # realtime_daily_buy_list 에 종목이 하나라도 있다면, 즉 매수할 종목이 하나라도 있다면 아래 로직을 들어간다.
        if len(realtime_daily_buy_list) > 0:
            # realtime_daily_buy_list 라는 리스트를 df_realtime_daily_buy_list 라는 데이터프레임으로 변환하는 과정
            # 차이점은 리스트는 컬럼에 대한 개념이 없는데, 데이터프레임은 컬럼이 있다.
            # 리스트가 갖고 있는 각 값들을 df의 columns에 대입해서 그 위치에 맞게 넣어준다.
            df_realtime_daily_buy_list = DataFrame(realtime_daily_buy_list,
                                                   columns=['index', 'index2', 'date', 'check_item', 'code',
                                                            'code_name', 'd1_diff_rate', 'close', 'open', 'high',
                                                            'low', 'volume',
                                                            'clo5', 'clo10', 'clo20', 'clo40', 'clo60', 'clo80',
                                                            'clo100', 'clo120',
                                                            "clo5_diff_rate", "clo10_diff_rate", "clo20_diff_rate",
                                                            "clo40_diff_rate", "clo60_diff_rate", "clo80_diff_rate",
                                                            "clo100_diff_rate", "clo120_diff_rate",
                                                            'yes_clo5', 'yes_clo10', 'yes_clo20', 'yes_clo40',
                                                            'yes_clo60',
                                                            'yes_clo80',
                                                            'yes_clo100', 'yes_clo120',
                                                            'vol5', 'vol10', 'vol20', 'vol40', 'vol60', 'vol80',
                                                            'vol100', 'vol120'])

            # lamda는 익명 함수이다. 여기서 int로 param을 보내야 6d ( 정수) 에서 안걸린다.
            df_realtime_daily_buy_list['code'] = df_realtime_daily_buy_list['code'].apply(
                lambda x: "{:0>6d}".format(int(x)))

            # 시뮬레이터의 경우 : reset일 경우
            if self.op != 'real':
                df_realtime_daily_buy_list['check_item'] = int(0)
                # [to_sql]
                # df_realtime_daily_buy_list 라는 데이터프레임을
                # simulator 데이터베이스의 realtime_daily_buy_list 테이블로 만들어주는 명령
                #
                # ** if_exists 옵션 **
                # # 데이터베이스에 테이블이 존재할 때 수행 동작을 지정한다.
                # 'fail', 'replace', 'append' 중 하나를 사용할 수 있는데 기본값은 'fail'이다.
                # 'fail'은 데이터베이스에 테이블이 있다면 아무 동작도 수행하지 않는다.
                # 'replace'는 테이블이 존재하면 기존 테이블을 삭제하고 새로 테이블을 생성한 후 데이터를 삽입한다.
                # 'append'는 테이블이 존재하면 데이터만을 추가한다.
                # 'realtime_daily_buy_list 는 테이블의 이름이다.
                # dataframe을 테이블로 한방에 만들어주는 것이다.
                df_realtime_daily_buy_list.to_sql('realtime_daily_buy_list', self.engine_simulator, if_exists='replace')

                # 현재 보유 중인 종목은 매수 리스트(realtime_daily_buy_list) 에서 제거 하는 로직
                # 보유하고 있는데 또 사려고 하면 안되니까 삭제.
                # 오늘 매수하였거나, 매도 날짜가 0이거나(아직 안팔고 갖고 있음), 오늘 매도한 종목들은 제외하고 싶다.
                if self.is_simul_table_exist(self.db_name, "all_item_db"):
                    sql = "delete from realtime_daily_buy_list where code in (select code from all_item_db where sell_date = '%s' or buy_date = '%s' or sell_date = '%s')"
                    # delete는 리턴 값이 없기 때문에 fetchall 쓰지 않는다.
                    self.engine_simulator.execute(sql % (0, date_rows_today, date_rows_today))

                # 영상 촬영 후 추가 된 코드입니다. AI챕터에서 다룰 예정입니다.
                if self.use_ai:
                    from ai_filter import ai_filter
                    # 기존 로직은 그대로 사용을 하되 ai_filter를 통해서 오를 것 같지 않은 종목들을 추가로 필터링한다.
                    # ai_filter를 통해서 나온 필터 결과들을 daily_buy_list db에서 삭제한다.
                    ai_filter(self.ai_filter_num, engine=self.engine_simulator, until=date_rows_yesterday)

                # 최종적으로 realtime_daily_buy_list 테이블에 저장 된 종목들을 가져와서 멤버에 넣는다.
                self.get_realtime_daily_buy_list()

            # 모의, 실전 투자 봇 의 경우 'real' 일 경우
            else:
                # check_item 컬럼에 0 으로 setting
                df_realtime_daily_buy_list['check_item'] = int(0)
                df_realtime_daily_buy_list.to_sql('realtime_daily_buy_list', self.engine_simulator, if_exists='replace')

                # 매수 대기 종목들 중에서 현재 보유 중인 종목들은 삭제한다.
                sql = "delete from realtime_daily_buy_list where code in (select code from possessed_item)"
                self.engine_simulator.execute(sql)

        # 매수할 종목이 없으면, df_realtime_daily_buy_list라는 데이터프레임의 길이를 저장하는
        # len_df_realtime_daily_buy_list에 다가 0을 넣는다.
        else:
            self.len_df_realtime_daily_buy_list = 0
            # 강의 촬영 후 추가 코드 (매수 조건에 맞는 종목이 하나도 없을 경우 realtime_daily_buy_list 를 비워준다)
            # dialect 객체는 데이터베이스의 특정 기능을 확인하거나 사용할 수 있게 해준다.
            if self.engine_simulator.dialect.has_table(self.engine_simulator, "realtime_daily_buy_list"):
                self.engine_simulator.execute("""
                    DELETE FROM realtime_daily_buy_list 
                """)

    # 현재의 주가를 all_item_db에 있는 보유한 종목들에 대해서 반영 한다.
    def db_to_all_item_present_price_update(self, code_name, d1_diff_rate, close, open, high, low, volume, clo5, clo10, clo20,
                                            clo40, clo60, clo80, clo100, clo120, option='ALL'):
        # 영상 촬영 후 아래 내용 업데이트 하였습니다.
        if self.op == 'real':  # 콜렉터에서 업데이트 할 때는 현재가를 종가로 업데이트(trader에서 실시간으로 present_price 업데이트함)
            present_price = close
        else:
            present_price = open  # 시뮬레이터에서는 open가를 현재가로 업데이트, 종가로 안하고 open으로 한 이유는 그냥 강의하는 사람의 스타일이라고 한다. 

        # option이 ALL이면 모든 데이터 업데이트
        if option == "ALL":
            sql = f"update all_item_db set d1_diff_rate = {d1_diff_rate}, close = {close}, open = {open}, high = {high}, " \
                  f"low = {low}, volume = {volume}, present_price = {present_price}, clo5 = {clo5}, clo10 = {clo10}, clo20 = {clo20}, " \
                  f"clo40 = {clo40}, clo60 = {clo60}, clo80 = {clo80}, clo100 = {clo100}, clo120 = {clo120} " \
                  f"where code_name = '{code_name}' and sell_date = {0}"
        # option이 OPEN이면 open, present_price 만 업데이트
        else:
            sql = f"update all_item_db set open = {open}, present_price = {present_price} where code_name = '{code_name}' and sell_date = {0}"

        self.engine_simulator.execute(sql)

    # jango_data 라는 테이블을 만들기 위한 self.jango 데이터프레임을 생성
    def init_df_jango(self):
        jango_temp = {'id': []}

        # 이것은 컬럼을 만들어주는 작업이다.
        self.jango = DataFrame(jango_temp,
                               columns=['date', 'today_earning_rate', 'sum_valuation_profit', 'total_profit',
                                        'today_profit',
                                        'today_profitcut_count', 'today_losscut_count', 'today_profitcut',
                                        'today_losscut',
                                        'd2_deposit', 'total_possess_count', 'today_buy_count', 'today_buy_list_count',
                                        'today_reinvest_count',
                                        'today_cant_reinvest_count',
                                        'total_asset',
                                        'total_invest',
                                        'sum_item_total_purchase', 'total_evaluation', 'today_rate',
                                        'today_invest_price', 'today_reinvest_price',
                                        'today_sell_price', 'volume_limit', 'reinvest_point', 'sell_point',
                                        'max_reinvest_count', 'invest_limit_rate', 'invest_unit',
                                        'rate_std_sell_point', 'limit_money', 'total_profitcut', 'total_losscut',
                                        'total_profitcut_count',
                                        'total_losscut_count', 'loan_money', 'start_kospi_point',
                                        'start_kosdaq_point', 'end_kospi_point', 'end_kosdaq_point',
                                        'today_buy_total_sell_count',
                                        'today_buy_total_possess_count', 'today_buy_today_profitcut_count',
                                        'today_buy_today_profitcut_rate', 'today_buy_today_losscut_count',
                                        'today_buy_today_losscut_rate',
                                        'today_buy_total_profitcut_count', 'today_buy_total_profitcut_rate',
                                        'today_buy_total_losscut_count', 'today_buy_total_losscut_rate',
                                        'today_buy_reinvest_count0_sell_count',
                                        'today_buy_reinvest_count1_sell_count', 'today_buy_reinvest_count2_sell_count',
                                        'today_buy_reinvest_count3_sell_count', 'today_buy_reinvest_count4_sell_count',
                                        'today_buy_reinvest_count4_sell_profitcut_count',
                                        'today_buy_reinvest_count4_sell_losscut_count',
                                        'today_buy_reinvest_count5_sell_count',
                                        'today_buy_reinvest_count5_sell_profitcut_count',
                                        'today_buy_reinvest_count5_sell_losscut_count',
                                        'today_buy_reinvest_count0_remain_count',
                                        'today_buy_reinvest_count1_remain_count',
                                        'today_buy_reinvest_count2_remain_count',
                                        'today_buy_reinvest_count3_remain_count',
                                        'today_buy_reinvest_count4_remain_count',
                                        'today_buy_reinvest_count5_remain_count'],
                               index=jango_temp['id'])
        # 이 상태에서 self.jango 는 empty 데이터프레임이다.
        # column 만 만들어진 상태이다.

    # all_item_db 라는 테이블을 만들기 위한 self.df_all_item 데이터프레임
    def init_df_all_item(self):
        df_all_item_temp = {'id': []}

        self.df_all_item = DataFrame(df_all_item_temp,
                                     columns=['id', 'order_num', 'code', 'code_name', 'rate', 'purchase_rate',
                                              'purchase_price',
                                              'present_price', 'valuation_price',
                                              'valuation_profit', 'holding_amount', 'buy_date', 'item_total_purchase',
                                              'chegyul_check', 'reinvest_count', 'reinvest_date', 'invest_unit',
                                              'reinvest_unit',
                                              'sell_date', 'sell_price', 'sell_rate', 'rate_std', 'rate_std_mod_val',
                                              'rate_std_htr', 'rate_htr',
                                              'rate_std_mod_val_htr', 'yes_close', 'close', 'd1_diff_rate', 'd1_diff',
                                              'open', 'high',
                                              'low',
                                              'volume', 'clo5', 'clo10', 'clo20', 'clo40', 'clo60', 'clo80',
                                              'clo100', 'clo120', "clo5_diff_rate", "clo10_diff_rate",
                                              "clo20_diff_rate", "clo40_diff_rate", "clo60_diff_rate",
                                              "clo80_diff_rate", "clo100_diff_rate", "clo120_diff_rate"])

    # 가장 초기에 매수 했을 때 all_item_db 에 추가하는 함수
    def db_to_all_item(self, min_date, df, index, code, code_name, purchase_price, yesterday_close):
        self.df_all_item.loc[0, 'code'] = code
        self.df_all_item.loc[0, 'code_name'] = code_name
        # 초기는 반드시 rate가 -0.33 이여야한다. -> 수수료, 세금을 반영함
        self.df_all_item.loc[0, 'rate'] = float(-0.33)

        if yesterday_close:
            self.df_all_item.loc[0, 'purchase_rate'] = round(
                (float(purchase_price) - float(yesterday_close)) / float(yesterday_close) * 100, 2)

        self.df_all_item.loc[0, 'purchase_price'] = purchase_price
        self.df_all_item.loc[0, 'present_price'] = purchase_price

        # #jackbot("code_name: "+ code_name + "purchase_price: "+ str(purchase_price))
        self.df_all_item.loc[0, 'holding_amount'] = int(self.invest_unit / purchase_price)
        self.df_all_item.loc[0, 'buy_date'] = min_date
        self.df_all_item.loc[0, 'item_total_purchase'] = self.df_all_item.loc[0, 'purchase_price'] * \
            self.df_all_item.loc[
            0, 'holding_amount']

        # 실시간으로 오늘 투자한 금액 합산
        self.today_invest_price = self.today_invest_price + self.df_all_item.loc[0, 'item_total_purchase']

        self.df_all_item.loc[0, 'chegyul_check'] = 0
        self.df_all_item.loc[0, 'id'] = 0
        # int로 넣어야 나중에 ++ 할수 있다.
        # self.df_all_item.loc[0, 'reinvest_date'] = '#'
        # self.df_all_item.loc[0, 'reinvest_count'] = int(0)
        # 다음에 투자할 금액은 invest_unit과 같은 금액이다.
        self.df_all_item.loc[0, 'invest_unit'] = self.invest_unit
        # self.df_all_item.loc[0, 'reinvest_unit'] = self.invest_unit
        self.df_all_item.loc[0, 'sell_rate'] = float(0)
        self.df_all_item.loc[0, 'yes_close'] = yesterday_close
        self.df_all_item.loc[0, 'close'] = df.loc[index, 'close']

        self.df_all_item.loc[0, 'open'] = df.loc[index, 'open']
        self.df_all_item.loc[0, 'high'] = df.loc[index, 'high']
        self.df_all_item.loc[0, 'low'] = df.loc[index, 'low']
        self.df_all_item.loc[0, 'volume'] = df.loc[index, 'volume']
        if df.loc[index, 'd1_diff_rate'] is not None:
            self.df_all_item.loc[0, 'd1_diff_rate'] = float(df.loc[index, 'd1_diff_rate'])
        self.df_all_item.loc[0, 'clo5'] = df.loc[index, 'clo5']
        self.df_all_item.loc[0, 'clo10'] = df.loc[index, 'clo10']
        self.df_all_item.loc[0, 'clo20'] = df.loc[index, 'clo20']
        self.df_all_item.loc[0, 'clo40'] = df.loc[index, 'clo40']
        self.df_all_item.loc[0, 'clo60'] = df.loc[index, 'clo60']
        self.df_all_item.loc[0, 'clo80'] = df.loc[index, 'clo80']
        self.df_all_item.loc[0, 'clo100'] = df.loc[index, 'clo100']
        self.df_all_item.loc[0, 'clo120'] = df.loc[index, 'clo120']

        if df.loc[index, 'clo5_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo5_diff_rate'] = float(df.loc[index, 'clo5_diff_rate'])
        if df.loc[index, 'clo10_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo10_diff_rate'] = float(df.loc[index, 'clo10_diff_rate'])
        if df.loc[index, 'clo20_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo20_diff_rate'] = float(df.loc[index, 'clo20_diff_rate'])
        if df.loc[index, 'clo40_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo40_diff_rate'] = float(df.loc[index, 'clo40_diff_rate'])

        if df.loc[index, 'clo60_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo60_diff_rate'] = float(df.loc[index, 'clo60_diff_rate'])
        if df.loc[index, 'clo80_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo80_diff_rate'] = float(df.loc[index, 'clo80_diff_rate'])
        if df.loc[index, 'clo100_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo100_diff_rate'] = float(df.loc[index, 'clo100_diff_rate'])
        if df.loc[index, 'clo120_diff_rate'] is not None:
            self.df_all_item.loc[0, 'clo120_diff_rate'] = float(df.loc[index, 'clo120_diff_rate'])

        self.df_all_item.loc[0, 'valuation_profit'] = int(0)

        # 컬럼 중에 nan 값이 있는 경우 0으로 변경 -> 이렇게 안하면 아래 데이터베이스에 넣을 때
        # AttributeError: 'numpy.int64' object has no attribute 'translate' 에러 발생
        self.df_all_item = self.df_all_item.fillna(0)

        self.df_all_item.to_sql('all_item_db', self.engine_simulator, if_exists='append')

    # 보유한 종목들을 가져오는 함수
    # sell_date가 0이면 현재 보유 중인 종목이다. 매도를 할 경우 sell_date에 매도 한 날짜가 찍힌다.
    def get_data_from_possessed_item(self):
        sql = "SELECT code_name from all_item_db where sell_date = '%s'"
        return self.engine_simulator.execute(sql % (0)).fetchall()

    # 보유 종복 수 반환 함수
    def get_count_possessed_item(self):
        sql = "SELECT count(*) from all_item_db where sell_date = '%s'"
        return self.engine_simulator.execute(sql % (0)).fetchall()[0][0]

    # 테이블의 존재 여부를 파악하는 함수
    def is_simul_table_exist(self, db_name, table_name):
        sql = "select 1 from information_schema.tables where table_schema = '%s' and table_name = '%s'"
        rows = self.engine_simulator.execute(sql % (db_name, table_name)).fetchall()
        if len(rows) == 1:
            return True
        else:
            return False

    # 일별, 분별 정산 함수
    # 시뮬레이팅시 지속적으로 호출된다.
    def check_balance(self):
        # all_item_db가 없으면 check_balance 함수를 나가라
        if self.is_simul_table_exist(self.db_name, "all_item_db") == False:
            return

        # 총 수익 금액 (종목별 평가 금액 합산)
        sql = "SELECT sum(valuation_profit) from all_item_db"
        self.sum_valuation_profit = self.engine_simulator.execute(sql).fetchall()[0][0]
        print("sum_valuation_profit: " + str(self.sum_valuation_profit))

        # 전재산이라고 보면 된다. 현재 총손익 까지 고려했을 때
        self.total_invest_price = self.start_invest_price + self.sum_valuation_profit

        # 현재 총 투자한 금액 계산
        sql = "select sum(item_total_purchase) from all_item_db where sell_date = '%s'"
        self.total_purchase_price = self.engine_simulator.execute(sql % (0)).fetchall()[0][0]
        if self.total_purchase_price is None:
            self.total_purchase_price = 0

        # 매도를 한 종목들 대상 수익 계산
        sql = "select sum(valuation_profit) from all_item_db where sell_date != '%s'"
        self.total_valuation_profit = self.engine_simulator.execute(sql % (0)).fetchall()[0][0]

        if self.total_valuation_profit is None:
            self.total_valuation_profit = 0

        # 현재 투자 가능한 금액(예수금) = (초기자본 + 매도한 종목의 수익) - 현재 총 투자 금액
        self.d2_deposit = self.start_invest_price + self.total_valuation_profit - self.total_purchase_price

    # 시뮬레이팅 할 날짜를 가져 오는 함수
    # 장이 열렸던 날 들을 self.date_rows 에 담기 위해서 gs글로벌의 date값을 대표적으로 가져온 것
    def get_date_for_simul(self):
        # simul_start_date로부터 simul_end_date까지 gs글로벌에서 장이 열린 날들을 가져온다.
        # group by는 date라는 column을 기준으로 중복을 제거한다. date라는 column을 기준으로 묶는다는 것이다.
        # 일반적인 상황에서는 date가 중복으로 있지 않을 것이기 때문에 group by를 쓰든 안쓰든 결과는 같을 것이다.
        sql = "select date from `gs글로벌` where date >= '%s' and date <= '%s' group by date"
        self.date_rows = self.engine_daily_craw.execute(sql % (self.simul_start_date, self.simul_end_date)).fetchall()
        print("get_date_for_simul : self.date_rows : ", self.date_rows)

    # daily_buy_list에 일자 테이블이 존재하는지 확인하는 함수
    def is_date_exist(self, date):
        print("is_date_exist 함수에 들어왔습니다!", date)
        # information_schema.tables 는 테이블의 메타 정보를 담고 있는 데이터베이스이다.
        sql = "select 1 from information_schema.tables where table_schema ='daily_buy_list' and table_name = '%s'"
        rows = self.engine_daily_buy_list.execute(sql % (date)).fetchall()
        if len(rows) == 1:
            return True
        else:
            return False

    # 잔액 체크 함수, 잔고가 있으면 True를 반환, 없으면 False를 반환
    def jango_check(self):
        if int(self.d2_deposit) >= (int(self.limit_money) + int(self.invest_unit)):
            return True
        else:
            print("돈부족해서 invest 불가!!!!!!!!")
            return False

    # 출력 함수
    def print_info(self, min_date):
        print("*&*&*&* self.simul_num :" + str(self.simul_num))
        # all_itme_db 테이블이 생성 되어 있으면 보유한 종목 수를 출력
        if self.is_simul_table_exist(self.db_name, "all_item_db"):
            print("simulating 시간: " + str(min_date))
            print("보유종목 수 !!: " + str(self.get_count_possessed_item()))

    # 특정 종목의 시작가를 가져오는 함수(일별)
    def get_now_open_price_by_date(self, code, date):
        sql = "select open from `" + date + "` where code = '%s'"
        open = self.engine_daily_buy_list.execute(sql % (code)).fetchall()
        if len(open) == 1:
            return open[0][0]
        else:
            print("daily_buy_list db의 " + str(date) + " 테이블에 " + str(code) + " 가 존재하지 않는다!")
            return False
        # 테이블의 존재 여부를 파악하는 함수

    # daily_craw 데이터 베이스에서 특정 종목이 존재하는 여부를 파악하는 함수
    def is_daily_craw_table_exist(self, code_name):
        sql = "select 1 from information_schema.tables where table_schema = 'daily_craw' and table_name = '%s'"
        rows = self.engine_daily_craw.execute(sql % (code_name)).fetchall()
        if len(rows) == 1:
            return True
        else:
            print("daily_craw db 에 " + str(code_name) + " 테이블이 존재하지 않는다. !! ")
            return False

    # min_craw 데이터 베이스에서 특정 종목이 존재하는 여부를 파악하는 함수
    def is_min_craw_table_exist(self, code_name):
        sql = "select 1 from information_schema.tables where table_schema = 'min_craw' and table_name = '%s'"
        rows = self.engine_craw.execute(sql % (code_name)).fetchall()
        if len(rows) == 1:
            return True
        else:
            print("min_craw db 에 " + str(code_name) + " 테이블이 존재하지 않는다. !! ")
            return False

    # 분별 현재 누적 거래량 가져오는 함수
    def get_now_volume_by_min(self, code_name, min_date):
        sql = "select sum_volume from `" + code_name + "` where date = '%s' and open != 0 and volume !=0 order by sum_volume desc limit 1"
        rows = self.engine_craw.execute(sql % (min_date)).fetchall()
        if len(rows) == 1:
            return rows[0][0]
        else:
            return False

    # 분별 현재 종가 가져오는 함수
    # (close가 일별 데이터에서는 일별 종가 이지만, 분별 데이터에서의 close는 각 분별에 대한 종가를 의미
    # 즉, 1분 간격으로 변화하는 시세를 가져오는 함수
    def get_now_close_price_by_min(self, code_name, min_date):
        sql = "select close from `" + code_name + "` where date = '{}' and open != 0 and volume !=0 order by sum_volume desc limit 1"
        rows = self.engine_craw.execute(sql.format(min_date)).fetchall()

        if len(rows) == 1:
            return rows[0][0]
        else:
            return False

    # 특정 종목의 종가를 가져오는 함수
    def get_now_close_price_by_date(self, code, date):
        sql = "select close from `" + date + "` where code = '%s' limit 1"
        return_price = self.engine_daily_buy_list.execute(sql % (code)).fetchall()

        if len(return_price) == 1:
            return return_price[0][0]
        else:
            return False

    # 특정 종목의 어제 종가를 가져오는 함수
    def get_yes_close_price_by_date(self, code, date):
        sql = "select close from `" + date + "` where code = '%s' limit 1"
        return_price = self.engine_daily_buy_list.execute(sql % (code)).fetchall()

        if len(return_price) == 1:
            return return_price[0][0]
        else:
            return False

    # 종목의 현재 일자에 대한 주가 정보를 가져 오는 함수
    # daily_buy_list 데이터 베이스에 있는 date(날짜) 테이블에서 code_name(종목명)에 대한 정보를 가져온다. 정보를 가져온다. 정보를 가져온다.
    def get_now_price_by_date(self, code_name, date):
        sql = "select d1_diff_rate, close, open, high, low, volume, clo5, clo10, clo20, clo40, clo60, clo80, clo100, clo120 from `" + \
            date + "` where code_name = '%s' limit 1"
        rows = self.engine_daily_buy_list.execute(sql % (code_name)).fetchall()

        if len(rows) == 1:
            return rows
        else:
            return False

    # all_item_db의 보유한 종목에 현재가를 실시간으로 반영하는 함수
    def db_to_all_item_present_price_update_by_min(self, code_name, now_close_price):
        sql = "update all_item_db set present_price = '%s' where code_name = '%s' and sell_date = 0"
        self.engine_simulator.execute(sql % (now_close_price, code_name))

    # 분 마다 보유한 종목의 시세를 업데이트 하는 함수
    def update_all_db_by_min(self, min_date):
        # 매분마다 possess db 가져와야한다
        possessed_code_name = self.get_data_from_possessed_item()
        for j in range(len(possessed_code_name)):
            # 현재 시간의 close 값을 가져온다.
            now_close_price = self.get_now_close_price_by_min(possessed_code_name[j][0], min_date)
            # print("possessed_code_name: ", possessed_code_name[j][0], "now_close_price: ", now_close_price, "min_date", min_date)
            if now_close_price:
                self.db_to_all_item_present_price_update_by_min(possessed_code_name[j][0], now_close_price)
            else:
                # print(min_date + " / " + str(possessed_code_name[j][0]) + " 의 open_price 가 존재하지 않는다")
                continue

    # 보유 중인 종목들의 주가를 일별로 업데이트 하는 함수
    # all_item_db에서 업데이트를 한다.  option = 'ALL' 의미는 인자값을 date 하나만 줬을 때 option에는 기본값으로 ALL을 준다는 의미
    def update_all_db_by_date(self, date, option='ALL'):
        print("update_all_db_by_date 함수에 들어왔다!")
        # 현재 보유 중인 종목 들의 code_name 리스트
        possessed_code_name_list = self.get_data_from_possessed_item()
        if len(possessed_code_name_list) == 0:
            print("현재 보유 중인 종목이 없다 !!!!!")
        for j in range(len(possessed_code_name_list)):
            # 현재 주가를 가져오는 함수
            code_name = possessed_code_name_list[j][0]
            rows = self.get_now_price_by_date(code_name, date)
            if rows == False:
                continue
            d1_diff_rate = rows[0][0]
            close = rows[0][1]
            open = rows[0][2]  # 0이나 False 가 아니면 전부 true이다. (값이 무엇이 있든간에)
            high = rows[0][3]
            low = rows[0][4]
            volume = rows[0][5]
            clo5 = rows[0][6]
            clo10 = rows[0][7]
            clo20 = rows[0][8]
            clo40 = rows[0][9]
            clo60 = rows[0][10]
            clo80 = rows[0][11]
            clo100 = rows[0][12]
            clo120 = rows[0][13]

            # 만약에 open가에 어떤 값이 있으면(True) 현재 주가를 all_item_db에 반영 하기 위해 아래 함수를 들어간다.
            if open:
                self.db_to_all_item_present_price_update(code_name, d1_diff_rate, close, open, high, low, volume, clo5, clo10, clo20,
                                                         clo40, clo60, clo80, clo100, clo120, option)
            else:
                continue

    # 보유 중인 종목들의 주가 이외의 기타 정보들을 업데이트 하는 함수
    def update_all_db_etc(self):
        # valuation_price 업데이트
        sql = f"update all_item_db set valuation_price = round((present_price  * holding_amount) - item_total_purchase * {self.fees_rate} - present_price*holding_amount*{self.fees_rate + self.tax_rate}) where sell_date = '%s'"
        self.engine_simulator.execute(sql % (0))

        # valuation_profit, rate 업데이트
        sql = "update all_item_db set rate= round((valuation_price - item_total_purchase)/item_total_purchase*100,2), valuation_profit =  valuation_price - item_total_purchase where sell_date = '%s';"
        self.engine_simulator.execute(sql % (0))

    # 언제 종목을 팔지(익절, 손절) 결정 하는 알고리즘.
    # !@##############################################################################################################################
    def get_sell_list(self, i):
        print("get_sell_list!!!")
        # 단순히 현재 보유 종목의 수익률이
        # 익절 기준 수익률(self.sell_point) 이 넘거나,
        # 손절 기준 수익률(self.losscut_point) 보다 떨어지면 파는 알고리즘
        if self.sell_algo_num == 1:
            # select 할 컬럼은 항상 코드명, 수익률, 매도할 종목의 현재가, 수익(손실)금액
            # sql 첫 번째 라인은 항상 고정
            sql = "SELECT code, rate, present_price, valuation_profit FROM all_item_db WHERE (sell_date = '%s') " \
                  "and (rate>='%s' or rate <= '%s')"
            # 수익률이 몇프로 이상이거나 몇프로 이하이면 판다.
            sell_list = self.engine_simulator.execute(sql % (0, self.sell_point, self.losscut_point)).fetchall()

        # 5 / 20 이동 평균선 데드크로스 이거나, losscut_point(손절 기준 수익률) 이하로 떨어지면 손절하는 알고리즘
        elif self.sell_algo_num == 2:
            sql = "SELECT code, rate, present_price, valuation_profit FROM all_item_db WHERE (sell_date = '%s') " \
                  "and ((clo5 < clo20) or rate <= '%s')"
            sell_list = self.engine_simulator.execute(sql % (0, self.losscut_point)).fetchall()

        # 5 / 40 이동 평균선 데드크로스 이거나, losscut_point(손절 기준 수익률) 이하로 떨어지면 손절하는 알고리즘
        elif self.sell_algo_num == 3:
            sql = "SELECT code, rate, present_price,valuation_profit FROM all_item_db WHERE (sell_date = '%s') " \
                  "and ((clo5 < clo40) or rate <= '%s')"

            sell_list = self.engine_simulator.execute(sql % (0, self.losscut_point)).fetchall()
        # 절대 모멘텀 전략 (특정일 전 보다 n% 이하로 떨어지면 매도) / code 버전
        elif self.sell_algo_num == 4:
            sell_list = []
            sql = "SELECT code, rate, present_price, valuation_profit FROM all_item_db WHERE sell_date = 0 " \
                  "group by code"
            # realtime_daily_buy_list_temp 로 일단 위 조건의 종목을을받는다.
            sell_list_temp = self.engine_simulator.execute(sql).fetchall()
            for row in sell_list_temp:
                code = row[0]
                present_price = row[2]
                # date_rows_yesterday 가 self.date_rows[i-1] 값이다.
                # date_rows_today 가 self.date_rows[i]
                # 오늘 기준 n일 전 날짜
                date_before = self.date_rows[i - self.day_before][0]
                # 오늘 기준 n일 전 종가
                date_before_close = self.get_now_close_price_by_date(code, date_before)
                if date_before_close != 0 and date_before_close != False:
                    diff_point_calc = (present_price - date_before_close) / date_before_close * 100
                    # 현재가(present_price)가 self.day_before 일 전 종가 보다 self.diff_point(0도 가능) 만큼 떨어 지면 매도
                    if diff_point_calc < self.diff_point * (-1):
                        sell_list.append(row)

        # 절대 모멘텀 전략 (특정일 전 보다 n% 이하로 떨어지면 매도) / query 버전
        elif self.sell_algo_num == 5:
            date_before = self.date_rows[i - self.day_before][0]
            sql = "SELECT ALLDB.code, ALLDB.rate, ALLDB.present_price, ALLDB.valuation_profit " \
                  "FROM all_item_db ALLDB, daily_buy_list.`" + date_before + "` BEFORE_DAY "\
                "WHERE ALLDB.code = BEFORE_DAY.code " \
                "AND ALLDB.sell_date = 0 "\
                "AND (ALLDB.present_price - BEFORE_DAY.close) / BEFORE_DAY.close * 100 < '%s' "
            sell_list = self.engine_simulator.execute(sql % (self.diff_point * (-1))).fetchall()

        # 절대 모멘텀 전략 + losscut_point 추가 (특정일 전 보다 n% 이하로 떨어지면 매도) / query 버전
        elif self.sell_algo_num == 6:
            date_before = self.date_rows[i - self.day_before][0]
            sql = "SELECT ALLDB.code, ALLDB.rate, ALLDB.present_price, ALLDB.valuation_profit " \
                  "FROM all_item_db ALLDB, daily_buy_list.`" + date_before + "` BEFORE_DAY " \
                "WHERE ALLDB.code = BEFORE_DAY.code " \
                "AND ALLDB.sell_date = 0 " \
                "AND ((ALLDB.present_price - BEFORE_DAY.close) / BEFORE_DAY.close * 100 < '%s' " \
                "OR ALLDB.rate <= '%s')"
            sell_list = self.engine_simulator.execute(sql % (self.diff_point * (-1), self.losscut_point)).fetchall()

        ##################################################################################################################################################################################################################
        else:
            print(f"{self.simul_num}번 알고리즘에 대한 self.sell_list_num 설정이 비었습니다. variable_setting 함수에서 self.sell_list_num을 확인해주세요.")
            sys.exit(1)

        return sell_list

    # 실제로 매도를 하는 함수 (매도 한 결과를 all_item_db에 반영)
    def sell_send_order(self, min_date, sell_price, sell_rate, code):
        # print("sell send order")
        sql = "UPDATE all_item_db SET sell_date= '%s', sell_price ='%s' ,sell_rate ='%s' WHERE code='%s' and sell_date = '%s' " \
              "ORDER BY buy_date desc LIMIT 1"
        self.engine_simulator.execute(sql % (min_date, sell_price, sell_rate, code, 0))
        # 매도 후 정산
        self.check_balance()

    # 매도를 하기 위한 함수
    def auto_trade_sell_stock(self, date, _i):
        # 알고리즘을 사용하여 매도 할 리스트를 가져오는 함수
        sell_list = self.get_sell_list(_i)
        for i in range(len(sell_list)):
            # 코드명
            get_sell_code = sell_list[i][0]
            # 수익률 : 일단 팔기로 결정이 된 리스트이고, 결국 팔았을때의 수익률이기 때문에 0이하면 손절 이상이면 익절일 것이다.
            get_sell_rate = sell_list[i][1]
            # 종목의 현재 주가
            get_present_price = sell_list[i][2]
            # 수익(손실) 금액 (종목의 순수익, 순손실 금액)
            valuation_profit = sell_list[i][3]

            if get_sell_rate < 0:
                print("손절 매도!!!!$$$$$$$$$$$ 수익: " + str(valuation_profit) + " / 수익률 : " + str(
                    get_sell_rate) + " / 종목코드: " + str(get_sell_code) + " $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

            else:
                print("익절 매도!!!!$$$$$$$$$$$ 수익: " + str(valuation_profit) + " / 수익률 : " + str(
                    get_sell_rate) + " / 종목코드: " + str(get_sell_code) + " $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

            # 실제로 매도를 하는 함수 (매도 한 결과를 all_item_db에 반영)
            self.sell_send_order(date, get_present_price, get_sell_rate, get_sell_code)

    # 몇개의 주를 살지 계산해주는 함수
    def buy_num_count(self, invest_unit, present_price):
        # jackbot("******************* buy_num_count!!!")
        return int(int(invest_unit) / int(present_price))

    # 금일 수익 계산 함수
    def get_today_profit(self, date):
        # jackbot("******************* get_today_profit!!!")
        sql = "SELECT sum(valuation_profit) from all_item_db where sell_date like '%s'"
        return self.engine_simulator.execute(sql % ("%%" + date + "%%")).fetchall()[0][0]

    # 총 매입금액 계산 함수
    def get_sum_item_total_purchase(self):

        # jackbot("******************* get_sum_item_total_purchase!!!")
        sql = "SELECT sum(item_total_purchase) from all_item_db where sell_date = '%s'"
        rows = self.engine_simulator.execute(sql % (0)).fetchall()[0][0]
        if rows is not None:
            return rows
        else:
            return 0

    # 총평가금액 계산 함수
    def get_sum_valuation_price(self):
        sql = "SELECT sum(valuation_price) from all_item_db where sell_date = '%s'"
        rows = self.engine_simulator.execute(sql % (0)).fetchall()[0][0]
        if rows is not None:
            return rows
        else:
            return 0

    # 오늘 일자 익절 종목 수
    def get_today_profitcut_count(self, date):
        sql = "SELECT count(code) from all_item_db where sell_date like '%s' and sell_rate>='%s'"
        return self.engine_simulator.execute(sql % ("%%" + date + "%%", 0)).fetchall()[0][0]

    # 오늘 일자 손절 종목 수
    def get_today_losscut_count(self, date):
        sql = "SELECT count(code) from all_item_db where sell_date like '%s' and sell_rate<'%s'"
        return self.engine_simulator.execute(sql % ("%%" + date + "%%", 0)).fetchall()[0][0]

    # 오늘 일자 매도금액
    def get_sum_today_sell_price(self, date):
        sql = "SELECT sum(valuation_price) from all_item_db where sell_date like '%s'"
        return self.engine_simulator.execute(sql % ("%%" + date + "%%")).fetchall()[0][0]

    # 오늘 일자 익절 종목 대상 수익
    def get_sum_today_profitcut(self, date):
        sql = "SELECT sum(valuation_profit) from all_item_db where sell_date like '%s' and valuation_profit >= '%s' "
        return self.engine_simulator.execute(sql % ("%%" + date + "%%", 0)).fetchall()[0][0]

    # 오늘 일자 손절 종목 대상 손실 금액
    def get_sum_today_losscut(self, date):
        sql = "SELECT sum(valuation_profit) from all_item_db where sell_date like '%s' and valuation_profit < '%s' "
        return self.engine_simulator.execute(sql % ("%%" + date + "%%", 0)).fetchall()[0][0]

    # 총 익절 종목 대상 수익
    def get_sum_total_profitcut(self):
        sql = "SELECT sum(valuation_profit) from all_item_db where sell_date != 0 and valuation_profit >= '%s' "
        return self.engine_simulator.execute(sql % (0)).fetchall()[0][0]

    # 총 손절 종목 대상 손실 금액
    def get_sum_total_losscut(self):
        sql = "SELECT sum(valuation_profit) from all_item_db where sell_date != 0 and valuation_profit < '%s' "
        return self.engine_simulator.execute(sql % (0)).fetchall()[0][0]

    # 전체 일자 익절한 종목 수
    def get_sum_total_profitcut_count(self):
        # jackbot("******************* get_sum_total_profitcut_count!!!")
        sql = "select count(code) from all_item_db where sell_date != 0 and valuation_profit >= '%s'"
        return self.engine_simulator.execute(sql % (0)).fetchall()[0][0]

    # 전체 일자 손절한 종목 수
    def get_sum_total_losscut_count(self):
        # jackbot("******************* get_sum_total_losscut_count!!!")
        sql = "select count(code) from all_item_db where sell_date != 0 and valuation_profit < '%s' "
        return self.engine_simulator.execute(sql % (0)).fetchall()[0][0]

    # jango_data의 저장 된 일자 반환 함수
    def get_len_jango_data_date(self):

        sql = "select date from jango_data"
        rows = self.engine_simulator.execute(sql).fetchall()

        return len(rows)

    # 총 보유한 종목 수
    def get_total_possess_count(self):
        # jackbot("******************* get_total_possess_count!!!")
        sql = "select count(code) from all_item_db where sell_date = '%s'"
        return self.engine_simulator.execute(sql % (0)).fetchall()[0][0]

    # jango_data 테이블을 만드는 함수
    # date_rows_today 날짜에 해당하는 정산을 하고, 잔고의 결과를 df에 담아서 jango_data 테이블에 append한다.
    def db_to_jango(self, date_rows_today):
        # 정산 함수 (현재 기준으로 계산된 것들을 멤버로 저장한다.)
        self.check_balance()
        if self.is_simul_table_exist(self.db_name, "all_item_db") == False:
            return

        # init_df_jango에서 만든 df에 데이터를 채워준다.
        self.jango.loc[0, 'date'] = date_rows_today

        # self.jango.loc[0, 'total_asset'] = self.total_invest_price - self.loan_money
        self.jango.loc[0, 'today_profit'] = self.get_today_profit(date_rows_today)
        self.jango.loc[0, 'sum_valuation_profit'] = self.sum_valuation_profit
        self.jango.loc[0, 'total_profit'] = self.total_valuation_profit

        self.jango.loc[0, 'total_invest'] = self.total_invest_price
        self.jango.loc[0, 'd2_deposit'] = self.d2_deposit
        # 총매입금액
        self.jango.loc[0, 'sum_item_total_purchase'] = self.get_sum_item_total_purchase()

        # 총평가금액
        self.jango.loc[0, 'total_evaluation'] = self.get_sum_valuation_price()
        self.jango.loc[0, 'today_profitcut_count'] = self.get_today_profitcut_count(date_rows_today)
        self.jango.loc[0, 'today_losscut_count'] = self.get_today_losscut_count(date_rows_today)

        self.jango.loc[0, 'today_invest_price'] = float(self.today_invest_price)

        # self.jango.loc[0, 'today_reinvest_price'] = self.today_reinvest_price
        self.jango.loc[0, 'today_sell_price'] = self.get_sum_today_sell_price(date_rows_today)

        # 오늘 기준 수익률 (키움 잔고 상단에 뜨는 수익률) -0.33 (수수료, 세금)
        try:
            self.jango.loc[0, 'today_rate'] = round(
                (float(self.jango.loc[0, 'total_evaluation']) - float(
                    self.jango.loc[0, 'sum_item_total_purchase'])) / float(
                    self.jango.loc[0, 'sum_item_total_purchase']) * 100 - 0.33, 2)
        except ZeroDivisionError as e:
            pass

        # self.jango.loc[0, 'volume_limit'] = self.volume_limit

        # self.jango.loc[0, 'reinvest_point'] = self.reinvest_point
        self.jango.loc[0, 'sell_point'] = self.sell_point
        # self.jango.loc[0, 'max_reinvest_count'] = self.max_reinvest_count
        self.jango.loc[0, 'invest_limit_rate'] = self.invest_limit_rate
        self.jango.loc[0, 'invest_unit'] = self.invest_unit

        self.jango.loc[0, 'limit_money'] = self.limit_money
        self.jango.loc[0, 'total_possess_count'] = self.get_total_possess_count()
        self.jango.loc[0, 'today_buy_list_count'] = self.len_df_realtime_daily_buy_list
        # self.jango.loc[0, 'today_reinvest_count'] = self.get_today_reinvest_count(date_rows_today)
        # self.jango.loc[0, 'today_cant_reinvest_count'] = self.get_today_cant_reinvest_count()

        # 오늘 익절한 금액
        self.jango.loc[0, 'today_profitcut'] = self.get_sum_today_profitcut(date_rows_today)
        # 오늘 손절한 금액
        self.jango.loc[0, 'today_losscut'] = self.get_sum_today_losscut(date_rows_today)

        # 지금까지 총 익절한 금액
        self.jango.loc[0, 'total_profitcut'] = self.get_sum_total_profitcut()

        # 지금까지 총 손절한 금액
        self.jango.loc[0, 'total_losscut'] = self.get_sum_total_losscut()

        # 지금까지 총 익절한놈들
        self.jango.loc[0, 'total_profitcut_count'] = self.get_sum_total_profitcut_count()

        # 지금까지 총 손절한 놈들

        self.jango.loc[0, 'total_losscut_count'] = self.get_sum_total_losscut_count()

        self.jango.loc[0, 'today_buy_count'] = 0
        self.jango.loc[0, 'today_buy_total_sell_count'] = 0
        self.jango.loc[0, 'today_buy_total_possess_count'] = 0

        self.jango.loc[0, 'today_buy_today_profitcut_count'] = 0

        self.jango.loc[0, 'today_buy_today_losscut_count'] = 0
        self.jango.loc[0, 'today_buy_total_profitcut_count'] = 0

        self.jango.loc[0, 'today_buy_total_losscut_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count0_sell_count'] = 0
        #
        # self.jango.loc[0, 'today_buy_reinvest_count1_sell_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count2_sell_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count3_sell_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count4_sell_count'] = 0
        #
        # self.jango.loc[0, 'today_buy_reinvest_count4_sell_profitcut_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count4_sell_losscut_count'] = 0
        #
        # self.jango.loc[0, 'today_buy_reinvest_count5_sell_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count5_sell_profitcut_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count5_sell_losscut_count'] = 0
        #
        # self.jango.loc[0, 'today_buy_reinvest_count0_remain_count'] = 0
        #
        # self.jango.loc[0, 'today_buy_reinvest_count1_remain_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count2_remain_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count3_remain_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count4_remain_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count4_remain_count'] = 0
        # self.jango.loc[0, 'today_buy_reinvest_count5_remain_count'] = 0

        # # 데이터베이스에 테이블이 존재할 때 수행 동작을 지정한다.
        # 'fail', 'replace', 'append' 중 하나를 사용할 수 있는데 기본값은 'fail'이다.
        # 'fail'은 데이터베이스에 테이블이 있다면 아무 동작도 수행하지 않는다.
        # 'replace'는 테이블이 존재하면 기존 테이블을 삭제하고 새로 테이블을 생성한 후 데이터를 삽입한다.
        # 'append'는 테이블이 존재하면 데이터만을 추가한다.
        # DataFrame에서 제공하는 to_sql 함수를 통해 self.engine_simulator의 jango_data 테이블에 jango를 추가한다.
        self.jango.to_sql('jango_data', self.engine_simulator, if_exists='append')

        #     # today_earning_rate
        sql = "update jango_data set today_earning_rate =round(today_profit / total_invest * '%s',2) WHERE date='%s'"
        # rows[i][0] 하는 이유는 rows[i]는 튜플( )로 나온다 그 튜플의 원소를 꺼내기 위해 rows[i]에 [0]을 추가
        # jango_data에서 오늘 날짜 데이터를 찾아서 수익률을 계산해서 업데이트 한다.
        self.engine_simulator.execute(sql % (100, date_rows_today))

    # 시뮬레이션이 다 끝났을 때 마지막 jango_data 정리
    def arrange_jango_data(self):
        if self.engine_simulator.dialect.has_table(self.engine_simulator, 'jango_data'):
            len_date = self.get_len_jango_data_date()
            sql = "select date from jango_data"
            rows = self.engine_simulator.execute(sql).fetchall()

            print('jango_data 최종 정산 중...')
            # 위에 전체
            for i in range(len_date):
                # today_buy_count
                sql = "UPDATE jango_data SET today_buy_count=(select count(*) from (select code from all_item_db where buy_date like '%s') b) WHERE date='%s'"
                # date 하는 이유는 rows[i]는 튜플로 나온다 그 튜플의 원소를 꺼내기 위해 [0]을 추가
                self.engine_simulator.execute(sql % ("%%" + str(rows[i][0]) + "%%", rows[i][0]))

                # today_buy_total_sell_count ( 익절, 손절 포함)
                sql = "UPDATE jango_data SET today_buy_total_sell_count=(select count(*) from (select code from all_item_db a where buy_date like '%s' and (a.sell_date != 0) group by code ) b) WHERE date='%s'"
                self.engine_simulator.execute(sql % ("%%" + rows[i][0] + "%%", rows[i][0]))

                # today_buy_total_possess_count 오늘 사고 계속 가지고 있는것들
                sql = "UPDATE jango_data SET today_buy_total_possess_count=(select count(*) from (select code from all_item_db a where buy_date like '%s' and a.sell_date = '%s' group by code ) b) WHERE date='%s'"
                self.engine_simulator.execute(sql % ("%%" + rows[i][0] + "%%", 0, rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_today_profitcut_count=(select count(*) from (select code from all_item_db where buy_date like '%s' and sell_date like '%s' and (sell_rate >= '%s' ) group by code ) b) WHERE date='%s'"
                self.engine_simulator.execute(sql % ("%%" + rows[i][0] + "%%", "%%" + rows[i][0] + "%%", 0, rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_today_profitcut_rate= round(CAST(today_buy_today_profitcut_count AS DECIMAL) /today_buy_count *100,2) WHERE date = '%s' AND today_buy_count > 0"
                self.engine_simulator.execute(sql % (rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_today_losscut_count=(select count(*) from (select code from all_item_db where buy_date like '%s' and sell_date like '%s' and sell_rate < '%s'  group by code ) b) WHERE date='%s'"
                self.engine_simulator.execute(sql % ("%%" + rows[i][0] + "%%", "%%" + rows[i][0] + "%%", 0, rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_today_losscut_rate=round(CAST(today_buy_today_losscut_count AS DECIMAL) /today_buy_count * 100,2) WHERE date = '%s' AND today_buy_count > 0"
                self.engine_simulator.execute(sql % (rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_total_profitcut_count=(select count(*) from (select code from all_item_db where buy_date like '%s' and sell_rate >= '%s'  group by code ) b) WHERE date='%s'"
                self.engine_simulator.execute(sql % ("%%" + rows[i][0] + "%%", 0, rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_total_profitcut_rate=round(CAST(today_buy_total_profitcut_count AS DECIMAL) /today_buy_count * 100,2) WHERE date = '%s' AND today_buy_count > 0"
                self.engine_simulator.execute(sql % (rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_total_losscut_count=(select count(*) from (select code from all_item_db where buy_date like '%s' and sell_rate < '%s'  group by code ) b) WHERE date='%s'"
                self.engine_simulator.execute(sql % ("%%" + rows[i][0] + "%%", 0, rows[i][0]))

                sql = "UPDATE jango_data SET today_buy_total_losscut_rate=round(CAST(today_buy_total_losscut_count AS DECIMAL)/today_buy_count*100,2) WHERE date = '%s' AND today_buy_count > 0"
                self.engine_simulator.execute(sql % (rows[i][0]))
        print('jango_data 최종 정산 완료')

    # 분 데이터를 가져오는 함수
    # 9시부터 15시 30분까지의 분별 시간을 가져온다.
    def get_date_min_for_simul(self, simul_start_date):
        # 촬영 후 업데이트 되었습니다
        dt_format = '%Y%m%d%H%M'
        simul_time = datetime.datetime.strptime(simul_start_date + "0900", dt_format)
        min_delta = datetime.timedelta(minutes=1)

        times = []
        while simul_time.hour != 15 or simul_time.minute != 31:
            times.append((datetime.datetime.strftime(simul_time, dt_format),))
            simul_time += min_delta

        self.min_date_rows = times

    # 분별 시뮬레이팅 함수
    # 새로운 종목 매수 및 보유한 종목의 데이터를 업데이트 하는 함수, 매도 함수도 포함
    def trading_by_min(self, date_rows_today, date_rows_yesterday, i):
        self.print_info(date_rows_today)

        # all_item_db가 존재하고, 현재 보유 중인 종목이 있다면 아래 로직을 들어간다.
        if self.is_simul_table_exist(self.db_name, "all_item_db") and len(self.get_data_from_possessed_item()) != 0:
            # 보유 중인 종목들의 주가를 일별로 업데이트 하는 함수(option 이 OPEN 이면 OPEN가만 업데이트)
            self.update_all_db_by_date(date_rows_today, option='OPEN')

        # 분별 시간 데이터를 가져온다.
        self.get_date_min_for_simul(date_rows_today)
        if len(self.min_date_rows) != 0:
            # 분 단위로 for문을 돈다
            for t in range(len(self.min_date_rows)):
                min = self.min_date_rows[t][0]
                # all_item_db가 존재하고 현재 보유 중인 종목이 있는 경우
                if self.is_simul_table_exist(self.db_name, "all_item_db") and len(self.get_data_from_possessed_item()) != 0:
                    self.print_info(min)
                    # 보유 중인 종목들의 주가를 분별로 업데이트 한다.
                    self.update_all_db_by_min(min)
                    self.update_all_db_etc()
                    # 매도 함수
                    self.auto_trade_sell_stock(min, i)
                    # self.buy_stop 이 False 이고, 보유 자산이 있으면 실제 매수를 한다.
                    if not self.buy_stop and self.jango_check():
                        # 매수 할 종목을 가져온다
                        self.get_realtime_daily_buy_list()

                        if self.len_df_realtime_daily_buy_list > 0:
                            self.auto_trade_stock_realtime(min, date_rows_today, date_rows_yesterday)
                        else:
                            print("realtime_daily_buy_list에 금일 매수 대상 종목이 0개 이다.  ")

                #  여긴 가장 초반에 all_itme_db를 만들어야 할때이거나 매수한 종목이 없을 때 들어가는 로직
                else:
                    if not self.buy_stop and self.jango_check():
                        self.auto_trade_stock_realtime(min, date_rows_today, date_rows_yesterday)

                # 9시에만 매수를 하는 경우는 한번만 9시에 매수 하고 self.buy_stop을 true로 변경하여 이후로 매수하지 않도록 설정
                if not self.buy_stop and self.only_nine_buy:
                    print("9시 매수 끝!!!!!!!!!!")
                    self.buy_stop = True

        else:
            print("min_craw db의 종목 테이블에 " + str(
                date_rows_today) + " 데이터가 존재 하지 않는다! self.simul_start_date 날짜를 변경 하세요! (분별 데이터는 콜렉터에서 최근 1년 데이터만 가져옵니다! ")

    # 새로운 종목 매수 및 보유한 종목의 데이터를 업데이트 하는 함수, 매도 함수도 포함
    def trading_by_date(self, date_rows_today, date_rows_yesterday, i):
        self.print_info(date_rows_today)

        # all_item_db가 존재하고, 현재 보유 중인 종목이 있다면 아래 로직을 들어간다.
        # 보유한 종목이 없으면 이 로직은 의미가 없다. 첫 날에는 all_item_db에는 아무것도 없는 상태일 것이다.
        if self.is_simul_table_exist(self.db_name, "all_item_db") and len(self.get_data_from_possessed_item()) != 0:
            # 보유 중인 종목들의 주가를 일별로 업데이트 하는 함수
            self.update_all_db_by_date(date_rows_today, option='OPEN')
            # 보유 중인 종목들의 주가 이외의 기타 정보들을 업데이트 하는 함수
            self.update_all_db_etc()
            # 매도 함수
            self.auto_trade_sell_stock(date_rows_today, i)

            # 보유 자산이 있다면, 실제 매수를 한다.
            if self.jango_check():
                # 돈있으면 매수 시작, 9시를 날짜에 붙인다.
                self.auto_trade_stock_realtime(str(date_rows_today) + "0900", date_rows_today, date_rows_yesterday)

        #  여긴 가장 초반에 all_itme_db를 만들어야 할때이거나 매수한 종목이 없을 때 들어가는 로직
        else:
            if self.jango_check():
                self.auto_trade_stock_realtime(str(date_rows_today) + "0900", date_rows_today, date_rows_yesterday)

    # 매일 시뮬레이팅 돌기 전 초기화 세팅
    def daily_variable_setting(self):
        self.buy_stop = False
        self.today_invest_price = 0

    # 분별 시뮬레이팅
    def simul_by_min(self, date_rows_today, date_rows_yesterday, i):
        print("**************************   date: " + date_rows_today)
        # 일별 시뮬레이팅 하며 변수 초기화(분별시뮬레이터의 경우도 하루 단위로 초기화)
        self.daily_variable_setting()
        # daily_buy_list에 시뮬레이팅 할 날짜에 해당하는 테이블과 전 날 테이블이 존재하는지 확인
        if self.is_date_exist(date_rows_today) and self.is_date_exist(date_rows_yesterday):
            # 우선 매수리스트를 가져온다.
            self.db_to_realtime_daily_buy_list(date_rows_today, date_rows_yesterday, i)
            # 분별 시뮬레이팅 시작한다.
            self.trading_by_min(date_rows_today, date_rows_yesterday, i)
            self.db_to_jango(date_rows_today)

            # [추가 코드]all_item_db가 존재하고, 현재 보유 중인 종목이 있다면 아래 로직을 들어간다.
            if self.is_simul_table_exist(self.db_name, "all_item_db") and len(self.get_data_from_possessed_item()) != 0:
                # 보유 중인 종목들의 주가를 일별로 업데이트 하는 함수(분별 종가 업데이트 이외에 clo5, clo20등등의 값을 업데이트)
                self.update_all_db_by_date(date_rows_today, option='ALL')

        else:
            print(date_rows_today + "테이블은 존재하지 않는다!!!")

    # 일별 시뮬레이팅
    def simul_by_date(self, date_rows_today, date_rows_yesterday, i):
        print("**************************   date: " + date_rows_today)
        # 일별 시뮬레이팅 하며 변수 초기화
        self.daily_variable_setting()
        # daily_buy_list에 시뮬레이팅 할 날짜에 해당하는 테이블과 전 날 테이블이 존재하는지 확인
        if self.is_date_exist(date_rows_today) and self.is_date_exist(date_rows_yesterday):
            # 당일 매수 할 종목들을 realtime_daily_buy_list 테이블에 세팅
            # 매일매일 무엇을 살지 정리한다. 그래서 전날에 정리를 했던 종목들을 당일날 9시에 사는 그런 그림이다.
            self.db_to_realtime_daily_buy_list(date_rows_today, date_rows_yesterday, i)
            # 트레이딩(매수, 매도) 함수 + 보유 종목의 현재가 업데이트 함수
            self.trading_by_date(date_rows_today, date_rows_yesterday, i)

            # [추가 코드]all_item_db가 존재하고, 현재 보유 중인 종목이 있다면 아래 로직을 들어간다.
            if self.is_simul_table_exist(self.db_name, "all_item_db") and len(self.get_data_from_possessed_item()) != 0:
                # 보유 중인 종목들의 주가를 일별로 업데이트 하는 함수(분별 종가 업데이트 이외에 clo5, clo20등등의 값을 업데이트)
                self.update_all_db_by_date(date_rows_today, option='ALL')

            # 일별 정산
            self.db_to_jango(date_rows_today)

        else:
            print(date_rows_today + "테이블은 존재하지 않는다!!!")

    # 날짜 별 로테이팅 함수 : 이 안에서 시뮬레이팅도 한다.
    def rotate_date(self):
        # start_date 부터 end_date 까지 장이 열린 날짜들이 date_rows에 담겨 있다.
        # 이 date_rows를 돌면서 시뮬레이팅을 하는 것이다.
        # 1부터 도는 이유는 0번째는 전날이 없기 때문에 정리할 종목이 없다. 전날에 정리한 종목을 다음날 9시에 사는 것이 시뮬레이팅의 매수 방식이기 때문이다.
        for i in range(1, len(self.date_rows)):
            print("self.date_rows!!", self.date_rows)
            # 시뮬레이팅 할 일자
            date_rows_today = self.date_rows[i][0]
            # 시뮬레이팅 하기 전의 일자
            date_rows_yesterday = self.date_rows[i - 1][0]

            # self.simul_reset 이 False, 즉 시뮬레이터를 멈춘 지점 부터 실행하기 위한 조건
            if not self.simul_reset and not self.simul_reset_lock:
                if int(date_rows_today) <= int(self.last_simul_date):
                    print("**************************   date: " + date_rows_today + "simul jango date exist pass ! ")
                    continue
                else:
                    self.simul_reset_lock = True

            # 분별 시뮬레이팅
            if self.use_min:
                self.simul_by_min(date_rows_today, date_rows_yesterday, i)
            # 일별 시뮬레이팅
            else:
                self.simul_by_date(date_rows_today, date_rows_yesterday, i)

        # 마지막 jango_data 정리
        self.arrange_jango_data()


# 수업 후 아래 함수 추가 되었습니다
# clauseelement : 실행하려는 SQl 쿼리, 이 값에서 % 문자를 찾고 대체한다.
def escape_percentage(conn, clauseelement, multiparams, params):
    # execute로 실행한 sql문이 들어왔을 때 %를 %%로 replace
    # %를 %%로 escape 처리한다. 데이터베이스 드라이버가 %를 포매팅 기호로 해석하지 못하게 만든다.
    if isinstance(clauseelement, str) and '%' in clauseelement and multiparams is not None:
        while True:
            # 정규식을 사용하여 %를 %%로 변환한다.
            # %가 %로 시작하거나 %s 뒤에 오는 경우는 제외(이미 이스케이프 된 경우)
            replaced = re.sub(r'([^%])%([^%s])', r'\1%%\2', clauseelement)
            if replaced == clauseelement:
                break
            clauseelement = replaced
    return clauseelement, multiparams, params


if __name__ == '__main__':
    logger.error('simulator.py로 실행해 주시기 바랍니다.')
    sys.exit(1)
