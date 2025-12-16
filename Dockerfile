FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY skillslike/ ./skillslike/
COPY skills/ ./skills/
COPY static/ ./static/

# 安装 uv 和依赖
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev

# 创建数据目录
RUN mkdir -p data/files

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["sh", "-c", "curl -f http://localhost:${PORT:-8000}/health || exit 1"]

# 启动命令
CMD ["uv", "run", "uvicorn", "skillslike.api.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
