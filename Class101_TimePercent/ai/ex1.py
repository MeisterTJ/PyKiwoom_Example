import sys
import logging

logger = logging.getLogger(__name__)
is_64bits = sys.maxsize > 2**32
if not is_64bits:
    logger.critical('64bit 환경으로 실행해 주시기 바랍니다.')
    exit(1)
import numpy as np
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

# X : input DATA
# numpy를 이용하면 행렬 계산 등을 할 수 있어서 성능이 좋다 -> 그래서 numpy 배열로 변환해서 사용하는 것
X = np.array([[1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6]])
# X_ = [[1,2,3],[2,3,4],[3,4,5],[4,5,6]] # 차이점 확인

# shape : 행렬의 차원
print(X.shape)

# y: 결과(라벨) [1,2,3] -> 4 / [2,3,4] ->5 / [3,4,5] ->6 / [4,5,6] -> 7
# x로 만약 5, 6, 7을 넣으면 8이 나올 것이라고 예측하는 것
# 2,3이 겹치고, 3,4가 겹치고, 4,5가 겹치고, 5,6이 겹치고
y = np.array([4, 5, 6, 7])
# 주식도 마찬가지로 1,2,3일 종가 데이터를 넣고 4일의 종가를 예측하는 것

# 케라스에서는 층(layer)을 조합하여 모델(model)을 만든다.
# 가장 흔한 모델 구조는 층을 차례대로 쌓은 Sequential 모델
model = Sequential()

# LSTM 활용하기 위해서는 3차원 데이터가 필요
# [data_size, time_steps, features] 3차원 array로 구성
# data_size : 데이터가 몇 개 인지 (4개)
#     ** data_size 는 생략 -> input_shape 에서 자동 계산
# time_steps : 한 묶음에 몇 개의 데이터가 있는지 (3개)
# features : 속성(컬럼)의 수 (차원) (1개) 
# 나중에는 features 가 종가, 거래량 등등 여러개가 될 수 있다.
# units : layer의 node수 , 메모리 셀의 개수(기억용량 정도)
# 1이면 예측 값이 확 떨어진다.
model.add(LSTM(units=32, input_shape=(3, 1)))  # input_shape = time_steps=3, features=1
model.add(Dense(units=1))  # 출력층

# loss : 최적화 과정에서 최소화될 손실 함수(loss function)를 설정
# mae : mean absolute error (평균 절대 오차)
#      (수치가 작은수록 정확성이 높은 것)
# optimizer : 최적화 알고리즘 선택
model.compile(loss='mae', optimizer='adam')

# model.fit (모델을 훈련 시키는 명령어)
# X[:,:,np.newaxis] -> X(2차원 배열) 에 축을 하나 추가해서 3차원 배열을 만드는 것 / lstm input 값은 3차원 데이터
# X[:, :, np.newaxis].shape = (4, 3, 1) -> 4개의 데이터(data_size), 3개의 시간 단계 (time_steps), 1개의 특성의 수(feature)
# y: 예측 정답지
# epochs : 학습을 1000번 돌리겠다.
# verbose : 학습 되는 로그 출력 여부(1:출력, 0: 출력x)
# 0 으로 해야 속도가 더 빠른다. 
model.fit(X[:, :, np.newaxis], y, epochs=1000, verbose=1)

# 이렇게 학습을 했을때 5, 6, 7을 넣으면 8을 예측할 수 있을까?
h = model.history.history
plt.plot(h['loss'])  # loss의 오차가 줄어들수록 훈련이 잘 된다는 것
# 그래프로 보기 위한 명령
plt.show()

# model.predict : 실제 위에서 만든 모델로 예측
# reshape : 기존 데이터는 유지하고 차원과 형상을 바꾸기 위해 사용, 아래는 3차원 1 * 3 * 1
# predict에 넣을 때도 3차원 데이터로 넣어야 한다. (1, 3, 1) -> 1개의 데이터, 3개의 시간 단계, 1개의 특성의 수
# 5, 6, 7을 넣었을 때 8이 나올 것이라고 예측 -> 7.88이 나온다.
predict = model.predict(np.array([5, 6, 7]).reshape(1, 3, 1))

# 백데이터가 많아야 좀 더 정확한 예측이 가능
print(predict)
