from openai import OpenAI
from pathlib import Path
import re


with open("apikey.txt", "r", encoding="utf-8") as key_file:
    api_key = key_file.read().strip()
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def split_text(text, max_length=2000):
    """将长文本分割成达到指定长度的段落（保护 Markdown “需要配对”的结构不被切断）"""

    def _is_fence_line(line: str):
        return re.match(r"^\s*(`{3,}|~{3,})", line)

    def _is_closing_fence(line: str, fence_char: str, fence_len: int) -> bool:
        # 关闭 fence 通常是纯 fence 字符 + 可选空白
        return re.match(rf"^\s*{re.escape(fence_char)}{{{fence_len},}}\s*$", line) is not None

    texts = []
    current_paragraphs = []
    current_length = 0

    # 需要“配对”的保护状态（保护常见的 Markdown 结构）
    in_fence = False
    fence_char = ""
    fence_len = 0
    in_math_block = False  # $$...$$ 或 \[...\]

    # 按段落分割
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        line = paragraph
        stripped = line.strip()

        # 先写入当前行
        current_paragraphs.append(line)
        current_length += len(line)

        # 数学块：只处理常见的“独占一行”的起止标记
        if stripped in {"$$", r"\\[", r"\\]"}:
            if stripped == "$$":
                in_math_block = not in_math_block
            elif stripped == r"\\[":
                in_math_block = True
            elif stripped == r"\\]":
                in_math_block = False

        # fenced code block：``` 或 ~~~
        if in_fence:
            if _is_closing_fence(line, fence_char, fence_len):
                in_fence = False
                fence_char = ""
                fence_len = 0
        else:
            m = _is_fence_line(line)
            if m:
                fence = m.group(1)
                fence_char = fence[0]
                fence_len = len(fence)
                in_fence = True

        in_protected_region = in_fence or in_math_block

        # 只在“不处于需要配对的区域”时才允许切分
        if current_length > max_length and not in_protected_region:
            texts.append("\n".join(current_paragraphs))
            current_paragraphs = []
            current_length = 0

    if current_paragraphs:
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
    # - 如果输入是文件：仅当后缀为 .md/.txt 才翻译，否则忽略
    # - 如果输入是文件夹：递归翻译其中所有 .md/.txt 文件，其余类型忽略
    allowed_suffixes = {".md", ".txt"}

    if input_path.is_file():
        if input_path.suffix.lower() not in allowed_suffixes:
            print("未找到可翻译的文件，已跳过。")
            return
        input_files = [input_path]
        output_root = input_path.parent
    else:
        input_files = sorted(
            [p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in allowed_suffixes]
        )
        if not input_files:
            print("未找到可翻译的文件，已结束。")
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
