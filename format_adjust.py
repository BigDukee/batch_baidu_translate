import os
import pandas as pd
import chardet

# =========================
# 新增：引入统一配置
# =========================
from config import OUTPUT_DIR, FINAL_DIR, QUOTE_LOG

# ---------------------------------------------
# Author: Lumiere
# Email: bigdukeyang@gmail.com
# Project: This is a Python batch translation tool that uses Baidu Translate API to translate Chinese content in CSV files into English and Vietnamese.
# ---------------------------------------------

# =========================
# ❌ 原始配置（已废弃，保留用于对照）
# =========================
# input_folder = "/Users/lumiere/PycharmProjects/PythonProject/batch_baidu_translate/batch_baidu_translate_release/code/output"
# output_root = os.path.join(os.path.dirname(input_folder.rstrip("/")), "translated_done")
# log_file = os.path.join(output_root, "quote_clean_log.txt")
#
# os.makedirs(output_root, exist_ok=True)
#
# with open(log_file, "w", encoding="utf-8") as f:
#     f.write("=== 多余引号清理记录 ===\n\n")

# =========================
# 新配置（来自 config）
# =========================
input_folder = OUTPUT_DIR
output_root = FINAL_DIR
log_file = QUOTE_LOG

# 自动创建目录
os.makedirs(output_root, exist_ok=True)

# 初始化日志
with open(log_file, "w", encoding="utf-8") as f:
    f.write("=== 多余引号清理记录 ===\n\n")


def log_change(filename, col_name, original, fixed):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{filename}] 列: {col_name}\n")
        f.write(f"  原始: {original}\n")
        f.write(f"  修正: {fixed}\n\n")


def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        raw = f.read()
    return chardet.detect(raw)["encoding"]


def try_read_with_sep(path, enc, sep):
    return pd.read_csv(path, dtype=str, encoding=enc, engine="python", sep=sep)


def read_with_auto_sep(path, enc):
    for sep in [",", "\t", ";"]:
        try:
            df = try_read_with_sep(path, enc, sep)
            if len(df.columns) >= 4:
                return df, sep
        except Exception:
            pass

    df = try_read_with_sep(path, enc, ",")
    return df, ","


def normalize_quote(value, filename, col_name):
    if pd.isna(value):
        return value

    s = str(value)
    original = s
    s_clean = s.replace("'", "")
    fixed = "'" + s_clean

    if original != fixed:
        log_change(filename, col_name, original, fixed)

    return fixed


def process_csv(src, dst):
    filename = os.path.basename(src)
    enc = detect_encoding(src)
    print(f"\n处理文件: {filename}   编码: {enc}")

    try:
        df, sep = read_with_auto_sep(src, enc)
    except Exception as e:
        print(f"无法读取（尝试多种分隔符）：{src}\n错误: {e}")
        return

    if len(df.columns) < 4:
        print(f"跳过 (列少于4): {src}")
        return

    col3 = df.columns[2]
    col4 = df.columns[3]

    df[col3] = df[col3].apply(lambda v: normalize_quote(v, filename, col3))
    df[col4] = df[col4].apply(lambda v: normalize_quote(v, filename, col4))

    os.makedirs(os.path.dirname(dst), exist_ok=True)

    try:
        df.to_csv(dst, index=False, encoding=enc, sep=sep)
        print(f"已保存: {dst}")
    except Exception:
        df.to_csv(dst, index=False, encoding="utf-8-sig", sep=sep)
        print(f"原编码保存失败，已用 utf-8-sig 保存: {dst}")


def batch_process_folder(folder):
    files = sorted(os.listdir(folder))
    for filename in files:
        if not filename.lower().endswith(".csv"):
            continue

        src = os.path.join(folder, filename)
        dst = os.path.join(output_root, filename)

        process_csv(src, dst)


# =========================
# 新增：主入口函数
# =========================
def main():
    print("========== 格式修正开始 ==========")
    print("输入目录:", input_folder)
    print("输出目录:", output_root)
    print("日志文件:", log_file)

    batch_process_folder(input_folder)

    print("\n全部文件处理完成！")
    print(f"Log 记录已保存到: {log_file}")
    print("========== 格式修正结束 ==========")


if __name__ == "__main__":
    main()