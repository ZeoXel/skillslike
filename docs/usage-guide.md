# SkillsLike 使用指南

## 目录

1. [架构概览](#架构概览)
2. [Skill Manifest 详解](#skill-manifest-详解)
3. [添加新 Skill](#添加新-skill)
4. [三种运行时类型](#三种运行时类型)
5. [测试和调试](#测试和调试)
6. [最佳实践](#最佳实践)
7. [常见场景示例](#常见场景示例)

---

## 架构概览

### 工作流程

```
用户消息 → Intent Router → 选择相关 Skills → Agent 调用工具 → 执行器运行 → 返回结果
```

### 核心组件关系

```
┌─────────────┐
│  用户输入    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Intent Router   │ ← 根据关键词匹配
│ (关键词匹配)     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Skill Registry  │ ← 加载 YAML manifests
│ (技能注册表)     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ LangGraph Agent │ ← 状态图执行
│ (决策执行)       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Executors     │ ← 实际执行逻辑
│ (执行器)         │
└─────────────────┘
   │       │      │
   ▼       ▼      ▼
Docker  Service  Anthropic
```

---

## Skill Manifest 详解

### 基本结构

每个 skill 都是一个 YAML 文件，定义了技能的元数据和执行方式。

```yaml
name: skill-name              # 必需：唯一标识符
description: "技能描述..."     # 必需：功能说明 + 触发关键词
inputs:                       # 可选：输入规范
  - type: file                # file, text, json
    formats: [pdf, docx]      # 文件格式（仅 file 类型）
    description: "输入描述"
outputs:                      # 可选：输出规范
  - type: file
    format: xlsx
    description: "输出描述"
runtime:                      # 必需：运行时配置
  type: docker                # docker, service, anthropic
  image: "镜像名"             # Docker 镜像
  timeout: 300                # 超时时间（秒）
requires:                     # 可选：依赖的环境变量/资源
  - OPENAI_API_KEY
tags:                         # 可选：分类标签
  - data-analysis
  - automation
metadata:                     # 可选：额外元数据
  version: "1.0.0"
  author: "Your Name"
```

### 字段说明

#### 1. `name` (必需)

- **格式**: 小写字母、数字、连字符
- **作用**: 唯一标识符，会转换为工具名称
- **示例**: `web-search`, `excel-analyzer`

#### 2. `description` (必需)

- **作用**:
  - 向用户说明功能
  - **关键词匹配路由**（非常重要！）
- **最佳实践**:
  - 前半部分：功能描述
  - 后半部分：触发关键词（中英文）

```yaml
description: "分析 Excel 表格并生成报告。Triggers on: Excel, spreadsheet, 表格, 分析, 数据"
```

#### 3. `inputs` (可选)

定义技能接受的输入类型：

```yaml
inputs:
  # 文件输入
  - type: file
    formats: [pdf, docx, txt, md]
    description: "要处理的文档"

  # 文本输入
  - type: text
    description: "用户指令或问题"

  # JSON 输入
  - type: json
    description: "结构化数据"
```

#### 4. `outputs` (可选)

定义技能的输出类型：

```yaml
outputs:
  - type: file
    format: xlsx
    description: "分析报告"

  - type: text
    description: "摘要说明"
```

#### 5. `runtime` (必需)

核心配置，决定如何执行技能。详见[三种运行时类型](#三种运行时类型)。

#### 6. `tags` (可选)

用于分类和组织：

```yaml
tags:
  - data-analysis
  - visualization
  - automation
```

---

## 添加新 Skill

### 步骤 1: 创建 Manifest 文件

在 `skills/` 目录下创建新的 YAML 文件：

```bash
# 创建文件
touch skills/my-new-skill.yaml
```

### 步骤 2: 编写 Manifest

选择适合的运行时类型，填写配置：

**示例：创建一个简单的文本处理 skill**

```yaml
name: text-translator
description: "翻译文本到多种语言。Triggers on: translate, 翻译, language, 语言"

inputs:
  - type: text
    description: "要翻译的文本"
  - type: text
    description: "目标语言"

outputs:
  - type: text
    description: "翻译结果"

runtime:
  type: service
  endpoint: http://localhost:8001/translate
  timeout: 30

tags:
  - translation
  - nlp

metadata:
  version: "1.0.0"
  supported_languages: ["en", "zh", "ja", "fr"]
```

### 步骤 3: 重载技能

有两种方式：

**方法 1: API 重载（推荐）**

```bash
curl -X POST http://localhost:8000/api/reload
```

**方法 2: 重启服务器**

```bash
# 停止
pkill -f uvicorn

# 启动
make run
```

### 步骤 4: 验证

```bash
# 检查技能列表
curl http://localhost:8000/api/skills | grep "text-translator"
```

---

## 三种运行时类型

### 1. Service Runtime（HTTP 服务）

**适用场景**: 已有的 HTTP API、微服务、云函数

**配置示例**:

```yaml
runtime:
  type: service
  endpoint: http://localhost:8001/my-service
  timeout: 60
  env:
    API_KEY: "your-key"
```

**执行器行为**:
- 发送 POST 请求到 `endpoint`
- 请求体: `{"message": "用户输入", ...}`
- 期望响应: `{"text": "结果", "file_id": "可选"}`

**实现示例** (FastAPI):

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/my-service")
async def my_service(request: dict):
    text = request.get("message", "")
    # 处理逻辑
    result = process(text)

    return {
        "text": f"处理结果: {result}",
        "file_id": None  # 如果生成文件，返回 file_id
    }
```

### 2. Docker Runtime（容器执行）

**适用场景**:
- 复杂的数据处理
- 需要特定环境的任务
- 隔离执行

**配置示例**:

```yaml
runtime:
  type: docker
  image: my-registry/my-skill:latest
  cmd: ["python", "main.py"]
  timeout: 300
  env:
    LOG_LEVEL: info
    WORKSPACE: /workspace
```

**实现示例** (Dockerfile):

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
```

**main.py**:

```python
import sys
import json

def main():
    # 从 stdin 读取输入
    input_data = json.loads(sys.stdin.read())
    message = input_data.get("message", "")

    # 处理逻辑
    result = process(message)

    # 输出到 stdout
    output = {
        "text": f"处理结果: {result}",
        "file_id": None
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

**注意**: 当前 Docker executor 是占位符，需要实现实际的容器调用逻辑。

### 3. Anthropic Runtime（官方技能）

**适用场景**: 使用 Anthropic 官方提供的 skills（Excel, PDF, etc.）

**配置示例**:

```yaml
runtime:
  type: anthropic
  skill_id: excel-skill
  timeout: 180
```

**支持的官方 skills**:
- `excel-skill` - Excel 分析
- `pdf-skill` - PDF 处理
- `docx-skill` - Word 文档
- `pptx-skill` - PowerPoint

**注意**: 当前 Anthropic executor 是占位符，需要实现实际的 API 调用。

---

## 测试和调试

### 1. 单元测试

为新 skill 创建测试：

```python
# tests/unit_tests/test_my_skill.py

from skillslike.registry import ManifestLoader

def test_load_my_skill():
    """测试加载自定义 skill manifest."""
    loader = ManifestLoader("skills/")
    manifest = loader.load_manifest("skills/my-new-skill.yaml")

    assert manifest.name == "my-new-skill"
    assert manifest.runtime.type == "service"
```

运行测试：

```bash
uv run pytest tests/unit_tests/test_my_skill.py -v
```

### 2. 集成测试

测试完整的工作流：

```bash
# 发送测试消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "翻译这段文本到英文",
    "thread_id": "test-session"
  }'
```

### 3. 查看日志

启动服务器时查看详细日志：

```bash
# 启动时会显示:
# - 加载的技能数量
# - 每次请求路由到哪些工具
# - 工具执行的详细信息

uvicorn skillslike.api.main:app --log-level debug
```

### 4. 调试关键词匹配

```python
# 测试脚本
from skillslike.router import IntentRouter
from skillslike.registry import SkillRegistry

registry = SkillRegistry("skills/")
router = IntentRouter(registry.get_all_manifests())

# 测试消息
message = "翻译这段文本"
keywords = router._extract_keywords(message)
print(f"提取的关键词: {keywords}")

# 查看技能的关键词
skill_keywords = router.get_skill_keywords("text-translator")
print(f"技能关键词: {skill_keywords}")
```

---

## 最佳实践

### 1. 关键词设计

✅ **好的实践**:

```yaml
description: "分析 Excel 表格生成可视化报告。Triggers on: Excel, spreadsheet, visualization, chart, 表格, 分析, 可视化, 图表"
```

- 包含中英文关键词
- 覆盖同义词和相关词
- 使用常见的用户表达

❌ **不好的实践**:

```yaml
description: "处理数据"  # 太简单，匹配不准确
```

### 2. Manifest 组织

**推荐目录结构**:

```
skills/
├── official/           # 官方 Anthropic skills
│   ├── excel.yaml
│   └── pdf.yaml
├── custom/             # 自定义 skills
│   ├── translator.yaml
│   └── analyzer.yaml
└── experimental/       # 实验性 skills
    └── new-skill.yaml
```

### 3. 版本管理

在 metadata 中记录版本：

```yaml
metadata:
  version: "1.2.0"
  changelog:
    - "1.2.0: 添加批量处理支持"
    - "1.1.0: 优化性能"
    - "1.0.0: 初始版本"
```

### 4. 错误处理

在 skill 实现中添加完善的错误处理：

```python
try:
    result = process(input_data)
    return {"text": result, "file_id": None}
except ValueError as e:
    return {"text": f"输入错误: {str(e)}", "error": True}
except Exception as e:
    return {"text": f"处理失败: {str(e)}", "error": True}
```

### 5. 超时设置

根据任务复杂度设置合理的超时：

- 简单文本处理: 30-60 秒
- 文件分析: 120-300 秒
- 大数据处理: 300-600 秒

```yaml
runtime:
  timeout: 120  # 2 分钟
```

---

## 常见场景示例

### 场景 1: 调用外部 API

**需求**: 调用 OpenAI API 进行文本总结

```yaml
name: text-summarizer
description: "总结长文本。Triggers on: summarize, summary, 总结, 摘要, 概括"

inputs:
  - type: text
    description: "要总结的文本"

outputs:
  - type: text
    description: "摘要"

runtime:
  type: service
  endpoint: http://localhost:8001/summarize
  timeout: 60

requires:
  - OPENAI_API_KEY

tags:
  - nlp
  - summarization
```

**服务实现**:

```python
from fastapi import FastAPI
from openai import OpenAI
import os

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/summarize")
async def summarize(request: dict):
    text = request.get("message", "")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一个专业的摘要助手"},
            {"role": "user", "content": f"总结以下文本:\n\n{text}"}
        ]
    )

    summary = response.choices[0].message.content

    return {
        "text": summary,
        "file_id": None
    }
```

### 场景 2: 数据库查询

**需求**: 查询用户数据

```yaml
name: user-query
description: "查询用户信息。Triggers on: query user, search user, 查询用户, 搜索用户"

inputs:
  - type: text
    description: "查询条件"

outputs:
  - type: json
    description: "查询结果"

runtime:
  type: service
  endpoint: http://localhost:8001/query-user
  timeout: 30

requires:
  - DATABASE_URL

tags:
  - database
  - query
```

### 场景 3: 文件转换

**需求**: PDF 转换为 Markdown

```yaml
name: pdf-to-markdown
description: "转换 PDF 为 Markdown。Triggers on: convert PDF, PDF to markdown, PDF转换, PDF转md"

inputs:
  - type: file
    formats: [pdf]
    description: "PDF 文件"

outputs:
  - type: file
    format: md
    description: "Markdown 文件"

runtime:
  type: docker
  image: my-registry/pdf-converter:latest
  cmd: ["python", "convert.py"]
  timeout: 180

tags:
  - conversion
  - pdf
  - markdown
```

### 场景 4: 数据分析 Pipeline

**需求**: 多步骤数据分析

```yaml
name: data-pipeline
description: "运行数据分析流程。Triggers on: analyze data, data pipeline, 数据分析, 分析流程"

inputs:
  - type: file
    formats: [csv, xlsx]
    description: "数据文件"
  - type: text
    description: "分析指令"

outputs:
  - type: file
    format: html
    description: "分析报告"
  - type: file
    format: csv
    description: "处理后的数据"

runtime:
  type: docker
  image: my-registry/data-pipeline:latest
  cmd: ["python", "pipeline.py"]
  timeout: 600
  env:
    PYTHONUNBUFFERED: "1"

requires:
  - ANALYSIS_CONFIG

tags:
  - data-science
  - analytics
  - pipeline

metadata:
  version: "2.1.0"
  capabilities:
    - statistical_analysis
    - visualization
    - data_cleaning
```

---

## 快速参考

### 创建新 Skill 检查清单

- [ ] 创建 YAML 文件在 `skills/` 目录
- [ ] 设置唯一的 `name`
- [ ] 编写清晰的 `description` + 关键词
- [ ] 定义 `inputs` 和 `outputs`
- [ ] 配置 `runtime` (service/docker/anthropic)
- [ ] 设置合理的 `timeout`
- [ ] 添加 `tags` 分类
- [ ] 实现对应的执行逻辑（服务/容器）
- [ ] 重载技能: `curl -X POST http://localhost:8000/api/reload`
- [ ] 测试: 发送包含关键词的消息
- [ ] 验证: 检查日志确认技能被正确路由

### 常用命令

```bash
# 查看所有技能
curl http://localhost:8000/api/skills

# 重载技能
curl -X POST http://localhost:8000/api/reload

# 测试对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你的测试消息", "thread_id": "test"}'

# 运行测试
uv run pytest tests/ -v

# 启动服务器
make run
```

---

## 下一步

1. **尝试修改示例 skill**: 编辑 `skills/examples/web-search.yaml`
2. **创建你的第一个 skill**: 参考[添加新 Skill](#添加新-skill)
3. **实现执行器**: 为 Docker/Service runtime 编写实际逻辑
4. **优化路由**: 改进关键词匹配或使用 embedding
5. **添加更多功能**: 文件上传、流式输出等

有问题随时查看文档或提问！🚀
