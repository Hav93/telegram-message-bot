#!/bin/bash
# 构建和部署脚本 - 解决服务端前端更新问题

echo "🔧 开始构建和部署流程..."

# 1. 检查Node.js环境
echo "📦 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "❌ 错误：未找到Node.js，请先安装Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ 错误：未找到npm，请先安装npm"
    exit 1
fi

echo "✅ Node.js版本: $(node --version)"
echo "✅ npm版本: $(npm --version)"

# 2. 进入前端目录并构建
echo "🏗️ 构建React前端..."
cd app/frontend || {
    echo "❌ 错误：无法进入app/frontend目录"
    exit 1
}

# 清理旧的构建文件
echo "🧹 清理旧的构建文件..."
rm -rf dist/
rm -rf node_modules/.cache/

# 安装依赖（如果需要）
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm ci
fi

# 构建前端
echo "🔨 开始构建..."
npm run build

# 检查构建是否成功
if [ ! -d "dist" ]; then
    echo "❌ 错误：前端构建失败，dist目录不存在"
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    echo "❌ 错误：前端构建失败，index.html不存在"
    exit 1
fi

echo "✅ 前端构建成功！"
echo "📁 构建文件位置: $(pwd)/dist"
ls -la dist/

# 3. 返回项目根目录
cd ../../

# 4. 检查后端配置
echo "🔍 检查后端前端路径配置..."
if grep -q "app/frontend/dist" app/backend/web_enhanced_clean.py; then
    echo "✅ 后端路径配置正确"
else
    echo "⚠️ 警告：后端可能未正确配置前端路径"
fi

# 5. 重启服务（如果正在运行）
echo "🔄 检查服务状态..."
if pgrep -f "python.*web_enhanced_clean.py" > /dev/null; then
    echo "⚠️ 检测到服务正在运行，建议重启以加载新的前端文件"
    echo "💡 请手动重启服务：pkill -f 'python.*web_enhanced_clean.py' && python app/backend/web_enhanced_clean.py"
else
    echo "✅ 服务未运行，可以启动服务"
fi

echo ""
echo "🎉 构建和部署检查完成！"
echo "📋 下一步操作："
echo "   1. 如果服务正在运行，请重启服务"
echo "   2. 如果服务未运行，请启动：python app/backend/web_enhanced_clean.py"
echo "   3. 访问 http://localhost:9393 查看效果"
echo "   4. 强制刷新浏览器缓存（Ctrl+F5 或 Cmd+Shift+R）"
