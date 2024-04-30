import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error as mae
from datetime import timedelta
import pickle
import os
from google.cloud import storage

# 環境変数読み込み
ENV = os.environ.get("ENV")

PATH_DATA_FORECASTS = os.environ.get("PATH_DATA_FORECASTS")
PATH_DATA_PLACES    = os.environ.get("PATH_DATA_PLACES")

FILE_NAME_KAIKA  = os.environ.get("FILE_NAME_KAIKA")
FILE_NAME_MANKAI = os.environ.get("FILE_NAME_MANKAI")

PATH_LOCAL_BUCKET = os.environ.get("PATH_LOCAL_BUCKET")

GCP_CLOUD_STORAGE_BUCKET = os.environ.get("GCP_CLOUD_STORAGE_BUCKET")
# 開発環境ではない場合はGCPに接続
if ENV != "development":
  client = storage.Client()
  bucket = client.bucket(GCP_CLOUD_STORAGE_BUCKET)

BASE_DATE = os.environ.get("BASE_DATE")
BASE_DATE_DATETIME = pd.to_datetime(BASE_DATE)
BASE_TIMEDELTA = timedelta(days=1)

TEST_SIZE = 0.2

# カラム名を定数に設定
COL_CODE       = "code"
COL_PLACE_CODE = "place_code"
COL_DATE       = "date"
COL_KAIKA      = "kaika_date"
COL_MANKAI     = "mankai_date"
COLS_DROP = [COL_CODE, "meter", "tavg", "tmin", "tmax", "prcp", "prefecture_en", "prefecture_jp", "spot_name"]


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
  else:
    # 本番モードではCloud Storageにアップロードする
    blob = storage.Blob(file_name, bucket)
    file_byte = pickle.dumps(file)
    blob.upload_from_string(file_byte, content_type='application/octet-stream')


# メイン処理開始
df = preprocess_data(get_data())

# データから満開日のデータを削ったデータで、開花日を予測するモデルを作成
kaika_model  = create_linear_regression_model(df.drop(columns=COL_MANKAI), COL_KAIKA)
# 開花日を削ったデータで、満開日を予測するモデルを作成
mankai_model = create_linear_regression_model(df.drop(columns=COL_KAIKA), COL_MANKAI)

#モデルの保存
dump_model(kaika_model, mankai_model)

