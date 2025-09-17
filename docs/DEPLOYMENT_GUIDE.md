# 🐳 Telegram Message Bot v3.0 部署指南

本指南详细介绍如何部署Telegram消息转发机器人v3.0版本。

## 📋 系统要求

### 最低配置
- **CPU**: 1核心
- **内存**: 512MB RAM
- **存储**: 2GB可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **CPU**: 2核心或以上
- **内存**: 1GB RAM或以上
- **存储**: 5GB可用空间
- **网络**: 带宽10Mbps或以上

### 软件依赖
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **操作系统**: Linux/Windows/macOS

## 🚀 部署方式

### 方式一：Docker Compose 部署（推荐）

#### 1. 准备项目文件

```bash
# 下载项目文件
git clone <repository-url>
cd telegram-message-bot-v3.0

# 或直接使用提供的项目包
unzip telegram-message-bot-v3.0.zip
cd "Telegram Message v3.0"
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**必填配置项**：
```env
# Telegram API配置
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
PHONE_NUMBER=+1234567890
ADMIN_USER_IDS=your_user_id

# 其他配置使用默认值即可
```

#### 3. 启动服务

```bash
# 构建并启动服务
docker-compose up -d

# 查看启动状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 4. 验证部署

```bash
# 检查服务状态
curl http://localhost:9393/api/system/enhanced-status

# 访问Web界面
# 浏览器打开: http://localhost:9393
```

### 方式二：Docker 手动部署

#### 1. 构建镜像

```bash
# 构建Docker镜像
docker build -t telegram-message-bot:v3.0 .

# 验证镜像构建成功
docker images telegram-message-bot:v3.0
```

#### 2. 创建数据目录

```bash
# 创建持久化数据目录
mkdir -p ./data ./logs ./sessions
chmod 755 ./data ./logs ./sessions
```

#### 3. 运行容器

```bash
docker run -d \
  --name telegram-message-bot \
  --restart unless-stopped \
  -p 9393:9393 \
  -e API_ID=your_api_id \
  -e API_HASH=your_api_hash \
  -e BOT_TOKEN=your_bot_token \
  -e PHONE_NUMBER=+1234567890 \
  -e ADMIN_USER_IDS=your_user_id \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/sessions:/app/sessions \
  telegram-message-bot:v3.0
```

### 方式三：本地开发部署

#### 1. 环境准备

```bash
# 确保Python 3.11+已安装
python --version

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置文件

```bash
# 复制配置模板
cp app.config.example app.config

# 编辑配置文件
nano app.config
```

#### 3. 启动服务

```bash
# 直接运行
python web_enhanced_clean.py

# 或使用后台运行
nohup python web_enhanced_clean.py > bot.log 2>&1 &
```

## ⚙️ 高级配置

### 代理配置

如果服务器无法直接访问Telegram，需要配置代理：

```env
# 启用代理
ENABLE_PROXY=true
PROXY_TYPE=http
PROXY_HOST=your_proxy_host
PROXY_PORT=your_proxy_port

# HTTP代理环境变量
HTTP_PROXY=http://proxy_host:proxy_port
HTTPS_PROXY=http://proxy_host:proxy_port
```

### SSL/HTTPS配置

#### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:9393;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 数据库配置

#### 使用PostgreSQL（可选）

```env
# 替换SQLite为PostgreSQL
DATABASE_URL=postgresql://username:password@localhost/telegram_bot
```

对应的docker-compose.yml添加：

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: telegram_bot
      POSTGRES_USER: username
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  telegram-bot:
    depends_on:
      - postgres
    # ... 其他配置

volumes:
  postgres_data:
```

## 🔧 维护操作

### 日常维护

#### 查看运行状态

```bash
# Docker Compose方式
docker-compose ps
docker-compose logs --tail=100

# Docker方式
docker ps
docker logs telegram-message-bot --tail=100
```

#### 重启服务

```bash
# Docker Compose方式
docker-compose restart

# Docker方式
docker restart telegram-message-bot
```

#### 更新服务

```bash
# 停止服务
docker-compose down

# 拉取最新代码/镜像
git pull
# 或更新镜像
docker pull telegram-message-bot:latest

# 重新启动
docker-compose up -d
```

### 备份与恢复

#### 数据备份

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/ sessions/

# 备份到远程
rsync -avz data/ user@backup-server:/backup/telegram-bot/
```

#### 数据恢复

```bash
# 停止服务
docker-compose down

# 恢复数据
tar -xzf backup-20250917.tar.gz

# 重启服务
docker-compose up -d
```

### 日志管理

#### 日志轮转配置

```bash
# 创建logrotate配置
sudo tee /etc/logrotate.d/telegram-bot << EOF
/path/to/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker-compose restart telegram-bot
    endscript
}
EOF
```

## 🚨 故障排除

### 常见问题诊断

#### 1. 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 9393

# 检查Docker服务
systemctl status docker

# 查看详细错误日志
docker-compose logs telegram-bot
```

#### 2. 无法连接Telegram

```bash
# 测试网络连接
curl -I https://api.telegram.org

# 检查代理配置
docker-compose exec telegram-bot env | grep PROXY

# 查看Telegram连接日志
docker-compose logs | grep -i telegram
```

#### 3. Web界面无法访问

```bash
# 检查服务监听端口
docker-compose exec telegram-bot netstat -tlnp | grep 9393

# 检查防火墙设置
sudo ufw status
sudo iptables -L

# 测试本地访问
curl http://localhost:9393
```

### 性能优化

#### 资源限制配置

```yaml
# docker-compose.yml
services:
  telegram-bot:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

#### 数据库优化

```env
# 增加SQLite性能
DATABASE_URL=sqlite:///data/bot.db?cache=shared&mode=rwc

# 或使用内存数据库（测试环境）
DATABASE_URL=sqlite:///:memory:
```

## 🔒 安全配置

### 防火墙设置

```bash
# 只允许必要端口访问
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 9393/tcp   # 禁止直接访问应用端口
sudo ufw enable
```

### 访问控制

```env
# 限制管理员访问
ADMIN_USER_IDS=123456789,987654321

# 设置强密码
SESSION_SECRET=your-very-strong-secret-key-here

# 启用访问日志
ENABLE_ACCESS_LOG=true
```

### 数据加密

```env
# 启用数据库加密（如果支持）
DATABASE_ENCRYPTION=true
DATABASE_KEY=your-encryption-key

# 启用会话加密
SESSION_ENCRYPTION=true
```

## 📊 监控配置

### Prometheus监控

```yaml
# docker-compose.yml 添加
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 健康检查配置

```yaml
# docker-compose.yml
services:
  telegram-bot:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9393/api/system/enhanced-status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

## 📱 移动端配置

### 通过Telegram访问

1. 创建专用管理机器人
2. 配置Webhook接收命令
3. 实现移动端管理功能

```python
# 示例：添加移动端管理命令
@bot.message_handler(commands=['status'])
def status_command(message):
    if message.from_user.id in ADMIN_USER_IDS:
        status = get_system_status()
        bot.reply_to(message, f"系统状态: {status}")
```

---

如有其他问题，请参考项目主README或提交Issue获取支持。
