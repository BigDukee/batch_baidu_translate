这是一个 Python 批量翻译工具，使用百度翻译 API 将 CSV 文件中的中文内容翻译为英文和越南语。

功能:
1.中文列（第二列）翻译为英文和越南语（分别写入第三列和第四列）
2.自动识别文件编码，VA软件导出格式为UTF-16，处理后文本依旧以UTF-16保存
3.翻译失败自动记录日志，方便找到错误点并人工矫正
4.翻译结果缓存，节约查询次数
5.多线程加速翻译，当前开通个人认证（高级版），QPS=10，节省时间
6.遍历指定文件夹下所有 CSV 文件进行翻译，节省操作数，一次执行，全部翻译
7.格式统一，现场可以直接使用


requirements:
pip install pandas chardet requests tqdm

APP_ID = "****************"
SECRET_KEY = "****************"
INPUT_DIR = r"****************"
OUTPUT_DIR = r"****************"

translate 将中文翻译成英文和越南语
format_adjust 适配VA格式

1.translate进行翻译
2.format_adjust进行格式整理