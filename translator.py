from openai import OpenAI


with open("C:\\Users\\luohao\\Desktop\\apikey.txt", "r", encoding="utf-8") as key_file:
    api_key = key_file.read().strip()
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def split_text(text, max_length=2000):
    """将长文本分割成达到指定长度的段落"""
    texts = []
    current_paragraphs = []
    current_length = 0

    # 按段落分割（简单实现）
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        if current_length > max_length:
            texts.append("\n".join(current_paragraphs))
            current_paragraphs = []
            current_length = 0
        current_paragraphs.append(paragraph)
        current_length += len(paragraph)

    texts.append("\n".join(current_paragraphs))
    return texts


def translate_text(text):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": f"请将以下英文内容翻译成中文（如果你收到的内容以中文为主，则将其翻译为英文），保持格式不变: \n{text}"},
        ],
        temperature=1.3
    )
    return response.choices[0].message.content


def main():
    INPUT_FILE = input("请输入要翻译的文件名: ")
    OUTPUT_FILE = INPUT_FILE.rsplit('.', 1)[0] + "_fy." + INPUT_FILE.rsplit('.', 1)[1]

    # 读取原始文件
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            original_text = f.read()
    except FileNotFoundError:
        print(f"错误：文件 {INPUT_FILE} 未找到")
        return

    # 分割文本
    texts = split_text(original_text)

    # 逐段翻译
    translated_text = []
    for i, text in enumerate(texts, 1):
        print(f"正在翻译第 {i}/{len(texts)} 部分...")
        translated_text.append(translate_text(text))

    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(translated_text))
    print(f"翻译完成，结果已保存到 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
