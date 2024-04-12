import zipfile
import shutil
import os

ZIP_FILE_NAME = "japan-cherry-blossoms-forecasts-2024.zip"
OUT_DIR = "data"

# いったんdataフォルダ削除
if os.path.isdir(OUT_DIR):
  shutil.rmtree(OUT_DIR)
# zipファイルをdataフォルダに展開
shutil.unpack_archive(ZIP_FILE_NAME, OUT_DIR)

# zipファイルも削除
os.remove(ZIP_FILE_NAME)