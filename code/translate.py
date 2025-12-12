import os
import pandas as pd
import chardet
import requests
import hashlib
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json

# ---------------------------------------------
# Author: Lumiere
# Email: bigdukeyang@gmail.com
# Project: This is a Python batch translation tool that uses Baidu Translate API to translate Chinese content in CSV files into English and Vietnamese.
# ---------------------------------------------


APP_ID = "*******************"
SECRET_KEY = "*******************"
API_URL = "https://fanyi-api.baidu.com/api/trans/vip/translate"

MAX_QPS = 10
THREADS = 10

request_count = 0
request_lock = threading.Lock()
last_reset_time = time.time()

translation_cache = {}
failed_log = []

INPUT_DIR = r"/Users/lumiere/PycharmProjects/PythonProject/batch_baidu_translate/test/translate_file"
OUTPUT_DIR = r"/Users/lumiere/PycharmProjects/PythonProject/batch_baidu_translate/test/translated_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def rate_limit():
    global request_count, last_reset_time
    with request_lock:
        now = time.time()
        if now - last_reset_time >= 1:
            request_count = 0
            last_reset_time = now
        if request_count >= MAX_QPS:
            time.sleep(max(0, 1 - (now - last_reset_time)))
            request_count = 0
            last_reset_time = time.time()
        request_count += 1

def baidu_translate(text, lang):
    if not isinstance(text, str):
        text = str(text)
    if text.strip() == "":
        return ""
    if text in translation_cache and lang in translation_cache[text]:
        return translation_cache[text][lang]

    for _ in range(3):
        try:
            rate_limit()
            salt = str(random.randint(32768, 65536))
            sign = make_md5(APP_ID + text + salt + SECRET_KEY)
            params = {"q": text, "from": "auto", "to": lang, "appid": APP_ID, "salt": salt, "sign": sign}
            res = requests.post(API_URL, data=params, timeout=5).json()
            if "trans_result" in res:
                dst = res["trans_result"][0]["dst"]
                translation_cache.setdefault(text, {})[lang] = dst
                return dst
            time.sleep(0.2)
        except:
            time.sleep(0.3)
    failed_log.append(f"[FAIL] {text}\n")
    return text

def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        return chardet.detect(f.read())['encoding']

def translate_line(idx, text):
    en = baidu_translate(text, "en")
    # 修改中文翻译越南语不对的bug
    # vie = baidu_translate(text, "vie")
    vie = baidu_translate(en, "vie") if en.strip() else ""
    return idx, en, vie

def process_csv(csv_file):
    print(f"\n处理文件：{csv_file}")
    enc = detect_encoding(csv_file)
    sep = "\t" if "utf-16" in enc.lower() else ","
    df = pd.read_csv(csv_file, encoding=enc, sep=sep)
    texts = list(df.iloc[:, 1])
    results = [None] * len(texts)

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(translate_line, i, t) for i, t in enumerate(texts)]
        for future in tqdm(as_completed(futures), total=len(futures), desc="翻译进度"):
            i, en, vie = future.result()
            results[i] = (en, vie)

    df.iloc[:, 2] = [r[0] for r in results]
    df.iloc[:, 3] = [r[1] for r in results]

    out_file = os.path.join(OUTPUT_DIR, os.path.basename(csv_file))
    df.to_csv(out_file, index=False, encoding=enc, sep=sep)
    print(f"保存完成：{out_file}")

def main():
    files = [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    if not files:
        print("translate_file 文件夹内没有 CSV 文件")
        return

    for f in files:
        process_csv(f)
        with open("translation_cache.json", "w", encoding="utf-8") as cache_file:
            json.dump(translation_cache, cache_file, ensure_ascii=False, indent=2)

    if failed_log:
        with open("failed_log.txt", "w", encoding="utf-8") as log_file:
            log_file.writelines(failed_log)
        print(f"翻译失败 {len(failed_log)} 条，已写入 failed_log.txt")
    else:
        print("全部翻译成功！")

if __name__ == "__main__":
    main()
