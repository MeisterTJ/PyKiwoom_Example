from daily_craw_config import daily_craw_config


class daily_crawler():
    def __init__(self, db_name, daily_craw_db_name, daily_buy_list_db_name):
        self.cc = daily_craw_config(db_name, daily_craw_db_name, daily_buy_list_db_name)
