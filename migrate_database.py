#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加缺失的字段
"""

import asyncio
import sys
import os
sys.path.append('app/backend')

async def migrate_database():
    """执行数据库迁移"""
    print("开始数据库迁移...")
    
    try:
        from database import db_manager, init_database
        from sqlalchemy import text
        
        # 初始化数据库连接
        await init_database()
        print("✅ 数据库连接已建立")
        
        async with db_manager.async_session() as session:
            # 检查replace_rules表是否存在is_regex字段
            try:
                result = await session.execute(text("PRAGMA table_info(replace_rules)"))
                columns = [row[1] for row in result.fetchall()]
                print(f"replace_rules表当前字段: {columns}")
                
                if 'is_regex' not in columns:
                    print("🔧 添加is_regex字段到replace_rules表...")
                    await session.execute(text("ALTER TABLE replace_rules ADD COLUMN is_regex BOOLEAN DEFAULT 1"))
                    await session.commit()
                    print("✅ is_regex字段已添加")
                else:
                    print("✅ is_regex字段已存在")
                    
            except Exception as e:
                print(f"❌ 迁移replace_rules表失败: {e}")
                
            # 验证迁移结果
            try:
                result = await session.execute(text("PRAGMA table_info(replace_rules)"))
                columns = [row[1] for row in result.fetchall()]
                print(f"迁移后replace_rules表字段: {columns}")
                
                if 'is_regex' in columns:
                    print("✅ 数据库迁移成功完成")
                    return True
                else:
                    print("❌ 数据库迁移失败")
                    return False
                    
            except Exception as e:
                print(f"❌ 验证迁移结果失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_after_migration():
    """迁移后测试"""
    print("\n=== 迁移后测试 ===")
    
    try:
        from services import ForwardRuleService
        
        # 测试规则查询
        rules = await ForwardRuleService.get_all_rules()
        print(f"✅ 成功获取 {len(rules)} 个规则")
        
        for rule in rules:
            print(f"  - 规则 {rule.id}: {rule.name}")
            
        return True
        
    except Exception as e:
        print(f"❌ 迁移后测试失败: {e}")
        return False

if __name__ == "__main__":
    async def main():
        # 执行迁移
        migration_success = await migrate_database()
        
        if migration_success:
            # 测试迁移结果
            test_success = await test_after_migration()
            
            if test_success:
                print("\n🎉 数据库迁移完成，转发规则API已修复！")
                print("现在可以重启Web服务，前端应该能正常显示规则了。")
            else:
                print("\n⚠️ 迁移完成但测试失败，可能还有其他问题")
        else:
            print("\n❌ 数据库迁移失败")
    
    asyncio.run(main())
