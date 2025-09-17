#!/usr/bin/env python3
"""
Telegram客户端管理器 - 解决事件循环冲突的核心模块
"""
import asyncio
import threading
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, ChatAdminRequiredError, UserPrivacyRestrictedError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from config import Config
from database import get_db
from models import ForwardRule, MessageLog
from filters import KeywordFilter, RegexReplacer
from proxy_utils import get_proxy_manager

logger = logging.getLogger(__name__)

class TelegramClientManager:
    """
    Telegram客户端管理器
    
    核心修复:
    1. 每个客户端运行在独立线程中
    2. 使用装饰器事件处理避免add_event_handler
    3. 直接使用run_until_disconnected，不包装在任务中
    4. 异步任务隔离，避免阻塞事件监听
    """
    
    def __init__(self, client_id: str, client_type: str = "user"):
        self.client_id = client_id
        self.client_type = client_type  # "user" or "bot"
        self.client: Optional[TelegramClient] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False
        self.connected = False
        self.user_info = None
        
        # 客户端配置
        # 机器人客户端配置
        self.bot_token: Optional[str] = None
        self.admin_user_id: Optional[str] = None
        
        # 用户客户端配置
        self.api_id: Optional[str] = None
        self.api_hash: Optional[str] = None
        self.phone: Optional[str] = None
        
        # 消息处理
        self.keyword_filter = KeywordFilter()
        self.regex_replacer = RegexReplacer()
        self.monitored_chats = set()
        
        # 状态回调
        self.status_callbacks: List[Callable] = []
        
        # 登录流程状态
        self.login_session = None
        self.login_state = "idle"  # idle, waiting_code, waiting_password, completed
        
        # 日志
        self.logger = logging.getLogger(f"TelegramClient-{client_id}")
    
    def add_status_callback(self, callback: Callable):
        """添加状态变化回调"""
        self.status_callbacks.append(callback)
    
    def _notify_status_change(self, status: str, data: Dict[str, Any] = None):
        """通知状态变化"""
        for callback in self.status_callbacks:
            try:
                callback(self.client_id, status, data or {})
            except Exception as e:
                self.logger.error(f"状态回调执行失败: {e}")
    
    def start(self) -> bool:
        """启动客户端（在独立线程中）"""
        if self.running:
            self.logger.warning("客户端已在运行中")
            return True
        
        try:
            self.thread = threading.Thread(
                target=self._run_client_thread,
                name=f"TelegramClient-{self.client_id}",
                daemon=True
            )
            self.thread.start()
            
            # 等待启动完成
            max_wait = 30  # 30秒超时
            start_time = time.time()
            while not self.running and (time.time() - start_time) < max_wait:
                time.sleep(0.1)
            
            if self.running:
                self.logger.info(f"✅ 客户端 {self.client_id} 启动成功")
                return True
            else:
                self.logger.error(f"❌ 客户端 {self.client_id} 启动超时")
                return False
                
        except Exception as e:
            self.logger.error(f"启动客户端失败: {e}")
            return False
    
    def stop(self):
        """停止客户端"""
        if not self.running:
            return
        
        self.running = False
        
        if self.loop and self.client:
            # 在客户端的事件循环中执行断开连接
            asyncio.run_coroutine_threadsafe(
                self.client.disconnect(), 
                self.loop
            )
        
        if self.thread:
            self.thread.join(timeout=10)
        
        self.logger.info(f"✅ 客户端 {self.client_id} 已停止")
    
    def _run_client_thread(self):
        """在独立线程中运行客户端"""
        try:
            # 创建独立的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 运行客户端
            self.loop.run_until_complete(self._run_client())
            
        except Exception as e:
            self.logger.error(f"客户端线程运行失败: {e}")
            self._notify_status_change("error", {"error": str(e)})
        finally:
            if self.loop:
                self.loop.close()
            self.running = False
            self.connected = False
    
    async def _run_client(self):
        """运行客户端主逻辑"""
        try:
            # 创建客户端
            await self._create_client()
            
            if not self.client:
                raise Exception("客户端创建失败")
            
            # 启动客户端
            if self.client_type == "bot":
                bot_token = self.bot_token or Config.BOT_TOKEN
                await self.client.start(bot_token=bot_token)
            else:
                phone = self.phone or Config.PHONE_NUMBER
                await self.client.start(phone=phone)
            
            # 获取用户信息
            self.user_info = await self.client.get_me()
            self.connected = True
            self.running = True
            
            self.logger.info(f"✅ {self.client_type} 客户端已连接: {getattr(self.user_info, 'username', '') or getattr(self.user_info, 'first_name', 'Unknown')}")
            self._notify_status_change("connected", {
                "user_info": {
                    "id": self.user_info.id,
                    "username": getattr(self.user_info, 'username', ''),
                    "first_name": getattr(self.user_info, 'first_name', ''),
                    "phone": getattr(self.user_info, 'phone', '')
                }
            })
            
            # 注册事件处理器（使用装饰器方式）
            self._register_event_handlers()
            
            # 更新监听聊天列表
            await self._update_monitored_chats()
            
            # 关键修复：直接使用run_until_disconnected，不包装在任务中
            self.logger.info(f"🎯 开始监听消息...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.logger.error(f"客户端运行失败: {e}")
            self._notify_status_change("error", {"error": str(e)})
            raise
        finally:
            self.running = False
            self.connected = False
            self._notify_status_change("disconnected", {})
    
    async def _create_client(self):
        """创建Telegram客户端"""
        try:
            # 获取代理配置
            proxy_manager = get_proxy_manager()
            proxy_config = proxy_manager.get_telethon_proxy()
            
            # 会话文件路径
            session_name = f"{Config.SESSIONS_DIR}/{self.client_type}_{self.client_id}"
            
            # 根据客户端类型使用不同的配置
            if self.client_type == "bot":
                # 机器人客户端使用bot_token
                bot_token = self.bot_token or Config.BOT_TOKEN
                if not bot_token:
                    raise ValueError(f"机器人客户端 {self.client_id} 缺少Bot Token")
                
                # 使用全局API配置创建机器人客户端
                self.client = TelegramClient(
                    session_name,
                    Config.API_ID,
                    Config.API_HASH,
                    proxy=proxy_config,
                    connection_retries=5,
                    retry_delay=2,
                    timeout=30,
                    auto_reconnect=True
                )
            else:
                # 用户客户端使用自定义API配置
                api_id = int(self.api_id) if self.api_id else Config.API_ID
                api_hash = self.api_hash or Config.API_HASH
                
                if not api_id or not api_hash:
                    raise ValueError(f"用户客户端 {self.client_id} 缺少API ID或API Hash")
                
                self.client = TelegramClient(
                    session_name,
                    api_id,
                    api_hash,
                    proxy=proxy_config,
                    connection_retries=5,
                    retry_delay=2,
                    timeout=30,
                    auto_reconnect=True
                )
            
            self.logger.info(f"📱 {self.client_type} 客户端已创建")
            
        except Exception as e:
            self.logger.error(f"创建客户端失败: {e}")
            raise
    
    def _register_event_handlers(self):
        """注册事件处理器（使用装饰器方式）"""
        if not self.client:
            return
        
        # 核心修复：使用装饰器事件处理替代add_event_handler
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            """处理新消息事件"""
            try:
                # 异步任务隔离：在独立任务中处理，避免阻塞事件监听
                asyncio.create_task(self._process_message(event))
            except Exception as e:
                self.logger.error(f"消息处理任务创建失败: {e}")
        
        @self.client.on(events.MessageEdited())
        async def handle_message_edited(event):
            """处理消息编辑事件"""
            try:
                asyncio.create_task(self._process_message(event, is_edited=True))
            except Exception as e:
                self.logger.error(f"消息编辑处理任务创建失败: {e}")
        
        self.logger.info("✅ 事件处理器已注册（装饰器方式）")
    
    async def _process_message(self, event, is_edited: bool = False):
        """处理消息（在独立任务中运行）"""
        try:
            message = event.message
            # 修复聊天ID转换问题 - 更准确的转换逻辑
            from telethon.tl.types import PeerChannel, PeerChat, PeerUser
            
            if isinstance(message.peer_id, PeerChannel):
                # 超级群组/频道：转换为 -100xxxxxxxxx 格式
                raw_chat_id = message.peer_id.channel_id
                chat_id = -1000000000000 - raw_chat_id
            elif isinstance(message.peer_id, PeerChat):
                # 普通群组：转换为负数
                raw_chat_id = message.peer_id.chat_id
                chat_id = -raw_chat_id
            else:
                # 私聊用户：保持正数
                raw_chat_id = message.peer_id.user_id
                chat_id = raw_chat_id
            
            self.logger.info(f"📨 收到消息: 原始ID={raw_chat_id}, 转换ID={chat_id}, 消息ID={message.id}")
            
            # 检查是否需要监听此聊天
            if chat_id not in self.monitored_chats:
                self.logger.info(f"🔍 聊天ID {chat_id} 不在监听列表中: {self.monitored_chats}")
                return
            
            self.logger.info(f"✅ 处理监听消息: 聊天ID={chat_id}, 消息ID={message.id}")
            
            # 获取适用的转发规则
            rules = await self._get_applicable_rules(chat_id)
            
            for rule in rules:
                try:
                    await self._process_rule(rule, message, event)
                except Exception as e:
                    self.logger.error(f"处理规则 {rule.id} 失败: {e}")
                    await self._log_message(rule.id, message, "failed", str(e))
                    
        except Exception as e:
            self.logger.error(f"消息处理失败: {e}")
    
    async def _get_applicable_rules(self, chat_id: int) -> List[ForwardRule]:
        """获取适用的转发规则"""
        try:
            async for db in get_db():
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload
                
                stmt = select(ForwardRule).options(
                    selectinload(ForwardRule.keywords),
                    selectinload(ForwardRule.replace_rules)
                ).where(
                    ForwardRule.source_chat_id == chat_id,
                    ForwardRule.is_active == True
                )
                
                result = await db.execute(stmt)
                rules = result.scalars().all()
                return list(rules)
                
        except Exception as e:
            self.logger.error(f"获取转发规则失败: {e}")
            return []
    
    async def _process_rule(self, rule: ForwardRule, message, event):
        """处理单个转发规则"""
        try:
            # 消息类型检查
            if not self._check_message_type(rule, message):
                return
            
            # 时间过滤检查
            if not self._check_time_filter(rule, message):
                return
            
            # 关键词过滤
            if rule.enable_keyword_filter and rule.keywords:
                if not self.keyword_filter.should_forward(message.text or "", rule.keywords):
                    return
            
            # 文本替换
            text_to_forward = message.text or ""
            if rule.enable_regex_replace and rule.replace_rules:
                text_to_forward = self.regex_replacer.apply_replacements(text_to_forward, rule.replace_rules)
            
            # 长度限制
            if rule.max_message_length and len(text_to_forward) > rule.max_message_length:
                text_to_forward = text_to_forward[:rule.max_message_length] + "..."
            
            # 转发延迟
            if rule.forward_delay > 0:
                await asyncio.sleep(rule.forward_delay)
            
            # 执行转发
            await self._forward_message(rule, message, text_to_forward)
            
            # 记录日志
            await self._log_message(rule.id, message, "success")
            
        except Exception as e:
            self.logger.error(f"规则处理失败: {e}")
            await self._log_message(rule.id, message, "failed", str(e))
    
    def _check_message_type(self, rule: ForwardRule, message) -> bool:
        """检查消息类型是否符合规则"""
        try:
            from telethon.tl.types import (
                MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage,
                MessageMediaGeo, MessageMediaVenue, MessageMediaContact,
                MessageMediaGame, MessageMediaInvoice, MessageMediaGeoLive,
                MessageMediaPoll, MessageMediaDice, MessageMediaStory
            )
            
            # 检查是否为纯文本消息（无媒体）
            if not message.media:
                # 纯文本消息检查
                if message.text and not getattr(rule, 'enable_text', True):
                    self.logger.debug(f"📝 文本消息被规则禁用: {rule.name}")
                    return False
                return True
            
            # 有媒体的消息 - 检查具体媒体类型
            media = message.media
            
            # 图片
            if isinstance(media, MessageMediaPhoto):
                if not getattr(rule, 'enable_photo', True):
                    self.logger.debug(f"🖼️ 图片消息被规则禁用: {rule.name}")
                    return False
                return True
            
            # 文档（包括视频、音频、文档等）
            if isinstance(media, MessageMediaDocument):
                document = media.document
                if hasattr(document, 'mime_type') and document.mime_type:
                    mime_type = document.mime_type.lower()
                    
                    # 视频
                    if mime_type.startswith('video/'):
                        if not getattr(rule, 'enable_video', True):
                            self.logger.debug(f"🎥 视频消息被规则禁用: {rule.name}")
                            return False
                        return True
                    
                    # 音频
                    if mime_type.startswith('audio/'):
                        if not getattr(rule, 'enable_audio', True):
                            self.logger.debug(f"🎵 音频消息被规则禁用: {rule.name}")
                            return False
                        return True
                    
                    # 文档/其他文件
                    if not getattr(rule, 'enable_document', True):
                        self.logger.debug(f"📄 文档消息被规则禁用: {rule.name}")
                        return False
                    return True
                
                # 检查是否为特殊类型（语音、贴纸、动图等）
                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        attr_type = type(attr).__name__
                        
                        # 语音消息
                        if 'Voice' in attr_type:
                            if not getattr(rule, 'enable_voice', True):
                                self.logger.debug(f"🎤 语音消息被规则禁用: {rule.name}")
                                return False
                            return True
                        
                        # 贴纸
                        if 'Sticker' in attr_type:
                            if not getattr(rule, 'enable_sticker', False):  # 默认禁用贴纸
                                self.logger.debug(f"😀 贴纸消息被规则禁用: {rule.name}")
                                return False
                            return True
                        
                        # 动图
                        if 'Animated' in attr_type or 'Video' in attr_type:
                            if not getattr(rule, 'enable_animation', True):
                                self.logger.debug(f"🎞️ 动图消息被规则禁用: {rule.name}")
                                return False
                            return True
            
            # 网页预览
            if isinstance(media, MessageMediaWebPage):
                if not getattr(rule, 'enable_webpage', True):
                    self.logger.debug(f"🌐 网页预览被规则禁用: {rule.name}")
                    return False
                return True
            
            # 其他媒体类型（地理位置、联系人、游戏等）
            # 默认允许，除非有特定的禁用设置
            self.logger.debug(f"🔍 未知媒体类型，默认允许: {type(media).__name__}")
            return True
            
        except Exception as e:
            self.logger.error(f"消息类型检查失败: {e}")
            # 出错时默认允许转发
            return True
    
    def _check_time_filter(self, rule: ForwardRule, message) -> bool:
        """检查时间过滤条件"""
        if not hasattr(rule, 'time_filter_type'):
            return True
        
        message_time = message.date
        current_time = datetime.now()
        
        if rule.time_filter_type == "after_start":
            return True  # 启动后的消息都转发
        elif rule.time_filter_type == "time_range":
            if hasattr(rule, 'start_time') and hasattr(rule, 'end_time'):
                if rule.start_time and rule.end_time:
                    return rule.start_time <= message_time <= rule.end_time
        
        return True
    
    async def _forward_message(self, rule: ForwardRule, original_message, text_to_forward: str):
        """转发消息"""
        try:
            target_chat_id = int(rule.target_chat_id)
            
            # 发送消息
            if original_message.media and getattr(rule, 'enable_media', True):
                # 转发媒体消息
                await self.client.send_message(
                    target_chat_id,
                    text_to_forward,
                    file=original_message.media,
                    link_preview=getattr(rule, 'enable_link_preview', True)
                )
            else:
                # 转发文本消息
                await self.client.send_message(
                    target_chat_id,
                    text_to_forward,
                    link_preview=getattr(rule, 'enable_link_preview', True)
                )
            
            self.logger.debug(f"✅ 消息已转发: {rule.source_chat_id} -> {target_chat_id}")
            
        except Exception as e:
            self.logger.error(f"转发消息失败: {e}")
            raise
    
    async def _log_message(self, rule_id: int, message, status: str, error_message: str = None):
        """记录消息日志"""
        try:
            async for db in get_db():
                # 获取聊天ID
                from telethon.tl.types import PeerChannel, PeerChat, PeerUser
                
                if isinstance(message.peer_id, PeerChannel):
                    source_chat_id = str(-1000000000000 - message.peer_id.channel_id)
                elif isinstance(message.peer_id, PeerChat):
                    source_chat_id = str(-message.peer_id.chat_id)
                else:
                    source_chat_id = str(message.peer_id.user_id)
                
                log_entry = MessageLog(
                    rule_id=rule_id,
                    source_chat_id=source_chat_id,
                    source_message_id=message.id,
                    target_chat_id="",  # 这里应该在转发成功后更新
                    original_text=message.text[:500] if message.text else "",
                    status=status,
                    error_message=error_message
                )
                db.add(log_entry)
                await db.commit()
                break
                
        except Exception as e:
            self.logger.error(f"记录消息日志失败: {e}")
    
    async def _update_monitored_chats(self):
        """更新监听的聊天列表"""
        try:
            async for db in get_db():
                from sqlalchemy import select, distinct
                
                # 获取所有活跃规则的源聊天ID
                stmt = select(distinct(ForwardRule.source_chat_id)).where(
                    ForwardRule.is_active == True
                )
                result = await db.execute(stmt)
                chat_ids = result.scalars().all()
                
                self.monitored_chats = set(int(chat_id) for chat_id in chat_ids)
                self.logger.info(f"🎯 更新监听聊天列表: {list(self.monitored_chats)}")
                
        except Exception as e:
            self.logger.error(f"更新监听聊天列表失败: {e}")
    
    async def send_verification_code(self) -> Dict[str, Any]:
        """发送验证码"""
        try:
            if self.client_type != 'user':
                return {"success": False, "message": "只有用户客户端支持验证码登录"}
            
            if not self.phone:
                return {"success": False, "message": "手机号未设置"}
            
            # 创建客户端
            await self._create_client()
            
            if not self.client:
                return {"success": False, "message": "客户端创建失败"}
            
            # 先连接客户端（不进行完整登录）
            await self.client.connect()
            
            if not self.client.is_connected():
                return {"success": False, "message": "客户端连接失败"}
            
            # 发送验证码
            result = await self.client.send_code_request(self.phone)
            self.login_session = result
            self.login_state = "waiting_code"
            
            self.logger.info(f"✅ 验证码已发送到 {self.phone}")
            return {
                "success": True,
                "message": f"验证码已发送到 {self.phone}",
                "step": "waiting_code"
            }
            
        except Exception as e:
            self.logger.error(f"发送验证码失败: {e}")
            return {
                "success": False,
                "message": f"发送验证码失败: {str(e)}"
            }
    
    async def submit_verification_code(self, code: str) -> Dict[str, Any]:
        """提交验证码"""
        try:
            if self.login_state != "waiting_code":
                return {"success": False, "message": "当前不在等待验证码状态"}
            
            if not self.login_session:
                return {"success": False, "message": "登录会话无效，请重新发送验证码"}
            
            if not self.client or not self.client.is_connected():
                return {"success": False, "message": "客户端未连接，请重新发送验证码"}
            
            # 提交验证码
            try:
                result = await self.client.sign_in(phone=self.phone, code=code)
                
                # 登录成功
                self.user_info = result
                self.login_state = "completed"
                self.connected = True
                
                self.logger.info(f"✅ 用户客户端登录成功: {getattr(result, 'username', '') or getattr(result, 'first_name', 'Unknown')}")
                
                return {
                    "success": True,
                    "message": "登录成功",
                    "step": "completed",
                    "user_info": {
                        "id": result.id,
                        "username": getattr(result, 'username', ''),
                        "first_name": getattr(result, 'first_name', ''),
                        "phone": getattr(result, 'phone', '')
                    }
                }
                
            except Exception as e:
                # 检查是否需要二步验证密码
                if "password" in str(e).lower() or "2fa" in str(e).lower():
                    self.login_state = "waiting_password"
                    return {
                        "success": True,
                        "message": "需要输入二步验证密码",
                        "step": "waiting_password"
                    }
                else:
                    self.login_state = "idle"
                    raise e
            
        except Exception as e:
            self.logger.error(f"提交验证码失败: {e}")
            self.login_state = "idle"
            return {
                "success": False,
                "message": f"验证码错误或已过期: {str(e)}"
            }
    
    async def submit_password(self, password: str) -> Dict[str, Any]:
        """提交二步验证密码"""
        try:
            if self.login_state != "waiting_password":
                return {"success": False, "message": "当前不在等待密码状态"}
            
            if not self.client or not self.client.is_connected():
                return {"success": False, "message": "客户端未连接，请重新发送验证码"}
            
            # 提交密码
            result = await self.client.sign_in(password=password)
            
            # 登录成功
            self.user_info = result
            self.login_state = "completed"
            self.connected = True
            
            self.logger.info(f"✅ 用户客户端二步验证成功: {getattr(result, 'username', '') or getattr(result, 'first_name', 'Unknown')}")
            
            return {
                "success": True,
                "message": "登录成功",
                "step": "completed",
                "user_info": {
                    "id": result.id,
                    "username": getattr(result, 'username', ''),
                    "first_name": getattr(result, 'first_name', ''),
                    "phone": getattr(result, 'phone', '')
                }
            }
            
        except Exception as e:
            self.logger.error(f"二步验证失败: {e}")
            self.login_state = "idle"
            return {
                "success": False,
                "message": f"密码错误: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        # 安全地序列化用户信息
        user_info_safe = None
        if self.user_info:
            try:
                user_info_safe = {
                    "id": getattr(self.user_info, 'id', None),
                    "username": getattr(self.user_info, 'username', None),
                    "first_name": getattr(self.user_info, 'first_name', None),
                    "last_name": getattr(self.user_info, 'last_name', None),
                    "phone": getattr(self.user_info, 'phone', None),
                    "bot": getattr(self.user_info, 'bot', None)
                }
            except Exception as e:
                self.logger.warning(f"序列化用户信息失败: {e}")
                user_info_safe = {"error": "序列化失败"}
        
        return {
            "client_id": self.client_id,
            "client_type": self.client_type,
            "running": self.running,
            "connected": self.connected,
            "login_state": getattr(self, 'login_state', 'idle'),
            "user_info": user_info_safe,
            "monitored_chats": list(self.monitored_chats),
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
    
    def get_chats_sync(self) -> List[Dict[str, Any]]:
        """同步获取聊天列表（线程安全）"""
        if not self.loop or not self.running or not self.connected:
            return []
        
        try:
            # 使用 run_coroutine_threadsafe 在客户端的事件循环中执行
            future = asyncio.run_coroutine_threadsafe(
                self._get_chats_async(),
                self.loop
            )
            # 等待结果，超时时间10秒
            return future.result(timeout=10)
        except Exception as e:
            self.logger.warning(f"获取聊天列表失败: {e}")
            return []
    
    async def _get_chats_async(self) -> List[Dict[str, Any]]:
        """在客户端事件循环中异步获取聊天列表"""
        try:
            if not self.client or not self.client.is_connected():
                return []
            
            # 不限制聊天数量，获取所有聊天
            dialogs = await self.client.get_dialogs()
            chats = []
            
            # 获取客户端用户信息用于显示
            client_display_name = "未知客户端"
            if self.user_info:
                if self.client_type == "bot":
                    client_display_name = f"机器人: {getattr(self.user_info, 'first_name', self.client_id)}"
                else:
                    first_name = getattr(self.user_info, 'first_name', '')
                    last_name = getattr(self.user_info, 'last_name', '')
                    username = getattr(self.user_info, 'username', '')
                    if username:
                        client_display_name = f"用户: {first_name} {last_name} (@{username})".strip()
                    else:
                        client_display_name = f"用户: {first_name} {last_name}".strip()
                    if not client_display_name.replace("用户: ", "").strip():
                        client_display_name = f"用户: {self.client_id}"
            
            for dialog in dialogs:
                try:
                    # 获取更详细的聊天信息
                    entity = dialog.entity
                    chat_type = "user"
                    if dialog.is_group:
                        chat_type = "group"
                    elif dialog.is_channel:
                        chat_type = "channel"
                    
                    # 获取聊天标题
                    title = dialog.title or dialog.name
                    if not title and hasattr(entity, 'first_name'):
                        # 对于私聊用户，组合姓名
                        first_name = getattr(entity, 'first_name', '')
                        last_name = getattr(entity, 'last_name', '')
                        title = f"{first_name} {last_name}".strip()
                    if not title:
                        title = "未知聊天"
                    
                    chat_data = {
                        "id": str(dialog.id),
                        "title": title,
                        "type": chat_type,
                        "username": getattr(entity, 'username', None),
                        "description": getattr(entity, 'about', None),
                        "members_count": getattr(entity, 'participants_count', 0) if hasattr(entity, 'participants_count') else 0,
                        "client_id": self.client_id,
                        "client_type": self.client_type,
                        "client_display_name": client_display_name,
                        "is_verified": getattr(entity, 'verified', False),
                        "is_scam": getattr(entity, 'scam', False),
                        "is_fake": getattr(entity, 'fake', False),
                        "unread_count": dialog.unread_count,
                        "last_message_date": dialog.date.isoformat() if dialog.date else None
                    }
                    chats.append(chat_data)
                except Exception as e:
                    self.logger.warning(f"处理聊天数据失败: {e}")
                    continue
            
            self.logger.info(f"✅ 客户端 {self.client_id} 获取到 {len(chats)} 个聊天")
            return chats
        except Exception as e:
            self.logger.error(f"获取聊天列表失败: {e}")
            return []
    
    async def refresh_monitored_chats(self):
        """刷新监听聊天列表（外部调用）"""
        if self.loop and self.running:
            asyncio.run_coroutine_threadsafe(
                self._update_monitored_chats(),
                self.loop
            )


class MultiClientManager:
    """
    多客户端管理器
    
    管理多个Telegram客户端实例，避免客户端竞争
    """
    
    def __init__(self):
        self.clients: Dict[str, TelegramClientManager] = {}
        self.logger = logging.getLogger("MultiClientManager")
    
    def add_client(self, client_id: str, client_type: str = "user") -> TelegramClientManager:
        """添加客户端"""
        if client_id in self.clients:
            self.logger.warning(f"客户端 {client_id} 已存在")
            return self.clients[client_id]
        
        client = TelegramClientManager(client_id, client_type)
        self.clients[client_id] = client
        
        self.logger.info(f"✅ 添加客户端: {client_id} ({client_type})")
        return client

    def add_client_with_config(self, client_id: str, client_type: str = "user", config_data: dict = None) -> TelegramClientManager:
        """添加带配置的客户端"""
        if client_id in self.clients:
            self.logger.warning(f"客户端 {client_id} 已存在")
            return self.clients[client_id]
        
        client = TelegramClientManager(client_id, client_type)
        
        # 存储客户端特定配置
        if config_data:
            if client_type == 'bot':
                client.bot_token = config_data.get('bot_token')
                client.admin_user_id = config_data.get('admin_user_id')
            elif client_type == 'user':
                client.api_id = config_data.get('api_id')
                client.api_hash = config_data.get('api_hash')
                client.phone = config_data.get('phone')
        
        self.clients[client_id] = client
        
        self.logger.info(f"✅ 添加带配置的客户端: {client_id} ({client_type})")
        return client
    
    def remove_client(self, client_id: str) -> bool:
        """移除客户端"""
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        client.stop()
        del self.clients[client_id]
        
        self.logger.info(f"✅ 移除客户端: {client_id}")
        return True
    
    def get_client(self, client_id: str) -> Optional[TelegramClientManager]:
        """获取客户端"""
        return self.clients.get(client_id)
    
    def start_client(self, client_id: str) -> bool:
        """启动客户端"""
        client = self.clients.get(client_id)
        if not client:
            return False
        
        return client.start()
    
    def stop_client(self, client_id: str) -> bool:
        """停止客户端"""
        client = self.clients.get(client_id)
        if not client:
            return False
        
        client.stop()
        return True
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有客户端状态"""
        return {
            client_id: client.get_status()
            for client_id, client in self.clients.items()
        }
    
    def stop_all(self):
        """停止所有客户端"""
        for client in self.clients.values():
            client.stop()
        self.clients.clear()
        self.logger.info("✅ 所有客户端已停止")


# 全局多客户端管理器实例
multi_client_manager = MultiClientManager()
