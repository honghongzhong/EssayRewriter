# Scirpt 1: AI 重写文本内容

base_url = 'https://ark.cn-beijing.volces.com/api/v3'
model_name = 'doubao-seed-2-0-mini-260215'
api_key = ''


from openai import OpenAI
import json
import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# CSL 数据文件路径
CSL_DIR = r'E:\AI_Writing\Data'
CSL_JSONL_PATH = os.path.join(CSL_DIR, 'csl.jsonl')
CSL_TSV_PATH = os.path.join(CSL_DIR, 'csl_camera_readly.tsv')

client = OpenAI(api_key=api_key, base_url=base_url)


# 全局 token 计数器
total_tokens_used = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}


def reset_token_counter():
    """重置 token 计数器"""
    global total_tokens_used
    total_tokens_used = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}


def chat_completion(prompt, system_prompt=None, temperature=0.7, max_tokens=2048):
    """调用 OpenAI 兼容 API 进行对话补全
    Args:
        prompt: 用户消息内容
        system_prompt: 系统提示词 (可选)
        temperature: 生成温度, 默认 0.7
        max_tokens: 最大生成 token 数, 默认 2048
    Returns:
        str: 模型回复的文本内容
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # 累计 token 使用量
    if response.usage:
        total_tokens_used['prompt_tokens'] += response.usage.prompt_tokens
        total_tokens_used['completion_tokens'] += response.usage.completion_tokens
        total_tokens_used['total_tokens'] += response.usage.total_tokens

    return response.choices[0].message.content



def get_csl_count(source='tsv'):
    """获取 CSL 数据的总条数
    Args:
        source: 'tsv' 使用 csl_camera_readly.tsv, 'jsonl' 使用 csl.jsonl
    Returns:
        int: 数据总条数
    """
    path = CSL_TSV_PATH if source == 'tsv' else CSL_JSONL_PATH
    with open(path, 'r', encoding='utf-8') as f:
        count = sum(1 for _ in f)
    return count


def read_csl_entry(index, source='tsv'):
    """读取指定索引的 CSL 数据条目
    Args:
        index: 行索引 (从 0 开始)
        source: 'tsv' 使用 csl_camera_readly.tsv, 'jsonl' 使用 csl.jsonl
    Returns:
        dict or str: TSV 返回 dict(title, abstract, keywords, discipline, category),
                     JSONL 返回原始文本字符串
    """
    path = CSL_TSV_PATH if source == 'tsv' else CSL_JSONL_PATH
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == index:
                if source == 'tsv':
                    parts = line.strip().split('\t')
                    return {
                        'title': parts[0] if len(parts) > 0 else '',
                        'abstract': parts[1] if len(parts) > 1 else '',
                        'keywords': parts[2] if len(parts) > 2 else '',
                        'discipline': parts[3] if len(parts) > 3 else '',
                        'category': parts[4] if len(parts) > 4 else '',
                    }
                else:
                    return json.loads(line)
    raise IndexError(f"索引 {index} 超出范围")


CORE_KEYPOINT_EXTRACT_PROMPT = """你是一个专业的中文学术文本分析助手。请根据以下学术论文的元信息和摘要内容，逐句提取每句话的关键要点。

论文信息：
- 标题：{title}
- 关键词：{keywords}
- 学科：{discipline}
- 门类：{category}
- 摘要：{abstract}

要求：
1. 按照摘要原文顺序，逐句提取关键要点
2. 每句话提取最核心的关键要点，可以还原原句的含义，不要过多
3. 输出格式为编号列表，每行一句：
   1. 要点A, 要点B, 要点C
   2. 要点D, 要点E
   ...
4. 只输出关键要点列表，不要输出任何额外说明"""


KEYPOINT_RECONSTRUCT_PROMPT = """你是一个专业的中文学术写作助手。请根据以下论文的元信息和逐句关键要点，撰写一段完整的学术论文摘要。

论文信息：
- 标题：{title}
- 学科：{discipline}
- 门类：{category}
- 原文总字数约：{char_count} 字

逐句关键要点：
{core_keypoints}

