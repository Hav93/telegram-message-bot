"""
业务逻辑服务层
"""
import asyncio
from datetime import datetime, timedelta
from models import get_local_now
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, update, and_, or_, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from database import get_db
from models import ForwardRule, Keyword, ReplaceRule, MessageLog, UserSession, BotSettings
from filters import KeywordFilter, RegexReplacer, MessageProcessor

class ForwardRuleService:
    """转发规则服务"""
    
    @staticmethod
    async def create_rule(
        name: str,
        source_chat_id: str,
        source_chat_name: str,
        target_chat_id: str,
        target_chat_name: str,
        **kwargs
    ) -> ForwardRule:
        """创建转发规则"""
        async for db in get_db():
            rule = ForwardRule(
                name=name,
                source_chat_id=source_chat_id,
                source_chat_name=source_chat_name,
                target_chat_id=target_chat_id,
                target_chat_name=target_chat_name,
                **kwargs
            )
            
            db.add(rule)
            await db.commit()
            await db.refresh(rule)
            
            logger.info(f"创建转发规则: {rule.name}")
            return rule
    
    @staticmethod
    async def get_rule_by_id(rule_id: int) -> Optional[ForwardRule]:
        """根据ID获取规则"""
        async for db in get_db():
            stmt = select(ForwardRule).where(ForwardRule.id == rule_id).options(
                selectinload(ForwardRule.keywords),
                selectinload(ForwardRule.replace_rules)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_rules_by_source_chat(source_chat_id: str) -> List[ForwardRule]:
        """根据源聊天ID获取规则"""
        async for db in get_db():
            stmt = select(ForwardRule).where(
                and_(
                    ForwardRule.source_chat_id == source_chat_id,
                    ForwardRule.is_active == True
                )
            ).options(
                selectinload(ForwardRule.keywords),
                selectinload(ForwardRule.replace_rules)
            )
            result = await db.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def get_all_rules() -> List[ForwardRule]:
        """获取所有规则（包括非活跃的）"""
        async for db in get_db():
            stmt = select(ForwardRule).options(
                selectinload(ForwardRule.keywords),
                selectinload(ForwardRule.replace_rules)
            )
            result = await db.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_all_active_rules() -> List[ForwardRule]:
        """获取所有活跃规则"""
        async for db in get_db():
            stmt = select(ForwardRule).where(ForwardRule.is_active == True).options(
                selectinload(ForwardRule.keywords),
                selectinload(ForwardRule.replace_rules)
            )
            result = await db.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def update_rule(rule_id: int, **kwargs) -> bool:
        """更新规则"""
        async for db in get_db():
            stmt = update(ForwardRule).where(ForwardRule.id == rule_id).values(**kwargs)
            result = await db.execute(stmt)
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"更新转发规则: {rule_id}")
                return True
            return False
    
    @staticmethod
    async def delete_rule(rule_id: int) -> bool:
        """删除规则"""
        async for db in get_db():
            stmt = delete(ForwardRule).where(ForwardRule.id == rule_id)
            result = await db.execute(stmt)
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"删除转发规则: {rule_id}")
                return True
            return False
    
    @staticmethod
    async def copy_rule(source_rule_id: int, target_rule_id: Optional[int] = None) -> Optional[ForwardRule]:
        """复制规则"""
        source_rule = await ForwardRuleService.get_rule_by_id(source_rule_id)
        if not source_rule:
            return None
        
        async for db in get_db():
            if target_rule_id:
                # 更新现有规则
                stmt = update(ForwardRule).where(ForwardRule.id == target_rule_id).values(
                    enable_keyword_filter=source_rule.enable_keyword_filter,
                    enable_regex_replace=source_rule.enable_regex_replace,
                    enable_media=source_rule.enable_media,
                    forward_delay=source_rule.forward_delay,
                    max_message_length=source_rule.max_message_length,
                    enable_link_preview=source_rule.enable_link_preview
                )
                await db.execute(stmt)
                
                # 复制关键词
                await KeywordService.copy_keywords(source_rule_id, target_rule_id)
                # 复制替换规则
                await ReplaceRuleService.copy_replace_rules(source_rule_id, target_rule_id)
                
                await db.commit()
                return await ForwardRuleService.get_rule_by_id(target_rule_id)
            else:
                # 创建新规则
                new_rule = ForwardRule(
                    name=f"{source_rule.name}_copy",
                    source_chat_id=source_rule.source_chat_id,
                    source_chat_name=source_rule.source_chat_name,
                    target_chat_id=source_rule.target_chat_id,
                    target_chat_name=source_rule.target_chat_name,
                    enable_keyword_filter=source_rule.enable_keyword_filter,
                    enable_regex_replace=source_rule.enable_regex_replace,
                    enable_media=source_rule.enable_media,
                    forward_delay=source_rule.forward_delay,
                    max_message_length=source_rule.max_message_length,
                    enable_link_preview=source_rule.enable_link_preview
                )
                
                db.add(new_rule)
                await db.commit()
                await db.refresh(new_rule)
                
                # 复制关键词和替换规则
                await KeywordService.copy_keywords(source_rule_id, new_rule.id)
                await ReplaceRuleService.copy_replace_rules(source_rule_id, new_rule.id)
                
                return new_rule

