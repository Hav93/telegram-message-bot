#!/usr/bin/env python3
"""
重置数据库并重新创建客户端记录
"""

import asyncio
import sys
import os
sys.path.append('app/backend')

async def reset_client_records():
    """重置客户端记录"""
    print("开始重置客户端记录...")
    
    try:
        from models import TelegramClient
        from database import db_manager, init_database
        from sqlalchemy import select, delete
        from config import Config
        
        # 初始化数据库
        await init_database()
        print("✅ 数据库初始化完成")
        
        async with db_manager.async_session() as session:
            # 1. 删除现有的客户端记录
            result = await session.execute(delete(TelegramClient))
            print(f"删除了 {result.rowcount} 个现有记录")
            
            # 2. 重新创建main_user记录
            main_user = TelegramClient(
                client_id='main_user',
                client_type='user',
                api_id=str(Config.API_ID) if hasattr(Config, 'API_ID') and Config.API_ID else None,
                api_hash=Config.API_HASH if hasattr(Config, 'API_HASH') and Config.API_HASH else None,
                phone=Config.PHONE_NUMBER if hasattr(Config, 'PHONE_NUMBER') and Config.PHONE_NUMBER else None,
                is_active=True,
                auto_start=False
            )
            session.add(main_user)
            print("✅ 创建main_user记录")
            
            # 3. 重新创建main_bot记录
            admin_user_id = None
            if hasattr(Config, 'ADMIN_USER_IDS') and Config.ADMIN_USER_IDS:
                if isinstance(Config.ADMIN_USER_IDS, list):
                    admin_user_id = ','.join(str(uid) for uid in Config.ADMIN_USER_IDS)
                else:
                    admin_user_id = str(Config.ADMIN_USER_IDS)
            
            main_bot = TelegramClient(
                client_id='main_bot',
                client_type='bot',
                bot_token=Config.BOT_TOKEN if hasattr(Config, 'BOT_TOKEN') and Config.BOT_TOKEN else None,
                admin_user_id=admin_user_id,
                is_active=True,
                auto_start=False
            )
            session.add(main_bot)
            print("✅ 创建main_bot记录")
            
            await session.commit()
            print("✅ 记录已提交到数据库")
        
        # 4. 验证结果
        print("\n验证创建结果:")
        async with db_manager.async_session() as session:
            result = await session.execute(select(TelegramClient))
            clients = result.scalars().all()
            
            for client in clients:
                print(f"  - {client.client_id} ({client.client_type})")
                print(f"    auto_start: {client.auto_start}")
                print(f"    admin_user_id: {client.admin_user_id}")
                if client.client_type == 'user':
                    print(f"    api_id: {client.api_id}")
                    print(f"    phone: {client.phone}")
                elif client.client_type == 'bot':
                    print(f"    bot_token: {'SET' if client.bot_token else 'None'}")
        
        print("\n✅ 客户端记录重置完成！")
        
    except Exception as e:
        print(f"❌ 重置失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reset_client_records())
