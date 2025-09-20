#!/bin/bash

# Telegram Message Bot v3.6 - 快速部署脚本
# 适用于Linux/macOS生产环境

set -e

echo "🚀 Telegram Message Bot v3.6 - 快速部署"
echo "============================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down 2>/dev/null || true

# 构建新镜像
echo "🔨 构建Docker镜像..."
docker build -t telegram-message-bot:v3.6 .

# 启动服务
echo "🌟 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if curl -f http://localhost:9393/api/system/enhanced-status &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📱 Web界面地址: http://localhost:9393"
    echo "🔧 配置流程:"
    echo "   1. 访问Web界面"
    echo "   2. 进入'客户端管理'页面配置Telegram API"
    echo "   3. 或在'设置'页面直接重启客户端"
    echo "   4. 享受增强的Telegram消息转发功能！"
    echo ""
    echo "📊 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请检查日志:"
    echo "docker-compose logs"
fi

echo "============================================"
echo "🎉 部署完成！"
