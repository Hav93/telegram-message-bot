#!/usr/bin/env python3
"""
服务端客户端显示问题完整诊断脚本
专门针对GitHub部署的服务端环境
"""

import asyncio
import sys
import os
import json
import sqlite3
from pathlib import Path

# 添加 app/backend 到路径
sys.path.append('app/backend')

async def check_github_deployment():
    """检查GitHub部署状态"""
    print("=== GitHub部署状态检查 ===")
    
    # 1. 检查前端构建文件
    frontend_dist = Path("app/frontend/dist")
    if frontend_dist.exists():
        print("✅ 前端构建目录存在")
        index_html = frontend_dist / "index.html"
        if index_html.exists():
            print("✅ index.html存在")
        else:
            print("❌ index.html不存在 - 前端构建可能失败")
            return False
    else:
        print("❌ 前端构建目录不存在 - GitHub Actions构建可能失败")
        return False
    
    # 2. 检查后端文件
    backend_files = [
        "app/backend/web_enhanced_clean.py",
        "app/backend/enhanced_bot.py", 
        "app/backend/models.py",
        "app/backend/database.py"
    ]
    
    for file_path in backend_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            return False
    
    return True

async def check_database_and_api():
    """检查数据库和API状态"""
    print("\n=== 数据库和API状态检查 ===")
    
    try:
        from models import TelegramClient
        from database import db_manager, init_database
        from sqlalchemy import select
        
        # 初始化数据库
        await init_database()
        print("✅ 数据库初始化成功")
        
        # 检查客户端记录
        async with db_manager.async_session() as session:
            result = await session.execute(select(TelegramClient))
            db_clients = result.scalars().all()
            
            print(f"数据库客户端记录: {len(db_clients)}")
            for client in db_clients:
                print(f"  - {client.client_id} ({client.client_type}) auto_start={client.auto_start}")
        
        # 模拟API响应
        clients_status = {}
        for db_client in db_clients:
            clients_status[db_client.client_id] = {
                "client_id": db_client.client_id,
                "client_type": db_client.client_type,
                "running": False,
                "connected": False,
                "login_state": "idle",
                "user_info": None,
                "monitored_chats": [],
                "thread_alive": False,
                "auto_start": db_client.auto_start
            }
        
        print(f"模拟API响应包含 {len(clients_status)} 个客户端")
        return len(clients_status) > 0, clients_status
        
    except Exception as e:
        print(f"❌ 数据库/API检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

async def check_frontend_api_call():
    """检查前端API调用逻辑"""
    print("\n=== 前端API调用逻辑检查 ===")
    
    try:
        # 检查前端服务文件
        clients_service = Path("app/frontend/src/services/clients.ts")
        if clients_service.exists():
            with open(clients_service, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'getClients' in content and '/api/clients' in content:
                    print("✅ 前端API调用逻辑存在")
                else:
                    print("❌ 前端API调用逻辑缺失")
                    return False
        else:
            print("❌ 前端服务文件不存在")
            return False
        
        # 检查ClientManagement页面
        client_page = Path("app/frontend/src/pages/ClientManagement/index.tsx")
        if client_page.exists():
            with open(client_page, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'auto_start' in content and 'useQuery' in content:
                    print("✅ ClientManagement页面包含auto_start功能")
                else:
                    print("❌ ClientManagement页面缺少auto_start功能")
                    return False
        else:
            print("❌ ClientManagement页面不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 前端检查失败: {e}")
        return False

def create_server_fix_script():
    """创建服务端修复脚本"""
    fix_script = '''#!/bin/bash
# 服务端客户端显示问题修复脚本

echo "开始修复服务端客户端显示问题..."

# 1. 停止现有服务
echo "1. 停止现有服务..."
pkill -f "python.*web_enhanced_clean.py" || true
pkill -f "python.*enhanced_bot.py" || true

# 2. 更新代码
echo "2. 更新代码..."
git pull origin main

# 3. 重建前端 (如果需要)
if [ -d "app/frontend" ]; then
    echo "3. 重建前端..."
    cd app/frontend
    npm ci
    npm run build
    cd ../..
else
    echo "3. 跳过前端构建 (目录不存在)"
fi

# 4. 初始化数据库
echo "4. 初始化数据库..."
cd app/backend
python -c "
import asyncio
import sys
sys.path.append('.')
from database import init_database
from enhanced_bot import EnhancedTelegramBot

async def setup():
    await init_database()
    bot = EnhancedTelegramBot()
    await bot._migrate_legacy_clients()
    print('数据库初始化完成')

asyncio.run(setup())
"

# 5. 启动服务
echo "5. 启动服务..."
nohup python web_enhanced_clean.py > ../../logs/web.log 2>&1 &
echo "Web服务已启动"

echo "修复完成！"
echo "请访问您的网站检查客户端管理页面"
'''
    
    with open('fix_server.sh', 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    # 创建Windows版本
    fix_script_bat = '''@echo off
REM 服务端客户端显示问题修复脚本 (Windows)

echo 开始修复服务端客户端显示问题...

REM 1. 停止现有服务
echo 1. 停止现有服务...
taskkill /f /im python.exe 2>nul

REM 2. 更新代码
echo 2. 更新代码...
git pull origin main

REM 3. 重建前端
if exist "app\\frontend" (
    echo 3. 重建前端...
    cd app\\frontend
    call npm ci
    call npm run build
    cd ..\..
) else (
    echo 3. 跳过前端构建 ^(目录不存在^)
)

REM 4. 初始化数据库
echo 4. 初始化数据库...
cd app\\backend
python -c "import asyncio; import sys; sys.path.append('.'); from database import init_database; from enhanced_bot import EnhancedTelegramBot; asyncio.run(init_database()); print('数据库初始化完成')"

REM 5. 启动服务
echo 5. 启动服务...
start /b python web_enhanced_clean.py > ..\\..\\logs\\web.log 2>&1
echo Web服务已启动

echo 修复完成！
echo 请访问您的网站检查客户端管理页面
pause
'''
    
    with open('fix_server.bat', 'w', encoding='utf-8') as f:
        f.write(fix_script_bat)
    
    os.chmod('fix_server.sh', 0o755)  # 给shell脚本执行权限

async def main():
    """主诊断流程"""
    print("🔍 开始服务端客户端显示问题诊断...")
    print("=" * 50)
    
    # 1. 检查GitHub部署状态
    github_ok = await check_github_deployment()
    
    # 2. 检查数据库和API
    db_ok, api_response = await check_database_and_api()
    
    # 3. 检查前端逻辑
    frontend_ok = await check_frontend_api_call()
    
    # 4. 生成诊断报告
    print("\n" + "=" * 50)
    print("🎯 诊断结果汇总")
    print("=" * 50)
    print(f"GitHub部署状态: {'✅ 正常' if github_ok else '❌ 异常'}")
    print(f"数据库/API状态: {'✅ 正常' if db_ok else '❌ 异常'}")
    print(f"前端逻辑状态: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    
    # 无论检查结果如何，都生成修复脚本供用户使用
    create_server_fix_script()
    print("✅ 修复脚本已生成 (fix_server.sh / fix_server.bat)")
    
    if github_ok and db_ok and frontend_ok:
        print("\n🎉 所有检查都通过！")
        print("问题可能是:")
        print("1. 浏览器缓存 - 强制刷新页面 (Ctrl+F5)")
        print("2. 服务重启后数据未加载 - 重启Web服务")
        print("3. 前端构建版本不匹配 - 重新构建前端")
        
        if api_response:
            print(f"\n📊 当前API应返回 {len(api_response)} 个客户端:")
            for client_id, info in api_response.items():
                print(f"  - {client_id}: auto_start={info['auto_start']}")
                
        print("\n🛠️ 如果问题仍然存在，可以运行修复脚本:")
        print("  Linux/Mac: chmod +x fix_server.sh && ./fix_server.sh")
        print("  Windows: fix_server.bat")
    else:
        print("\n🔧 发现问题，已生成修复脚本:")
        print("  - fix_server.sh (Linux/Mac)")  
        print("  - fix_server.bat (Windows)")
        print("\n运行修复脚本:")
        print("  Linux/Mac: chmod +x fix_server.sh && ./fix_server.sh")
        print("  Windows: fix_server.bat")
        
        create_server_fix_script()
        print("✅ 修复脚本已生成")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n诊断被用户中断")
    except Exception as e:
        print(f"\n诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
