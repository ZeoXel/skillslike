#!/bin/bash

# SkillsLike 一键部署脚本
# 使用方法: ./deploy.sh [dev|prod]

set -e

MODE=${1:-dev}
ENV_FILE=".env"

echo "🚀 SkillsLike 部署脚本"
echo "📦 部署模式: $MODE"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   访问: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 复制..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo ""
    echo "⚠️  请编辑 .env 文件，填入你的 API 密钥:"
    echo "   nano .env"
    echo ""
    read -p "按 Enter 继续编辑，或 Ctrl+C 退出..."
    ${EDITOR:-nano} .env
fi

# 验证关键环境变量
echo "🔍 验证环境变量..."
source $ENV_FILE

if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ 错误: 必须配置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY"
    exit 1
fi

echo "✅ 环境变量验证通过"
echo ""

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/files
mkdir -p logs
echo "✅ 目录创建完成"
echo ""

# 根据模式部署
if [ "$MODE" == "prod" ]; then
    echo "🏭 生产环境部署"
    echo ""

    # 构建镜像
    echo "🔨 构建 Docker 镜像..."
    docker-compose build --no-cache
    echo "✅ 镜像构建完成"
    echo ""

    # 启动服务
    echo "🚀 启动服务..."
    docker-compose up -d
    echo "✅ 服务已启动"
    echo ""

    # 等待服务就绪
    echo "⏳ 等待服务启动..."
    sleep 5

    # 健康检查
    echo "🏥 健康检查..."
    for i in {1..10}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            echo "✅ 服务健康检查通过"
            break
        fi
        echo "   尝试 $i/10..."
        sleep 2
    done

    echo ""
    echo "🎉 部署完成！"
    echo ""
    echo "📊 查看日志:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🌐 访问地址:"
    echo "   http://localhost:8000"
    echo ""
    echo "🔍 查看运行状态:"
    echo "   docker-compose ps"
    echo ""
    echo "🛑 停止服务:"
    echo "   docker-compose down"

elif [ "$MODE" == "dev" ]; then
    echo "💻 开发环境部署"
    echo ""

    # 检查 uv 是否安装
    if ! command -v uv &> /dev/null; then
        echo "📦 安装 uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi

    # 安装依赖
    echo "📦 安装 Python 依赖..."
    uv sync
    echo "✅ 依赖安装完成"
    echo ""

    # 启动服务
    echo "🚀 启动开发服务器..."
    echo ""
    echo "访问地址: http://localhost:8000"
    echo "按 Ctrl+C 停止服务"
    echo ""

    uv run uvicorn skillslike.api.main:app --host 0.0.0.0 --port 8000 --reload

else
    echo "❌ 错误: 未知的部署模式 '$MODE'"
    echo ""
    echo "使用方法:"
    echo "  ./deploy.sh dev   # 开发环境"
    echo "  ./deploy.sh prod  # 生产环境"
    exit 1
fi
