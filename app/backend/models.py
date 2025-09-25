"""
数据模型定义
"""
from datetime import datetime, timezone
import os
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

def get_local_now():
    """获取本地时区的当前时间"""
    try:
        import pytz
        tz_name = os.environ.get('TZ', 'UTC')
        if tz_name == 'Asia/Shanghai':
            tz = pytz.timezone('Asia/Shanghai')
            return datetime.now(tz)
        elif tz_name != 'UTC':
            # 尝试使用指定的时区
            try:
                tz = pytz.timezone(tz_name)
                return datetime.now(tz)
            except pytz.UnknownTimeZoneError:
                # 如果时区无效，使用UTC
                return datetime.now(pytz.UTC)
        else:
            # 使用UTC时区
            return datetime.now(pytz.UTC)
    except ImportError:
        # 如果pytz不可用，使用系统本地时间
        return datetime.now()

class ForwardRule(Base):
    """转发规则模型"""
    __tablename__ = 'forward_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='规则名称')
    source_chat_id = Column(String(50), nullable=False, comment='源聊天ID')
    source_chat_name = Column(String(200), comment='源聊天名称')
    target_chat_id = Column(String(50), nullable=False, comment='目标聊天ID')
    target_chat_name = Column(String(200), comment='目标聊天名称')
    
    # 功能开关
    is_active = Column(Boolean, default=True, comment='是否启用')
    enable_keyword_filter = Column(Boolean, default=False, comment='是否启用关键词过滤')
    enable_regex_replace = Column(Boolean, default=False, comment='是否启用正则替换')
    
    # 客户端选择
    client_id = Column(String(50), default='main_user', comment='使用的客户端ID')
    client_type = Column(String(20), default='user', comment='客户端类型: user/bot')
    
    # 消息类型支持
    enable_text = Column(Boolean, default=True, comment='是否转发文本消息')
    enable_media = Column(Boolean, default=True, comment='是否转发媒体文件')
    enable_photo = Column(Boolean, default=True, comment='是否转发图片')
    enable_video = Column(Boolean, default=True, comment='是否转发视频')
    enable_document = Column(Boolean, default=True, comment='是否转发文档')
    enable_audio = Column(Boolean, default=True, comment='是否转发音频')
    enable_voice = Column(Boolean, default=True, comment='是否转发语音')
    enable_sticker = Column(Boolean, default=False, comment='是否转发贴纸')
    enable_animation = Column(Boolean, default=True, comment='是否转发动图')
    enable_webpage = Column(Boolean, default=True, comment='是否转发网页预览')
    
    # 高级设置
    forward_delay = Column(Integer, default=0, comment='转发延迟(秒)')
    max_message_length = Column(Integer, default=4096, comment='最大消息长度')
    enable_link_preview = Column(Boolean, default=True, comment='是否启用链接预览')
    
    # 时间过滤设置
    time_filter_type = Column(String(20), default='after_start', comment='时间过滤类型: after_start(启动后), time_range(时间段), from_time(指定时间开始), today_only(仅当天), all_messages(所有消息)')
    start_time = Column(DateTime, comment='开始时间(用于time_range和from_time类型)')
    end_time = Column(DateTime, comment='结束时间(用于time_range类型)')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    # 关系
    keywords = relationship("Keyword", back_populates="rule", cascade="all, delete-orphan")
    replace_rules = relationship("ReplaceRule", back_populates="rule", cascade="all, delete-orphan")
    message_logs = relationship("MessageLog", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ForwardRule(id={self.id}, name='{self.name}')>"

class Keyword(Base):
    """关键词模型"""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('forward_rules.id'), nullable=False)
    keyword = Column(String(500), nullable=False, comment='关键词')
    is_regex = Column(Boolean, default=False, comment='是否为正则表达式')
    is_exclude = Column(Boolean, default=False, comment='是否为排除关键词')
    case_sensitive = Column(Boolean, default=False, comment='是否区分大小写')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    # 关系
    rule = relationship("ForwardRule", back_populates="keywords")
    
    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}')>"

class ReplaceRule(Base):
    """替换规则模型"""
    __tablename__ = 'replace_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('forward_rules.id'), nullable=False)
    name = Column(String(100), comment='替换规则名称')
    pattern = Column(Text, nullable=False, comment='正则表达式模式')
    replacement = Column(Text, nullable=False, comment='替换内容')
    priority = Column(Integer, default=0, comment='优先级，数字越小优先级越高')
    is_regex = Column(Boolean, default=True, comment='是否为正则表达式')
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_global = Column(Boolean, default=False, comment='是否全局替换')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    # 关系
    rule = relationship("ForwardRule", back_populates="replace_rules")
    
    def __repr__(self):
        return f"<ReplaceRule(id={self.id}, name='{self.name}')>"

