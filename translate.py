import os
import pandas as pd
import chardet
import requests
import hashlib
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# ✅ 新增：程序退出自动保存用
import atexit

from config import (
    INPUT_DIR,
    OUTPUT_DIR,
    APP_ID,
    SECRET_KEY,
    API_URL,
    MAX_QPS,
    THREADS,
    CACHE_FILE,
    FAILED_LOG,
    PROTECTED_TERMS
)

# =========================
# 全局变量
# =========================
request_count = 0
request_lock = threading.Lock()
last_reset_time = time.time()

translation_cache = {}
failed_log = []

# =========================
# ✅ 新增：缓存保存控制（防止频繁写文件）
# =========================
save_counter = 0
SAVE_INTERVAL = 50  # 每50次翻译保存一次（可自行调整）

# =========================
# ✅ 缓存初始化
# =========================
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            translation_cache = json.load(f)
        print(f"已加载缓存：{len(translation_cache)} 条")
    except Exception as e:
        print(f"缓存加载失败，使用空缓存: {e}")
        translation_cache = {}
else:
    translation_cache = {}

# =========================
# 工具函数
# =========================
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
    global save_counter  # ✅ 新增

    if not isinstance(text, str):
        text = str(text)

    if text.strip() == "":
        return ""

    # # =========================
    # # ✅ 核心：严格术语保护（完全匹配）
    # # =========================
    # print(PROTECTED_TERMS)
    # if text in PROTECTED_TERMS:
    #     return text


    # ✅ 查缓存
    if text in translation_cache and lang in translation_cache[text]:
        return translation_cache[text][lang]

    for _ in range(3):
        try:
            rate_limit()

            salt = str(random.randint(32768, 65536))
            sign = make_md5(APP_ID + text + salt + SECRET_KEY)

            params = {
                "q": text,
                "from": "auto",
                "to": lang,
                "appid": APP_ID,
                "salt": salt,
                "sign": sign
            }

            res = requests.post(API_URL, data=params, timeout=5).json()

            if "trans_result" in res:
                dst = res["trans_result"][0]["dst"]

                translation_cache.setdefault(text, {})[lang] = dst

                # =========================
                # ✅ 新增：批量保存缓存
                # =========================
                save_counter += 1
                if save_counter >= SAVE_INTERVAL:
                    save_cache()
                    save_counter = 0

                return dst

            time.sleep(0.2)

        except Exception:
            time.sleep(0.3)

    failed_log.append(f"[FAIL] {text}\n")
    return text


def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        return chardet.detect(f.read())['encoding']


def translate_line(idx, text):
    # =========================
    # 严格术语保护（完全匹配）
    # =========================
    text_str = str(text).strip()
    if text_str in PROTECTED_TERMS:
        return idx, text_str, text_str

    en = baidu_translate(text, "en")
    vie = baidu_translate(en, "vie") if en.strip() else ""
    return idx, en, vie


# =========================
# ✅ 核心：支持进度回调
# =========================
def process_csv(csv_file, progress_callback=None):
    print(f"\n处理文件：{csv_file}")

    enc = detect_encoding(csv_file)
    sep = "\t" if enc and "utf-16" in enc.lower() else ","

    df = pd.read_csv(csv_file, encoding=enc, sep=sep)

    texts = list(df.iloc[:, 1])
    results = [None] * len(texts)

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(translate_line, i, t) for i, t in enumerate(texts)]

        total = len(futures)
        done_count = 0

        for future in as_completed(futures):
            i, en, vie = future.result()
            results[i] = (en, vie)

            done_count += 1

            # ✅ 回调 GUI
            if progress_callback:
                progress_callback(done_count, total)

    # 写回
    if df.shape[1] < 4:
        for _ in range(4 - df.shape[1]):
            df[f"new_col_{_}"] = ""

    df.iloc[:, 2] = [r[0] for r in results]
    df.iloc[:, 3] = [r[1] for r in results]

    out_file = os.path.join(OUTPUT_DIR, os.path.basename(csv_file))
    df.to_csv(out_file, index=False, encoding=enc, sep=sep)

    print(f"保存完成：{out_file}")


def save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(translation_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"缓存写入失败: {e}")


# =========================
# ✅ 新增：程序退出自动保存缓存
# =========================
atexit.register(save_cache)


def main():
    files = [
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.endswith(".csv")
    ]

    for f in files:
        process_csv(f)
        save_cache()

    if failed_log:
        with open(FAILED_LOG, "w", encoding="utf-8") as f:
            f.writelines(failed_log)


if __name__ == "__main__":
    main()