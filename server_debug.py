#!/usr/bin/env python3
"""
服务端客户端显示问题诊断脚本
"""

import asyncio
import sys
import os
import sqlite3
import json
from pathlib import Path

# 添加 app/backend 到路径
sys.path.append('app/backend')

async def check_database_state():
    """检查数据库状态"""
    print("=== 数据库状态检查 ===")
    
    db_path = Path("data/bot.db")
    if not db_path.exists():
        print("ERROR: 数据库文件不存在!")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查telegram_clients表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telegram_clients'")
        if not cursor.fetchone():
            print("ERROR: telegram_clients表不存在!")
            return False
        
        # 查询客户端记录
        cursor.execute("SELECT client_id, client_type, auto_start, is_active FROM telegram_clients")
        clients = cursor.fetchall()
        
        print(f"数据库中的客户端记录数量: {len(clients)}")
        for client in clients:
            print(f"  - {client[0]} ({client[1]}) auto_start={client[2]} active={client[3]}")
        
        conn.close()
        return len(clients) > 0
        
    except Exception as e:
        print(f"ERROR: 数据库检查失败: {e}")
        return False

async def check_api_logic():
    """检查API逻辑"""
    print("\n=== API逻辑检查 ===")
    
    try:
        from models import TelegramClient
        from database import get_db
        from sqlalchemy import select
        from enhanced_bot import EnhancedTelegramBot
        
        # 1. 检查数据库查询
        clients_from_db = []
        async for db in get_db():
            result = await db.execute(select(TelegramClient))
            clients_from_db = result.scalars().all()
            break
        
        print(f"通过SQLAlchemy查询到的客户端: {len(clients_from_db)}")
        for client in clients_from_db:
            print(f"  - {client.client_id} auto_start={client.auto_start}")
        
        # 2. 检查enhanced_bot实例
        enhanced_bot = EnhancedTelegramBot()
        runtime_clients = {}
        if hasattr(enhanced_bot, 'get_client_status'):
            runtime_clients = enhanced_bot.get_client_status()
        
        print(f"运行时客户端数量: {len(runtime_clients)}")
        
        # 3. 模拟API响应组装
        clients_status = {}
        clients_status.update(runtime_clients)
        
        for db_client in clients_from_db:
            if db_client.client_id in clients_status:
                clients_status[db_client.client_id]['auto_start'] = db_client.auto_start
            else:
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
        
        print(f"最终API响应中的客户端数量: {len(clients_status)}")
        for client_id, info in clients_status.items():
            print(f"  - {client_id}: running={info.get('running')} auto_start={info.get('auto_start')}")
        
        return len(clients_status) > 0
        
    except Exception as e:
        print(f"ERROR: API逻辑检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_config_completeness():
    """检查配置完整性"""
    print("\n=== 配置完整性检查 ===")
    
    try:
        from config import Config
        
        config_items = [
            ('API_ID', getattr(Config, 'API_ID', None)),
            ('API_HASH', 'SET' if getattr(Config, 'API_HASH', None) else None),
            ('PHONE_NUMBER', getattr(Config, 'PHONE_NUMBER', None)),
            ('BOT_TOKEN', 'SET' if getattr(Config, 'BOT_TOKEN', None) else None),
        ]
        
        missing_config = []
        for key, value in config_items:
            if value:
                print(f"  ✓ {key}: {value}")
            else:
                print(f"  ✗ {key}: 未设置")
                missing_config.append(key)
        
        if missing_config:
            print(f"WARNING: 缺少配置项: {missing_config}")
        
        return len(missing_config) == 0
        
    except Exception as e:
        print(f"ERROR: 配置检查失败: {e}")
        return False

def create_fix_script():
    """创建修复脚本"""
    script_content = '''#!/usr/bin/env python3
"""
客户端显示修复脚本
"""

import asyncio
import sys
import os
sys.path.append('app/backend')

async def fix_clients():
    """修复客户端显示问题"""
    from models import TelegramClient
    from database import get_db, init_database
    from sqlalchemy import select
    from config import Config
    
    print("开始修复客户端显示问题...")
    
    # 1. 确保数据库初始化
    await init_database()
    print("✓ 数据库已初始化")
    
    # 2. 检查和创建客户端记录
    async for db in get_db():
        # 检查main_user
        result = await db.execute(select(TelegramClient).filter(TelegramClient.client_id == 'main_user'))
        if not result.scalar_one_or_none():
            main_user = TelegramClient(
                client_id='main_user',
                client_type='user',
                api_id=str(Config.API_ID) if hasattr(Config, 'API_ID') and Config.API_ID else None,
                api_hash=Config.API_HASH if hasattr(Config, 'API_HASH') and Config.API_HASH else None,
                phone=Config.PHONE_NUMBER if hasattr(Config, 'PHONE_NUMBER') and Config.PHONE_NUMBER else None,
                auto_start=False,
                is_active=True
            )
            db.add(main_user)
            print("✓ 创建main_user记录")
        
        # 检查main_bot
        result = await db.execute(select(TelegramClient).filter(TelegramClient.client_id == 'main_bot'))
        if not result.scalar_one_or_none():
            main_bot = TelegramClient(
                client_id='main_bot',
                client_type='bot',
                bot_token=Config.BOT_TOKEN if hasattr(Config, 'BOT_TOKEN') and Config.BOT_TOKEN else None,
                auto_start=False,
                is_active=True
            )
            db.add(main_bot)
            print("✓ 创建main_bot记录")
        
        await db.commit()
        break
    
    print("✓ 客户端记录修复完成")
    print("请重启Web服务检查客户端是否显示")

if __name__ == "__main__":
    asyncio.run(fix_clients())
'''
    
    with open('fix_clients.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("\n=== 修复建议 ===")
    print("1. 运行修复脚本: python fix_clients.py")
    print("2. 重启Web服务")
    print("3. 检查前端客户端管理页面")

async def main():
    """主函数"""
    print("开始服务端客户端显示问题诊断...\n")
    
    # 执行各项检查
    db_ok = await check_database_state()
    api_ok = await check_api_logic()
    config_ok = await check_config_completeness()
    
    print(f"\n=== 诊断结果 ===")
    print(f"数据库状态: {'OK' if db_ok else 'ERROR'}")
    print(f"API逻辑: {'OK' if api_ok else 'ERROR'}")
    print(f"配置完整性: {'OK' if config_ok else 'WARNING'}")
    
    if not db_ok or not api_ok:
        create_fix_script()
        print("\n=== 自动修复 ===")
        print("发现问题，已生成修复脚本 fix_clients.py")
        print("请运行: python fix_clients.py")
    else:
        print("\n=== 结论 ===")
        print("后端逻辑看起来正常，问题可能在于:")
        print("1. 前端缓存问题 - 尝试强制刷新浏览器")
        print("2. API调用失败 - 检查浏览器开发者工具网络标签")
        print("3. 前端过滤逻辑 - 检查是否有条件过滤了auto_start=false的客户端")

if __name__ == "__main__":
    asyncio.run(main())
