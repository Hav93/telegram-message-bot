@echo off
REM 构建和部署脚本 - Windows版本

echo 🔧 开始构建和部署流程...

REM 1. 检查Node.js环境
echo 📦 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到npm，请先安装npm
    pause
    exit /b 1
)

echo ✅ Node.js和npm已安装

REM 2. 进入前端目录并构建
echo 🏗️ 构建React前端...
cd app\frontend
if errorlevel 1 (
    echo ❌ 错误：无法进入app\frontend目录
    pause
    exit /b 1
)

REM 清理旧的构建文件
echo 🧹 清理旧的构建文件...
if exist dist rmdir /s /q dist
if exist node_modules\.cache rmdir /s /q node_modules\.cache

REM 安装依赖（如果需要）
if not exist node_modules (
    echo 📦 安装前端依赖...
    npm ci
)

REM 构建前端
echo 🔨 开始构建...
npm run build

REM 检查构建是否成功
if not exist dist (
    echo ❌ 错误：前端构建失败，dist目录不存在
    pause
    exit /b 1
)

if not exist dist\index.html (
    echo ❌ 错误：前端构建失败，index.html不存在
    pause
    exit /b 1
)

echo ✅ 前端构建成功！
echo 📁 构建文件位置: %cd%\dist
dir dist

REM 3. 返回项目根目录
cd ..\..

echo.
echo 🎉 构建完成！
echo 📋 下一步操作：
echo    1. 重启Python服务以加载新的前端文件
echo    2. 访问 http://localhost:9393 查看效果
echo    3. 强制刷新浏览器缓存 (Ctrl+F5)
echo.
pause
