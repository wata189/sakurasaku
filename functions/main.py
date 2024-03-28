import os
import pickle
import pandas as pd
import geopandas as gpd
import geopandas.tools as gpt
from datetime import timedelta
from sklearn.linear_model import LinearRegression
from google.cloud import storage

ENV = os.environ.get("ENV")
CLIENT_URL  = os.environ.get("CLIENT_URL")
headers = {
  "Access-Control-Allow-Origin": CLIENT_URL
}

FILE_NAME_KAIKA  = os.environ.get("FILE_NAME_KAIKA")
FILE_NAME_MANKAI = os.environ.get("FILE_NAME_MANKAI")

PATH_LOCAL_BUCKET = os.environ.get("PATH_LOCAL_BUCKET")

GCP_CLOUD_STORAGE_BUCKET = os.environ.get("GCP_CLOUD_STORAGE_BUCKET")
# 開発環境ではない場合はGCPに接続
if(ENV != "development"):
  client = storage.Client()
  bucket = client.bucket(GCP_CLOUD_STORAGE_BUCKET)

BASE_DATE = os.environ.get("BASE_DATE")
BASE_DATE_DATETIME = pd.to_datetime(BASE_DATE)
BASE_TIMEDELTA = timedelta(days=1)

def main(request):
  query_parameter = request.args.to_dict()


  #パラメータチェック
  check_obj = check_query_parameter(query_parameter)
  if not(check_obj["result"]):
    # エラー返す処理
    return (check_obj, check_obj["status_code"], headers)

  lat_param = float(query_parameter.get("lat"))
  lon_param = float(query_parameter.get("lon"))
  forecast = forecast_date(lat_param, lon_param)

  return (forecast, 200, headers)

def check_query_parameter(query_parameter:dict):
  result = True
  status_code = 200
  err_msg = None

  lat_param = query_parameter.get("lat")
  lon_param = query_parameter.get("lon")
  check_list = [
    # lat, lonが存在すること
    {"function": is_exist, "param": lat_param, "status_code": 400, "err_msg": "緯度が入力されていません"},
    {"function": is_exist, "param": lon_param, "status_code": 400, "err_msg": "経度が入力されていません"},
    # lat, lonがfloat型に変換できること
    {"function": is_float, "param": lat_param, "status_code": 400, "err_msg": "緯度は数値を入力してください"},
    {"function": is_float, "param": lon_param, "status_code": 400, "err_msg": "経度は数値を入力してください"},
    # lat, lonが範囲内であること
    {"function": is_latitude, "param": lat_param, "status_code": 400, "err_msg": "緯度は90以下を入力してください"},
    {"function": is_longitude, "param": lon_param, "status_code": 400, "err_msg": "経度は180以下を入力してください"},

    # lat, lonが日本国内であること
    {"function": is_japan, "param": {"lat": lat_param, "lon": lon_param}, "status_code": 400, "err_msg": "その地点は日本ではありません"}
  ]

  for check in check_list:
    if not(check["function"](check["param"])):
      result = False
      status_code = check["status_code"]
      err_msg = check["err_msg"]
      break

  return {
    "result": result,
    "status_code": status_code,
    "err_msg": err_msg
  }

def is_exist(param:any):
  return param is not None

def is_float(param:str):
  try:
      float(param)  # 文字列を実際にfloat関数で変換してみる
  except ValueError:
      return False
  else:
      return True

def is_latitude(param:str):
  return -90 <= float(param) <= 90

def is_longitude(param:str):
  return -180 <= float(param) <= 180
  
def is_japan(param:dict):
  lat = float(param.get("lat"))
  lon = float(param.get("lon"))

  df = pd.DataFrame([{"lat_center": lat, "lon_center": lon}])
  gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon_center, df.lat_center))
  reverse_geocodes = gpt.reverse_geocode(gdf["geometry"], provider='nominatim', user_agent='test')
  address = reverse_geocodes["address"][0]
  print(address)

  if address is None:
    return False

  country = address.split(",")[-1] # geopandasからの返却値addressは最後尾に国名が入っている
  return str.strip(country) == "日本"



def forecast_date(lat_param:float, lon_param:float):
  # モデルをダンプしたファイルから取り出し
  kaika_model, mankai_model = open_model()

  # 日数を予測
  param = pd.DataFrame([{"lat":lat_param, "lon":lon_param}])
  kaika_days  = kaika_model.predict(param)
  mankai_days = mankai_model.predict(param)

  kaika_date  = plus_base_date(kaika_days[0])
  mankai_date = plus_base_date(mankai_days[0])

  return {
    "kaika_date": kaika_date.strftime("%Y-%m-%d"),
    "mankai_date": mankai_date.strftime("%Y-%m-%d")
  }

def open_model():
  kaika_model = open_model_file(FILE_NAME_KAIKA)
  mankai_model = open_model_file(FILE_NAME_MANKAI)
  return [kaika_model, mankai_model]

def open_model_file(file_name:str):
  model = None
  # 開発環境の場合はローカルファイルから取り出し
  if(ENV == "development"):
    with open(os.path.join(PATH_LOCAL_BUCKET, file_name), mode='rb') as f:
      model:LinearRegression = pickle.load(f)
  else:
    # 本番などの場合はGCPに接続
    blob = bucket.blob(file_name)
    model = pickle.loads(blob.download_as_string())
  
  return model


"""
基準日に日数を足した日付を取得する

Args:
    days (float): 日数

Returns:
    pd.Timestamp: 基準日に日数を足した日付
"""
def plus_base_date(days:float) -> pd.Timestamp:
  return (BASE_DATE_DATETIME + BASE_TIMEDELTA * days)
