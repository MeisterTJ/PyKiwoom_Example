# https://wikidocs.net/77493
# 테마 그룹 출력
from pykiwoom.kiwoom import *
import pprint

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

group = kiwoom.GetThemeGroupList(1)
pprint.pprint(group)