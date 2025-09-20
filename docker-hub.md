# Docker Hub 自动构建配置

## 🔗 Docker Hub 仓库链接
- **仓库地址**: https://hub.docker.com/r/hav93/telegram-message-bot
- **拉取命令**: `docker pull hav93/telegram-message-bot:latest`

## 🏷️ 可用标签
- `latest` - 最新稳定版本
- `v3.6` - v3.6版本
- `3.6.0` - 具体版本号

## 📊 镜像信息
- **基础镜像**: python:3.11-slim
- **架构支持**: linux/amd64, linux/arm64
- **镜像大小**: ~200MB
- **更新频率**: 跟随GitHub主分支自动构建

## 🔄 自动构建规则
- **源分支**: main
- **构建触发**: 
  - Push到main分支
  - 创建新的Git标签
  - 手动触发构建

## 📝 使用说明
```bash
# 拉取最新版本
docker pull hav93/telegram-message-bot:latest

# 拉取指定版本
docker pull hav93/telegram-message-bot:v3.6

# 运行容器
docker run -d --name telegram-bot hav93/telegram-message-bot:latest
```
