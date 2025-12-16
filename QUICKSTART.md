# SkillsLike 快速开始指南

## 🚀 5分钟快速体验

### 1. 克隆项目并配置

```bash
# 克隆项目
git clone https://github.com/your-org/skillslike.git
cd skillslike

# 复制环境变量配置
cp .env.example .env

# 编辑配置文件，填入你的 API 密钥
nano .env
```

在 `.env` 中配置:
```bash
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.bltcy.ai
USE_OPENAI_COMPATIBLE=true
```

### 2. 使用 Docker 启动 (推荐)

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查健康状态
curl http://localhost:8000/health
```

**或者** 使用 Python 直接运行:

```bash
# 安装依赖
uv sync

# 启动服务
uv run uvicorn skillslike.api.main:app --host 0.0.0.0 --port 8000
```

### 3. 访问 Web 界面

打开浏览器访问: **http://localhost:8000**

你会看到:
- 左侧: 可用技能列表 (4个示例技能)
- 右侧: 聊天界面

### 4. 测试功能

在聊天框输入:

**图像生成测试:**
```
帮我画一只可爱的橘猫
```

**知识重组测试:**
```
帮我整理一下关于人工智能的知识
```

**网络搜索测试:**
```
搜索最新的 AI 新闻
```

---

## 📝 添加自己的 Skill

### 步骤 1: 创建 Skill Manifest

创建文件 `skills/my-awesome-skill.yaml`:

```yaml
name: my-awesome-skill
description: >
  我的第一个自定义技能。
  触发关键词: test, demo, 测试
version: 1.0.0

inputs:
  - name: query
    type: string
    description: "用户查询"
    required: true

outputs:
  - name: result
    type: string
    description: "处理结果"

runtime:
  type: custom
  timeout: 30

tags:
  - demo
  - custom
```

### 步骤 2: 创建 Executor

创建文件 `skillslike/executors/my_awesome_executor.py`:

```python
"""My awesome skill executor."""

import logging
from pydantic import BaseModel, Field
from skillslike.executors.base import BaseExecutor

logger = logging.getLogger(__name__)


class MyAwesomeInput(BaseModel):
    """Input schema."""
    query: str = Field(description="User query")


class MyAwesomeExecutor(BaseExecutor):
    """My awesome skill executor."""

    def get_input_schema(self) -> type[BaseModel]:
        return MyAwesomeInput

    def execute(self, query: str) -> str:
        """Execute the skill."""
        logger.info(f"Executing my awesome skill: {query}")

        # 你的自定义逻辑
        result = f"✨ 处理完成！你的查询是: {query}"

        return result
```

### 步骤 3: 注册 Executor

编辑 `skillslike/registry/registry.py`，在 `build_tool()` 方法中添加:

```python
from skillslike.executors.my_awesome_executor import MyAwesomeExecutor

# 在 build_tool() 方法中添加:
if manifest.name == "my-awesome-skill":
    executor = MyAwesomeExecutor(manifest)
    tool = StructuredTool.from_function(
        func=executor.execute,
        name=manifest.name.replace("-", "_"),
        description=manifest.description,
        args_schema=executor.get_input_schema(),
    )
```

### 步骤 4: 重启服务

```bash
# Docker 环境
docker-compose restart skillslike-api

# 或直接运行
# Ctrl+C 停止服务，然后重新运行
uv run uvicorn skillslike.api.main:app --host 0.0.0.0 --port 8000
```

### 步骤 5: 测试你的 Skill

在聊天界面输入:
```
测试一下 demo 功能
```

应该会看到你的 skill 被调用！

---

## 🌐 部署到生产环境

### 方案 1: Docker + Nginx (推荐)

1. **配置域名解析**
   - 添加 A 记录指向你的服务器 IP

2. **获取 SSL 证书**
```bash
# 使用 Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

3. **配置 Nginx**

取消 `docker-compose.yml` 中 nginx 部分的注释，然后创建 `nginx.conf`:

```nginx
# 见 PRODUCTION_DEPLOYMENT.md 中的完整配置
```

4. **启动完整服务**
```bash
docker-compose up -d
```

5. **访问**
```
https://your-domain.com
```

### 方案 2: 云服务商一键部署

**阿里云 / 腾讯云 / AWS:**
1. 购买云服务器 (2核4G 起步)
2. 安装 Docker 和 Docker Compose
3. 克隆项目并配置 `.env`
4. 运行 `docker-compose up -d`
5. 配置安全组 (开放 80, 443 端口)

---

## 📊 监控和维护

### 查看日志

```bash
# 实时日志
docker-compose logs -f skillslike-api

# 最近 100 行
docker-compose logs --tail=100 skillslike-api

# 查看特定技能的日志
docker-compose logs skillslike-api | grep "image_gen"
```

### 健康检查

```bash
# API 健康状态
curl http://localhost:8000/health

# 查看已加载的技能
curl http://localhost:8000/api/skills | jq
```

### 性能监控

添加 Prometheus metrics 端点:
```
http://localhost:8000/metrics
```

---

## 🆘 常见问题

### 1. 技能没有被触发？

**原因**: Intent Router 没有匹配到关键词

**解决**:
- 检查 skill YAML 中的 `description` 是否包含明确的触发关键词
- 查看日志: `docker-compose logs skillslike-api | grep "Routed to"`
- 尝试更明确的用户输入

### 2. API 调用失败？

**检查**:
```bash
# 验证环境变量
docker-compose exec skillslike-api env | grep API_KEY

# 测试 API 连接
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  $OPENAI_BASE_URL/v1/models
```

### 3. 图像生成超时？

- 检查网络连接
- 增加 timeout: 在 YAML 中设置 `runtime.timeout: 120`
- 查看详细错误: `docker-compose logs | grep ERROR`

### 4. 前端无法访问？

```bash
# 检查端口占用
lsof -i :8000

# 检查防火墙
sudo ufw status

# 测试 API
curl http://localhost:8000/api/skills
```

---

## 📚 下一步

- 阅读 [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) 了解完整部署流程
- 查看 [docs/usage-guide.md](docs/usage-guide.md) 学习高级用法
- 参考 [IMAGE_GEN_GUIDE.md](IMAGE_GEN_GUIDE.md) 了解图像生成详情

---

## 🎯 核心概念总结

```
Skill = YAML (配置) + Executor (实现)
         ↓
   Tool Registry 加载
         ↓
   Intent Router 路由 (根据关键词)
         ↓
   LangGraph Agent 执行
         ↓
   返回结果给用户
```

**添加新 Skill 只需 3 步**:
1. 写 YAML 定义
2. 写 Executor 实现
3. 在 Registry 注册

**用户使用流程**:
1. 打开网页
2. 输入消息
3. 系统自动选择合适的 Skill
4. 返回结果

就是这么简单！🎉
