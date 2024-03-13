import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error as mae
from datetime import timedelta
import pickle
import os


PATH_FORE_CASTS = os.environ.get("PATH_FORE_CASTS")
PATH_PLACES     = os.environ.get("PATH_PLACES")

PATH_DUMP_KAIKA  = os.environ.get("PATH_DUMP_KAIKA")
PATH_DUMP_MANKAI = os.environ.get("PATH_DUMP_MANKAI")

BASE_DATE = os.environ.get("BASE_DATE")
BASE_DATE_DATETIME = pd.to_datetime(BASE_DATE)
BASE_TIMEDELTA = timedelta(days=1)

TEST_SIZE = 0.2
# TODO: LightGBMなどやるときの変数
#EVAL_METRICS = "mae"
# ROUND = 1000
# STOPPING_ROUND = 100

COL_PLACE_CODE = "place_code"
COL_DATE       = "date"
COL_KAIKA      = "kaika_date"
COL_MANKAI     = "mankai_date"
COLS_DROP = [COL_PLACE_CODE, "meter", "tavg", "tmin", "tmax", "prcp", "prefecture_en", "prefecture_jp", "spot_name"]


'''
与えられたデータフレーム・目的変数から重回帰分析モデルを作成する

Args:
    df (pd.DataFrame): 教師データ.
    objectiv_col (str): 目的変数.

Returns:
    LinearRegression: 作成した重回帰分析のモデル
'''
def create_linear_regression_model(df: pd.DataFrame, objectiv_col: str):
  train_x, train_y, val_x, val_y = split_data_frame(df, objectiv_col)

  print("train start!")
  model = LinearRegression()
  model.fit(train_x, train_y)
  print("train end!")

  # maeでモデル評価
  print("mae↓")
  vals = model.predict(val_x)
  print(mae(vals, val_y))

  return model

"""
データをトレーニングデータと検証用データに分割する

Args:
    df (pd.DataFrame): 教師データ.
    objectiv_col (str): 目的変数.

Returns:
    List[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]: トレーニング用説明変数、トレーニング用目的変数、検証用説明変数、検証用目的変数をまとめたリスト
"""
def split_data_frame(df:pd.DataFrame, objectiv_col:str):
  df_train, df_val =train_test_split(df, test_size=TEST_SIZE)
  train_y = df_train[objectiv_col]
  train_x = df_train.drop(objectiv_col, axis=1)

  val_y = df_val[objectiv_col]
  val_x = df_val.drop(objectiv_col, axis=1)
  return [train_x, train_y, val_x, val_y]

"""
開花予測データを取得する

Returns:
    pd.DataFrame: 開花予測データ
"""
def get_forecasts_data():
  return pd.read_csv(PATH_FORE_CASTS)

"""
桜スポットの位置データを取得する

Returns:
    pd.DataFrame: 桜スポットの位置データ
"""
def get_places_data():
  return pd.read_csv(PATH_PLACES)

"""
予測に使用するデータを取得する

Returns:
    pd.DataFrame: 予測用データ
"""
def get_data():
  df_forecasts = get_forecasts_data()
  df_places = get_places_data()
  df = pd.merge(df_forecasts, df_places, on=COL_PLACE_CODE)
  return df

"""
日付と基準日の差を計算する

Args:
    date_str (str): 日付（YYYY-MM-DD形式）

Returns:
    float: 引数に与えた日付と基準日の差（単位：日）
"""
def minus_base_date(date_str:str):
  delta = pd.to_datetime(date_str) - BASE_DATE_DATETIME
  return (delta / BASE_TIMEDELTA)

"""
データの前処理を行う

Args:
    df (pd.DataFrame): 元データ

Returns:
    pd.DataFrame: 前処理を行ったデータ
"""
def preprocess_data(df: pd.DataFrame):
  # 不要なcol削除
  ret_df = df.drop(columns=COLS_DROP)
  
  # 最新日のみにフィルタリング
  max_date = max(ret_df[COL_DATE])
  ret_df = ret_df[ret_df[COL_DATE] == max_date]

  # フィルタリングしたらdate列も不要
  ret_df = ret_df.drop(columns=[COL_DATE])

  # 日付を差に変換
  ret_df[COL_KAIKA]  = ret_df[COL_KAIKA].apply(minus_base_date)
  ret_df[COL_MANKAI] = ret_df[COL_MANKAI].apply(minus_base_date)
  
  return ret_df

#モデルのダンプ
def dump_model(kaika_model:any, mankai_model:any):
  with open(PATH_DUMP_KAIKA, mode='wb') as f:
      pickle.dump(kaika_model, f, protocol=2)
  
  with open(PATH_DUMP_MANKAI, mode='wb') as f:
      pickle.dump(mankai_model, f, protocol=2)

def main():
  df = preprocess_data(get_data())

  # データから満開日のデータを削ったデータで、開花日を予測するモデルを作成
  kaika_model  = create_linear_regression_model(df.drop(columns=COL_MANKAI), COL_KAIKA)
  # 開花日を削ったデータで、満開日を予測するモデルを作成
  mankai_model = create_linear_regression_model(df.drop(columns=COL_KAIKA), COL_MANKAI)

  #モデルの保存
  dump_model(kaika_model, mankai_model)


main()