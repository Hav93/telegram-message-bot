# Telegram Message Bot v3.6 - 生产环境配置指南

## 📋 配置说明

本项目已移除所有硬编码配置，支持灵活的环境变量配置。

## 🔧 必需配置

### Telegram API 配置
```bash
API_ID=your_api_id_here
API_HASH=your_api_hash_here  
BOT_TOKEN=your_bot_token_here
PHONE_NUMBER=+86your_phone_number
ADMIN_USER_IDS=your_user_id_here
```

## 🌐 代理配置（可选）

### 外网环境（推荐）
外网环境通常不需要代理，使用默认配置即可：
```bash
ENABLE_PROXY=false
```

### 内网环境
如果在内网环境需要通过代理访问Telegram：
```bash
ENABLE_PROXY=true
PROXY_TYPE=http
PROXY_HOST=your_proxy_host
PROXY_PORT=your_proxy_port
PROXY_USERNAME=your_proxy_username  # 可选
PROXY_PASSWORD=your_proxy_password  # 可选
```

### 标准HTTP代理环境变量
也支持标准的HTTP代理环境变量：
```bash
HTTP_PROXY=http://proxy_host:proxy_port
HTTPS_PROXY=http://proxy_host:proxy_port
```

## 🚀 部署方式

### 方式1：使用 .env 文件
1. 复制 `app.config.example` 为 `.env`
2. 填入您的配置信息
3. 运行 `docker-compose up -d`

### 方式2：直接设置环境变量
```bash
export API_ID=your_api_id_here
export API_HASH=your_api_hash_here
export BOT_TOKEN=your_bot_token_here
export PHONE_NUMBER=+86your_phone_number  
export ADMIN_USER_IDS=your_user_id_here
export ENABLE_PROXY=false  # 外网环境
docker-compose up -d
```

### 方式3：Docker运行时传递
```bash
docker run -d \
  -e API_ID=your_api_id_here \
  -e API_HASH=your_api_hash_here \
  -e BOT_TOKEN=your_bot_token_here \
  -e PHONE_NUMBER=+86your_phone_number \
  -e ADMIN_USER_IDS=your_user_id_here \
  -e ENABLE_PROXY=false \
  -p 9393:9393 \
  telegram-message-bot:v3.6
```

## 📝 其他可选配置

```bash
# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# 日志管理
ENABLE_LOG_CLEANUP=false
LOG_RETENTION_DAYS=30
LOG_CLEANUP_TIME=02:00
MAX_LOG_SIZE=100

# 时区
TZ=Asia/Shanghai
```

## ✅ 配置验证

启动后查看日志确认配置正确：
```bash
docker-compose logs | grep "配置验证"
```

正确配置应显示：
- ✅ Telegram API 配置完整
- ✅ 代理配置（如启用）
- ✅ 管理员配置正确

## 🔒 安全建议

1. **不要在代码中硬编码敏感信息**
2. **使用 .env 文件时确保不提交到版本控制**
3. **定期轮换 API 密钥和令牌**
4. **限制管理员用户权限**

## 🌍 不同环境示例

### 国内环境（需要代理）
```bash
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
PHONE_NUMBER=+86your_phone
ADMIN_USER_IDS=your_user_id
ENABLE_PROXY=true
PROXY_TYPE=http
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```

### 海外环境（无需代理）
```bash
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
PHONE_NUMBER=+1your_phone
ADMIN_USER_IDS=your_user_id
ENABLE_PROXY=false
```
