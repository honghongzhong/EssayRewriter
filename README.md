# EssayRewriter

[English](#english) | [中文](#中文)

---

## English

### Overview

This repository provides a complete pipeline for building a **AIGC-rate-reduction** training dataset for academic text, along with instructions for using the fine-tuned model. The dataset is derived from the [CSL (Chinese Scientific Literature)](https://github.com/ydli-ai/CSL) corpus. AI-style academic abstracts are rewritten into a more natural, human-like style using a large language model, and the resulting pairs are packaged into an SFT-ready conversational dataset.

> **Note**: The fine-tuned model was trained on Alibaba Cloud and cannot be exported due to platform restrictions. Only the dataset and data-building scripts are open-sourced here.

---

### Repository Structure

```
EssayRewriter/
├── Dataset/
│   └── csl.jsonl          # SFT training dataset (JSONL format)
└── Scripts/
    ├── rewrite.py          # Script 1: Rewrite academic abstracts using an LLM
    ├── extract_abstract.py # Script 2: Extract the abstract column from a TSV file
    └── build_jsonl.py      # Script 3: Merge original and rewritten text pairs into JSONL
```

---

### Dataset

`Dataset/csl.jsonl` is a JSONL file in the standard OpenAI chat format. Each record contains three roles:

| Role | Content |
|------|---------|
| `system` | Persona definition for an academic text rewriting assistant |
| `user` | Several AI-style academic abstracts to be rewritten into human style |
| `assistant` | The corresponding human-style rewritten output |

Each training sample randomly batches 5–10 abstracts together to improve the model's generalization on bulk rewriting tasks.

---

### Usage

#### Prerequisites

```bash
pip install openai
```

#### Step 1 — Extract Abstracts (`extract_abstract.py`)

Extract the abstract column from the raw CSL TSV file:

```bash
python Scripts/extract_abstract.py
```

> Reads `csl_camera_readly.tsv` by default and outputs `csl_camera_readly_abstract_only.tsv`. Edit the paths inside the script as needed.

#### Step 2 — Rewrite Abstracts (`rewrite.py`)

Call an OpenAI-compatible LLM to rewrite each abstract in a two-stage process:

1. **Keypoint extraction** — extract the core points of each sentence;
2. **Keypoint reconstruction** — rewrite a fluent, natural academic abstract from those keypoints.

```bash
# Fill in your API key and model name in the script, then run:
python Scripts/rewrite.py
```

> The script defaults to the Volcengine Doubao endpoint but works with any OpenAI-compatible API.

#### Step 3 — Build the Training Dataset (`build_jsonl.py`)

Merge the original abstract file (TSV1) and the rewritten abstract file (TSV2) line-by-line, group them into random batches, and produce the JSONL training set:

```bash
python Scripts/build_jsonl.py <tsv1_path> <tsv2_path> [--template <template_path>] [--output <output_path>]
```

| Argument | Description |
|----------|-------------|
| `tsv1` | Path to the original AI-style abstracts (written into `user.content`) |
| `tsv2` | Path to the human/model-rewritten abstracts (written into `assistant.content`) |
| `--template` | Path to the conversation template JSONL (uses built-in default if omitted) |
| `--output` | Output path for the generated JSONL file |

---

### Model Training

Upload the generated `csl.jsonl` to any platform that supports SFT fine-tuning (e.g., Alibaba Cloud Bailian, Volcengine MaaS, etc.), select a suitable base model, and perform supervised fine-tuning to obtain an academic rewriting model capable of reducing AIGC detection rates.

---

### License

The dataset is released under the [CSL original license](https://github.com/ydli-ai/CSL). Scripts are released under the [MIT License](LICENSE).

---

## 中文

### 项目简介

本项目提供了一套用于构建**学术文本降 AIGC 率**训练数据集的完整流程，以及基于该数据集微调所得模型的使用说明。数据集来源于 [CSL（中文科学文献）](https://github.com/ydli-ai/CSL) 数据集，通过大模型将 AI 风格的学术摘要改写为更符合人类写作习惯的版本，最终构建对话格式的 SFT 训练数据。

> **注意**：微调所得模型在阿里云平台上训练，受平台限制无法导出，因此暂不开源。本仓库仅开放数据集与数据构建脚本。

---

### 仓库结构

```
EssayRewriter/
├── Dataset/
│   └── csl.jsonl          # SFT 训练数据集（JSONL 格式）
└── Scripts/
    ├── rewrite.py          # 脚本 1：调用大模型对学术摘要进行改写
    ├── extract_abstract.py # 脚本 2：从 TSV 文件中提取摘要字段
    └── build_jsonl.py      # 脚本 3：将原文与改写文本对合并为 JSONL 训练集
```

---

### 数据集说明

`Dataset/csl.jsonl` 为标准 OpenAI 对话格式的 JSONL 文件，每条记录包含三个角色：

| 角色 | 内容 |
|------|------|
| `system` | 学术文本改写助手的角色设定 |
| `user` | 包含若干段 AI 风格学术摘要，要求将其改写为人类风格 |
| `assistant` | 对应的人类风格改写结果 |

每条训练样本将 5～10 篇摘要随机打包为一组，以提升模型对批量改写任务的泛化能力。

---

### 使用流程

#### 环境依赖

```bash
pip install openai
```

#### 步骤一：提取摘要（`extract_abstract.py`）

从 CSL 原始 TSV 文件中提取摘要列，生成仅含摘要的纯文本文件：

```bash
python Scripts/extract_abstract.py
```

> 默认读取 `csl_camera_readly.tsv`，输出 `csl_camera_readly_abstract_only.tsv`。请在脚本中修改路径。

#### 步骤二：改写摘要（`rewrite.py`）

调用兼容 OpenAI 接口的大模型，对摘要逐条进行两阶段改写：

1. **关键要点提取**：逐句提取每句话的核心要点；
2. **要点还原重写**：依据要点重新撰写自然流畅的学术摘要。

```bash
# 在脚本中填入 API Key 与模型名称后运行
python Scripts/rewrite.py
```

> 默认使用火山引擎 Doubao 接口，可替换为任意 OpenAI 兼容接口。

#### 步骤三：构建训练集（`build_jsonl.py`）

将原始摘要文件（TSV1）与改写摘要文件（TSV2）按行对应，随机分组打包，生成 JSONL 训练集：

```bash
python Scripts/build_jsonl.py <tsv1_path> <tsv2_path> [--template <template_path>] [--output <output_path>]
```

| 参数 | 说明 |
|------|------|
| `tsv1` | 原始 AI 风格摘要文件路径（写入 `user.content`） |
| `tsv2` | 人工/模型改写后的摘要文件路径（写入 `assistant.content`） |
| `--template` | 对话模板 JSONL 文件路径（默认使用内置模板） |
| `--output` | 输出 JSONL 文件路径 |

---

### 模型训练

将生成的 `csl.jsonl` 上传至支持 SFT 微调的平台（如阿里云百炼、火山引擎 MaaS 等），选择合适的基座模型进行监督微调，即可得到具备降低 AIGC 检测率能力的学术改写模型。

---

### 许可证

数据集依照 [CSL 原始许可证](https://github.com/ydli-ai/CSL) 发布。脚本代码采用 [MIT License](LICENSE)。
