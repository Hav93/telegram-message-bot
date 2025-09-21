#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Telegram消息转发机器人 - 干净的Web启动器
解决实时监听问题的核心版本
"""

import logging
import asyncio
import os
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_enhanced_clean.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def auto_database_migration(enhanced_bot=None):
    """自动数据库迁移和修复"""
    try:
        from database import get_db
        from models import MessageLog, ForwardRule
        from sqlalchemy import select, delete, func, text, update
        
        logger.info("🔧 开始自动数据库迁移...")
        
        async for db in get_db():
            # 1. 检查是否已有 rule_name 字段
            try:
                await db.execute(text("SELECT rule_name FROM message_logs LIMIT 1"))
                has_rule_name_column = True
                logger.info("✅ rule_name 字段已存在")
            except Exception:
                has_rule_name_column = False
                logger.info("🔧 需要添加 rule_name 字段")
            
            # 2. 如果没有 rule_name 字段，则添加
            if not has_rule_name_column:
                await db.execute(text("ALTER TABLE message_logs ADD COLUMN rule_name VARCHAR(100)"))
                logger.info("✅ 已添加 rule_name 字段")
                
                # 3. 获取当前所有规则的ID和名称映射
                current_rules = await db.execute(select(ForwardRule.id, ForwardRule.name))
                rule_mapping = {rule[0]: rule[1] for rule in current_rules.fetchall()}
                
                logger.info(f"🔧 当前规则映射: {rule_mapping}")
                
                # 4. 更新现有日志的 rule_name
                for rule_id, rule_name in rule_mapping.items():
                    update_result = await db.execute(
                        update(MessageLog)
                        .where(MessageLog.rule_id == rule_id)
                        .values(rule_name=rule_name)
                    )
                    if update_result.rowcount > 0:
                        logger.info(f"🔧 更新规则ID {rule_id} 的日志名称为 '{rule_name}': {update_result.rowcount} 条")
                
                # 5. 删除孤立的消息日志（rule_id不在当前规则表中）
                valid_rule_ids = list(rule_mapping.keys())
                if valid_rule_ids:  # 只有在有有效规则时才清理孤立日志
                    delete_result = await db.execute(
                        delete(MessageLog).where(~MessageLog.rule_id.in_(valid_rule_ids))
                    )
                    if delete_result.rowcount > 0:
                        logger.info(f"🧹 删除了 {delete_result.rowcount} 条孤立的消息日志")
                
                await db.commit()
                logger.info("✅ 自动数据库迁移完成")
            else:
                logger.info("✅ 数据库结构检查完成，无需迁移")
            
            # 检查并更新聊天名称（启动时只设置占位符，避免事件循环冲突）
            await auto_update_chat_names(db, None)  # 不传递enhanced_bot，只设置占位符
            break
            
    except Exception as e:
        logger.error(f"❌ 自动数据库迁移失败: {e}")

async def auto_update_chat_names(db, enhanced_bot=None):
    """自动更新聊天名称 - 直接从Telegram获取真实名称"""
    try:
        from models import ForwardRule
        from sqlalchemy import select, update
        
        logger.info("🔄 开始检查聊天名称...")
        
        # 获取所有聊天名称为空或占位符格式的规则
        rules_to_update = await db.execute(
            select(ForwardRule).where(
                (ForwardRule.source_chat_name.is_(None)) | 
                (ForwardRule.source_chat_name == '') |
                (ForwardRule.source_chat_name.like('聊天 %')) |  # 识别占位符格式
                (ForwardRule.target_chat_name.is_(None)) | 
                (ForwardRule.target_chat_name == '') |
                (ForwardRule.target_chat_name.like('聊天 %'))    # 识别占位符格式
            )
        )
        rules = rules_to_update.fetchall()
        
        if not rules:
            logger.info("✅ 所有规则的聊天名称都已设置")
            return
        
        logger.info(f"🔄 发现 {len(rules)} 个规则需要更新聊天名称")
        
        # 尝试从Telegram客户端直接获取真实聊天名称
        updated_count = 0
        real_names_count = 0
        
        # 检查是否有可用的Telegram客户端
        client_wrapper = None
        if enhanced_bot and hasattr(enhanced_bot, 'multi_client_manager') and enhanced_bot.multi_client_manager:
            client_manager = enhanced_bot.multi_client_manager
            if hasattr(client_manager, 'client_wrappers') and client_manager.client_wrappers:
                # 获取第一个可用的客户端
                client_wrapper = next(iter(client_manager.client_wrappers.values()))
                logger.info("🔗 找到可用的Telegram客户端，将获取真实聊天名称")
            elif hasattr(client_manager, 'clients') and client_manager.clients:
                # 兼容旧版本的属性名
                client_wrapper = next(iter(client_manager.clients.values()))
                logger.info("🔗 找到可用的Telegram客户端，将获取真实聊天名称")
        
        for rule_tuple in rules:
            rule = rule_tuple[0]  # SQLAlchemy返回的是tuple
            updated_fields = {}
            
            # 更新源聊天名称（包括占位符格式的名称）
            needs_source_update = (
                not rule.source_chat_name or 
                rule.source_chat_name.strip() == '' or
                rule.source_chat_name.startswith('聊天 ')  # 检查占位符格式
            )
            
            if needs_source_update:
                source_name = f"聊天 {rule.source_chat_id}"  # 默认占位符
                
                if client_wrapper and rule.source_chat_id:
                    try:
                        source_entity = await client_wrapper.client.get_entity(int(rule.source_chat_id))
                        # 优先使用 title 字段，这是最通用的名称字段
                        if hasattr(source_entity, 'title') and source_entity.title:
                            source_name = source_entity.title
                            real_names_count += 1
                        elif hasattr(source_entity, 'username') and source_entity.username:
                            source_name = f"@{source_entity.username}"
                            real_names_count += 1
                        elif hasattr(source_entity, 'first_name') and source_entity.first_name:
                            last_name = getattr(source_entity, 'last_name', '')
                            source_name = f"{source_entity.first_name} {last_name}".strip()
                            real_names_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ 无法获取源聊天 {rule.source_chat_id} 的信息: {e}")
                
                updated_fields['source_chat_name'] = source_name
            
            # 更新目标聊天名称（包括占位符格式的名称）
            needs_target_update = (
                not rule.target_chat_name or 
                rule.target_chat_name.strip() == '' or
                rule.target_chat_name.startswith('聊天 ')  # 检查占位符格式
            )
            
            if needs_target_update:
                target_name = f"聊天 {rule.target_chat_id}"  # 默认占位符
                
                if client_wrapper and rule.target_chat_id:
                    try:
                        target_entity = await client_wrapper.client.get_entity(int(rule.target_chat_id))
                        # 优先使用 title 字段，这是最通用的名称字段
                        if hasattr(target_entity, 'title') and target_entity.title:
                            target_name = target_entity.title
                            real_names_count += 1
                        elif hasattr(target_entity, 'username') and target_entity.username:
                            target_name = f"@{target_entity.username}"
                            real_names_count += 1
                        elif hasattr(target_entity, 'first_name') and target_entity.first_name:
                            last_name = getattr(target_entity, 'last_name', '')
                            target_name = f"{target_entity.first_name} {last_name}".strip()
                            real_names_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ 无法获取目标聊天 {rule.target_chat_id} 的信息: {e}")
                
                updated_fields['target_chat_name'] = target_name
            
            if updated_fields:
                await db.execute(
                    update(ForwardRule)
                    .where(ForwardRule.id == rule.id)
                    .values(**updated_fields)
                )
                updated_count += 1
                logger.info(f"🔄 更新规则 {rule.name}: {updated_fields}")
        
        if updated_count > 0:
            await db.commit()
            if real_names_count > 0:
                logger.info(f"✅ 已为 {updated_count} 个规则更新聊天名称，其中 {real_names_count} 个获取了真实名称")
            else:
                logger.info(f"✅ 已为 {updated_count} 个规则设置占位符聊天名称")
                if not client_wrapper:
                    logger.info("💡 提示: Telegram客户端未配置，使用了占位符名称")
        
    except Exception as e:
        logger.error(f"❌ 自动更新聊天名称失败: {e}")

async def delayed_chat_names_update(enhanced_bot, delay_seconds=10):
    """延迟更新聊天名称，避免事件循环冲突"""
    try:
        import asyncio
        logger.info(f"⏰ 将在 {delay_seconds} 秒后尝试更新聊天名称...")
        await asyncio.sleep(delay_seconds)
        
        from database import get_db
        async for db in get_db():
            await auto_update_chat_names(db, enhanced_bot)
            break
            
    except Exception as e:
        logger.error(f"❌ 延迟更新聊天名称失败: {e}")

async def main():
    """主函数"""
    try:
        logger.info("🚀 启动增强版Telegram消息转发机器人Web界面")
        
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        # 加载配置
        logger.info("📄 加载配置...")
        from config import Config
        
        # 启动增强版机器人管理器
        logger.info("🤖 启动增强版机器人管理器...")
        try:
            from enhanced_bot import EnhancedTelegramBot
            from telegram_client_manager import multi_client_manager
            
            # 创建增强版机器人实例
            enhanced_bot = EnhancedTelegramBot()
            logger.info("✅ 增强版机器人管理器已创建")
            
            # 启动机器人（后台运行，支持无配置Web-only模式）
            await enhanced_bot.start(web_mode=True)
            logger.info("✅ 增强版机器人已在后台启动")
            
        except ImportError as e:
            logger.error(f"❌ 增强版机器人管理器加载失败: {e}")
            logger.info("💡 使用传统模式启动...")
            enhanced_bot = None
        
        # 自动数据库迁移
        await auto_database_migration(enhanced_bot)
        
        # 延迟更新聊天名称（避免事件循环冲突）
        if enhanced_bot:
            logger.info("⏰ 将通过API端点触发聊天名称更新，请稍后手动调用或等待自动触发")
        
        # 创建简化的FastAPI应用
        logger.info("🌐 启动Web服务器...")
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        from fastapi.staticfiles import StaticFiles
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(
            title="Telegram消息转发机器人 - 增强版",
            description="Telegram消息转发机器人v3.6",
            version="3.7.0"
        )
        
        # 添加启动事件处理器
        @app.on_event("startup")
        async def startup_event():
            """应用启动后执行的任务"""
            if enhanced_bot:
                logger.info("🚀 FastAPI应用启动完成，开始延迟更新聊天名称...")
                import asyncio
                # 创建后台任务
                asyncio.create_task(delayed_chat_names_update(enhanced_bot))
        
        # 添加CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 挂载React前端
        frontend_dist = Path("frontend/dist")
        if frontend_dist.exists():
            app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="react-assets")
            app.mount("/static", StaticFiles(directory=frontend_dist), name="react-static")
            logger.info("✅ React前端已挂载")
        else:
            logger.warning("⚠️ React前端构建文件不存在")
        
        # 增强版API - 客户端管理
        @app.get("/api/clients")
        async def get_all_clients():
            """获取所有客户端状态"""
            try:
                if enhanced_bot:
                    clients_status = enhanced_bot.get_client_status()
                    return JSONResponse(content={
                        "success": True,
                        "clients": clients_status
                    })
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "增强版机器人不可用，运行在传统模式"
                    })
            except Exception as e:
                logger.error(f"获取客户端状态失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取客户端状态失败: {str(e)}"
                }, status_code=500)
        
        @app.get("/api/system/enhanced-status")
        async def get_enhanced_system_status():
            """获取增强版系统状态"""
            try:
                # 由于我们使用的是web_enhanced_clean.py，始终返回增强模式
                if enhanced_bot and hasattr(enhanced_bot, 'get_client_status'):
                    clients_status = enhanced_bot.get_client_status()
                    return JSONResponse(content={
                        "success": True,
                        "enhanced_mode": True,
                        "app_version": Config.APP_VERSION,
                        "app_name": Config.APP_NAME,
                        "app_description": Config.APP_DESCRIPTION,
                        "clients": clients_status,
                        "total_clients": len(clients_status),
                        "running_clients": sum(1 for client in clients_status.values() if client.get("running", False)),
                        "connected_clients": sum(1 for client in clients_status.values() if client.get("connected", False))
                    })
                else:
                    # 即使enhanced_bot为None，仍然返回增强模式为true
                    # 因为我们使用的是web_enhanced_clean.py
                    return JSONResponse(content={
                        "success": True,
                        "enhanced_mode": True,
                        "app_version": Config.APP_VERSION,
                        "app_name": Config.APP_NAME,
                        "app_description": Config.APP_DESCRIPTION,
                        "clients": {},
                        "total_clients": 0,
                        "running_clients": 0,
                        "connected_clients": 0,
                        "message": "增强模式已启用，正在初始化..."
                    })
            except Exception as e:
                logger.error(f"获取增强版系统状态失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "enhanced_mode": True,  # 保持增强模式状态
                    "message": f"获取系统状态失败: {str(e)}"
                }, status_code=500)
        
        # 基础API代理 - 转发到传统API（如果需要）
        @app.get("/api/rules")
        async def get_rules():
            """获取规则列表（代理到服务）"""
            try:
                from services import ForwardRuleService
                rules = await ForwardRuleService.get_all_rules()
                
                # 添加调试日志
                logger.info(f"📋 获取到 {len(rules)} 条规则")
                for rule in rules:
                    logger.info(f"📋 规则 {rule.id}: name='{rule.name}', type={type(rule.name)}, len={len(rule.name) if rule.name else 0}")
                
                # 检查消息日志中的规则关联
                from database import get_db
                from models import MessageLog
                from sqlalchemy import select, func
                
                async for db in get_db():
                    # 统计每个规则ID的消息日志数量
                    log_stats = await db.execute(
                        select(MessageLog.rule_id, func.count(MessageLog.id).label('count'))
                        .group_by(MessageLog.rule_id)
                    )
                    log_results = log_stats.fetchall()
                    
                    logger.info(f"📊 消息日志统计:")
                    for log_stat in log_results:
                        logger.info(f"📊 规则ID {log_stat[0]}: {log_stat[1]} 条日志")
                    
                    # 检查最近的几条日志记录
                    recent_logs = await db.execute(
                        select(MessageLog.id, MessageLog.rule_id, MessageLog.source_message_id, 
                               MessageLog.source_chat_id, MessageLog.status)
                        .order_by(MessageLog.created_at.desc())
                        .limit(5)
                    )
                    recent_results = recent_logs.fetchall()
                    
                    logger.info(f"📊 最近5条消息日志:")
                    for log in recent_results:
                        logger.info(f"📊 日志ID={log[0]}, 规则ID={log[1]}, 消息ID={log[2]}, 源聊天={log[3]}, 状态={log[4]}")
                    break
                
                # 将规则对象转换为字典，包含关联数据
                rules_data = []
                for rule in rules:
                    rule_dict = {
                        "id": rule.id,
                        "name": rule.name,
                        "source_chat_id": rule.source_chat_id,
                        "source_chat_name": rule.source_chat_name,
                        "target_chat_id": rule.target_chat_id,
                        "target_chat_name": rule.target_chat_name,
                        "is_active": rule.is_active,
                        "enable_keyword_filter": rule.enable_keyword_filter,
                        "enable_regex_replace": getattr(rule, 'enable_regex_replace', False),
                        "client_id": getattr(rule, 'client_id', 'main_user'),
                        "client_type": getattr(rule, 'client_type', 'user'),
                        
                        # 消息类型过滤
                        "enable_text": getattr(rule, 'enable_text', True),
                        "enable_photo": getattr(rule, 'enable_photo', True),
                        "enable_video": getattr(rule, 'enable_video', True),
                        "enable_document": getattr(rule, 'enable_document', True),
                        "enable_audio": getattr(rule, 'enable_audio', True),
                        "enable_voice": getattr(rule, 'enable_voice', True),
                        "enable_sticker": getattr(rule, 'enable_sticker', False),
                        "enable_animation": getattr(rule, 'enable_animation', True),
                        "enable_webpage": getattr(rule, 'enable_webpage', True),
                        
                        # 高级设置
                        "forward_delay": getattr(rule, 'forward_delay', 0),
                        "max_message_length": getattr(rule, 'max_message_length', 4096),
                        "enable_link_preview": getattr(rule, 'enable_link_preview', True),
                        
                        # 时间过滤
                        "time_filter_type": getattr(rule, 'time_filter_type', 'after_start'),
                        "start_time": rule.start_time.isoformat() if rule.start_time else None,
                        "end_time": rule.end_time.isoformat() if rule.end_time else None,
                        
                        "created_at": rule.created_at.isoformat() if rule.created_at else None,
                        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
                        "keywords": [{"word": kw.word, "mode": kw.mode} for kw in rule.keywords] if rule.keywords else [],
                        "replace_rules": [{"pattern": rr.pattern, "replacement": rr.replacement} for rr in rule.replace_rules] if rule.replace_rules else []
                    }
                    rules_data.append(rule_dict)
                
                return JSONResponse(content={
                    "success": True,
                    "rules": rules_data
                })
            except Exception as e:
                logger.error(f"获取规则失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取规则失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/rules")
        async def create_rule(request: Request):
            """创建规则"""
            try:
                data = await request.json()
                from services import ForwardRuleService
                
                # 验证必需的字段
                required_fields = ['name', 'source_chat_id', 'target_chat_id']
                for field in required_fields:
                    if field not in data:
                        return JSONResponse(content={
                            "success": False,
                            "message": f"缺少必需字段: {field}"
                        }, status_code=400)
                
                # 提取参数，允许可选字段
                kwargs = {k: v for k, v in data.items() if k not in required_fields}
                
                rule = await ForwardRuleService.create_rule(
                    name=data['name'],
                    source_chat_id=data['source_chat_id'],
                    source_chat_name=data.get('source_chat_name', ''),
                    target_chat_id=data['target_chat_id'],
                    target_chat_name=data.get('target_chat_name', ''),
                    **kwargs
                )
                # 序列化规则数据
                rule_data = None
                if rule:
                    rule_data = {
                        "id": rule.id,
                        "name": rule.name,
                        "source_chat_id": rule.source_chat_id,
                        "source_chat_name": rule.source_chat_name,
                        "target_chat_id": rule.target_chat_id,
                        "target_chat_name": rule.target_chat_name,
                        "is_active": rule.is_active,
                        "enable_keyword_filter": rule.enable_keyword_filter,
                        "enable_regex_replace": getattr(rule, 'enable_regex_replace', False),
                        "client_id": getattr(rule, 'client_id', 'main_user'),
                        "client_type": getattr(rule, 'client_type', 'user'),
                        
                        # 消息类型过滤
                        "enable_text": getattr(rule, 'enable_text', True),
                        "enable_photo": getattr(rule, 'enable_photo', True),
                        "enable_video": getattr(rule, 'enable_video', True),
                        "enable_document": getattr(rule, 'enable_document', True),
                        "enable_audio": getattr(rule, 'enable_audio', True),
                        "enable_voice": getattr(rule, 'enable_voice', True),
                        "enable_sticker": getattr(rule, 'enable_sticker', False),
                        "enable_animation": getattr(rule, 'enable_animation', True),
                        "enable_webpage": getattr(rule, 'enable_webpage', True),
                        
                        # 高级设置
                        "forward_delay": getattr(rule, 'forward_delay', 0),
                        "max_message_length": getattr(rule, 'max_message_length', 4096),
                        "enable_link_preview": getattr(rule, 'enable_link_preview', True),
                        
                        # 时间过滤
                        "time_filter_type": getattr(rule, 'time_filter_type', 'after_start'),
                        "start_time": rule.start_time.isoformat() if rule.start_time else None,
                        "end_time": rule.end_time.isoformat() if rule.end_time else None,
                        
                        "created_at": rule.created_at.isoformat() if rule.created_at else None,
                        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
                    }
                
                return JSONResponse(content={
                    "success": True,
                    "rule": rule_data,
                    "message": "规则创建成功"
                })
            except Exception as e:
                logger.error(f"创建规则失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"创建规则失败: {str(e)}"
                }, status_code=500)

        @app.get("/api/rules/{rule_id}")
        async def get_rule(rule_id: int):
            """获取单个规则详情"""
            try:
                from services import ForwardRuleService
                rule = await ForwardRuleService.get_rule_by_id(rule_id)
                
                if not rule:
                    return JSONResponse(content={
                        "success": False,
                        "message": "规则不存在"
                    }, status_code=404)
                
                # 序列化规则数据
                rule_dict = {
                    "id": rule.id,
                    "name": rule.name,
                    "source_chat_id": rule.source_chat_id,
                    "source_chat_name": rule.source_chat_name,
                    "target_chat_id": rule.target_chat_id,
                    "target_chat_name": rule.target_chat_name,
                    "is_active": rule.is_active,
                    "enable_keyword_filter": rule.enable_keyword_filter,
                    "enable_regex_replace": getattr(rule, 'enable_regex_replace', False),
                    "client_id": getattr(rule, 'client_id', 'main_user'),
                    "client_type": getattr(rule, 'client_type', 'user'),
                    
                    # 消息类型过滤
                    "enable_text": getattr(rule, 'enable_text', True),
                    "enable_photo": getattr(rule, 'enable_photo', True),
                    "enable_video": getattr(rule, 'enable_video', True),
                    "enable_document": getattr(rule, 'enable_document', True),
                    "enable_audio": getattr(rule, 'enable_audio', True),
                    "enable_voice": getattr(rule, 'enable_voice', True),
                    "enable_sticker": getattr(rule, 'enable_sticker', False),
                    "enable_animation": getattr(rule, 'enable_animation', True),
                    "enable_webpage": getattr(rule, 'enable_webpage', True),
                    
                    # 高级设置
                    "forward_delay": getattr(rule, 'forward_delay', 0),
                    "max_message_length": getattr(rule, 'max_message_length', 4096),
                    "enable_link_preview": getattr(rule, 'enable_link_preview', True),
                    
                    # 时间过滤
                    "time_filter_type": getattr(rule, 'time_filter_type', 'after_start'),
                    "start_time": rule.start_time.isoformat() if rule.start_time else None,
                    "end_time": rule.end_time.isoformat() if rule.end_time else None,
                    
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
                    "keywords": [{"word": kw.word, "mode": kw.mode} for kw in rule.keywords] if rule.keywords else [],
                    "replace_rules": [{"pattern": rr.pattern, "replacement": rr.replacement} for rr in rule.replace_rules] if rule.replace_rules else []
                }
                
                return JSONResponse(content={
                    "success": True,
                    "rule": rule_dict
                })
            except Exception as e:
                logger.error(f"获取规则详情失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取规则详情失败: {str(e)}"
                }, status_code=500)

        @app.put("/api/rules/{rule_id}")
        async def update_rule(rule_id: int, request: Request):
            """更新规则"""
            try:
                data = await request.json()
                from services import ForwardRuleService
                
                # 获取现有规则
                existing_rule = await ForwardRuleService.get_rule_by_id(rule_id)
                if not existing_rule:
                    return JSONResponse(content={
                        "success": False,
                        "message": "规则不存在"
                    }, status_code=404)
                
                # 过滤掉不应该更新的字段
                allowed_fields = {
                    'name', 'source_chat_id', 'source_chat_name', 'target_chat_id', 'target_chat_name',
                    'is_active', 'enable_keyword_filter', 'enable_regex_replace', 'client_id', 'client_type',
                    'enable_text', 'enable_media', 'enable_photo', 'enable_video', 'enable_document',
                    'enable_audio', 'enable_voice', 'enable_sticker', 'enable_animation', 'enable_webpage',
                    'forward_delay', 'max_message_length', 'enable_link_preview', 'time_filter_type',
                    'start_time', 'end_time'
                }
                update_data = {k: v for k, v in data.items() if k in allowed_fields}
                
                # 检查是否是激活规则的操作（基于更新前的状态）
                is_activating = (
                    'is_active' in update_data and 
                    update_data['is_active'] is True and 
                    existing_rule.is_active is False
                )
                
                # 调试日志
                logger.info(f"规则更新调试 - rule_id: {rule_id}")
                logger.info(f"  - 原始请求数据: {data}")
                logger.info(f"  - 过滤后更新数据: {update_data}")
                logger.info(f"  - 现有规则状态: is_active={existing_rule.is_active}")
                logger.info(f"  - 是否激活操作: {is_activating}")
                
                # 更新规则
                success = await ForwardRuleService.update_rule(rule_id, **update_data)
                
                if not success:
                    return JSONResponse(content={
                        "success": False,
                        "message": "更新规则失败"
                    }, status_code=500)
                
                # 获取更新后的规则
                updated_rule = await ForwardRuleService.get_rule_by_id(rule_id)
                
                # 如果是激活规则且enhanced_bot存在，触发历史消息转发
                if is_activating and enhanced_bot:
                    try:
                        # 获取最近24小时内的历史消息进行转发
                        await enhanced_bot.forward_history_messages(rule_id, hours=24)
                        logger.info(f"规则 {rule_id} 激活，已触发历史消息转发")
                    except Exception as history_error:
                        logger.warning(f"历史消息转发失败: {history_error}")
                        # 不影响规则更新的成功响应
                
                return JSONResponse(content={
                    "success": True,
                    "rule": {
                        "id": updated_rule.id,
                        "name": updated_rule.name,
                        "source_chat_id": updated_rule.source_chat_id,
                        "source_chat_name": updated_rule.source_chat_name,
                        "target_chat_id": updated_rule.target_chat_id,
                        "target_chat_name": updated_rule.target_chat_name,
                        "is_active": updated_rule.is_active,
                        "enable_keyword_filter": updated_rule.enable_keyword_filter,
                        "enable_regex_replace": getattr(updated_rule, 'enable_regex_replace', False),
                        "client_id": getattr(updated_rule, 'client_id', 'main_user'),
                        "client_type": getattr(updated_rule, 'client_type', 'user'),
                        
                        # 消息类型过滤
                        "enable_text": getattr(updated_rule, 'enable_text', True),
                        "enable_photo": getattr(updated_rule, 'enable_photo', True),
                        "enable_video": getattr(updated_rule, 'enable_video', True),
                        "enable_document": getattr(updated_rule, 'enable_document', True),
                        "enable_audio": getattr(updated_rule, 'enable_audio', True),
                        "enable_voice": getattr(updated_rule, 'enable_voice', True),
                        "enable_sticker": getattr(updated_rule, 'enable_sticker', False),
                        "enable_animation": getattr(updated_rule, 'enable_animation', True),
                        "enable_webpage": getattr(updated_rule, 'enable_webpage', True),
                        
                        # 高级设置
                        "forward_delay": getattr(updated_rule, 'forward_delay', 0),
                        "max_message_length": getattr(updated_rule, 'max_message_length', 4096),
                        "enable_link_preview": getattr(updated_rule, 'enable_link_preview', True),
                        
                        # 时间过滤
                        "time_filter_type": getattr(updated_rule, 'time_filter_type', 'after_start'),
                        "start_time": updated_rule.start_time.isoformat() if updated_rule.start_time else None,
                        "end_time": updated_rule.end_time.isoformat() if updated_rule.end_time else None,
                        
                        "created_at": updated_rule.created_at.isoformat() if updated_rule.created_at else None,
                        "updated_at": updated_rule.updated_at.isoformat() if updated_rule.updated_at else None
                    } if updated_rule else None,
                    "message": "规则更新成功"
                })
            except Exception as e:
                logger.error(f"更新规则失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"更新规则失败: {str(e)}"
                }, status_code=500)

        @app.delete("/api/rules/{rule_id}")
        async def delete_rule(rule_id: int):
            """删除规则"""
            try:
                from services import ForwardRuleService
                
                # 检查规则是否存在
                existing_rule = await ForwardRuleService.get_rule_by_id(rule_id)
                if not existing_rule:
                    return JSONResponse(content={
                        "success": False,
                        "message": "规则不存在"
                    }, status_code=404)
                
                # 删除规则
                success = await ForwardRuleService.delete_rule(rule_id)
                
                if not success:
                    return JSONResponse(content={
                        "success": False,
                        "message": "删除规则失败"
                    }, status_code=500)
                
                return JSONResponse(content={
                    "success": True,
                    "message": "规则删除成功"
                })
            except Exception as e:
                logger.error(f"删除规则失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"删除规则失败: {str(e)}"
                }, status_code=500)
        
        @app.get("/api/chats")
        async def get_chats():
            """获取聊天列表"""
            try:
                # 从增强版机器人获取聊天列表
                if enhanced_bot and enhanced_bot.multi_client_manager:
                    all_chats = []
                    clients_info = []
                    
                    for client_id, client_wrapper in enhanced_bot.multi_client_manager.clients.items():
                        if client_wrapper.connected:
                            try:
                                # 使用线程安全方法获取聊天列表
                                client_chats = client_wrapper.get_chats_sync()
                                all_chats.extend(client_chats)
                                
                                # 收集客户端信息
                                client_info = {
                                    "client_id": client_id,
                                    "client_type": client_wrapper.client_type,
                                    "chat_count": len(client_chats),
                                    "display_name": client_chats[0]["client_display_name"] if client_chats else f"{client_wrapper.client_type}: {client_id}"
                                }
                                clients_info.append(client_info)
                                
                            except Exception as e:
                                logger.warning(f"获取客户端 {client_id} 聊天列表失败: {e}")
                                continue
                    
                    # 按客户端分组聊天
                    chats_by_client = {}
                    for chat in all_chats:
                        client_id = chat["client_id"]
                        if client_id not in chats_by_client:
                            chats_by_client[client_id] = []
                        chats_by_client[client_id].append(chat)
                    
                    return JSONResponse(content={
                        "success": True,
                        "chats": all_chats,
                        "chats_by_client": chats_by_client,
                        "clients_info": clients_info,
                        "total_chats": len(all_chats),
                        "connected_clients": len(clients_info)
                    })
                else:
                    return JSONResponse(content={
                        "success": True,
                        "chats": [],
                        "chats_by_client": {},
                        "clients_info": [],
                        "total_chats": 0,
                        "connected_clients": 0
                    })
            except Exception as e:
                logger.error(f"获取聊天列表失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取聊天列表失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/refresh-chats")
        async def refresh_chats():
            """刷新聊天列表"""
            try:
                # 在增强模式下，聊天列表是实时的，无需特别刷新
                return JSONResponse(content={
                    "success": True,
                    "message": "聊天列表已刷新",
                    "updated_count": 0
                })
            except Exception as e:
                logger.error(f"刷新聊天列表失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"刷新聊天列表失败: {str(e)}"
                }, status_code=500)
        
        @app.get("/api/logs")
        async def get_logs(page: int = 1, limit: int = 20, status: str = None, 
                          date: str = None, start_date: str = None, end_date: str = None):
            """获取日志列表"""
            try:
                from models import MessageLog
                from sqlalchemy import desc, select, and_, func
                from database import get_db
                from datetime import datetime, date as date_type
                
                async for db in get_db():
                    # 构建查询
                    query = select(MessageLog)
                    
                    # 状态过滤
                    if status:
                        query = query.where(MessageLog.status == status)
                    
                    # 日期过滤
                    if date:
                        # 单日期筛选
                        try:
                            target_date = datetime.strptime(date, '%Y-%m-%d').date()
                            query = query.where(func.date(MessageLog.created_at) == target_date)
                        except ValueError:
                            logger.warning(f"无效的日期格式: {date}")
                    
                    elif start_date or end_date:
                        # 日期范围筛选
                        date_conditions = []
                        if start_date:
                            try:
                                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                                date_conditions.append(func.date(MessageLog.created_at) >= start_dt)
                            except ValueError:
                                logger.warning(f"无效的开始日期格式: {start_date}")
                        
                        if end_date:
                            try:
                                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                                date_conditions.append(func.date(MessageLog.created_at) <= end_dt)
                            except ValueError:
                                logger.warning(f"无效的结束日期格式: {end_date}")
                        
                        if date_conditions:
                            query = query.where(and_(*date_conditions))
                    
                    # 排序（最新的在前）
                    query = query.order_by(desc(MessageLog.created_at))
                    
                    # 分页
                    offset = (page - 1) * limit
                    paginated_query = query.offset(offset).limit(limit)
                    
                    # 执行查询，预加载规则信息
                    from sqlalchemy.orm import joinedload
                    paginated_query = paginated_query.options(joinedload(MessageLog.rule))
                    result = await db.execute(paginated_query)
                    logs = result.scalars().all()
                    
                    # 获取总数
                    count_query = select(MessageLog)
                    if status:
                        count_query = count_query.where(MessageLog.status == status)
                    count_result = await db.execute(count_query)
                    total = len(count_result.scalars().all())
                    
                    # 序列化日志数据
                    logs_data = []
                    for log in logs:
                        # 获取规则名称（通过预加载的关系）
                        rule_name = None
                        if log.rule and hasattr(log.rule, 'name'):
                            rule_name = log.rule.name
                        elif log.rule_id:
                            rule_name = f"规则 #{log.rule_id}"
                        
                        log_data = {
                            "id": log.id,
                            "rule_id": log.rule_id,
                            "rule_name": rule_name,
                            # 前端期望的字段名映射
                            "message_id": log.source_message_id,  # 前端期望 message_id
                            "forwarded_message_id": log.target_message_id,  # 前端期望 forwarded_message_id
                            "source_chat_id": log.source_chat_id,
                            "source_chat_name": log.source_chat_name,
                            "target_chat_id": log.target_chat_id,
                            "target_chat_name": log.target_chat_name,
                            "message_text": log.original_text,  # 前端期望 message_text
                            "message_type": log.media_type or 'text',  # 前端期望 message_type
                            "status": log.status,
                            "error_message": log.error_message,
                            "processing_time": log.processing_time,
                            "created_at": log.created_at.isoformat() if log.created_at else None
                        }
                        logs_data.append(log_data)
                    
                    return JSONResponse(content={
                        "success": True,
                        "items": logs_data,  # 前端期望 items 字段
                        "total": total,
                        "page": page,
                        "limit": limit
                    })
                    
            except Exception as e:
                logger.error(f"获取日志失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取日志失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/rules/update-chat-names")
        async def update_chat_names():
            """更新规则中的聊天名称"""
            try:
                from services import ForwardRuleService
                from database import get_db
                from models import ForwardRule
                from sqlalchemy import select, update
                
                # 获取所有规则
                rules = await ForwardRuleService.get_all_rules()
                updated_rules = []
                
                async for db in get_db():
                    for rule in rules:
                        updated_fields = {}
                        
                        # 尝试获取源聊天名称
                        if not rule.source_chat_name or rule.source_chat_name.strip() == '':
                            try:
                                # 这里需要从Telegram客户端获取聊天信息
                                # 暂时使用聊天ID作为占位符，实际应该调用Telegram API
                                source_name = f"聊天 {rule.source_chat_id}"
                                updated_fields['source_chat_name'] = source_name
                                logger.info(f"🔄 更新源聊天名称: {rule.source_chat_id} -> {source_name}")
                            except Exception as e:
                                logger.warning(f"⚠️ 无法获取源聊天 {rule.source_chat_id} 的名称: {e}")
                        
                        # 尝试获取目标聊天名称
                        if not rule.target_chat_name or rule.target_chat_name.strip() == '':
                            try:
                                # 这里需要从Telegram客户端获取聊天信息
                                # 暂时使用聊天ID作为占位符，实际应该调用Telegram API
                                target_name = f"聊天 {rule.target_chat_id}"
                                updated_fields['target_chat_name'] = target_name
                                logger.info(f"🔄 更新目标聊天名称: {rule.target_chat_id} -> {target_name}")
                            except Exception as e:
                                logger.warning(f"⚠️ 无法获取目标聊天 {rule.target_chat_id} 的名称: {e}")
                        
                        # 如果有字段需要更新
                        if updated_fields:
                            await db.execute(
                                update(ForwardRule)
                                .where(ForwardRule.id == rule.id)
                                .values(**updated_fields)
                            )
                            updated_rules.append({
                                "rule_id": rule.id,
                                "rule_name": rule.name,
                                "updates": updated_fields
                            })
                    
                    await db.commit()
                    break
                
                logger.info(f"✅ 聊天名称更新完成: 更新了 {len(updated_rules)} 个规则")
                
                return JSONResponse(content={
                    "success": True,
                    "message": f"聊天名称更新完成，更新了 {len(updated_rules)} 个规则",
                    "updated_rules": updated_rules
                })
                
            except Exception as e:
                logger.error(f"❌ 更新聊天名称失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"更新失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/rules/fetch-chat-info")
        async def fetch_chat_info():
            """从Telegram获取真实的聊天信息"""
            try:
                from services import ForwardRuleService
                from database import get_db
                from models import ForwardRule
                from sqlalchemy import select, update
                
                # 检查是否有可用的Telegram客户端
                if not enhanced_bot or not hasattr(enhanced_bot, 'multi_client_manager'):
                    return JSONResponse(content={
                        "success": False,
                        "message": "Telegram客户端未配置，无法获取聊天信息"
                    }, status_code=400)
                
                client_manager = enhanced_bot.multi_client_manager
                if not client_manager or not client_manager.client_wrappers:
                    return JSONResponse(content={
                        "success": False,
                        "message": "没有可用的Telegram客户端"
                    }, status_code=400)
                
                # 获取第一个可用的客户端
                client_wrapper = next(iter(client_manager.client_wrappers.values()))
                
                rules = await ForwardRuleService.get_all_rules()
                updated_rules = []
                
                async for db in get_db():
                    for rule in rules:
                        updated_fields = {}
                        
                        try:
                            # 获取源聊天信息
                            if rule.source_chat_id and (not rule.source_chat_name or rule.source_chat_name.strip() == ''):
                                try:
                                    source_entity = await client_wrapper.client.get_entity(int(rule.source_chat_id))
                                    # 优先使用 title 字段，这是最通用的名称字段
                                    if hasattr(source_entity, 'title') and source_entity.title:
                                        source_name = source_entity.title
                                    elif hasattr(source_entity, 'username') and source_entity.username:
                                        source_name = f"@{source_entity.username}"
                                    elif hasattr(source_entity, 'first_name') and source_entity.first_name:
                                        last_name = getattr(source_entity, 'last_name', '')
                                        source_name = f"{source_entity.first_name} {last_name}".strip()
                                    else:
                                        source_name = f"聊天 {rule.source_chat_id}"
                                    
                                    updated_fields['source_chat_name'] = source_name
                                    logger.info(f"🔄 获取到源聊天名称: {rule.source_chat_id} -> {source_name}")
                                except Exception as e:
                                    logger.warning(f"⚠️ 无法获取源聊天 {rule.source_chat_id} 的信息: {e}")
                            
                            # 获取目标聊天信息
                            if rule.target_chat_id and (not rule.target_chat_name or rule.target_chat_name.strip() == ''):
                                try:
                                    target_entity = await client_wrapper.client.get_entity(int(rule.target_chat_id))
                                    # 优先使用 title 字段，这是最通用的名称字段
                                    if hasattr(target_entity, 'title') and target_entity.title:
                                        target_name = target_entity.title
                                    elif hasattr(target_entity, 'username') and target_entity.username:
                                        target_name = f"@{target_entity.username}"
                                    elif hasattr(target_entity, 'first_name') and target_entity.first_name:
                                        last_name = getattr(target_entity, 'last_name', '')
                                        target_name = f"{target_entity.first_name} {last_name}".strip()
                                    else:
                                        target_name = f"聊天 {rule.target_chat_id}"
                                    
                                    updated_fields['target_chat_name'] = target_name
                                    logger.info(f"🔄 获取到目标聊天名称: {rule.target_chat_id} -> {target_name}")
                                except Exception as e:
                                    logger.warning(f"⚠️ 无法获取目标聊天 {rule.target_chat_id} 的信息: {e}")
                            
                            # 如果有字段需要更新
                            if updated_fields:
                                await db.execute(
                                    update(ForwardRule)
                                    .where(ForwardRule.id == rule.id)
                                    .values(**updated_fields)
                                )
                                updated_rules.append({
                                    "rule_id": rule.id,
                                    "rule_name": rule.name,
                                    "updates": updated_fields
                                })
                        
                        except Exception as e:
                            logger.error(f"❌ 处理规则 {rule.id} 时出错: {e}")
                            continue
                    
                    await db.commit()
                    break
                
                logger.info(f"✅ 从Telegram获取聊天名称完成: 更新了 {len(updated_rules)} 个规则")
                
                return JSONResponse(content={
                    "success": True,
                    "message": f"从Telegram获取聊天名称完成，更新了 {len(updated_rules)} 个规则",
                    "updated_rules": updated_rules
                })
                
            except Exception as e:
                logger.error(f"❌ 从Telegram获取聊天信息失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/logs/fix-rule-association")
        async def fix_rule_association():
            """修复规则和消息日志的关联关系 - 添加规则名称字段"""
            try:
                from database import get_db
                from models import MessageLog, ForwardRule
                from sqlalchemy import select, delete, func, text, update
                
                async for db in get_db():
                    # 1. 检查是否已有 rule_name 字段
                    try:
                        await db.execute(text("SELECT rule_name FROM message_logs LIMIT 1"))
                        has_rule_name_column = True
                        logger.info("🔧 rule_name 字段已存在")
                    except Exception:
                        has_rule_name_column = False
                        logger.info("🔧 需要添加 rule_name 字段")
                    
                    # 2. 如果没有 rule_name 字段，则添加
                    if not has_rule_name_column:
                        await db.execute(text("ALTER TABLE message_logs ADD COLUMN rule_name VARCHAR(100)"))
                        logger.info("✅ 已添加 rule_name 字段")
                    
                    # 3. 获取当前所有规则的ID和名称映射
                    current_rules = await db.execute(select(ForwardRule.id, ForwardRule.name))
                    rule_mapping = {rule[0]: rule[1] for rule in current_rules.fetchall()}
                    
                    logger.info(f"🔧 当前规则映射: {rule_mapping}")
                    
                    # 4. 更新现有日志的 rule_name
                    for rule_id, rule_name in rule_mapping.items():
                        update_result = await db.execute(
                            update(MessageLog)
                            .where(MessageLog.rule_id == rule_id)
                            .values(rule_name=rule_name)
                        )
                        logger.info(f"🔧 更新规则ID {rule_id} 的日志名称为 '{rule_name}': {update_result.rowcount} 条")
                    
                    # 5. 删除孤立的消息日志（rule_id不在当前规则表中）
                    valid_rule_ids = list(rule_mapping.keys())
                    delete_result = await db.execute(
                        delete(MessageLog).where(~MessageLog.rule_id.in_(valid_rule_ids))
                    )
                    deleted_count = delete_result.rowcount
                    
                    await db.commit()
                    
                    logger.info(f"✅ 修复完成: 删除了 {deleted_count} 条孤立的消息日志")
                    
                    return JSONResponse(content={
                        "success": True,
                        "message": f"修复完成，添加了rule_name字段并删除了 {deleted_count} 条孤立日志",
                        "deleted_count": deleted_count,
                        "rule_mapping": rule_mapping,
                        "added_rule_name_column": not has_rule_name_column
                    })
                    
            except Exception as e:
                logger.error(f"❌ 修复规则关联失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"修复失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/logs/batch-delete")
        async def batch_delete_logs(request: Request):
            """批量删除日志"""
            try:
                data = await request.json()
                ids = data.get('ids', [])
                
                if not ids:
                    return JSONResponse(content={
                        "success": False,
                        "message": "未提供要删除的日志ID"
                    }, status_code=400)
                
                from models import MessageLog
                from database import get_db
                from sqlalchemy import select, delete
                
                async for db in get_db():
                    # 验证日志是否存在
                    existing_logs = await db.execute(
                        select(MessageLog.id).where(MessageLog.id.in_(ids))
                    )
                    existing_ids = [row[0] for row in existing_logs.fetchall()]
                    
                    if not existing_ids:
                        return JSONResponse(content={
                            "success": False,
                            "message": "未找到要删除的日志"
                        }, status_code=404)
                    
                    # 记录删除前的日志信息
                    logs_to_delete = await db.execute(
                        select(MessageLog.id, MessageLog.source_message_id, MessageLog.source_chat_id, 
                               MessageLog.rule_id, MessageLog.status).where(MessageLog.id.in_(existing_ids))
                    )
                    deleted_logs_info = logs_to_delete.fetchall()
                    
                    # 批量删除
                    delete_query = delete(MessageLog).where(MessageLog.id.in_(existing_ids))
                    result = await db.execute(delete_query)
                    await db.commit()
                    
                    logger.info(f"批量删除了 {result.rowcount} 条日志")
                    for log_info in deleted_logs_info:
                        logger.info(f"🗑️ 删除日志: ID={log_info[0]}, 消息ID={log_info[1]}, 源聊天={log_info[2]}, 规则ID={log_info[3]}, 状态={log_info[4]}")
                    
                    return JSONResponse(content={
                        "success": True,
                        "message": f"成功删除 {result.rowcount} 条日志",
                        "deleted_count": result.rowcount
                    })
                    
            except Exception as e:
                logger.error(f"批量删除日志失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"删除失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/logs/clear")
        async def clear_logs(request: Request):
            """清空日志（支持过滤条件）"""
            try:
                data = await request.json()
                
                from models import MessageLog
                from database import get_db
                from sqlalchemy import delete, and_, func
                from datetime import datetime
                
                async for db in get_db():
                    # 构建删除条件
                    conditions = []
                    
                    # 状态过滤
                    if data.get('status'):
                        conditions.append(MessageLog.status == data['status'])
                    
                    # 日期过滤
                    if data.get('date'):
                        try:
                            target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                            conditions.append(func.date(MessageLog.created_at) == target_date)
                        except ValueError:
                            logger.warning(f"无效的日期格式: {data['date']}")
                    
                    elif data.get('start_date') or data.get('end_date'):
                        if data.get('start_date'):
                            try:
                                start_dt = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                                conditions.append(func.date(MessageLog.created_at) >= start_dt)
                            except ValueError:
                                pass
                        
                        if data.get('end_date'):
                            try:
                                end_dt = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                                conditions.append(func.date(MessageLog.created_at) <= end_dt)
                            except ValueError:
                                pass
                    
                    # 执行删除
                    delete_query = delete(MessageLog)
                    if conditions:
                        delete_query = delete_query.where(and_(*conditions))
                    
                    result = await db.execute(delete_query)
                    await db.commit()
                    
                    logger.info(f"清空了 {result.rowcount} 条日志")
                    
                    return JSONResponse(content={
                        "success": True,
                        "message": f"成功清空 {result.rowcount} 条日志",
                        "deleted_count": result.rowcount
                    })
                    
            except Exception as e:
                logger.error(f"清空日志失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"清空失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/clients")
        async def add_client(request: Request):
            """添加新客户端"""
            try:
                data = await request.json()
                client_id = data.get('client_id')
                client_type = data.get('client_type')
                
                if not client_id or not client_type:
                    return JSONResponse(content={
                        "success": False,
                        "message": "客户端ID和类型不能为空"
                    }, status_code=400)
                
                if client_type not in ['user', 'bot']:
                    return JSONResponse(content={
                        "success": False,
                        "message": "客户端类型必须是 user 或 bot"
                    }, status_code=400)
                
                # 验证机器人客户端必需字段
                if client_type == 'bot':
                    bot_token = data.get('bot_token')
                    admin_user_id = data.get('admin_user_id')
                    
                    if not bot_token:
                        return JSONResponse(content={
                            "success": False,
                            "message": "机器人客户端必须提供Bot Token"
                        }, status_code=400)
                    
                    if not admin_user_id:
                        return JSONResponse(content={
                            "success": False,
                            "message": "机器人客户端必须提供管理员用户ID"
                        }, status_code=400)
                
                # 验证用户客户端必需字段
                elif client_type == 'user':
                    api_id = data.get('api_id')
                    api_hash = data.get('api_hash')
                    phone = data.get('phone')
                    
                    if not api_id:
                        return JSONResponse(content={
                            "success": False,
                            "message": "用户客户端必须提供API ID"
                        }, status_code=400)
                    
                    if not api_hash:
                        return JSONResponse(content={
                            "success": False,
                            "message": "用户客户端必须提供API Hash"
                        }, status_code=400)
                    
                    if not phone:
                        return JSONResponse(content={
                            "success": False,
                            "message": "用户客户端必须提供手机号"
                        }, status_code=400)
                
                if enhanced_bot:
                    # 传递配置参数给客户端管理器
                    client = enhanced_bot.multi_client_manager.add_client_with_config(
                        client_id, 
                        client_type,
                        config_data=data  # 传递完整的配置数据
                    )
                    
                    # 如果是用户客户端，需要验证码登录流程
                    if client_type == 'user':
                        return JSONResponse(content={
                            "success": True,
                            "message": f"用户客户端 {client_id} 添加成功，请准备接收验证码",
                            "need_verification": True,
                            "client_id": client_id
                        })
                    else:
                        return JSONResponse(content={
                            "success": True,
                            "message": f"机器人客户端 {client_id} 添加成功"
                        })
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "增强版客户端管理器不可用"
                    }, status_code=400)
            except Exception as e:
                logger.error(f"添加客户端失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"添加客户端失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/clients/{client_id}/start")
        async def start_client(client_id: str):
            """启动客户端"""
            try:
                if enhanced_bot:
                    success = enhanced_bot.multi_client_manager.start_client(client_id)
                    if success:
                        return JSONResponse(content={
                            "success": True,
                            "message": f"客户端 {client_id} 启动成功"
                        })
                    else:
                        return JSONResponse(content={
                            "success": False,
                            "message": f"客户端 {client_id} 启动失败"
                        }, status_code=400)
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "增强版客户端管理器不可用"
                    }, status_code=400)
            except Exception as e:
                logger.error(f"启动客户端失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"启动客户端失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/clients/{client_id}/stop")
        async def stop_client(client_id: str):
            """停止客户端"""
            try:
                if enhanced_bot:
                    success = enhanced_bot.multi_client_manager.stop_client(client_id)
                    if success:
                        return JSONResponse(content={
                            "success": True,
                            "message": f"客户端 {client_id} 停止成功"
                        })
                    else:
                        return JSONResponse(content={
                            "success": False,
                            "message": f"客户端 {client_id} 不存在或已停止"
                        }, status_code=400)
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "增强版客户端管理器不可用"
                    }, status_code=400)
            except Exception as e:
                logger.error(f"停止客户端失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"停止客户端失败: {str(e)}"
                }, status_code=500)
        
        @app.delete("/api/clients/{client_id}")
        async def remove_client(client_id: str):
            """删除客户端"""
            try:
                if enhanced_bot:
                    success = enhanced_bot.multi_client_manager.remove_client(client_id)
                    if success:
                        return JSONResponse(content={
                            "success": True,
                            "message": f"客户端 {client_id} 删除成功"
                        })
                    else:
                        return JSONResponse(content={
                            "success": False,
                            "message": f"客户端 {client_id} 不存在或删除失败"
                        }, status_code=400)
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "增强版客户端管理器不可用"
                    }, status_code=400)
            except Exception as e:
                logger.error(f"删除客户端失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"删除客户端失败: {str(e)}"
                }, status_code=500)
        
        # 系统设置API
        @app.get("/api/settings")
        async def get_settings():
            """获取系统设置"""
            try:
                from config import Config
                
                # 返回当前配置
                settings = {
                    "api_id": getattr(Config, 'API_ID', ''),
                    "api_hash": getattr(Config, 'API_HASH', ''),
                    "bot_token": getattr(Config, 'BOT_TOKEN', ''),
                    "phone_number": getattr(Config, 'PHONE_NUMBER', ''),
                    "admin_user_ids": getattr(Config, 'ADMIN_USER_IDS', ''),
                    "enable_proxy": getattr(Config, 'ENABLE_PROXY', False),
                    "proxy_type": getattr(Config, 'PROXY_TYPE', 'http'),
                    "proxy_host": getattr(Config, 'PROXY_HOST', '127.0.0.1'),
                    "proxy_port": getattr(Config, 'PROXY_PORT', '7890'),
                    "proxy_username": getattr(Config, 'PROXY_USERNAME', ''),
                    "proxy_password": "***" if getattr(Config, 'PROXY_PASSWORD', '') else '',
                    "enable_log_cleanup": getattr(Config, 'ENABLE_LOG_CLEANUP', False),
                    "log_retention_days": getattr(Config, 'LOG_RETENTION_DAYS', '30'),
                    "log_cleanup_time": getattr(Config, 'LOG_CLEANUP_TIME', '02:00'),
                    "max_log_size": getattr(Config, 'MAX_LOG_SIZE', '100'),
                }
                
                return JSONResponse(content={
                    "success": True,
                    "config": settings
                })
            except Exception as e:
                logger.error(f"获取设置失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取设置失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/settings")
        async def save_settings(request: Request):
            """保存系统设置"""
            try:
                data = await request.json()
                
                # 构建新的配置内容
                config_lines = []
                
                # Telegram配置
                config_lines.append("# Telegram API配置")
                config_lines.append(f"API_ID={data.get('api_id', '')}")
                config_lines.append(f"API_HASH={data.get('api_hash', '')}")
                config_lines.append(f"BOT_TOKEN={data.get('bot_token', '')}")
                config_lines.append(f"PHONE_NUMBER={data.get('phone_number', '')}")
                config_lines.append(f"ADMIN_USER_IDS={data.get('admin_user_ids', '')}")
                config_lines.append("")
                
                # 代理配置
                config_lines.append("# 代理配置")
                config_lines.append(f"ENABLE_PROXY={str(data.get('enable_proxy', False)).lower()}")
                config_lines.append(f"PROXY_TYPE={data.get('proxy_type', 'http')}")
                config_lines.append(f"PROXY_HOST={data.get('proxy_host', '127.0.0.1')}")
                config_lines.append(f"PROXY_PORT={data.get('proxy_port', '7890')}")
                config_lines.append(f"PROXY_USERNAME={data.get('proxy_username', '')}")
                if data.get('proxy_password') and data.get('proxy_password') != '***':
                    config_lines.append(f"PROXY_PASSWORD={data.get('proxy_password', '')}")
                config_lines.append("")
                
                # 日志管理配置
                config_lines.append("# 日志管理配置")
                config_lines.append(f"ENABLE_LOG_CLEANUP={str(data.get('enable_log_cleanup', False)).lower()}")
                config_lines.append(f"LOG_RETENTION_DAYS={data.get('log_retention_days', '30')}")
                config_lines.append(f"LOG_CLEANUP_TIME={data.get('log_cleanup_time', '02:00')}")
                config_lines.append(f"MAX_LOG_SIZE={data.get('max_log_size', '100')}")
                config_lines.append("")
                
                # 写入配置文件
                config_content = '\n'.join(config_lines)
                
                # 确保config目录存在
                import os
                from pathlib import Path
                os.makedirs('config', exist_ok=True)
                
                # 写入到持久化配置文件
                config_files_to_write = [
                    Path("config/app.config"),  # 持久化配置文件
                    Path("app.config")          # 兼容性配置文件
                ]
                
                success_count = 0
                errors = []
                
                for config_file in config_files_to_write:
                    try:
                        config_file.write_text(config_content, encoding='utf-8')
                        os.chmod(config_file, 0o644)
                        success_count += 1
                        logger.info(f"✅ 配置已写入: {config_file}")
                    except Exception as e:
                        error_msg = f"写入配置文件 {config_file} 失败: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                if success_count > 0:
                    # 重新加载配置以确保立即生效
                    try:
                        from config import Config
                        Config.reload()
                        logger.info("✅ 配置重新加载成功")
                    except Exception as e:
                        logger.error(f"⚠️ 配置重新加载失败: {e}")
                    
                    return JSONResponse(content={
                        "success": True,
                        "message": f"设置已保存到 {success_count} 个配置文件",
                        "files_written": success_count,
                        "errors": errors if errors else None
                    })
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "所有配置文件写入失败",
                        "errors": errors
                    }, status_code=500)
                    
            except Exception as e:
                logger.error(f"保存设置失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"保存设置失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/telegram/restart-client")
        async def restart_telegram_client(request: Request):
            """重启Telegram客户端以应用新配置"""
            try:
                # 重新加载配置
                try:
                    from config import Config
                    Config.reload()
                    logger.info("✅ 配置重新加载完成")
                except Exception as reload_error:
                    logger.warning(f"⚠️ 配置重新加载失败，但继续重启: {reload_error}")
                
                # 验证新配置（允许跳过验证失败继续重启）
                config_valid = True
                try:
                    from config import validate_config
                    validate_config()
                    logger.info("✅ 新配置验证通过")
                except ValueError as config_error:
                    logger.warning(f"⚠️ 配置验证失败，但仍允许重启: {config_error}")
                    config_valid = False
                
                # 重启或启动Telegram客户端
                if enhanced_bot:
                    if hasattr(enhanced_bot, 'multi_client_manager') and enhanced_bot.multi_client_manager:
                        # 如果客户端管理器已存在，重启客户端
                        if hasattr(enhanced_bot.multi_client_manager, 'restart_clients'):
                            await enhanced_bot.multi_client_manager.restart_clients()
                            logger.info("✅ Telegram客户端重启完成")
                        else:
                            # 重新初始化客户端管理器
                            await enhanced_bot.start(web_mode=True)
                            logger.info("✅ Telegram客户端重新初始化完成")
                    else:
                        # 如果之前是Web-only模式，现在启动Telegram客户端
                        await enhanced_bot.start(web_mode=True)
                        logger.info("✅ Telegram客户端首次启动完成")
                    
                    if config_valid:
                        return JSONResponse(content={
                            "success": True,
                            "message": "Telegram客户端重启成功，新配置已生效"
                        })
                    else:
                        return JSONResponse(content={
                            "success": True,
                            "message": "客户端重启成功，但配置可能不完整。请在客户端管理页面完成配置"
                        })
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "增强版机器人未初始化"
                    }, status_code=400)
                
            except Exception as e:
                logger.error(f"❌ 重启Telegram客户端失败: {str(e)}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"重启失败: {str(e)}"
                }, status_code=500)
        
        @app.post("/api/clients/{client_id}/login")
        async def client_login(client_id: str, request: Request):
            """用户客户端登录流程"""
            try:
                data = await request.json()
                step = data.get('step')  # 'send_code', 'submit_code', 'submit_password'
                
                if not enhanced_bot:
                    return JSONResponse(content={
                        "success": False,
                        "message": "增强版客户端管理器不可用"
                    }, status_code=400)
                
                client_manager = enhanced_bot.multi_client_manager.clients.get(client_id)
                if not client_manager:
                    return JSONResponse(content={
                        "success": False,
                        "message": f"客户端 {client_id} 不存在"
                    }, status_code=404)
                
                if client_manager.client_type != 'user':
                    return JSONResponse(content={
                        "success": False,
                        "message": "只有用户客户端支持验证码登录"
                    }, status_code=400)
                
                if step == 'send_code':
                    # 发送验证码
                    result = await client_manager.send_verification_code()
                    return JSONResponse(content=result)
                
                elif step == 'submit_code':
                    # 提交验证码
                    code = data.get('code')
                    if not code:
                        return JSONResponse(content={
                            "success": False,
                            "message": "验证码不能为空"
                        }, status_code=400)
                    
                    result = await client_manager.submit_verification_code(code)
                    return JSONResponse(content=result)
                
                elif step == 'submit_password':
                    # 提交二步验证密码
                    password = data.get('password')
                    if not password:
                        return JSONResponse(content={
                            "success": False,
                            "message": "密码不能为空"
                        }, status_code=400)
                    
                    result = await client_manager.submit_password(password)
                    return JSONResponse(content=result)
                
                else:
                    return JSONResponse(content={
                        "success": False,
                        "message": "无效的登录步骤"
                    }, status_code=400)
                
            except Exception as e:
                logger.error(f"客户端登录失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"客户端登录失败: {str(e)}"
                }, status_code=500)
        
        # React前端路由
        from fastapi import Request
        from fastapi.responses import HTMLResponse
        
        @app.get("/")
        async def serve_react_root():
            """服务React应用根路径"""
            if frontend_dist.exists():
                index_file = frontend_dist / "index.html"
                if index_file.exists():
                    with open(index_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return HTMLResponse(content=content)
            return HTMLResponse(content="<h1>增强版机器人Web界面</h1><p>React前端未构建，请运行 cd frontend && npm run build</p>")
        
        @app.get("/{path:path}")
        async def serve_react_spa(path: str):
            """服务React应用 - SPA路由"""
            # 排除API路径
            if path.startswith('api/'):
                return JSONResponse(content={"detail": "API路径不存在"}, status_code=404)
                
            if frontend_dist.exists():
                index_file = frontend_dist / "index.html"
                if index_file.exists():
                    with open(index_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return HTMLResponse(content=content)
            return HTMLResponse(content="<h1>增强版机器人Web界面</h1><p>React前端未构建</p>")
        
        # 启动Web服务器
        logger.info(f"🌐 启动Web服务器: http://0.0.0.0:{Config.WEB_PORT}")
        logger.info("💡 功能说明:")
        logger.info(f"   - React前端: http://localhost:{Config.WEB_PORT}")
        logger.info("   - 客户端管理: /api/clients")
        logger.info("   - 系统状态: /api/system/enhanced-status")
        
        # 返回app实例以便外部启动
        return app
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        # 创建应用实例
        app = asyncio.run(main())
        
        if app:
            # 启动Web服务器
            import uvicorn
            from config import Config
            uvicorn.run(
                app,
                host=Config.WEB_HOST,
                port=Config.WEB_PORT,
                log_level="info"
            )
    except KeyboardInterrupt:
        logger.info("👋 程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
