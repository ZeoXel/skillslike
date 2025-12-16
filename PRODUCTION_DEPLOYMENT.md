# SkillsLike 生产环境部署指南

## 📚 目录

- [系统架构概览](#系统架构概览)
- [Skill 添加流程](#skill-添加流程)
- [生产环境部署](#生产环境部署)
- [Web 用户体验流程](#web-用户体验流程)
- [运维监控](#运维监控)

---

## 系统架构概览

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                        用户访问层                              │
│  Web 前端 (http://your-domain.com)                           │
│  - static/index.html (聊天界面)                               │
│  - static/js/app.js (前端逻辑)                                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
┌────────────────────▼────────────────────────────────────────┐
│                     FastAPI 服务层                             │
│  skillslike/api/main.py                                      │
│  - POST /api/chat (对话接口)                                  │
│  - GET /api/skills (技能列表)                                 │
│  - GET /api/file/{file_id} (文件下载)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Agent 核心层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Intent Router │→│ Tool Registry │→│ LangGraph    │      │
│  │ 意图路由      │  │ 工具注册表    │  │ Agent 循环   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Skill 执行层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Anthropic   │  │ Service     │  │ Docker      │         │
│  │ Executor    │  │ Executor    │  │ Executor    │         │
│  │ (Claude API)│  │ (HTTP API)  │  │ (Container) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  外部服务 & 存储                              │
│  - API 提供商 (bltcy.ai, OpenAI, etc.)                       │
│  - 文件存储 (data/files/)                                     │
│  - 状态存储 (MemorySaver/Redis/SQLite)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Skill 添加流程

### 1. 创建 Skill Manifest (YAML)

**位置**: `skills/your-skill-name.yaml`

```yaml
name: your-skill-name
description: >
  Skill 描述，包含触发关键词。例如：Generate images using AI.
  Triggers: draw, image, picture, 画, 图片, 生成
version: 1.0.0

# 输入参数定义
inputs:
  - name: prompt
    type: string
    description: "图像描述"
    required: true
  - name: size
    type: string
    description: "图像尺寸"
    required: false
    default: "1024x1024"

# 输出定义
outputs:
  - name: image_url
    type: string
    description: "生成的图像URL"
  - name: file_id
    type: string
    description: "存储的文件ID"

# 运行时配置
runtime:
  type: service  # 可选: anthropic, service, docker, custom
  endpoint: https://api.provider.com/v1/images/generations
  timeout: 60
  env:
    MODEL_NAME: nano-banana-2
    DEFAULT_SIZE: 4K

# 依赖和标签
requires: []
tags:
  - image-generation
  - ai
  - creative

metadata:
  author: Your Name
  cost_tier: medium
  rate_limit: 10/minute
```

### 2. 创建 Executor 实现 (Python)

**位置**: `skillslike/executors/your_skill_executor.py`

```python
"""Executor for your custom skill."""

import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from skillslike.executors.base import BaseExecutor

logger = logging.getLogger(__name__)


class YourSkillInput(BaseModel):
    """Input schema for your skill."""

    prompt: str = Field(description="Description of what to generate")
    size: str = Field(
        default="1024x1024",
        description="Output size",
    )


class YourSkillExecutor(BaseExecutor):
    """Executor for your custom skill.

    Calls external API or runs custom logic.
    """

    def get_input_schema(self) -> type[BaseModel]:
        """Get the input schema for this executor.

        Returns:
            Pydantic model class for input validation.
        """
        return YourSkillInput

    def execute(self, prompt: str, size: str = "1024x1024") -> str:
        """Execute the skill.

        Args:
            prompt: User input.
            size: Output size.

        Returns:
            Execution result.

        Raises:
            RuntimeError: If execution fails.
        """
        if not prompt:
            msg = "Skill requires a 'prompt' parameter"
            raise RuntimeError(msg)

        logger.info("Executing skill: prompt='%s', size=%s", prompt[:50], size)

        # Get configuration from manifest
        endpoint = self.manifest.runtime.endpoint
        timeout = self.manifest.runtime.timeout

        # Call external API or run custom logic
        try:
            response = httpx.post(
                endpoint,
                json={"prompt": prompt, "size": size},
                timeout=timeout,
            )
            response.raise_for_status()

            result = response.json()
            logger.info("Skill execution successful")

            # Process and return result
            return f"执行成功！结果: {result}"

        except httpx.HTTPError as e:
            msg = f"Skill execution failed: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e
```

### 3. 注册 Executor 到 Registry

**位置**: `skillslike/registry/registry.py`

在 `build_tool()` 方法中添加条件分支：

```python
def build_tool(self, manifest: SkillManifest) -> StructuredTool:
    """Build a LangChain StructuredTool from a skill manifest."""
    from skillslike.executors.anthropic_executor import AnthropicExecutor
    from skillslike.executors.custom_executor import CustomExecutor
    from skillslike.executors.image_gen_executor import ImageGenExecutor
    from skillslike.executors.your_skill_executor import YourSkillExecutor  # 导入

    # 根据 skill name 或 runtime type 选择 executor
    if manifest.name == "your-skill-name":
        executor = YourSkillExecutor(manifest)
        tool = StructuredTool.from_function(
            func=executor.execute,
            name=manifest.name.replace("-", "_"),
            description=manifest.description,
            args_schema=executor.get_input_schema(),  # 提供 schema
        )
    elif manifest.name == "nano-banana-image-gen":
        executor = ImageGenExecutor(manifest)
        tool = StructuredTool.from_function(
            func=executor.execute,
            name=manifest.name.replace("-", "_"),
            description=manifest.description,
            args_schema=executor.get_input_schema(),
        )
    elif manifest.runtime.type == "anthropic":
        executor = AnthropicExecutor(manifest)
        tool = StructuredTool.from_function(
            func=executor.execute,
            name=manifest.name.replace("-", "_"),
            description=manifest.description,
        )
    else:
        executor = CustomExecutor(manifest)
        tool = StructuredTool.from_function(
            func=executor.execute,
            name=manifest.name.replace("-", "_"),
            description=manifest.description,
        )

    return tool
```

### 4. 测试 Skill

创建测试脚本 `test_your_skill.py`:

```python
"""Test script for your custom skill."""

import requests

API_BASE = "http://localhost:8000"

def test_your_skill():
    """Test the custom skill."""
    request_data = {
        "message": "使用你的技能做点什么",
        "thread_id": "test-skill-001"
    }

    response = requests.post(
        f"{API_BASE}/api/chat",
        json=request_data,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(result['text'])
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_your_skill()
```

运行测试：
```bash
python test_your_skill.py
```

---

## 生产环境部署

### 方案 1: Docker 部署 (推荐)

#### 1.1 创建 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir uv && \
    uv sync --frozen

# 创建数据目录
RUN mkdir -p data/files

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "skillslike.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  skillslike-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      # API 配置
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - USE_OPENAI_COMPATIBLE=true

      # 应用配置
      - SKILLS_DIR=skills/
      - FILE_STORE_DIR=data/files/
      - CHECKPOINT_STORE=redis

      # Redis 配置 (可选)
      - REDIS_URL=redis://redis:6379

    volumes:
      - ./data:/app/data
      - ./skills:/app/skills
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/usr/share/nginx/html/static
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - skillslike-api
    restart: unless-stopped

volumes:
  redis-data:
```

#### 1.3 配置 Nginx (反向代理)

创建 `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream skillslike_backend {
        server skillslike-api:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # 重定向到 HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL 证书
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # 静态文件
        location /static/ {
            alias /usr/share/nginx/html/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API 代理
        location /api/ {
            proxy_pass http://skillslike_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 超时设置 (图像生成可能较慢)
            proxy_read_timeout 120s;
            proxy_connect_timeout 120s;
            proxy_send_timeout 120s;
        }

        # 健康检查
        location /health {
            proxy_pass http://skillslike_backend/health;
        }

        # 前端页面
        location / {
            proxy_pass http://skillslike_backend;
            proxy_set_header Host $host;
        }
    }
}
```

#### 1.4 部署步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-org/skillslike.git
cd skillslike

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑 API 密钥

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f skillslike-api

# 5. 检查健康状态
curl http://localhost:8000/health

# 6. 访问前端
# http://your-domain.com
```

### 方案 2: 云服务部署 (AWS/Alibaba Cloud)

#### 2.1 使用 AWS ECS

```yaml
# ecs-task-definition.json
{
  "family": "skillslike-api",
  "containerDefinitions": [
    {
      "name": "skillslike",
      "image": "your-registry/skillslike:latest",
      "memory": 2048,
      "cpu": 1024,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-api-key"
        },
        {
          "name": "OPENAI_BASE_URL",
          "value": "https://api.bltcy.ai"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/skillslike",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

部署命令:
```bash
# 构建镜像
docker build -t skillslike:latest .

# 推送到 ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URL
docker tag skillslike:latest YOUR_ECR_URL/skillslike:latest
docker push YOUR_ECR_URL/skillslike:latest

# 创建服务
aws ecs create-service \
  --cluster skillslike-cluster \
  --service-name skillslike-api \
  --task-definition skillslike-api \
  --desired-count 2 \
  --launch-type FARGATE
```

#### 2.2 使用阿里云容器服务

```bash
# 登录阿里云容器镜像服务
docker login --username=your-username registry.cn-hangzhou.aliyuncs.com

# 构建并推送
docker build -t registry.cn-hangzhou.aliyuncs.com/your-namespace/skillslike:latest .
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/skillslike:latest

# 在阿里云控制台创建容器服务应用
# 或使用 kubectl 部署到 ACK
```

### 方案 3: 传统服务器部署

```bash
# 1. 安装依赖
sudo apt update
sudo apt install python3.12 python3.12-venv nginx supervisor

# 2. 克隆项目
cd /opt
git clone https://github.com/your-org/skillslike.git
cd skillslike

# 3. 安装 Python 依赖
python3.12 -m venv .venv
source .venv/bin/activate
pip install uv
uv sync

# 4. 配置环境变量
cp .env.example .env
nano .env

# 5. 配置 Supervisor (进程管理)
sudo nano /etc/supervisor/conf.d/skillslike.conf
```

Supervisor 配置:
```ini
[program:skillslike]
command=/opt/skillslike/.venv/bin/uvicorn skillslike.api.main:app --host 0.0.0.0 --port 8000
directory=/opt/skillslike
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/skillslike/err.log
stdout_logfile=/var/log/skillslike/out.log
environment=
    OPENAI_API_KEY="your-api-key",
    OPENAI_BASE_URL="https://api.bltcy.ai"
```

```bash
# 6. 启动服务
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start skillslike

# 7. 配置 Nginx (参考方案 1 的 nginx.conf)
sudo cp nginx.conf /etc/nginx/sites-available/skillslike
sudo ln -s /etc/nginx/sites-available/skillslike /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Web 用户体验流程

### 1. 用户访问流程

```
用户浏览器
    ↓
打开 https://your-domain.com
    ↓
加载 static/index.html (前端界面)
    ↓
前端 JS 初始化
    ↓
调用 GET /api/skills 获取可用技能列表
    ↓
显示聊天界面 + 技能列表
```

### 2. 对话交互流程

```
用户输入消息: "帮我画一只小猫"
    ↓
前端发送 POST /api/chat
    {
        "message": "帮我画一只小猫",
        "thread_id": "session-xxx"
    }
    ↓
FastAPI 接收请求
    ↓
Intent Router 分析关键词 ["画", "小猫"]
    ↓
匹配到 nano-banana-image-gen skill
    ↓
加载对应的 Tool (只加载匹配的，不是全部)
    ↓
LangGraph Agent 执行
    ├─ LLM 决定调用 nano_banana_image_gen 工具
    ├─ ImageGenExecutor.execute() 调用 API
    ├─ 下载生成的图片
    ├─ 存储到 data/files/
    └─ 返回 file_id
    ↓
Agent 生成友好的回复文本
    ↓
FastAPI 返回响应
    {
        "text": "我已经为你生成了一只可爱的小猫！",
        "files": ["file-id-xxx"],
        "thread_id": "session-xxx"
    }
    ↓
前端接收响应
    ↓
检测到 file_id，自动渲染图片
    <img src="/api/file/file-id-xxx">
    ↓
用户看到图片
```

### 3. 前端关键代码

**发送消息** (`static/js/app.js`):
```javascript
async function sendMessage(message) {
    const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            thread_id: currentThreadId
        })
    });

    const data = await response.json();

    // 显示回复
    displayMessage('assistant', data.text);

    // 如果有文件，显示图片
    if (data.files && data.files.length > 0) {
        data.files.forEach(fileId => {
            displayImage(fileId);
        });
    }
}

function displayImage(fileId) {
    const imgUrl = `${API_BASE}/api/file/${fileId}`;
    const imgHtml = `<img src="${imgUrl}" class="max-w-full rounded-lg">`;
    // 添加到聊天界面
}
```

### 4. 用户体验优化

#### 4.1 前端优化

```javascript
// 1. 添加 loading 状态
function showTypingIndicator() {
    const indicator = `
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    chatMessages.insertAdjacentHTML('beforeend', indicator);
}

// 2. 实时显示技能列表
async function loadSkills() {
    const response = await fetch(`${API_BASE}/api/skills`);
    const skills = await response.json();

    skills.forEach(skill => {
        displaySkillBadge(skill);
    });
}

// 3. 错误处理
try {
    const response = await sendMessage(message);
} catch (error) {
    displayError('请求失败，请稍后重试');
}
```

#### 4.2 后端优化

在 `skillslike/api/main.py` 添加速率限制和缓存:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("20/minute")  # 限制每分钟 20 次请求
async def chat(request: ChatRequest):
    # ... 处理逻辑
```

---

## 运维监控

### 1. 日志监控

#### 1.1 配置日志

在 `skillslike/config.py` 添加:
```python
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/skillslike.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

#### 1.2 查看日志

```bash
# Docker 环境
docker-compose logs -f skillslike-api

# 传统服务器
tail -f /var/log/skillslike/out.log

# 使用 ELK Stack 聚合日志
```

### 2. 性能监控

#### 2.1 Prometheus + Grafana

在 `skillslike/api/main.py` 添加 metrics:
```python
from prometheus_client import Counter, Histogram, make_asgi_app

# Metrics
request_count = Counter('requests_total', 'Total requests', ['endpoint', 'status'])
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    request_duration.observe(duration)
    request_count.labels(endpoint=request.url.path, status=response.status_code).inc()

    return response

# 添加 metrics 端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

#### 2.2 健康检查

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "skills_loaded": len(registry.get_all_manifests()),
        "timestamp": datetime.utcnow().isoformat(),
    }
```

### 3. 告警配置

创建 `alerting-rules.yml` (Prometheus):
```yaml
groups:
  - name: skillslike
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowRequests
        expr: histogram_quantile(0.95, request_duration_seconds) > 30
        for: 5m
        annotations:
          summary: "95th percentile latency > 30s"
```

### 4. 备份策略

```bash
#!/bin/bash
# backup.sh - 每日备份脚本

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/skillslike/$DATE"

# 备份文件存储
mkdir -p $BACKUP_DIR
cp -r /app/data/files $BACKUP_DIR/

# 备份技能配置
cp -r /app/skills $BACKUP_DIR/

# 备份数据库 (如果使用 SQLite checkpoint)
cp /app/data/checkpoints.db $BACKUP_DIR/

# 上传到 S3
aws s3 sync $BACKUP_DIR s3://your-bucket/skillslike-backups/$DATE/

# 清理 30 天前的备份
find /backup/skillslike -mtime +30 -exec rm -rf {} \;
```

---

## 快速部署检查清单

### 部署前准备

- [ ] 配置 `.env` 文件，填入所有 API 密钥
- [ ] 检查 `skills/` 目录中的所有 YAML 文件是否正确
- [ ] 确保所有 executor 都已正确实现和注册
- [ ] 运行单元测试: `pytest`
- [ ] 本地测试前端和 API: `uvicorn skillslike.api.main:app --reload`

### Docker 部署

- [ ] 构建镜像: `docker build -t skillslike:latest .`
- [ ] 测试容器: `docker run -p 8000:8000 skillslike:latest`
- [ ] 配置 `docker-compose.yml` 环境变量
- [ ] 配置 Nginx SSL 证书
- [ ] 启动: `docker-compose up -d`
- [ ] 检查健康: `curl http://localhost:8000/health`

### 生产环境

- [ ] 配置域名 DNS 解析
- [ ] 配置 SSL/TLS 证书 (Let's Encrypt)
- [ ] 设置防火墙规则 (只开放 80, 443 端口)
- [ ] 配置日志轮转和监控
- [ ] 设置备份策略
- [ ] 配置告警规则
- [ ] 进行压力测试

### 监控和维护

- [ ] 配置 Prometheus + Grafana 监控
- [ ] 配置告警通知 (邮件/Slack/钉钉)
- [ ] 定期查看日志和错误率
- [ ] 定期更新依赖包
- [ ] 定期备份数据

---

## 故障排查

### 常见问题

**1. Skill 未被加载**
```bash
# 检查日志
docker-compose logs skillslike-api | grep "Loaded skill"

# 验证 YAML 语法
python -c "import yaml; print(yaml.safe_load(open('skills/your-skill.yaml')))"
```

**2. API 调用失败**
```bash
# 检查环境变量
docker-compose exec skillslike-api env | grep API_KEY

# 测试 API 连接
curl -X POST https://api.bltcy.ai/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**3. 图片生成超时**
- 增加 Nginx `proxy_read_timeout`
- 检查 API 提供商状态
- 查看 executor 日志: `grep "image_gen_executor" logs/skillslike.log`

---

## 总结

完整的生产部署流程:

1. **开发环境**: 创建 YAML + Executor → 本地测试
2. **构建镜像**: Docker build → 推送到镜像仓库
3. **部署服务**: Docker Compose / K8s / 云服务
4. **配置网关**: Nginx / ALB 反向代理
5. **监控运维**: 日志 + Metrics + 告警
6. **用户访问**: Web 前端 → API → Agent → Skill Execution

每添加一个新 Skill，只需:
- 添加 `skills/new-skill.yaml`
- 创建 `skillslike/executors/new_skill_executor.py`
- 在 `registry.py` 注册
- 重启服务: `docker-compose restart skillslike-api`

用户无需了解内部实现，通过简单的 Web 界面即可体验所有技能！
