#!/bin/bash

# AI Interactive Novel System 启动脚本

echo "🚀 启动 AI Interactive Novel System..."

# 检查是否存在.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env文件不存在，正在复制模板..."
    cp .env.example .env
    echo "✅ 已创建.env文件，请编辑配置后重新运行"
    echo "📝 需要配置的主要项目："
    echo "   - GEMINI_API_KEY: 你的Gemini API密钥"
    echo "   - OLLAMA_BASE_URL: Ollama服务地址（如果使用）"
    exit 1
fi

# 检查UV是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ UV包管理器未安装"
    echo "📦 请运行以下命令安装UV："
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
uv sync

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

# 启动服务
echo "🌟 启动服务..."
echo "📖 API文档地址："
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "🔧 按 Ctrl+C 停止服务"
echo ""

uv run python main.py