from PyQt5.QtCore import *
from ALBA_Kiwoom import Kiwoom
from urllib.request import urlopen
from bs4 import BeautifulSoup

class Crawling(QThread):
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui

        self.kiwoom = Kiwoom()

        # 크롤링하고자 하는 사이트
        response = urlopen("http://adrinfo.kr/")
        soup = BeautifulSoup(response, "html.parser")

        i = 0
        values = []
        for link in soup.select("h2.card-title"):
            values.append(link.text.strip()[0:5].strip())
            i += 1

        self.kiwoom.kospi = float(values[0])
        self.kiwoom.kosdaq = float(values[1])
