import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error as mae
from datetime import timedelta
import pickle
import os
from google.cloud import storage
from sklearn.preprocessing import PolynomialFeatures

# 定数設定
ENV = "development"

PATH_DATA_FORECASTS = "../data/cherry_blossom_forecasts.csv"
PATH_DATA_PLACES    = "../data/cherry_blossom_places.csv"

FILE_NAME_KAIKA  = "model_kaika.sav"
FILE_NAME_MANKAI = "model_mankai.sav"

PATH_LOCAL_BUCKET = "functions/bucket"


BASE_DATE = "2024-01-01"
BASE_DATE_DATETIME = pd.to_datetime(BASE_DATE)
BASE_TIMEDELTA = timedelta(days=1)

TEST_SIZE = 0.2
# TODO: LightGBMなどやるときの変数
#EVAL_METRICS = "mae"
# ROUND = 1000
# STOPPING_ROUND = 100

# カラム名を定数に設定
COL_CODE       = "code"
COL_PLACE_CODE = "place_code"
COL_DATE       = "date"
COL_KAIKA      = "kaika_date"
COL_MANKAI     = "mankai_date"
COLS_DROP = [COL_CODE, "meter", "tavg", "tmin", "tmax", "prcp", "prefecture_en", "prefecture_jp", "spot_name"]

def create_polynomial_linear_regression_model(df: pd.DataFrame, objectiv_col: str, degree: int):
  """
  与えられたデータフレーム・目的変数から多項式回帰分析モデルを作成する

  Args:
      df (pd.DataFrame): 教師データ.
      objectiv_col (str): 目的変数.
      degree (int): 多項式の次数.

  Returns:
      LinearRegression: 作成した多項式回帰分析のモデル
  """
  train_x, train_y, val_x, val_y = split_data_frame(df, objectiv_col)
  quadratic = PolynomialFeatures(
    degree=degree,                  # 多項式の次数
    interaction_only=False,    # Trueの場合、ある特徴量を2乗以上した項が除かれる
    include_bias=True,         # Trueの場合、バイアス項を含める
    order='C'                  # 出力する配列の計算順序
  )


  print("train start!")
  model = LinearRegression()
  model.fit(quadratic.fit_transform(train_x), train_y)
  print("train end!")

  # maeでモデル評価
  print("mae↓")
  vals = model.predict(quadratic.fit_transform(val_x))
  print(mae(vals, val_y))

  return model

def create_log_linear_regression_model(df: pd.DataFrame, objectiv_col: str):
  """
  与えられたデータフレーム・目的変数から対数回帰分析モデルを作成する

  Args:
      df (pd.DataFrame): 教師データ.
      objectiv_col (str): 目的変数.

  Returns:
      LinearRegression: 作成した対数回帰分析のモデル
  """
  train_x, train_y, val_x, val_y = split_data_frame(df, objectiv_col)


  print("train start!")
  model = LinearRegression()
  model.fit(train_x.apply(np.log), train_y)
  print("train end!")

  # maeでモデル評価
  print("mae↓")
  vals = model.predict(val_x.apply(np.log))
  print(mae(vals, val_y))

  return model

def create_sqrt_linear_regression_model(df: pd.DataFrame, objectiv_col: str):
  """
  与えられたデータフレーム・目的変数からルートの回帰分析モデルを作成する

  Args:
      df (pd.DataFrame): 教師データ.
      objectiv_col (str): 目的変数.

  Returns:
      LinearRegression: 作成したルートの回帰分析のモデル
  """
  train_x, train_y, val_x, val_y = split_data_frame(df, objectiv_col)


  print("train start!")
  model = LinearRegression()
  model.fit(train_x.apply(np.sqrt), train_y)
  print("train end!")

  # maeでモデル評価
  print("mae↓")
  vals = model.predict(val_x.apply(np.sqrt))
  print(mae(vals, val_y))

  return model

