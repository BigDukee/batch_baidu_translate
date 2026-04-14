import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import os

import translate
import format_adjust

# ===== ✅ 新增：用于编码检测 =====
import pandas as pd
import chardet


# =========================
# GUI 主程序
# =========================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("yzy出品，必属精品")
        self.root.geometry("700x700")
        info_text = "适应VA的中英越语批量翻译工具 | Version: v6.1.1 | Build: 2026-04-14"
        tk.Label(root, text=info_text, fg="gray").pack(pady=5)

        # 运行状态锁（防止重复点击）
        self.is_running = False

        # ===== ✅ 新增：进度变量 =====
        self.current_done = 0
        self.current_total = 0
        self.progress_lock = threading.Lock()

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        # CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        # print(CURRENT_DIR)

        tk.Label(root, text="输入文件夹").pack()
        self.input_entry = tk.Entry(root, width=80)
        # self.input_entry.insert(0, CURRENT_DIR)
        self.input_entry.pack()
        tk.Button(root, text="选择", command=self.select_input).pack()

        tk.Label(root, text="输出文件夹").pack()
        self.final_entry = tk.Entry(root, width=80)
        # self.input_entry.insert(0, CURRENT_DIR)
        self.final_entry.pack()
        tk.Button(root, text="选择", command=self.select_final).pack()

        tk.Label(root, text="json配置文件路径（translation_cache.json，可选，选择后节约token）").pack()
        self.cache_entry = tk.Entry(root, width=80)
        # self.input_entry.insert(0, CURRENT_DIR)
        self.cache_entry.pack()
        tk.Button(root, text="选择", command=self.select_cache).pack()

        tk.Label(root, text="APP_ID（必填）").pack()
        self.appid_entry = tk.Entry(root, width=50)
        self.appid_entry.pack()

        tk.Label(root, text="SECRET_KEY（必填）").pack()
        self.secret_entry = tk.Entry(root, width=50, show="*")
        self.secret_entry.pack()

        tk.Label(root, text="MAX_QPS（可选，个人用户最大10）").pack()
        self.qps_entry = tk.Entry(root, width=20)
        self.qps_entry.pack()

        tk.Label(root, text="THREADS（可选，建议10）").pack()
        self.thread_entry = tk.Entry(root, width=20)
        self.thread_entry.pack()

        tk.Label(root, text="单文件进度").pack()
        self.progress_file = ttk.Progressbar(root, length=400)
        self.progress_file.pack()

        tk.Label(root, text="总进度").pack()
        self.progress_all = ttk.Progressbar(root, length=400)
        self.progress_all.pack()

        # ===== ✅ 新增：数字进度 =====
        self.progress_label = tk.Label(root, text="0 / 0")
        self.progress_label.pack()

        # 按钮引用（用于禁用/启用）
        self.start_button = tk.Button(root, text="开始", command=self.run_pipeline, bg="#4CAF50", fg="white")
        self.start_button.pack(pady=20)

    def select_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def select_final(self):
        path = filedialog.askdirectory()
        if path:
            self.final_entry.delete(0, tk.END)
            self.final_entry.insert(0, path)

    def select_cache(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            self.cache_entry.delete(0, tk.END)
            self.cache_entry.insert(0, path)

    # =========================
    # 主流程入口
    # =========================
    def run_pipeline(self):
        if self.is_running:
            return

        if not self.input_entry.get() or not self.final_entry.get():
            messagebox.showerror("错误", "输入路径和输出路径 必须填写！")
            return

        if self.input_entry.get() == self.final_entry.get():
            messagebox.showerror("错误", "输入路径和输出路径 不能是同一个文件夹")
            return

        # if not self.cache_entry.get():
        #     messagebox.showerror("错误", "JSON路径 必须填写！")
        #     return

        if not self.appid_entry.get() or not self.secret_entry.get():
            messagebox.showerror("错误", "APP_ID 和 SECRET_KEY 必须填写！")
            return



        self.is_running = True
        self.start_button.config(state="disabled")

        thread = threading.Thread(target=self.pipeline_task)
        thread.start()

    def pipeline_task(self):
        try:
            if self.input_entry.get():
                translate.INPUT_DIR = self.input_entry.get()

            if self.final_entry.get():
                format_adjust.output_root = self.final_entry.get()

            # if self.cache_entry.get():
            #     translate.CACHE_FILE = self.cache_entry.get()

            # =========================
            # SON路径逻辑
            # =========================
            if self.cache_entry.get():
                translate.CACHE_FILE = self.cache_entry.get()
            else:
                translate.CACHE_FILE = os.path.join(
                    self.final_entry.get(),
                    "translation_cache.json"
                )
            # 确保目录存在
            os.makedirs(os.path.dirname(translate.CACHE_FILE), exist_ok=True)

            translate.APP_ID = self.appid_entry.get()
            translate.SECRET_KEY = self.secret_entry.get()

            if self.qps_entry.get():
                translate.MAX_QPS = int(self.qps_entry.get())

            if self.thread_entry.get():
                translate.THREADS = int(self.thread_entry.get())

            files = [f for f in os.listdir(translate.INPUT_DIR) if f.endswith(".csv")]
            total = len(files)

            for i, f in enumerate(files):
                path = os.path.join(translate.INPUT_DIR, f)

                # ===== ✅ 修复编码问题 =====
                with open(path, "rb") as file:
                    raw = file.read()
                    enc = chardet.detect(raw)['encoding']

                sep = "\t" if enc and "utf-16" in enc.lower() else ","

                try:
                    df = pd.read_csv(path, encoding=enc, sep=sep)
                except:
                    df = pd.read_csv(path, encoding="utf-8", errors="ignore", sep=sep)

                self.current_total = len(df)
                self.current_done = 0

                # ===== ✅ Monkey Patch =====
                original_func = translate.translate_line

                def wrapped_translate_line(idx, text):
                    result = original_func(idx, text)

                    with self.progress_lock:
                        self.current_done += 1
                        done = self.current_done
                        total_lines = self.current_total

                    percent = done / total_lines * 100

                    self.root.after(0, self.update_progress_ui, percent, done, total_lines)

                    return result

                translate.translate_line = wrapped_translate_line

                # ===== 原逻辑（不动）=====
                self.progress_file['value'] = 0
                translate.process_csv(path)

                # ===== 恢复函数 =====
                translate.translate_line = original_func

                self.progress_all['value'] = (i + 1) / total * 100
                self.root.update_idletasks()

            format_adjust.batch_process_folder(translate.OUTPUT_DIR)

            messagebox.showinfo("完成", "全部处理完成！")

        finally:
            self.is_running = False
            self.start_button.config(state="normal")

    # =========================
    # UI更新（线程安全）
    # =========================
    def update_progress_ui(self, percent, done, total):
        self.progress_file['value'] = percent
        self.progress_label.config(text=f"{done} / {total}")


# =========================
# 启动
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
