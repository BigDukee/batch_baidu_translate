import translate
import format_adjust

def main():
    print("========== Step 1: 开始翻译 ==========")
    translate.main()   # 执行翻译

    print("\n========== Step 2: 翻译完成，开始格式修正 ==========")

    # 方式1（直接调用函数）
    format_adjust.main()

    print("\n========== 全流程完成 ==========")


if __name__ == "__main__":
    main()