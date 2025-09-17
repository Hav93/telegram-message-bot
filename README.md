# 🚀 Telegram Message Bot v3.0

一个功能强大的Telegram消息转发机器人，支持多客户端管理、智能过滤、关键词替换等高级功能。

## ✨ 主要功能

- 🔄 **多渠道消息转发**：支持用户账号和机器人双模式转发
- 👥 **多客户端管理**：同时管理多个Telegram账号
- 🎯 **智能过滤系统**：关键词过滤、正则表达式替换
- 🌐 **Web管理界面**：现代化的React前端管理界面
- 📊 **实时监控**：转发统计、系统状态监控
- 🔒 **安全机制**：管理员权限控制、会话管理
- 🌍 **代理支持**：HTTP/SOCKS代理支持
- 📝 **详细日志**：完整的操作日志记录

## 🏗️ 技术架构

### 后端技术栈
- **Python 3.11+** - 主要开发语言
- **FastAPI** - 高性能Web框架
- **Telethon** - Telegram客户端库
- **SQLAlchemy** - ORM数据库操作
- **SQLite** - 轻量级数据库
- **Uvicorn** - ASGI服务器

### 前端技术栈
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全的JavaScript
- **Ant Design** - UI组件库
- **React Query** - 数据状态管理
- **Vite** - 构建工具

## 📦 快速部署

### 方式一：Docker Compose（推荐）

1. **准备配置文件**
   ```bash
   # 复制环境变量示例文件
   cp .env.example .env
   
   # 编辑配置文件，填入实际值
   nano .env
   ```

2. **启动服务**
   ```bash
   # 构建并启动
   docker-compose up -d
   
   # 查看日志
   docker-compose logs -f
   ```

3. **访问界面**
   ```
   Web管理界面: http://localhost:9393
   ```

### 方式二：Docker 手动部署

1. **构建镜像**
   ```bash
   docker build -t telegram-message-bot:v3.0 .
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name telegram-message-bot \
     -p 9393:9393 \
     --env-file .env \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/sessions:/app/sessions \
     telegram-message-bot:v3.0
   ```

### 方式三：本地开发部署

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**
   ```bash
   cp app.config.example app.config
   # 编辑 app.config 填入配置
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
| `BOT_TOKEN` | 机器人Token | [@BotFather](https://t.me/BotFather) |
| `PHONE_NUMBER` | 手机号 | 用于用户客户端登录 |
| `ADMIN_USER_IDS` | 管理员用户ID | 获取方式见下文 |

### 获取用户ID

1. 向 [@userinfobot](https://t.me/userinfobot) 发送任意消息
2. 机器人会回复你的用户ID
3. 将ID填入 `ADMIN_USER_IDS` 配置项

### 代理配置（可选）

如果需要使用代理访问Telegram：

```env
ENABLE_PROXY=true
PROXY_TYPE=http
PROXY_HOST=127.0.0.1
PROXY_PORT=1080
HTTP_PROXY=http://127.0.0.1:1080
HTTPS_PROXY=http://127.0.0.1:1080
```

## 🎯 使用指南

### 1. 初次设置

1. 启动服务后，访问 `http://localhost:9393`
2. 进入"客户端管理"页面
3. 添加用户客户端，输入手机号
4. 完成验证码登录流程

### 2. 创建转发规则

1. 进入"转发规则"页面
2. 点击"新建规则"
3. 配置源群组和目标群组
4. 设置过滤条件和替换规则
5. 启用规则

### 3. 监控运行状态

1. "仪表板"页面查看转发统计
2. "系统日志"页面查看详细日志
3. "客户端管理"页面查看连接状态

## 🔧 高级配置

### 消息过滤

支持多种过滤方式：
- **关键词过滤**：包含/排除特定关键词
- **正则表达式**：复杂模式匹配
- **媒体类型**：图片、视频、文档等
- **发送者过滤**：特定用户消息

### 内容替换

支持消息内容处理：
- **关键词替换**：简单字符串替换
- **正则替换**：高级模式替换
- **格式化处理**：添加前缀、后缀等

### 性能优化

- **批量处理**：`MESSAGE_BATCH_SIZE` 控制批处理大小
- **处理延迟**：`MESSAGE_PROCESSING_DELAY` 控制处理间隔
- **日志管理**：自动清理过期日志文件

## 📊 系统监控

### 健康检查

Docker容器内置健康检查：
```bash
# 手动检查服务状态
curl http://localhost:9393/api/system/enhanced-status
```

### 日志管理

- **日志位置**：`logs/bot.log`
- **日志轮转**：自动按大小和时间轮转
- **日志清理**：可配置自动清理策略

### 性能监控

- **转发统计**：实时转发数量统计
- **客户端状态**：连接状态和错误监控
- **系统资源**：内存和CPU使用情况

## 🛠️ 故障排除

### 常见问题

1. **无法连接Telegram**
   - 检查网络连接
   - 确认代理配置
   - 查看防火墙设置

2. **验证码登录失败**
   - 确认手机号格式正确
   - 检查短信是否收到
   - 尝试重新获取验证码

3. **消息转发不工作**
   - 检查规则配置
   - 确认客户端连接状态
   - 查看系统日志

### 日志分析

```bash
# 查看最新日志
docker-compose logs -f --tail=100

# 搜索错误日志
docker-compose logs | grep ERROR

# 查看特定时间段日志
docker-compose logs --since="2025-01-01T00:00:00"
```

## 🔒 安全建议

1. **配置文件安全**
   - 不要将配置文件提交到版本控制
   - 使用强密码和复杂的SESSION_SECRET

2. **网络安全**
   - 使用反向代理（如Nginx）
   - 启用HTTPS
   - 限制访问IP范围

3. **权限控制**
   - 正确配置管理员用户ID
   - 定期检查访问日志
   - 及时更新系统

## 📚 API文档

### REST API端点

- `GET /api/system/enhanced-status` - 系统状态
- `GET /api/clients` - 客户端列表
- `POST /api/clients` - 添加客户端
- `GET /api/rules` - 转发规则列表
- `POST /api/rules` - 创建转发规则
- `GET /api/logs` - 系统日志

### WebSocket接口

- `/ws/status` - 实时状态更新
- `/ws/logs` - 实时日志推送

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持与反馈

- **Issue报告**：[GitHub Issues](https://github.com/your-repo/issues)
- **功能建议**：[GitHub Discussions](https://github.com/your-repo/discussions)
- **使用交流**：[Telegram群组](https://t.me/your-group)

## 📋 更新日志

### v3.0 (2025-09-17)
- ✨ 重构增强版机器人架构
- 🎨 全新React前端界面
- 🔧 修复规则显示问题
- 🐳 优化Docker部署
- 📊 改进监控和日志

### v2.2 (2025-09-13)
- 🔄 多端共存功能
- 🎯 智能过滤优化
- 🛠️ Bug修复和稳定性改进

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**
