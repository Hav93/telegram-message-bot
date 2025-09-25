#!/bin/bash

# Telegram Message Bot v3.0 部署脚本
# 适配 NAS 环境优化版本

echo "========================================="
echo "  Telegram Message Bot v3.0 部署脚本"
echo "========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装或不在 PATH 中"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装或不在 PATH 中"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data logs sessions temp

# 设置目录权限（针对NAS环境）
echo "🔧 设置目录权限..."
chmod 755 data logs sessions temp

# 检查配置文件
if [ ! -f "app.config.example" ]; then
    echo "⚠️  未找到 app.config.example 文件"
else
    echo "📄 配置文件示例存在"
fi

# 构建前端
echo "🎨 构建前端..."
cd app/frontend
npm ci && npm run build
cd ../..

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker build -t telegram-message-bot:v3.0 .

if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败"
    exit 1
fi

echo "✅ 镜像构建成功"

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 服务启动失败"
    exit 1
fi

echo "✅ 服务启动成功"

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 显示日志
echo "📝 显示最新日志..."
docker-compose logs --tail=20

echo "========================================="
echo "🎉 部署完成！"
echo ""
echo "Web 界面: http://localhost:9393"
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "========================================="