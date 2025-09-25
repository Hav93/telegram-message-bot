#!/usr/bin/env python3
"""
增强版Telegram消息转发机器人 - 修复实时监听问题
"""
import asyncio
import logging
import signal
import sys
from typing import Dict, Any
from pathlib import Path

from telegram_client_manager import MultiClientManager, multi_client_manager
from config import Config, validate_config
from database import init_database
from utils import setup_logging

class EnhancedTelegramBot:
    """
    增强版Telegram机器人
    
    核心修复:
    1. 独立事件循环: 每个Telegram客户端运行在独立的线程和事件循环中
    2. 直接使用run_until_disconnected: 不包装在任务中，让其自然管理事件循环
    3. 装饰器事件处理: 使用@client.on(events.NewMessage)替代add_event_handler
    4. 异步任务隔离: 消息转发处理在独立任务中进行，避免阻塞事件监听
    """
    
    def __init__(self):
        self.logger = setup_logging()
        self.multi_client_manager = multi_client_manager
        self.running = False
        
        # 状态回调
        self.status_callbacks = []
        
    def add_status_callback(self, callback):
        """添加状态变化回调"""
        self.status_callbacks.append(callback)
    
    def _notify_status_change(self, client_id: str, status: str, data: Dict[str, Any]):
        """处理客户端状态变化"""
        self.logger.info(f"客户端 {client_id} 状态变化: {status}")
        
        # 通知所有回调
        for callback in self.status_callbacks:
            try:
                callback(client_id, status, data)
            except Exception as e:
                self.logger.error(f"状态回调执行失败: {e}")
    
    async def _auto_start_clients(self):
        """自动启动设置了auto_start=True的客户端"""
        try:
            from models import TelegramClient
            from database import get_db
            from sqlalchemy import select
            
            async for db in get_db():
                # 查询所有启用自动启动的客户端
                result = await db.execute(
                    select(TelegramClient).where(
                        TelegramClient.auto_start == True,
                        TelegramClient.is_active == True
                    )
                )
                auto_start_clients = result.scalars().all()
                
                if auto_start_clients:
                    self.logger.info(f"🔄 发现 {len(auto_start_clients)} 个需要自动启动的客户端")
                    
                    for db_client in auto_start_clients:
                        try:
                            # 准备配置数据
                            config_data = {}
                            if db_client.client_type == 'bot':
                                config_data = {
                                    'bot_token': db_client.bot_token,
                                    'admin_user_id': db_client.admin_user_id
                                }
                            elif db_client.client_type == 'user':
                                config_data = {
                                    'api_id': db_client.api_id,
                                    'api_hash': db_client.api_hash,
                                    'phone': db_client.phone
                                }
                            
                            # 添加到运行时管理器
                            client = self.multi_client_manager.add_client_with_config(
                                db_client.client_id,
                                db_client.client_type,
                                config_data=config_data
                            )
                            client.add_status_callback(self._notify_status_change)
                            
                            # 启动客户端
                            client.start()
                            self.logger.info(f"✅ 自动启动客户端: {db_client.client_id} ({db_client.client_type})")
                            
                        except Exception as client_error:
                            self.logger.error(f"❌ 自动启动客户端 {db_client.client_id} 失败: {client_error}")
                else:
                    self.logger.info("💡 没有设置自动启动的客户端")
                break
                
        except Exception as e:
            self.logger.error(f"❌ 自动启动客户端失败: {e}")
    
    async def _migrate_legacy_clients(self):
        """迁移传统客户端到数据库"""
        try:
            from models import TelegramClient
            from database import get_db
            from sqlalchemy import select
            from config import Config
            
            async for db in get_db():
                # 定义传统客户端 - 无论配置如何都创建基本记录
                legacy_clients = []
                
                # 主用户客户端 - 始终创建记录
                legacy_clients.append({
                    'client_id': 'main_user',
                    'client_type': 'user',
                    'api_id': str(Config.API_ID) if hasattr(Config, 'API_ID') and Config.API_ID else None,
                    'api_hash': Config.API_HASH if hasattr(Config, 'API_HASH') and Config.API_HASH else None,
                    'phone': Config.PHONE_NUMBER if hasattr(Config, 'PHONE_NUMBER') and Config.PHONE_NUMBER else None
                })
                
                # 主机器人客户端 - 始终创建记录
                admin_user_id = None
                if hasattr(Config, 'ADMIN_USER_IDS') and Config.ADMIN_USER_IDS:
                    # 将列表转换为逗号分隔的字符串
                    if isinstance(Config.ADMIN_USER_IDS, list):
                        admin_user_id = ','.join(str(uid) for uid in Config.ADMIN_USER_IDS)
                    else:
                        admin_user_id = str(Config.ADMIN_USER_IDS)
                
                legacy_clients.append({
                    'client_id': 'main_bot',
                    'client_type': 'bot',
                    'bot_token': Config.BOT_TOKEN if hasattr(Config, 'BOT_TOKEN') and Config.BOT_TOKEN else None,
                    'admin_user_id': admin_user_id
                })
                
                # 检查并迁移每个传统客户端
                for client_data in legacy_clients:
                    result = await db.execute(
                        select(TelegramClient).where(
                            TelegramClient.client_id == client_data['client_id']
                        )
                    )
                    existing_client = result.scalar_one_or_none()
                    
                    if not existing_client:
                        # 创建新的客户端记录
                        db_client = TelegramClient(
                            client_id=client_data['client_id'],
                            client_type=client_data['client_type'],
                            api_id=client_data.get('api_id'),
                            api_hash=client_data.get('api_hash'),
                            phone=client_data.get('phone'),
                            bot_token=client_data.get('bot_token'),
                            admin_user_id=client_data.get('admin_user_id'),
                            is_active=True,
                            auto_start=False  # 默认不自动启动
                        )
                        db.add(db_client)
                        self.logger.info(f"📥 迁移传统客户端到数据库: {client_data['client_id']} ({client_data['client_type']})")
                    else:
                        self.logger.info(f"✅ 传统客户端已存在: {client_data['client_id']}")
                
                await db.commit()
                self.logger.info("✅ 传统客户端迁移完成")
                break
                
        except Exception as e:
            self.logger.error(f"❌ 传统客户端迁移失败: {e}")
    
    async def start(self, web_mode: bool = False, skip_config_validation: bool = False):
        """启动机器人"""
        try:
            self.logger.info("🚀 启动增强版Telegram消息转发机器人")
            
            # 验证配置（Web模式下可以跳过）
            if not skip_config_validation:
                try:
                    validate_config()
                    self.logger.info("✅ 配置验证通过")
                except ValueError as config_error:
                    if web_mode:
                        self.logger.warning(f"⚠️ 配置未完整，将以Web-only模式启动: {config_error}")
                        self.logger.info("🌐 启动Web界面进行配置...")
                        return  # 跳过Telegram客户端启动，仅启动Web服务
                    else:
                        raise  # 非Web模式时仍然抛出配置错误
            else:
                self.logger.info("⏭️ 跳过配置验证（Web-only模式）")
            
            # 创建目录
            Config.create_directories()
            
            # 初始化数据库
            await init_database()
            self.logger.info("✅ 数据库初始化完成")
            
            # 迁移传统客户端到数据库（如果不存在）
            await self._migrate_legacy_clients()
            
            # 自动启动设置了auto_start=True的客户端
            await self._auto_start_clients()
            
            # 客户端启动完全由自动启动逻辑控制
            # 不再无条件启动客户端，避免绕过auto_start设置
            self.logger.info("✅ 客户端启动已由自动启动逻辑控制")
            
            self.running = True
            
            if web_mode:
                self.logger.info("🌐 Web模式启动完成，客户端将在后台运行")
                return True
            else:
                # 等待信号
                await self._wait_for_signal()
                
        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            raise
    
    async def stop(self):
        """停止机器人"""
        self.logger.info("🛑 停止机器人...")
        
        self.running = False
        self.multi_client_manager.stop_all()
        
        self.logger.info("✅ 机器人已停止")
    
    async def _wait_for_signal(self):
        """等待停止信号"""
        def signal_handler(signum, frame):
            self.logger.info(f"收到信号 {signum}，准备停止...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()
    
    def get_client_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有客户端状态"""
        return self.multi_client_manager.get_all_status()
    
    def refresh_monitored_chats(self):
        """刷新所有客户端的监听聊天列表"""
        for client_id, client in self.multi_client_manager.clients.items():
            try:
                asyncio.create_task(client.refresh_monitored_chats())
            except Exception as e:
                self.logger.error(f"刷新客户端 {client_id} 监听聊天失败: {e}")
    
    def get_login_status(self) -> Dict[str, Any]:
        """获取登录状态（兼容原有接口）"""
        user_client = self.multi_client_manager.get_client("main_user")
        if not user_client:
            return {
                "success": False,
                "logged_in": False,
                "message": "用户客户端不存在"
            }
        
        status = user_client.get_status()
        return {
            "success": status["running"],
            "logged_in": status["connected"],
            "message": "已连接" if status["connected"] else "未连接",
            "user": status["user_info"]
        }
    
    def cache_chat_list_for_web_sync(self) -> Dict[str, Any]:
        """缓存聊天列表（兼容原有接口）"""
        try:
            # 这里可以实现聊天列表缓存逻辑
            return {
                "success": True,
                "message": "聊天列表缓存成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"缓存失败: {str(e)}"
            }
    
    def get_chat_list_sync(self):
        """同步获取聊天列表（兼容原有接口）"""
        # 这里可以实现获取聊天列表的逻辑
        return []
    
    async def forward_history_messages(self, rule_id: int, hours: int = 24):
        """转发历史消息（当规则从关闭状态激活时）"""
        try:
            from services import ForwardRuleService
            
            # 获取规则信息
            rule = await ForwardRuleService.get_rule_by_id(rule_id)
            if not rule:
                self.logger.warning(f"规则 {rule_id} 不存在，跳过历史消息转发")
                return
            
            if not rule.is_active:
                self.logger.warning(f"规则 {rule_id} 未激活，跳过历史消息转发")
                return
            
            self.logger.info(f"规则 {rule_id} 激活，开始处理历史消息...")
            
            # 使用多客户端管理器的历史消息处理方法
            if hasattr(self.multi_client_manager, 'process_history_messages'):
                result = self.multi_client_manager.process_history_messages(rule)
                if result and result.get('success'):
                    # 显示详细的处理统计
                    total_fetched = result.get('total_fetched', 0)
                    forwarded = result.get('forwarded', 0)
                    skipped = result.get('skipped', 0) 
                    errors = result.get('errors', 0)
                    
                    self.logger.info(f"规则 {rule_id} 历史消息处理完成:")
                    self.logger.info(f"  📥 获取: {total_fetched} 条")
                    self.logger.info(f"  ✅ 转发: {forwarded} 条")
                    self.logger.info(f"  ⏭️ 跳过: {skipped} 条")
                    self.logger.info(f"  ❌ 错误: {errors} 条")
                else:
                    self.logger.warning(f"规则 {rule_id} 历史消息处理失败: {result.get('message', 'Unknown error') if result else 'No result'}")
            else:
                self.logger.warning(f"多客户端管理器不支持历史消息处理")
            
        except Exception as e:
            self.logger.error(f"转发历史消息失败: {e}")
            raise


async def main():
    """主函数"""
    bot = EnhancedTelegramBot()
    
    try:
        await bot.start(web_mode=False)
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        logging.error(f"程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/enhanced_bot.log', encoding='utf-8')
        ]
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)
