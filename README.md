# 🚀 Telegram消息转发机器人

[![Docker Hub](https://img.shields.io/docker/pulls/hav93/telegram-message-bot.svg)](https://hub.docker.com/r/hav93/telegram-message-bot)
[![Docker Image Version](https://img.shields.io/docker/v/hav93/telegram-message-bot)](https://hub.docker.com/r/hav93/telegram-message-bot/tags)
[![Docker Image Size](https://img.shields.io/docker/image-size/hav93/telegram-message-bot/latest)](https://hub.docker.com/r/hav93/telegram-message-bot)

**版本**: v3.6.0  
**更新时间**: 2025年9月20日

一个功能强大的Telegram消息转发机器人，支持多客户端管理、智能过滤、关键词替换等高级功能。

## ✨ 主要功能

- 🔄 **智能消息转发**: 支持用户账号和机器人双模式转发
- 👥 **多客户端管理**: 同时管理多个Telegram账号
- 🎯 **智能过滤系统**: 关键词过滤、正则表达式替换、媒体类型筛选
- 🌐 **现代化Web界面**: React + TypeScript + Ant Design
- 📊 **实时监控**: 转发统计、系统状态、详细日志
- 🔒 **安全机制**: 管理员权限控制、会话管理
- 🌍 **代理支持**: HTTP/SOCKS代理支持

## 🖥️ Web界面功能

### 📊 仪表板
- 实时转发统计和系统状态
- 活跃规则概览
- 消息处理图表
- 系统健康监控

### 🔧 转发规则
- 创建和管理转发规则
- 关键词过滤设置
- 正则表达式替换
- 媒体类型选择
- 时间过滤配置

### 👥 客户端管理
- 添加/删除Telegram客户端
- 用户账号和机器人管理
- 客户端连接状态监控
- 登录验证流程

### 💬 聊天管理
- 源群组和目标群组选择
- 群组信息查看
- 权限验证

### 📝 系统日志
- 实时日志查看
- 错误信息追踪
- 转发记录统计
- 日志过滤和搜索

### ⚙️ 系统设置
- 基础配置管理
- 代理设置
- Telegram API配置
- 客户端重启控制

## 🚀 部署方法

### 方式一：Docker Compose（推荐）

1. **创建项目目录**
   ```bash
   mkdir telegram-message-bot && cd telegram-message-bot
   ```

2. **创建配置文件**
   ```bash
   # 创建 docker-compose.yml
   cat > docker-compose.yml << 'EOF'
   version: '3.8'
   
   services:
     telegram-message-bot:
       image: hav93/telegram-message-bot:latest
       container_name: telegram-message-bot
       restart: always
       ports:
         - "9393:9393"
       environment:
         - TZ=Asia/Shanghai
         - API_ID=${API_ID}
         - API_HASH=${API_HASH}
         - BOT_TOKEN=${BOT_TOKEN}
         - PHONE_NUMBER=${PHONE_NUMBER}
         - ADMIN_USER_IDS=${ADMIN_USER_IDS}
         - ENABLE_PROXY=${ENABLE_PROXY:-false}
         - PROXY_TYPE=${PROXY_TYPE:-http}
         - PROXY_HOST=${PROXY_HOST:-127.0.0.1}
         - PROXY_PORT=${PROXY_PORT:-1080}
         - DATABASE_URL=sqlite:///data/bot.db
         - WEB_HOST=0.0.0.0
         - WEB_PORT=9393
         - LOG_LEVEL=${LOG_LEVEL:-INFO}
       volumes:
         - ./data:/app/data
         - ./logs:/app/logs
         - ./sessions:/app/sessions
         - ./temp:/app/temp
   EOF

   # Telegram API配置（必需）
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   PHONE_NUMBER=+86your_phone
   ADMIN_USER_IDS=your_user_id
   
   # 代理配置（可选，外网环境通常不需要）
   ENABLE_PROXY=false
   #PROXY_TYPE=http
   #PROXY_HOST=127.0.0.1
   #PROXY_PORT=1080
   
   # 日志级别
   LOG_LEVEL=INFO
   EOF
   ```

3. **启动服务**
   ```bash
   # 拉取镜像并启动
   docker-compose up -d
   
   # 查看运行状态
   docker-compose ps
   ```

4. **访问Web界面**
   ```
   http://localhost:9393
   ```

### 方式二：Docker Hub镜像

> 🐳 **Docker Hub仓库**: [hav93/telegram-message-bot](https://hub.docker.com/r/hav93/telegram-message-bot)

1. **拉取镜像**
   ```bash
   docker pull hav93/telegram-message-bot:latest
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name telegram-message-bot \
     -p 9393:9393 \
     --env-file app.config \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/sessions:/app/sessions \
     hav93/telegram-message-bot:latest
   ```

### 方式三：源码部署

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置文件**
   ```bash
   cp app.config.example app.config
   # 编辑配置文件
   ```

3. **启动服务**
   ```bash
   python web_enhanced_clean.py
   ```

## ⚙️ 配置说明

### 必需配置项

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `API_ID` | Telegram API ID | [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API Hash | [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | 机器人Token（可选） | [@BotFather](https://t.me/BotFather) |
| `PHONE_NUMBER` | 手机号 | 用于用户客户端登录 |
| `ADMIN_USER_IDS` | 管理员用户ID | [@userinfobot](https://t.me/userinfobot) |

### 代理配置（可选）

```env
ENABLE_PROXY=false
PROXY_TYPE=http
PROXY_HOST=127.0.0.1
PROXY_PORT=1080
```

## 🎯 快速开始

1. **启动服务**：按照上述部署方法启动
2. **访问Web界面**：打开 `http://localhost:9393`
3. **配置客户端**：在"客户端管理"页面添加Telegram账号
4. **创建规则**：在"转发规则"页面设置转发规则
5. **监控运行**：在"仪表板"页面查看运行状态

## 💬 交流与支持

### 🔗 社区交流
- **Telegram群组**: [https://t.me/+a-1QAurcpxZhZThl](https://t.me/+a-1QAurcpxZhZThl)

### 🤝 支持方式
- ⭐ **GitHub Star**: 给项目点个星星
- 🐛 **Bug 反馈**: 提交 Issue 帮助改进
- 💡 **功能建议**: 分享您的想法和需求
- 📢 **推荐分享**: 向朋友推荐这个项目

## 🙏 感谢

感谢所有使用和支持本项目的朋友们！您的反馈和建议让这个项目变得更好。

### ☕ 请作者喝杯咖啡

如果这个项目对您有帮助，欢迎请作者喝杯咖啡 ☕

![微信支付](https://raw.githubusercontent.com/your-repo/telegram-message-bot/main/docs/wechat-pay.png)

*微信扫码支付*

## 📄 许可证与免责声明

### 许可证
本项目采用 [MIT 许可证](LICENSE)，您可以自由使用、修改和分发。

### 免责声明
本项目仅供学习和技术交流使用。使用者应当：
- 遵守当地法律法规和Telegram服务条款
- 不得将本软件用于任何违法违规活动
- 使用本软件产生的任何后果由使用者自行承担
- 开发者不对使用本软件造成的任何损失承担责任

**请合理合法地使用本项目，尊重他人隐私和权益。**

---

⭐ **如果这个项目对您有帮助，请给个Star支持一下！** ⭐

## ☕ 请作者喝杯咖啡

如果这个项目对您有帮助，欢迎请作者喝杯咖啡！您的支持是我们持续改进的动力。

<div align="center">

### 微信支付
<img src="wechat_pay_qr.png" alt="微信支付收款码" width="300">

*请使用微信扫一扫*

</div>