ver = "#version 0.0.2"
print(f"demo Version: {ver}")

import os
import sys
import pymysql
import pandas as pd

from tensorflow.keras.layers import LSTM
from SPPModel import load_data, evaluate, DataNotEnough, create_model, predict, plot_graph, train

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from library import cf

conn = pymysql.connect(host=cf.db_ip,
                       port=int(cf.db_port),
                       user=cf.db_id,
                       password=cf.db_passwd,
                       db='daily_craw',
                       charset='utf8mb4')

# 5개를 특성으로 사용한다. 
FEATURE_COLUMNS = ["close", "volume", "open", "high", "low"]
code_name = '삼성전자'
start = '20200101'
until = '20250131'
# sql = """
#     SELECT {} FROM `{}`
#     WHERE STR_TO_DATE(date, '%Y%m%d%H%i') <= '{}'
# """.format(','.join(FEATURE_COLUMNS), code_name, until)
sql = """
    SELECT {} FROM `{}`
    WHERE STR_TO_DATE(date, '%Y%m%d%H%i') BETWEEN '{}' AND '{}'
""".format(','.join(FEATURE_COLUMNS), code_name, start, until)

df = pd.read_sql(sql, conn)
if not len(df):
    print(f'{code_name}의 {until}까지 데이터가 존재하지 않습니다.')
    exit(1)


# 하나의 시퀀스에 담을 데이터 수
N_STEPS = 100
# 단위 :(일/분) 몇 일(분) 뒤의 종가를 예측 할 것 인지 설정 : daily_craw -> 일 / min_craw -> 분
LOOKUP_STEP = 1
#  train 범위 : test_size 가 0.2 이면 X_train, y_train에 80% 데이터로 트레이닝 하고 X_test,y_test에 나머지 20%로 테스트를 하겠다는 의미
TEST_SIZE = 0.2

# layer 수
N_LAYERS = 4

CELL = LSTM
# layer의 node수
UNITS = 50

# overfitting 방지를 위해 몇개의 노드를 죽이고 남은 노드들을 통해서만 훈련을 하는 것(0.2 -> 20%를 죽인다)
# 마치 시험 문제의 답만 외워서 실제 응용문제는 못 푸는 것과 비슷하다. 실전에서 더 좋은 성능을 보임.
DROPOUT = 0.2

# mean absolute error (평균 절대 오차)
LOSS = "mae"

# 최적화 알고리즘 선택
OPTIMIZER = "adam"

# 각 학습 반복에 사용할 데이터 샘플 수
BATCH_SIZE = 64

# 학습 횟수
EPOCHS = 10

# 학습 시에는 셔플링을 통해 더 좋은 모델을 만들지만
# 실제 예측할 때는 시간 순서를 유지하여 예측의 정확성을 높인다. 
try:
    # shuffle: split을 해주기 이전에 시퀀스를 섞을건지 여부
    shuffled_data = load_data(df=df, n_steps=N_STEPS, lookup_step=LOOKUP_STEP, test_size=TEST_SIZE, shuffle=True)
except DataNotEnough:
    print('데이터가 충분하지 않습니다. ')
    exit(1)
model = create_model(n_steps=N_STEPS, loss=LOSS, units=UNITS, cell=CELL, n_layers=N_LAYERS, dropout=DROPOUT)

# 학습 시작, 학습 결과는 model에 반영이 되고, 기록은 history에 저장된다. 
history = train(shuffled_data, model, EPOCHS, BATCH_SIZE, verbose=1)

# shuffle 되지 않은 df로 다시 new_df에 저장
new_df = pd.read_sql(sql, conn)

data = load_data(df=new_df, n_steps=N_STEPS, lookup_step=LOOKUP_STEP, test_size=TEST_SIZE, shuffle=False)

mae = evaluate(data, model)
print(f"Mean Absolute Error: {mae}")

future_price = predict(data, model, n_steps=N_STEPS)
print(f"Future price after {LOOKUP_STEP} days is {future_price:.2f}")
plot_graph(model, data)
