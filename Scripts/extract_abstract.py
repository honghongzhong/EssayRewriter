# Script 2: 提取原文本主段落内容，剔除标题、类别

import os

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

    # 单列文本场景
    text = line.strip()
    pseudo_title = text[:40] if text else ''
    return {
        'title': pseudo_title,
        'abstract': text,
        'keywords': '',
        'discipline': '',
        'category': '',
    }

def main():
    input_path = r'E:\AI_Writing\Data\csl_camera_readly.tsv'
    output_path = r'E:\AI_Writing\Data\csl_camera_readly_abstract_only.tsv'

    if not os.path.exists(input_path):
        print(f"错误: 找不到输入文件 {input_path}")
        return

    print(f"开始读取: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f_in, \
         open(output_path, 'w', encoding='utf-8', newline='\n') as f_out:
        
        count = 0
        for line in f_in:
            entry = build_entry_from_line(line)
            abstract = entry.get('abstract', '')
            
            # 将提取出的只包含 abstract 的文本写入新文件，逐行对应
            f_out.write(f"{abstract}\n")
            count += 1
            
    print(f"提取完成！共处理了 {count} 行数据。")
    print(f"仅包含 abstract 的新文件已保存至: {output_path}")

if __name__ == '__main__':
    main()