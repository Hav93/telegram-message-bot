#!/usr/bin/env python3
"""
修复数据库中的admin_user_id类型问题
"""

import asyncio
import sys
import os
sys.path.append('app/backend')

async def fix_admin_user_id():
    """修复admin_user_id字段的类型问题"""
    print("开始修复数据库中的admin_user_id类型问题...")
    
    try:
        from models import TelegramClient
        from database import db_manager, init_database
        from sqlalchemy import select, text
        from config import Config
        
        # 初始化数据库
        await init_database()
        print("✅ 数据库初始化完成")
        
        async with db_manager.async_session() as session:
            # 1. 查找有问题的记录
            result = await session.execute(select(TelegramClient))
            clients = result.scalars().all()
            
            print(f"检查 {len(clients)} 个客户端记录...")
            
            fixed_count = 0
            for client in clients:
                print(f"检查客户端: {client.client_id}")
                
                # 检查admin_user_id字段
                if client.client_id == 'main_bot':
                    # 重新设置正确的admin_user_id
                    admin_user_id = None
                    if hasattr(Config, 'ADMIN_USER_IDS') and Config.ADMIN_USER_IDS:
                        if isinstance(Config.ADMIN_USER_IDS, list):
                            admin_user_id = ','.join(str(uid) for uid in Config.ADMIN_USER_IDS)
                        else:
                            admin_user_id = str(Config.ADMIN_USER_IDS)
                    
                    if admin_user_id != client.admin_user_id:
                        print(f"  修复admin_user_id: {client.admin_user_id} -> {admin_user_id}")
                        client.admin_user_id = admin_user_id
                        fixed_count += 1
            
            if fixed_count > 0:
                await session.commit()
                print(f"✅ 修复了 {fixed_count} 个记录")
            else:
                print("✅ 没有需要修复的记录")
        
        # 2. 验证修复结果
        print("\n验证修复结果:")
        async with db_manager.async_session() as session:
            result = await session.execute(select(TelegramClient))
            clients = result.scalars().all()
            
            for client in clients:
                print(f"  - {client.client_id} ({client.client_type}) admin_user_id={client.admin_user_id}")
        
        print("\n✅ 数据库修复完成！")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_admin_user_id())