class MessageLog(Base):
    """消息日志模型"""
    __tablename__ = 'message_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('forward_rules.id'), nullable=True)
    rule_name = Column(String(100), comment='规则名称（用于稳定关联）')
    
    # 源消息信息
    source_chat_id = Column(String(50), nullable=False, comment='源聊天ID')
    source_chat_name = Column(String(200), comment='源聊天名称')
    source_message_id = Column(Integer, nullable=False, comment='源消息ID')
    
    # 目标消息信息
    target_chat_id = Column(String(50), nullable=False, comment='目标聊天ID')
    target_chat_name = Column(String(200), comment='目标聊天名称')
    target_message_id = Column(Integer, comment='目标消息ID')
    
    # 消息内容
    original_text = Column(Text, comment='原始消息文本')
    processed_text = Column(Text, comment='处理后消息文本')
    media_type = Column(String(50), comment='媒体类型')
    
    # 状态信息
    status = Column(String(20), default='success', comment='转发状态')
    error_message = Column(Text, comment='错误信息')
    processing_time = Column(Integer, comment='处理时间(毫秒)')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    # 关系
    rule = relationship("ForwardRule", back_populates="message_logs")
    
    def __repr__(self):
        return f"<MessageLog(id={self.id}, status='{self.status}')>"

class UserSession(Base):
    """用户会话模型"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, comment='用户ID')
    username = Column(String(100), comment='用户名')
    first_name = Column(String(100), comment='名字')
    last_name = Column(String(100), comment='姓氏')
    phone_number = Column(String(20), comment='手机号码')
    is_admin = Column(Boolean, default=False, comment='是否为管理员')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    last_activity = Column(DateTime, default=get_local_now, comment='最后活动时间')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"

class TelegramClient(Base):
    """Telegram客户端配置模型"""
    __tablename__ = 'telegram_clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), unique=True, nullable=False, comment='客户端ID')
    client_type = Column(String(20), nullable=False, comment='客户端类型: user/bot')
    
    # 机器人客户端配置
    bot_token = Column(String(500), comment='机器人Token')
    admin_user_id = Column(String(50), comment='管理员用户ID')
    
    # 用户客户端配置
    api_id = Column(String(50), comment='Telegram API ID')
    api_hash = Column(String(100), comment='Telegram API Hash')
    phone = Column(String(20), comment='手机号')
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment='是否启用')
    auto_start = Column(Boolean, default=False, comment='是否自动启动')
    last_connected = Column(DateTime, comment='最后连接时间')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    def __repr__(self):
        return f"<TelegramClient(id={self.id}, client_id='{self.client_id}', type='{self.client_type}')>"

class BotSettings(Base):
    """机器人设置模型"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, comment='设置键')
    value = Column(Text, comment='设置值')
    description = Column(String(500), comment='设置描述')
    data_type = Column(String(20), default='string', comment='数据类型')
    is_system = Column(Boolean, default=False, comment='是否为系统设置')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    def __repr__(self):
        return f"<BotSettings(key='{self.key}', value='{self.value}')>"

# 数据库操作辅助类
class DatabaseHelper:
    """数据库操作辅助类"""
    
    @staticmethod
    def create_default_settings():
        """创建默认设置"""
        default_settings = [
            {
                'key': 'max_forward_delay',
                'value': '5',
                'description': '最大转发延迟(秒)',
                'data_type': 'integer',
                'is_system': True
            },
            {
                'key': 'enable_media_forward',
                'value': 'true',
                'description': '是否启用媒体转发',
                'data_type': 'boolean',
                'is_system': True
            },
            {
                'key': 'max_message_length',
                'value': '4096',
                'description': '最大消息长度',
                'data_type': 'integer',
                'is_system': True
            },
            {
                'key': 'log_retention_days',
                'value': '30',
                'description': '日志保留天数',
                'data_type': 'integer',
                'is_system': True
            },
            {
                'key': 'enable_debug_mode',
                'value': 'false',
                'description': '是否启用调试模式',
                'data_type': 'boolean',
                'is_system': False
            }
        ]
        
        return default_settings
    
    @staticmethod
    def get_table_names():
        """获取所有表名"""
        return [
            'forward_rules',
            'keywords',
            'replace_rules',
            'message_logs',
            'user_sessions',
            'telegram_clients',
            'bot_settings'
        ]
