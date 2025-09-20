@echo off
REM Telegram Message Bot v3.6 - Windows快速部署脚本

echo 🚀 Telegram Message Bot v3.6 - 快速部署
echo ============================================

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 停止旧容器
echo 🛑 停止旧容器...
docker-compose down >nul 2>&1

REM 构建新镜像
echo 🔨 构建Docker镜像...
docker build -t telegram-message-bot:v3.6 .

REM 启动服务
echo 🌟 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:9393/api/system/enhanced-status' -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo ❌ 服务启动失败，请检查日志:
    echo docker-compose logs
    pause
    exit /b 1
)

echo ✅ 服务启动成功！
echo.
echo 📱 Web界面地址: http://localhost:9393
echo 🔧 配置流程:
echo    1. 访问Web界面
echo    2. 进入'客户端管理'页面配置Telegram API
echo    3. 或在'设置'页面直接重启客户端  
echo    4. 享受增强的Telegram消息转发功能！
echo.
echo 📊 查看日志: docker-compose logs -f
echo 🛑 停止服务: docker-compose down
echo ============================================
echo 🎉 部署完成！

pause
