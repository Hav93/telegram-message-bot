@echo off
REM 服务端客户端显示问题修复脚本 (Windows)

echo 开始修复服务端客户端显示问题...

REM 1. 停止现有服务
echo 1. 停止现有服务...
taskkill /f /im python.exe 2>nul

REM 2. 更新代码
echo 2. 更新代码...
git pull origin main

REM 3. 重建前端
if exist "app\frontend" (
    echo 3. 重建前端...
    cd app\frontend
    call npm ci
    call npm run build
    cd ..\..
) else (
    echo 3. 跳过前端构建 ^(目录不存在^)
)

REM 4. 初始化数据库
echo 4. 初始化数据库...
cd app\backend
python -c "import asyncio; import sys; sys.path.append('.'); from database import init_database; from enhanced_bot import EnhancedTelegramBot; asyncio.run(init_database()); print('数据库初始化完成')"

REM 5. 启动服务
echo 5. 启动服务...
start /b python web_enhanced_clean.py > ..\..\logs\web.log 2>&1
echo Web服务已启动

echo 修复完成！
echo 请访问您的网站检查客户端管理页面
pause
