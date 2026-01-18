from openai import OpenAI
from pathlib import Path


with open("apikey.txt", "r", encoding="utf-8") as key_file:
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
    input_path_str = input("请输入要翻译的文件或文件夹名: ").strip().strip('"')
    if not input_path_str:
        print("错误：输入为空")
        return

    input_path = Path(input_path_str)
    if not input_path.exists():
        print(f"错误：路径 {input_path} 不存在")
        return

    # 文件选择逻辑：
    # - 如果输入是文件：只翻译该文件
    # - 如果输入是文件夹：递归翻译其中所有 .md/.html/.txt 文件
    if input_path.is_file():
        input_files = [input_path]
        output_root = input_path.parent
    else:
        allowed_suffixes = {".md", ".html", ".txt"}
        input_files = sorted(
            [p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in allowed_suffixes]
        )
        if not input_files:
            print(f"错误：文件夹 {input_path} 中未找到 .md/.html/.txt 文件")
            return
        output_root = input_path.parent

    # 输出目录/文件命名：保持原目录结构，根目录加 _fy 后缀
    # 例：handbook-v2/xxx.md -> handbook-v2_fy/xxx.md
    if input_path.is_dir():
        output_base_dir = output_root / f"{input_path.name}_fy"
    else:
        output_base_dir = None

    total_files = len(input_files)
    for file_index, input_file in enumerate(input_files, 1):
        if input_path.is_file():
            output_file = input_file.with_name(f"{input_file.stem}_fy{input_file.suffix}")
        else:
            rel_path = input_file.relative_to(input_path)
            output_file = output_base_dir / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n[{file_index}/{total_files}] 正在翻译文件: {input_file}")

        # 读取原始文件
        try:
            original_text = input_file.read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"错误：文件 {input_file} 未找到，跳过")
            continue

        # 分割文本
        texts = split_text(original_text)

        # 逐段翻译
        translated_text = []
        for i, text in enumerate(texts, 1):
            print(f"  正在翻译第 {i}/{len(texts)} 部分...")
            translated_text.append(translate_text(text))

        # 保存结果
        output_file.write_text("\n\n".join(translated_text), encoding='utf-8')
        print(f"  已保存: {output_file}")

    if input_path.is_dir():
        print(f"\n全部翻译完成，结果已保存到文件夹: {output_base_dir}")


if __name__ == "__main__":
    main()
