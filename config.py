import os
import shutil

# =========================
# 1. 项目根目录（核心）
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(BASE_DIR)

BASE_DIR_CACHE = os.path.join(BASE_DIR, "cache")
print(BASE_DIR_CACHE)

if not os.path.exists(BASE_DIR_CACHE):
    os.makedirs(BASE_DIR_CACHE)


# =========================
# 2. 输入 / 输出路径
# =========================
# /Users/lumiere/PycharmProjects/PythonProject/batch_baidu_translate/batch_baidu_translate_release/code V5/translated_done
INPUT_DIR = os.path.join(BASE_DIR_CACHE, "input")
OUTPUT_DIR = os.path.join(BASE_DIR_CACHE, "output")
FINAL_DIR = os.path.join(BASE_DIR_CACHE, "translated_done")

# 自动创建目录（防止报错）
for path in [INPUT_DIR, OUTPUT_DIR, FINAL_DIR]:
    os.makedirs(path, exist_ok=True)

# =========================
# 3. 翻译API配置
# =========================
# APP_ID = "20251212002517465"
# SECRET_KEY = "vQcCfc0BtIjU8F1J8vw7"
APP_ID = "1"
SECRET_KEY = "12"
API_URL = "https://fanyi-api.baidu.com/api/trans/vip/translate"

# =========================
# 4. 性能参数
# =========================
MAX_QPS = 10      # 每秒最大请求数
THREADS = 10      # 线程数

# =========================
# 5. 日志路径
# =========================
CACHE_FILE = os.path.join(BASE_DIR_CACHE, "translation_cache.json")
FAILED_LOG = os.path.join(BASE_DIR_CACHE, "failed_log.txt")
QUOTE_LOG = os.path.join(BASE_DIR_CACHE, "quote_clean_log.txt")
print("缓存路径：",CACHE_FILE)
# =========================
# 6. 术语保护
# =========================
PROTECTED_TERMS = {"'Home", "'Alert", "'Config", "'Data", "'Vision", "'Setting"}
# print("PROTECTED_TERMS", PROTECTED_TERMS)