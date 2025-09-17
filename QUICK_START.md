# 🚀 Telegram Message Bot v3.0 - 快速开始

## 📦 一键部署

### 第一步：下载配置文件

复制以下内容保存为 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  telegram-message-bot:
    image: hav93/telegram-message-bot:3.0
    container_name: telegram-message-bot
    restart: always
    networks:
      - telegram-net

    ports:
      - 9393:9393

    environment:
      - TZ=Asia/Shanghai
      # === Telegram API配置 ===
      - API_ID=your_api_id_here                    # 从 https://my.telegram.org 获取
      - API_HASH=your_api_hash_here               # 从 https://my.telegram.org 获取
      - BOT_TOKEN=your_bot_token_here         # 从 @BotFather 获取
      - PHONE_NUMBER=your_phone_number_here       # 您的手机号（国际格式）
      - ADMIN_USER_IDS=your_admin_user_ids     # 管理员用户ID（多个用逗号分隔）
      - HTTP_PROXY=your_http_proxy_here           # 代理地址（可选）
      - HTTPS_PROXY=your_https_proxy_here         # 代理地址（可选）
      - DATABASE_URL=sqlite:///data/bot.db
      
      # Web界面配置
      - WEB_HOST=0.0.0.0
      - WEB_PORT=9393
      
      # 权限配置
      - PUID=1000
      - PGID=1000
      
    volumes:
      - /path/to/your/data:/app/data
      - /path/to/your/logs:/app/logs
      - /path/to/your/temp:/app/temp
      - /path/to/your/sessions:/app/sessions
      - /path/to/your/config:/app/config
      
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:9393/').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  telegram-net:
    driver: bridge
```

### 第二步：修改配置

只需要修改以下几个必要参数：

1. **API_ID** 和 **API_HASH**：从 [https://my.telegram.org](https://my.telegram.org) 获取
2. **BOT_TOKEN**：从 [@BotFather](https://t.me/BotFather) 获取
3. **PHONE_NUMBER**：您的手机号（国际格式，如：+8613800138000）
4. **ADMIN_USER_IDS**：管理员用户ID（从 [@userinfobot](https://t.me/userinfobot) 获取）
5. **数据目录路径**：修改 `/path/to/your/` 为实际路径

**代理配置（可选）**：
- 如果不需要代理，删除 `HTTP_PROXY` 和 `HTTPS_PROXY` 行
- 如果需要代理，填入格式：`http://ip:port` 或 `http://username:password@ip:port`

### 第三步：启动服务

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps
```

### 第四步：访问界面

浏览器打开：**http://localhost:9393**

## 📱 获取必要信息

### 1. 获取 API_ID 和 API_HASH

1. 访问 [https://my.telegram.org](https://my.telegram.org)
2. 用手机号登录
3. 点击 "API development tools"
4. 创建新应用，获取 `api_id` 和 `api_hash`

### 2. 获取 BOT_TOKEN

1. 在Telegram中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称
4. 获取 Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 3. 获取用户ID

1. 在Telegram中找到 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息
3. 机器人会回复您的用户ID

## 🎯 使用指南

### 初次设置

1. 启动后访问 Web界面
2. 进入 "客户端管理" → 添加用户客户端
3. 输入手机号完成验证码登录

### 创建转发规则

1. 进入 "转发规则" → 点击 "新建规则"
2. 设置源群组和目标群组
3. 配置过滤条件（可选）
4. 启用规则

## 🔧 常见问题

### Q: 容器启动失败
**A:** 检查配置是否正确，查看日志：`docker-compose logs`

### Q: 无法连接Telegram
**A:** 检查网络或配置代理，确保能访问 api.telegram.org

### Q: 验证码登录失败
**A:** 确认手机号格式正确（+86开头），检查短信验证码

### Q: Web界面无法访问
**A:** 检查端口9393是否被占用，防火墙是否开放

## 🛠️ 管理命令

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新镜像
docker-compose pull
docker-compose up -d
```

## 📊 功能特性

- ✅ **自动消息转发**：群组到群组的消息转发
- ✅ **智能过滤**：关键词、正则表达式过滤
- ✅ **内容替换**：自动替换消息内容
- ✅ **多客户端**：支持用户账号和机器人同时工作
- ✅ **Web管理**：现代化的管理界面
- ✅ **实时监控**：转发统计和状态监控
- ✅ **代理支持**：支持HTTP/SOCKS代理
- ✅ **Docker部署**：一键容器化部署

---

**🎉 现在开始使用您的Telegram消息转发机器人吧！**
