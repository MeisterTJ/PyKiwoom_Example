# https://wikidocs.net/77487
# 감리구분
# '정상', '투자주의', '투자경고', '투자위험', '투자주의환기종목'

from pykiwoom.kiwoom import *

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

감리구분 = kiwoom.GetMasterConstruction("005930")
print(감리구분)