class KeywordService:
    """关键词服务"""
    
    @staticmethod
    async def add_keyword(rule_id: int, keyword: str, is_regex: bool = False, 
                         is_exclude: bool = False, case_sensitive: bool = False) -> Keyword:
        """添加关键词"""
        async for db in get_db():
            kw = Keyword(
                rule_id=rule_id,
                keyword=keyword,
                is_regex=is_regex,
                is_exclude=is_exclude,
                case_sensitive=case_sensitive
            )
            
            db.add(kw)
            await db.commit()
            await db.refresh(kw)
            
            logger.info(f"添加关键词: {keyword} (规则ID: {rule_id})")
            return kw
    
    @staticmethod
    async def get_keywords_by_rule(rule_id: int) -> List[Keyword]:
        """获取规则的所有关键词"""
        async for db in get_db():
            stmt = select(Keyword).where(Keyword.rule_id == rule_id)
            result = await db.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def delete_keyword(keyword_id: int) -> bool:
        """删除关键词"""
        async for db in get_db():
            stmt = delete(Keyword).where(Keyword.id == keyword_id)
            result = await db.execute(stmt)
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"删除关键词: {keyword_id}")
                return True
            return False
    
    @staticmethod
    async def delete_keywords_by_rule(rule_id: int) -> int:
        """删除规则的所有关键词"""
        async for db in get_db():
            stmt = delete(Keyword).where(Keyword.rule_id == rule_id)
            result = await db.execute(stmt)
            await db.commit()
            
            logger.info(f"删除规则 {rule_id} 的所有关键词")
            return result.rowcount
    
    @staticmethod
    async def copy_keywords(source_rule_id: int, target_rule_id: int) -> int:
        """复制关键词"""
        source_keywords = await KeywordService.get_keywords_by_rule(source_rule_id)
        
        async for db in get_db():
            count = 0
            for kw in source_keywords:
                new_kw = Keyword(
                    rule_id=target_rule_id,
                    keyword=kw.keyword,
                    is_regex=kw.is_regex,
                    is_exclude=kw.is_exclude,
                    case_sensitive=kw.case_sensitive
                )
                db.add(new_kw)
                count += 1
            
            await db.commit()
            logger.info(f"复制 {count} 个关键词从规则 {source_rule_id} 到 {target_rule_id}")
            return count

class ReplaceRuleService:
    """替换规则服务"""
    
    @staticmethod
    async def add_replace_rule(rule_id: int, name: str, pattern: str, 
                              replacement: str, priority: int = 0) -> ReplaceRule:
        """添加替换规则"""
        async for db in get_db():
            replace_rule = ReplaceRule(
                rule_id=rule_id,
                name=name,
                pattern=pattern,
                replacement=replacement,
                priority=priority
            )
            
            db.add(replace_rule)
            await db.commit()
            await db.refresh(replace_rule)
            
            logger.info(f"添加替换规则: {name} (规则ID: {rule_id})")
            return replace_rule
    
    @staticmethod
    async def get_replace_rules_by_rule(rule_id: int) -> List[ReplaceRule]:
        """获取规则的所有替换规则"""
        async for db in get_db():
            stmt = select(ReplaceRule).where(
                ReplaceRule.rule_id == rule_id
            ).order_by(ReplaceRule.priority)
            result = await db.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def delete_replace_rule(replace_rule_id: int) -> bool:
        """删除替换规则"""
        async for db in get_db():
            stmt = delete(ReplaceRule).where(ReplaceRule.id == replace_rule_id)
            result = await db.execute(stmt)
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"删除替换规则: {replace_rule_id}")
                return True
            return False
    
    @staticmethod
    async def copy_replace_rules(source_rule_id: int, target_rule_id: int) -> int:
        """复制替换规则"""
        source_rules = await ReplaceRuleService.get_replace_rules_by_rule(source_rule_id)
        
        async for db in get_db():
            count = 0
            for rule in source_rules:
                new_rule = ReplaceRule(
                    rule_id=target_rule_id,
                    name=rule.name,
                    pattern=rule.pattern,
                    replacement=rule.replacement,
                    priority=rule.priority,
                    is_active=rule.is_active,
                    is_global=rule.is_global
                )
                db.add(new_rule)
                count += 1
            
            await db.commit()
            logger.info(f"复制 {count} 个替换规则从规则 {source_rule_id} 到 {target_rule_id}")
            return count

