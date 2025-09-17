#!/usr/bin/env python3
"""
聊天助手工具 - 用于获取私密群组信息和管理转发规则
"""
import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User, Dialog
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from config import Config
from proxy_utils import get_proxy_manager

class ChatHelper:
    """聊天助手类"""
    
    def __init__(self):
        self.client = None
        self.proxy_manager = get_proxy_manager()
    
    async def init_client(self):
        """初始化Telegram客户端"""
        try:
            # 获取代理配置
            proxy_config = self.proxy_manager.get_telethon_proxy()
            
            # 创建客户端
            if proxy_config:
                print("🌐 使用代理连接...")
                self.client = TelegramClient(
                    'data/helper_session',
                    Config.API_ID,
                    Config.API_HASH,
                    proxy=proxy_config
                )
            else:
                print("🔗 直连模式...")
                self.client = TelegramClient(
                    'data/helper_session',
                    Config.API_ID,
                    Config.API_HASH
                )
            
            await self.client.start(phone=Config.PHONE_NUMBER)
            print("✅ 客户端初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 客户端初始化失败: {e}")
            return False
    
    async def get_all_chats(self, include_private=True, include_groups=True, include_channels=True):
        """获取所有聊天列表"""
        try:
            print("📋 获取聊天列表...")
            
            # 获取所有对话
            dialogs = await self.client.get_dialogs()
            
            chats = []
            for dialog in dialogs:
                entity = dialog.entity
                
                # 分类聊天类型
                chat_type = "未知"
                if isinstance(entity, User):
                    if not include_private:
                        continue
                    chat_type = "私聊" if not entity.bot else "机器人"
                elif isinstance(entity, Chat):
                    if not include_groups:
                        continue
                    chat_type = "群组"
                elif isinstance(entity, Channel):
                    if entity.megagroup:
                        if not include_groups:
                            continue
                        chat_type = "超级群组"
                    else:
                        if not include_channels:
                            continue
                        chat_type = "频道"
                
                # 获取聊天信息
                chat_info = {
                    'id': entity.id,
                    'title': getattr(entity, 'title', getattr(entity, 'first_name', '未命名')),
                    'type': chat_type,
                    'username': getattr(entity, 'username', None),
                    'participants_count': getattr(entity, 'participants_count', 0),
                    'is_private': not hasattr(entity, 'username') or entity.username is None,
                    'last_message_date': dialog.date,
                    'unread_count': dialog.unread_count
                }
                
                chats.append(chat_info)
            
            # 按最后消息时间排序
            chats.sort(key=lambda x: x['last_message_date'], reverse=True)
            
            print(f"✅ 获取到 {len(chats)} 个聊天")
            return chats
            
        except Exception as e:
            print(f"❌ 获取聊天列表失败: {e}")
            return []
    
    async def search_chats(self, keyword: str):
        """搜索聊天"""
        try:
            print(f"🔍 搜索包含 '{keyword}' 的聊天...")
            
            all_chats = await self.get_all_chats()
            
            # 搜索匹配的聊天
            matched_chats = []
            for chat in all_chats:
                if (keyword.lower() in chat['title'].lower() or 
                    (chat['username'] and keyword.lower() in chat['username'].lower())):
                    matched_chats.append(chat)
            
            print(f"✅ 找到 {len(matched_chats)} 个匹配的聊天")
            return matched_chats
            
        except Exception as e:
            print(f"❌ 搜索聊天失败: {e}")
            return []
    
    async def get_chat_info(self, chat_identifier: str):
        """获取特定聊天的详细信息"""
        try:
            print(f"📱 获取聊天信息: {chat_identifier}")
            
            # 尝试获取实体
            entity = await self.client.get_entity(chat_identifier)
            
            chat_info = {
                'id': entity.id,
                'title': getattr(entity, 'title', getattr(entity, 'first_name', '未命名')),
                'username': getattr(entity, 'username', None),
                'type': self._get_entity_type(entity),
                'participants_count': getattr(entity, 'participants_count', 0),
                'description': getattr(entity, 'about', ''),
                'is_verified': getattr(entity, 'verified', False),
                'is_scam': getattr(entity, 'scam', False),
                'is_fake': getattr(entity, 'fake', False),
                'restriction_reason': getattr(entity, 'restriction_reason', []),
                'access_hash': getattr(entity, 'access_hash', None)
            }
            
            print("✅ 聊天信息获取成功")
            return chat_info
            
        except Exception as e:
            print(f"❌ 获取聊天信息失败: {e}")
            return None
    
    def _get_entity_type(self, entity):
        """获取实体类型"""
        if isinstance(entity, User):
            return "机器人" if entity.bot else "用户"
        elif isinstance(entity, Chat):
            return "群组"
        elif isinstance(entity, Channel):
            return "超级群组" if entity.megagroup else "频道"
        else:
            return "未知"
    
    async def display_chats(self, chats: List[Dict], show_details=False):
        """显示聊天列表"""
        if not chats:
            print("📝 没有找到聊天")
            return
        
        print("\n" + "="*80)
        print(f"📋 聊天列表 (共 {len(chats)} 个)")
        print("="*80)
        
        for i, chat in enumerate(chats, 1):
            # 基本信息
            title = chat['title'][:40] + "..." if len(chat['title']) > 40 else chat['title']
            chat_id = chat['id']
            chat_type = chat['type']
            
            # 格式化ID（负数用于群组/频道）
            formatted_id = str(chat_id) if chat_id > 0 else str(chat_id)
            
            print(f"\n{i:2d}. {title}")
            print(f"    ID: {formatted_id}")
            print(f"    类型: {chat_type}")
            
            if chat.get('username'):
                print(f"    用户名: @{chat['username']}")
            else:
                print(f"    私密聊天: 是")
            
            if show_details:
                if chat.get('participants_count', 0) > 0:
                    print(f"    成员数: {chat['participants_count']}")
                
                if chat.get('unread_count', 0) > 0:
                    print(f"    未读消息: {chat['unread_count']}")
                
                last_msg_time = chat.get('last_message_date')
                if last_msg_time:
                    print(f"    最后消息: {last_msg_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*80)
    
    async def get_recent_messages(self, chat_identifier: str, limit: int = 10):
        """获取最近的消息"""
        try:
            print(f"📨 获取最近 {limit} 条消息...")
            
            entity = await self.client.get_entity(chat_identifier)
            messages = await self.client.get_messages(entity, limit=limit)
            
            print(f"\n📨 {entity.title or entity.first_name} 的最近消息:")
            print("-" * 60)
            
            for i, msg in enumerate(messages, 1):
                if msg.text:
                    text = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                    sender = "未知"
                    if msg.sender:
                        sender = getattr(msg.sender, 'first_name', '') or getattr(msg.sender, 'title', 'Unknown')
                    
                    print(f"{i:2d}. [{msg.date.strftime('%H:%M:%S')}] {sender}: {text}")
                else:
                    print(f"{i:2d}. [{msg.date.strftime('%H:%M:%S')}] [媒体消息]")
            
            print("-" * 60)
            return messages
            
        except Exception as e:
            print(f"❌ 获取消息失败: {e}")
            return []
    
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.disconnect()
            print("🔌 客户端已断开连接")

async def main():
    """主函数"""
    print("🛠️ Telegram 聊天助手工具")
    print("=" * 50)
    
    helper = ChatHelper()
    
    # 初始化客户端
    if not await helper.init_client():
        return 1
    
    try:
        while True:
            print("\n📋 可用操作:")
            print("1. 显示所有聊天")
            print("2. 显示群组和频道")
            print("3. 搜索聊天")
            print("4. 获取聊天详细信息")
            print("5. 查看最近消息")
            print("0. 退出")
            
            choice = input("\n请选择操作 (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                print("\n🔍 获取所有聊天...")
                chats = await helper.get_all_chats()
                await helper.display_chats(chats, show_details=True)
                
            elif choice == "2":
                print("\n🔍 获取群组和频道...")
                chats = await helper.get_all_chats(
                    include_private=False,
                    include_groups=True,
                    include_channels=True
                )
                await helper.display_chats(chats, show_details=True)
                
            elif choice == "3":
                keyword = input("\n🔍 请输入搜索关键词: ").strip()
                if keyword:
                    chats = await helper.search_chats(keyword)
                    await helper.display_chats(chats, show_details=True)
                
            elif choice == "4":
                chat_id = input("\n📱 请输入聊天ID或用户名: ").strip()
                if chat_id:
                    chat_info = await helper.get_chat_info(chat_id)
                    if chat_info:
                        print(f"\n📋 聊天详细信息:")
                        for key, value in chat_info.items():
                            if value:
                                print(f"  {key}: {value}")
                
            elif choice == "5":
                chat_id = input("\n📨 请输入聊天ID或用户名: ").strip()
                if chat_id:
                    try:
                        limit = int(input("请输入消息数量 (默认10): ").strip() or "10")
                        await helper.get_recent_messages(chat_id, limit)
                    except ValueError:
                        print("❌ 请输入有效的数字")
            
            else:
                print("❌ 无效的选择")
    
    except KeyboardInterrupt:
        print("\n⏹️ 操作被用户中断")
    
    finally:
        await helper.close()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