def create_linear_regression_model(df: pd.DataFrame, objectiv_col: str):
  """
  与えられたデータフレーム・目的変数から重回帰分析モデルを作成する

  Args:
      df (pd.DataFrame): 教師データ.
      objectiv_col (str): 目的変数.

  Returns:
      LinearRegression: 作成した重回帰分析のモデル
  """
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


def split_data_frame(df:pd.DataFrame, objectiv_col:str):
  """
  データをトレーニングデータと検証用データに分割する

  Args:
      df (pd.DataFrame): 教師データ.
      objectiv_col (str): 目的変数.

  Returns:
      List[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]: トレーニング用説明変数、トレーニング用目的変数、検証用説明変数、検証用目的変数をまとめたリスト
  """
  df_train, df_val =train_test_split(df, test_size=TEST_SIZE)
  train_y = df_train[objectiv_col]
  train_x = df_train.drop(objectiv_col, axis=1)

  val_y = df_val[objectiv_col]
  val_x = df_val.drop(objectiv_col, axis=1)
  return [train_x, train_y, val_x, val_y]

def get_forecasts_data():
  """
  開花予測データを取得する

  Returns:
      pd.DataFrame: 開花予測データ
  """
  return pd.read_csv(PATH_DATA_FORECASTS)

def get_places_data():
  """
  桜スポットの位置データを取得する

  Returns:
      pd.DataFrame: 桜スポットの位置データ
  """
  return pd.read_csv(PATH_DATA_PLACES)

def get_data():
  """
  予測に使用するデータを取得する

  Returns:
      pd.DataFrame: 予測用データ
  """
  df_forecasts = get_forecasts_data()
  df_places = get_places_data()
  df = pd.merge(df_forecasts, df_places, left_on=COL_PLACE_CODE, right_on=COL_CODE)
  return df


def minus_base_date(date_str:str):
  """
  日付と基準日の差を計算する

  Args:
      date_str (str): 日付（YYYY-MM-DD形式）

  Returns:
      float: 引数に与えた日付と基準日の差（単位：日）
  """
  delta = pd.to_datetime(date_str) - BASE_DATE_DATETIME
  return (delta / BASE_TIMEDELTA)

def preprocess_data(df: pd.DataFrame):
  """
  データの前処理を行う

  Args:
      df (pd.DataFrame): 元データ

  Returns:
      pd.DataFrame: 前処理を行ったデータ
  """
  # 不要なcol削除
  ret_df = df.drop(columns=COLS_DROP)
  
  # place_codeごとに最新の日付を取得してフィルタリング
  ret_df["max_date"] = ret_df.groupby(COL_PLACE_CODE).transform(np.max)[COL_DATE]
  ret_df = ret_df[ret_df["max_date"] == ret_df[COL_DATE]]

  # フィルタリングしたら日付、place_codeも不要
  ret_df = ret_df.drop(columns=[COL_DATE, COL_PLACE_CODE, "max_date"])

  # 日付を差に変換
  ret_df[COL_KAIKA]  = ret_df[COL_KAIKA].apply(minus_base_date)
  ret_df[COL_MANKAI] = ret_df[COL_MANKAI].apply(minus_base_date)
  
  return ret_df

def dump_model(kaika_model:any, mankai_model:any):
  """
  作成したモデルをファイルとして保存する
  モデルの種類は変わっていくため、引数はany型にしておく

  Args:
      kaika_model (any): 開花日の予測モデル
      mankai_model (any): 満開日の予測モデル

  Returns:
      None

  """
  dump_file(kaika_model, FILE_NAME_KAIKA)
  dump_file(mankai_model, FILE_NAME_MANKAI)

def dump_file(file: any, file_name: str):
  """
  ファイルをローカルまたはCloud Storageにダンプする

  Args:
      file_name (str): ファイル名
  
  Returns:
      None
  """
  if ENV == "development":
    with open(os.path.join(PATH_LOCAL_BUCKET, file_name), mode='wb') as f:
        pickle.dump(file, f, protocol=2)


