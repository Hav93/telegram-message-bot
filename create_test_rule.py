#!/usr/bin/env python3
"""
创建测试规则验证功能
"""

import asyncio
import sys
import os
sys.path.append('app/backend')

async def create_test_rule():
    """创建测试规则"""
    print("创建测试规则...")
    
    try:
        from services import ForwardRuleService
        from database import init_database
        
        await init_database()
        print("✅ 数据库初始化完成")
        
        # 创建测试规则
        test_rule = await ForwardRuleService.create_rule(
            name="测试转发规则",
            source_chat_id="123456789",
            source_chat_name="测试源聊天",
            target_chat_id="987654321", 
            target_chat_name="测试目标聊天",
            is_active=True,
            enable_keyword_filter=False,
            enable_regex_replace=False,
            client_id="main_user",
            client_type="user"
        )
        
        print(f"✅ 测试规则创建成功: ID={test_rule.id}, 名称='{test_rule.name}'")
        
        # 验证规则列表
        rules = await ForwardRuleService.get_all_rules()
        print(f"✅ 现在数据库中有 {len(rules)} 个规则")
        
        for rule in rules:
            print(f"  - 规则 {rule.id}: {rule.name}")
            print(f"    源聊天: {rule.source_chat_id} ({rule.source_chat_name})")
            print(f"    目标聊天: {rule.target_chat_id} ({rule.target_chat_name})")
            print(f"    状态: {'启用' if rule.is_active else '禁用'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建测试规则失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_test_rule())
    
    if success:
        print("\n🎉 测试规则创建成功！")
        print("现在前端应该能显示规则了。")
        print("如果还是不显示，请检查:")
        print("1. 重启Web服务")
        print("2. 清除浏览器缓存")
        print("3. 检查浏览器控制台错误")
    else:
        print("\n❌ 测试规则创建失败")
