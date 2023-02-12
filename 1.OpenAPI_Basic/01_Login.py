# https://wikidocs.net/77481
from pykiwoom.kiwoom import *

kiwoom = Kiwoom()
# 블로킹 로그인의 의미는 로그인이 완료될 때까지 다음 줄의 코드가 수행되지 않고 블로킹되는 것을 의미한다.
kiwoom.CommConnect(block=True)
print("블로킹 로그인 완료")