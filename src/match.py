# module
import os
import cv2
import requests
import numpy as np
from fastapi import FastAPI, File
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import APIRouter

load_dotenv()

router = APIRouter()

class ImageRequest(BaseModel):
    img_url: str

# 一致とみなす閾値
positive_threshold = 0.8  # 0.8 ~ 1.0 の範囲
negative_threshold = -0.8 # -0.8 ~ -1.0 の範囲

# キャプチャされたスクリーンショットがリザルト画面と一致するかチェック
def check_result_screen(screenshot_img, template_img):
    # カラー画像のままでテンプレートマッチングを実行
    screenshot = cv2.cvtColor(screenshot_img, cv2.COLOR_BGR2GRAY)
    template = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    
    # 画像をリサイズ
    template = cv2.resize(template, (1920, 1080))
    
    # # エッジ強調 (オプション)
    # screenshot = cv2.Canny(screenshot, 50, 150)
    # template = cv2.Canny(template, 50, 150)

    # トリミング
    screenshot = screenshot[935:935+60, 832:832+100]
    template = template[935:935+60, 832:832+100]

    # テンプレートマッチング
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"max_val: {max_val}")

    # max_val が指定された範囲にあるかどうかを判定
    if positive_threshold <= max_val <= 1.0 or -1.0 <= max_val <= negative_threshold:
        return True
    else:
        return False


# スクリーンショットが取得されたときに呼び出される処理
@router.post("/")
def process_screenshot(file: bytes = File()):
    # 画像の読み込み
    response = requests.get(os.getenv("TEMPLATE_IMAGE_URL"))

    # 画像データをnumpy配列に変換
    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)

    # 画像データをデコードし、cv2形式で読み込む
    template = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    screenshot = cv2.imdecode(np.frombuffer(file, np.uint8), cv2.IMREAD_COLOR)

    if screenshot is None:
        print(f"Error: Could not load image from {screenshot}")
        return

    if check_result_screen(screenshot, template):
        print("Success: リザルト画面が確認されました。")
        return 'success'
    else:
        print("No match: リザルト画面ではありません。")
        return 'fail'
