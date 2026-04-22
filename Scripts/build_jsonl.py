# Script 3: 由两份对比数据生成训练集

import argparse
import copy
import json
import random
from pathlib import Path


DEFAULT_TEMPLATE = Path(r"E:\AI_Writing\Data\template_csl.jsonl")
DEFAULT_OUTPUT = Path(r"E:\AI_Writing\Data\csl.jsonl")


def read_lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\r\n") for line in f]


def load_template_first_record(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            return json.loads(line)
    raise ValueError(f"模板文件为空或没有可解析的 JSON 行: {path}")


def find_message(template: dict, role: str) -> dict:
    messages = template.get("messages")
    if not isinstance(messages, list):
        raise ValueError("模板 JSON 缺少 messages 列表")

    for message in messages:
        if isinstance(message, dict) and message.get("role") == role:
            return message
    raise ValueError(f"模板 JSON 中找不到 role={role!r} 的消息")


def build_groups(n: int) -> list[tuple[int, int]]:
    groups: list[tuple[int, int]] = []
    i = 0
    while i < n:
        remaining = n - i
        if remaining < 5:
            size = remaining
        else:
            size = min(random.randint(5, 10), remaining)
        groups.append((i, i + size))
        i += size
    return groups


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将两个一一对应的 TSV 文本按随机 5~10 行分组，写入 JSONL。"
    )
    parser.add_argument("tsv1", help="1号 TSV 文件路径（写入 user.content）")
    parser.add_argument("tsv2", help="2号 TSV 文件路径（写入 assistant.content）")
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE),
        help=f"模板 JSONL 路径（默认: {DEFAULT_TEMPLATE}）",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"输出 JSONL 路径（默认: {DEFAULT_OUTPUT}）",
    )
    args = parser.parse_args()

    tsv1_path = Path(args.tsv1)
    tsv2_path = Path(args.tsv2)
    template_path = Path(args.template)
    output_path = Path(args.output)

    lines1_raw = read_lines(tsv1_path)
    lines2_raw = read_lines(tsv2_path)

    if len(lines1_raw) != len(lines2_raw):
        raise ValueError(
            f"两个 TSV 原始总行数不一致: {len(lines1_raw)} vs {len(lines2_raw)}"
        )

    paired: list[tuple[str, str]] = []
    for a, b in zip(lines1_raw, lines2_raw):
        if not a.strip() or not b.strip():
            continue
        paired.append((a, b))

    template = load_template_first_record(template_path)
    user_msg_template = find_message(template, "user")
    assistant_msg_template = find_message(template, "assistant")
    user_prefix = user_msg_template.get("content", "")
    if not isinstance(user_prefix, str):
        raise ValueError("模板中的 user.content 不是字符串")

    groups = build_groups(len(paired))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        for start, end in groups:
            chunk = paired[start:end]
            user_text = "\n".join(x[0] for x in chunk)
            assistant_text = "\n".join(x[1] for x in chunk)

            record = copy.deepcopy(template)
            user_msg = find_message(record, "user")
            assistant_msg = find_message(record, "assistant")

            user_msg["content"] = user_prefix + user_text
            assistant_msg["content"] = assistant_text

            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"完成: 原始行数={len(lines1_raw)}, 过滤后行数={len(paired)}, "
        f"输出组数={len(groups)}, 输出文件={output_path}"
    )


if __name__ == "__main__":
    main()
