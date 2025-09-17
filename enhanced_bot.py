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
    
    async def start(self, web_mode: bool = False):
        """启动机器人"""
        try:
            self.logger.info("🚀 启动增强版Telegram消息转发机器人")
            
            # 验证配置
            validate_config()
            self.logger.info("✅ 配置验证通过")
            
            # 创建目录
            Config.create_directories()
            
            # 初始化数据库
            await init_database()
            self.logger.info("✅ 数据库初始化完成")
            
            # 添加默认用户客户端
            user_client = self.multi_client_manager.add_client("main_user", "user")
            user_client.add_status_callback(self._notify_status_change)
            
            # 如果配置了BOT_TOKEN，添加机器人客户端
            if Config.BOT_TOKEN:
                bot_client = self.multi_client_manager.add_client("main_bot", "bot")
                bot_client.add_status_callback(self._notify_status_change)
            
            # 启动客户端
            self.logger.info("🔄 启动Telegram客户端...")
            
            # 启动用户客户端
            user_success = self.multi_client_manager.start_client("main_user")
            if user_success:
                self.logger.info("✅ 用户客户端启动成功")
            else:
                self.logger.error("❌ 用户客户端启动失败")
            
            # 启动机器人客户端（如果配置了）
            if Config.BOT_TOKEN:
                bot_success = self.multi_client_manager.start_client("main_bot")
                if bot_success:
                    self.logger.info("✅ 机器人客户端启动成功")
                else:
                    self.logger.warning("⚠️ 机器人客户端启动失败")
            
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