class MessageLogService:
    """消息日志服务"""
    
    @staticmethod
    async def log_message(rule_id: Optional[int], source_chat_id: str, source_message_id: int,
                         target_chat_id: str, target_message_id: Optional[int] = None,
                         original_text: str = "", processed_text: str = "",
                         status: str = "success", error_message: str = "",
                         processing_time: int = 0, media_type: str = "") -> MessageLog:
        """记录消息日志"""
        async for db in get_db():
            log = MessageLog(
                rule_id=rule_id,
                source_chat_id=source_chat_id,
                source_message_id=source_message_id,
                target_chat_id=target_chat_id,
                target_message_id=target_message_id,
                original_text=original_text,
                processed_text=processed_text,
                status=status,
                error_message=error_message,
                processing_time=processing_time,
                media_type=media_type
            )
            
            db.add(log)
            await db.commit()
            await db.refresh(log)
            
            return log
    
    @staticmethod
    async def get_logs_by_rule(rule_id: int, limit: int = 100) -> List[MessageLog]:
        """获取规则的消息日志"""
        async for db in get_db():
            stmt = select(MessageLog).where(
                MessageLog.rule_id == rule_id
            ).order_by(desc(MessageLog.created_at)).limit(limit)
            result = await db.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def clean_old_logs(days: int = 30) -> int:
        """清理旧日志"""
        cutoff_date = get_local_now() - timedelta(days=days)
        
        async for db in get_db():
            stmt = delete(MessageLog).where(MessageLog.created_at < cutoff_date)
            result = await db.execute(stmt)
            await db.commit()
            
            logger.info(f"清理了 {result.rowcount} 条旧日志")
            return result.rowcount

class UserSessionService:
    """用户会话服务"""
    
    @staticmethod
    async def create_or_update_session(user_id: int, **kwargs) -> UserSession:
        """创建或更新用户会话"""
        async for db in get_db():
            stmt = select(UserSession).where(UserSession.user_id == user_id)
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                # 更新现有会话
                for key, value in kwargs.items():
                    setattr(session, key, value)
                session.last_activity = get_local_now()
            else:
                # 创建新会话
                session = UserSession(user_id=user_id, **kwargs)
                db.add(session)
            
            await db.commit()
            await db.refresh(session)
            
            return session
    
    @staticmethod
    async def get_session_by_user_id(user_id: int) -> Optional[UserSession]:
        """根据用户ID获取会话"""
        async for db in get_db():
            stmt = select(UserSession).where(UserSession.user_id == user_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def is_admin(user_id: int) -> bool:
        """检查用户是否为管理员"""
        session = await UserSessionService.get_session_by_user_id(user_id)
        return session.is_admin if session else False

class BotSettingsService:
    """机器人设置服务"""
    
    @staticmethod
    async def get_setting(key: str, default_value: str = "") -> str:
        """获取设置值"""
        async for db in get_db():
            stmt = select(BotSettings).where(BotSettings.key == key)
            result = await db.execute(stmt)
            setting = result.scalar_one_or_none()
            
            return setting.value if setting else default_value
    
    @staticmethod
    async def set_setting(key: str, value: str, description: str = "", 
                         data_type: str = "string") -> BotSettings:
        """设置配置值"""
        async for db in get_db():
            stmt = select(BotSettings).where(BotSettings.key == key)
            result = await db.execute(stmt)
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.value = value
                setting.description = description
                setting.data_type = data_type
                setting.updated_at = get_local_now()
            else:
                setting = BotSettings(
                    key=key,
                    value=value,
                    description=description,
                    data_type=data_type
                )
                db.add(setting)
            
            await db.commit()
            await db.refresh(setting)
            
            return setting
    
    @staticmethod
    async def get_all_settings() -> List[BotSettings]:
        """获取所有设置"""
        async for db in get_db():
            stmt = select(BotSettings).order_by(BotSettings.key)
            result = await db.execute(stmt)
            return result.scalars().all()

class MessageProcessingService:
    """消息处理服务"""
    
    def __init__(self):
        self.processor = MessageProcessor()
    
    async def process_message(self, rule: ForwardRule, message_text: str) -> Optional[str]:
        """处理消息"""
        try:
            # 获取关键词和替换规则
            keywords = rule.keywords if rule.enable_keyword_filter else []
            replace_rules = rule.replace_rules if rule.enable_regex_replace else []
            
            # 处理消息
            processed_text = self.processor.process_message(
                message_text, keywords, replace_rules
            )
            
            return processed_text
            
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            return None