要求：
1. 根据每句的关键要点依次撰写对应的句子，还原为完整段落
2. 每一个序号对应的关键要点都必须在重构的句子中体现，且要准确表达其含义
3. 使用学术论文摘要的标准写作风格
4. 语言流畅自然，逻辑清晰，段落衔接合理
5. 重构后的摘要总字数应控制在 {char_count} 字左右，与原文篇幅相当
6. 只输出摘要段落，不要输出任何额外说明"""


def extract_core_keypoints(entry, temperature=0.3):
    """从 TSV 条目的完整信息中逐句提取关键要点
    Args:
        entry: read_csl_entry 返回的 dict (包含 title, abstract, keywords, discipline, category)
        temperature: 生成温度, 默认 0.3
    Returns:
        str: 编号列表形式的逐句关键要点
    """
    prompt = CORE_KEYPOINT_EXTRACT_PROMPT.format(
        title=entry['title'],
        keywords=entry['keywords'],
        discipline=entry['discipline'],
        category=entry['category'],
        abstract=entry['abstract'],
    )
    return chat_completion(prompt, temperature=temperature)


def reconstruct_from_keypoints(entry, core_keypoints, temperature=0.7):
    """根据逐句关键要点和元信息重构学术摘要，字数与原文相当
    Args:
        entry: read_csl_entry 返回的 dict (包含 title, abstract, discipline, category)
        core_keypoints: 逐句关键要点字符串
        temperature: 生成温度, 默认 0.7
    Returns:
        str: 重构后的摘要段落
    """
    char_count = len(entry['abstract'])
    prompt = KEYPOINT_RECONSTRUCT_PROMPT.format(
        title=entry['title'],
        discipline=entry['discipline'],
        category=entry['category'],
        core_keypoints=core_keypoints,
        char_count=char_count,
    )
    return chat_completion(prompt, temperature=temperature)


def build_entry_from_line(raw_line):
    """将输入行转换为脚本已有函数可用的 entry 结构。
    兼容两种输入：
    1) 单列纯文本（每行一个待改写文本）
    2) 5 列 TSV（title/abstract/keywords/discipline/category）
    """
    line = raw_line.rstrip('\r\n')
    parts = line.split('\t')

    if len(parts) >= 5:
        return {
            'title': parts[0].strip(),
            'abstract': parts[1].strip(),
            'keywords': parts[2].strip(),
            'discipline': parts[3].strip(),
            'category': parts[4].strip(),
        }

    # 单列文本场景：将整行作为摘要，标题使用前缀占位，确保“先提取 keypoint 再重构”的函数链可直接复用
    text = line.strip()
    pseudo_title = text[:40] if text else ''
    return {
        'title': pseudo_title,
        'abstract': text,
        'keywords': '',
        'discipline': '',
        'category': '',
    }


def to_single_line_text(text):
    """保证输出严格一行一个样本，避免 LLM 多行输出打乱行对齐。"""
    if text is None:
        return ''
    return ' '.join(str(text).replace('\r', '\n').split('\n')).strip()


def rewrite_one_line(index, raw_line, extract_temperature=0.3, reconstruct_temperature=0.7, max_retries=3):
    """严格按“先提取 keypoint，再 reconstruct”的顺序处理单行文本。"""
    entry = build_entry_from_line(raw_line)

    # 空行保持空行，保证行号对齐
    if not entry['abstract'].strip():
        return index, '', None

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            core_keypoints = extract_core_keypoints(entry, temperature=extract_temperature)
            rewritten = reconstruct_from_keypoints(
                entry,
                core_keypoints,
                temperature=reconstruct_temperature,
            )
            return index, to_single_line_text(rewritten), None
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(1.0 * (2 ** (attempt - 1)))

    # 重试后仍失败时，回退原文以保证输出行数与顺序完全一致
    return index, to_single_line_text(entry['abstract']), str(last_error)


def rewrite_tsv_file(
    input_path,
    output_path,
    workers=8,
    extract_temperature=0.3,
    reconstruct_temperature=0.7,
    max_retries=3,
    limit=0,
):
    """多线程改写 TSV（逐行独立处理），并保证输入输出逐行一一对应。"""
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if limit and limit > 0:
        lines = lines[:limit]

    total = len(lines)
    results = [''] * total
    errors = []

    print(f'开始处理: {input_path}')
    print(f'总行数: {total}, 线程数: {max(1, workers)}')

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(
                rewrite_one_line,
                idx,
                line,
                extract_temperature,
                reconstruct_temperature,
                max_retries,
            ): idx
            for idx, line in enumerate(lines)
        }

        done = 0
        for fut in as_completed(futures):
            idx = futures[fut]
            done += 1
            try:
                row_idx, rewritten, err = fut.result()
                results[row_idx] = rewritten
                if err:
                    errors.append((row_idx, err))
            except Exception as e:
                # 极端异常时也保持对齐：回退原文
                entry = build_entry_from_line(lines[idx])
                results[idx] = to_single_line_text(entry['abstract'])
                errors.append((idx, str(e)))

            if done % 20 == 0 or done == total:
                print(f'进度: {done}/{total}')

    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        for line in results:
            f.write(f'{line}\n')

    if errors:
        err_path = output_path + '.errors.jsonl'
        with open(err_path, 'w', encoding='utf-8') as ef:
            for idx, err in sorted(errors, key=lambda x: x[0]):
                ef.write(json.dumps({'line_index': idx, 'error': err}, ensure_ascii=False) + '\n')
        print(f'完成，但有失败行回退原文: {len(errors)} 行')
        print(f'错误明细: {err_path}')
    else:
        print('全部行处理成功。')

    print(f'输出文件: {output_path}')
    print(f'Token 使用: {total_tokens_used}')


def _default_output_path(input_path):
    base, ext = os.path.splitext(input_path)
    ext = ext if ext else '.tsv'
    return f'{base}_rewritten{ext}'


def main():
    parser = argparse.ArgumentParser(description='按“提取 keypoint -> reconstruct”批量改写 TSV 单行文本')
    parser.add_argument('--input', default=CSL_TSV_PATH, help='输入 TSV 路径')
    parser.add_argument('--output', default=None, help='输出 TSV 路径（默认: 输入名 + _rewritten）')
    parser.add_argument('--workers', type=int, default=8, help='并发线程数')
    parser.add_argument('--extract-temperature', type=float, default=0.3, help='keypoint 提取温度')
    parser.add_argument('--reconstruct-temperature', type=float, default=0.7, help='重构温度')
    parser.add_argument('--max-retries', type=int, default=3, help='单行失败最大重试次数')
    parser.add_argument('--limit', type=int, default=0, help='仅处理前 N 行（0 表示全部）')
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output or _default_output_path(input_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f'输入文件不存在: {input_path}')

    reset_token_counter()
    rewrite_tsv_file(
        input_path=input_path,
        output_path=output_path,
        workers=args.workers,
        extract_temperature=args.extract_temperature,
        reconstruct_temperature=args.reconstruct_temperature,
        max_retries=args.max_retries,
        limit=args.limit,
    )


if __name__ == '__main__':
    main()
