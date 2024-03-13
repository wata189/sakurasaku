import os
import pickle
import pandas as pd
from datetime import timedelta
from sklearn.linear_model import LinearRegression

def main(request):
  query_parameter = request.args.to_dict()

  lat_param = query_parameter.get("lat")
  lon_param = query_parameter.get("lon")

  ###########TODO:パラメータチェック
  # TODO: lat, lonが存在すること
  # TODO: lat, lonがfloat型なこと
  # TODO: lat, lonの範囲チェック　日本国内想定

  forecast = forecast_date(float(lat_param), float(lon_param))

  return forecast

PATH_DUMP_KAIKA  = os.environ.get("PATH_DUMP_KAIKA")
PATH_DUMP_MANKAI = os.environ.get("PATH_DUMP_MANKAI")

BASE_DATE = os.environ.get("BASE_DATE")
BASE_DATE_DATETIME = pd.to_datetime(BASE_DATE)
BASE_TIMEDELTA = timedelta(days=1)

def forecast_date(lat_param:float, lon_param:float):
  # モデルをダンプしたファイルから取り出し
  kaika_model, mankai_model = open_model()

  # 日数を予測
  param = pd.DataFrame([{"lat":lat_param, "lon":lon_param}])
  kaika_days  = kaika_model.predict(param)
  mankai_days = mankai_model.predict(param)

  kaika_date  = plus_base_date(kaika_days[0])
  mankai_date = plus_base_date(mankai_days[0])

  return {"kaika_date": kaika_date, "mankai_date": mankai_date}

def open_model():
  with open(PATH_DUMP_KAIKA, mode='rb') as f:
      kaika_model = pickle.load(f)

  with open(PATH_DUMP_MANKAI, mode='rb') as f:
      mankai_model = pickle.load(f)

  return [kaika_model, mankai_model]

"""
基準日に日数を足した日付を取得する

Args:
    days (float): 日数

Returns:
    pd.Timestamp: 基準日に日数を足した日付
"""
def plus_base_date(days:float):
  return (BASE_DATE_DATETIME + BASE_TIMEDELTA * days)
