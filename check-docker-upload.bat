@echo off
echo ========================================
echo   Docker Hub 镜像上传状态检查
echo ========================================
echo.

echo 📋 本地镜像列表:
docker images hav93/telegram-message-bot --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo.

echo 🔍 检查Docker Hub镜像状态...
echo.

echo 📦 尝试拉取v3.0标签 (测试是否已上传):
docker pull hav93/telegram-message-bot:3.0 2>nul && echo "✅ v3.0标签已成功上传到Docker Hub" || echo "❌ v3.0标签尚未上传完成"
echo.

echo 📦 尝试拉取latest标签 (测试是否已上传):
docker pull hav93/telegram-message-bot:latest 2>nul && echo "✅ latest标签已成功上传到Docker Hub" || echo "❌ latest标签尚未上传完成"
echo.

echo 🌐 Docker Hub仓库地址:
echo https://hub.docker.com/r/hav93/telegram-message-bot
echo.

echo ========================================
echo 上传完成后，用户可以使用以下命令拉取:
echo docker pull hav93/telegram-message-bot:3.0
echo docker pull hav93/telegram-message-bot:latest
echo ========================================
pause
