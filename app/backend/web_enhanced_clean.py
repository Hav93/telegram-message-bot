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

# 设置日志 - 使用统一的日志轮转机制
from log_manager import get_logger
logger = get_logger('web', 'web_enhanced_clean.log')

async def auto_database_migration(enhanced_bot=None):
    """自动数据库迁移和修复"""
    try:
        from database import get_db
        from models import MessageLog, ForwardRule
        from sqlalchemy import select, delete, func, text, update
        
        logger.info("🔧 开始自动数据库迁移...")
        
        async for db in get_db():
            # 0. 首先检查表是否存在
            try:
                await db.execute(text("SELECT 1 FROM message_logs LIMIT 1"))
                table_exists = True
                logger.info("✅ message_logs 表已存在")
            except Exception:
                table_exists = False
                logger.info("⚠️ message_logs 表不存在，跳过迁移")
                # 如果表不存在，说明是全新安装，不需要迁移
                break
            
            # 1. 检查是否已有 rule_name 字段（仅在表存在时）
            if table_exists:
                try:
                    await db.execute(text("SELECT rule_name FROM message_logs LIMIT 1"))
                    has_rule_name_column = True
                    logger.info("✅ rule_name 字段已存在")
                except Exception:
                    has_rule_name_column = False
                    logger.info("🔧 需要添加 rule_name 字段")
            
            # 2. 如果表存在但没有 rule_name 字段，则添加
            if table_exists and not has_rule_name_column:
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
            elif table_exists:
                logger.info("✅ 数据库结构检查完成，无需迁移")
            else:
                logger.info("✅ 全新数据库安装，无需迁移")
            
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
                
                # 使用线程安全的方法获取真实聊天名称
                if client_wrapper and rule.source_chat_id:
                    try:
                        # 使用新的线程安全方法
                        source_title = client_wrapper.get_chat_title_sync(rule.source_chat_id)
                        if not source_title.startswith("聊天 "):
                            source_name = source_title
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
                
                # 使用线程安全的方法获取真实聊天名称
                if client_wrapper and rule.target_chat_id:
                    try:
                        # 使用新的线程安全方法
                        target_title = client_wrapper.get_chat_title_sync(rule.target_chat_id)
                        if not target_title.startswith("聊天 "):
                            target_name = target_title
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

async def auto_trigger_history_messages(enhanced_bot):
    """启动时自动检查激活的规则并触发历史消息转发"""
    try:
        from services import ForwardRuleService
        from datetime import datetime, timedelta
        from timezone_utils import get_user_now, database_time_to_user_time
        
        # 获取所有激活的规则
        active_rules = await ForwardRuleService.get_all_rules()
        activated_rules = [rule for rule in active_rules if rule.is_active]
        
        if not activated_rules:
            logger.info("📝 未找到任何激活的转发规则")
            return
            
        logger.info(f"📝 发现 {len(activated_rules)} 个激活的规则，开始根据时间过滤设置触发历史消息转发...")
        
        # 为每个激活的规则根据其时间过滤设置触发历史消息转发
        for rule in activated_rules:
            try:
                # 根据规则的时间过滤类型决定是否处理历史消息
                time_filter_type = getattr(rule, 'time_filter_type', 'after_start')
                
                if time_filter_type == 'after_start':
                    # 仅转发启动后的消息 - 不处理历史消息
                    logger.info(f"📝 规则 '{rule.name}' 设置为仅转发启动后消息，跳过历史消息处理")
                    continue
                    
                elif time_filter_type == 'today_only':
                    # 仅转发当天消息 - 从今天0点开始
                    logger.info(f"🔄 规则 '{rule.name}' 设置为仅转发当天消息，处理今日历史消息...")
                    await enhanced_bot.forward_history_messages(rule.id, hours=None)  # 让底层逻辑处理
                    
                elif time_filter_type == 'from_time':
                    # 从指定时间开始 - 根据start_time决定，不做时间限制
                    if hasattr(rule, 'start_time') and rule.start_time:
                        start_time = database_time_to_user_time(rule.start_time)
                        current_time = get_user_now()
                        hours_diff = (current_time - start_time).total_seconds() / 3600
                        
                        if hours_diff > 0:
                            logger.info(f"🔄 规则 '{rule.name}' 从指定时间开始，处理 {start_time.strftime('%Y-%m-%d %H:%M:%S')} 以来的所有历史消息...")
                            await enhanced_bot.forward_history_messages(rule.id, hours=int(hours_diff) + 1)  # 处理所有时间范围内的消息
                        else:
                            logger.info(f"📝 规则 '{rule.name}' 的开始时间在未来，跳过历史消息处理")
                    else:
                        logger.info(f"⚠️ 规则 '{rule.name}' 设置为从指定时间开始但未设置开始时间，处理最近24小时")
                        await enhanced_bot.forward_history_messages(rule.id, hours=24)
                        
                elif time_filter_type == 'time_range':
                    # 时间段过滤 - 根据start_time和end_time，不做时间限制
                    if hasattr(rule, 'start_time') and rule.start_time:
                        start_time = database_time_to_user_time(rule.start_time)
                        current_time = get_user_now()
                        hours_diff = (current_time - start_time).total_seconds() / 3600
                        
                        if hours_diff > 0:
                            logger.info(f"🔄 规则 '{rule.name}' 设置时间段过滤，处理指定时间段的所有历史消息...")
                            await enhanced_bot.forward_history_messages(rule.id, hours=int(hours_diff) + 1)  # 处理完整时间段的消息
                        else:
                            logger.info(f"📝 规则 '{rule.name}' 的时间段在未来，跳过历史消息处理")
                    else:
                        logger.info(f"⚠️ 规则 '{rule.name}' 设置为时间段过滤但未设置时间，处理最近24小时")
                        await enhanced_bot.forward_history_messages(rule.id, hours=24)
                        
                elif time_filter_type == 'all_messages':
                    # 所有消息 - 处理所有历史消息，不做时间限制
                    logger.info(f"🔄 规则 '{rule.name}' 设置为转发所有消息，处理所有可用的历史消息...")
                    await enhanced_bot.forward_history_messages(rule.id, hours=None)  # 不限制时间，让底层逻辑处理
                    
                else:
                    # 未知类型，默认处理最近24小时
                    logger.warning(f"⚠️ 规则 '{rule.name}' 有未知的时间过滤类型 '{time_filter_type}'，默认处理最近24小时")
                    await enhanced_bot.forward_history_messages(rule.id, hours=24)
                    
            except Exception as rule_error:
                logger.error(f"❌ 规则 '{rule.name}' 历史消息转发失败: {rule_error}")
                
    except Exception as e:
        logger.error(f"❌ 启动时历史消息转发检查失败: {e}")

async def main():
    """主函数"""
    try:
        logger.info("🚀 启动增强版Telegram消息转发机器人Web界面")
        
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        # 启动日志清理任务
        from log_manager import schedule_log_cleanup
        asyncio.create_task(schedule_log_cleanup())
        logger.info("📋 日志清理定时任务已启动")
        
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
        
        # 确保数据库初始化（无论配置是否完整）
        logger.info("🗄️ 初始化数据库...")
        try:
            from database import init_database
            await init_database()
            logger.info("✅ 数据库初始化完成")
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
        
        # 自动数据库迁移
        await auto_database_migration(enhanced_bot)
        
        # 启动时检查激活的规则并触发历史消息转发
        if enhanced_bot:
            logger.info("🔍 检查启动时激活的规则...")
            await auto_trigger_history_messages(enhanced_bot)
        
        # 聊天名称更新提示
        if enhanced_bot:
            logger.info("💡 聊天名称更新方式:")
            logger.info("   1. 访问规则列表页面时自动更新")
            logger.info("   2. 手动调用: curl -X POST http://localhost:9393/api/rules/fetch-chat-info")
        
        # 创建简化的FastAPI应用
        logger.info("🌐 启动Web服务器...")
        from fastapi import FastAPI, Request, File, UploadFile
        from fastapi.responses import JSONResponse
        from datetime import datetime
        from fastapi.staticfiles import StaticFiles
        from fastapi.middleware.cors import CORSMiddleware
        
        # 再次确认数据库已准备就绪
        try:
            from database import get_db
            from sqlalchemy import text
            async for db in get_db():
                await db.execute(text("SELECT 1"))
                logger.info("✅ 数据库连接测试成功")
                break
        except Exception as e:
            logger.error(f"❌ 数据库连接测试失败: {e}")
            logger.info("🔧 尝试修复数据库...")
            try:
                from database import db_manager
                await db_manager.create_tables()
                logger.info("✅ 数据库修复成功")
            except Exception as repair_error:
                logger.error(f"❌ 数据库修复失败: {repair_error}")
                raise
        
        app = FastAPI(
            title="Telegram消息转发机器人 - 增强版",
            description="Telegram消息转发机器人v3.8",
            version="3.9.0"
        )
        
        # 添加启动事件处理器
        @app.on_event("startup")
        async def startup_event():
            """应用启动后执行的任务"""
            if enhanced_bot:
                logger.info("🚀 FastAPI应用启动完成，聊天名称将通过前端自动更新或手动调用API")
                logger.info("💡 提示: 访问规则列表页面时会自动检测并更新占位符聊天名称")
                logger.info("🔧 手动更新命令: curl -X POST http://localhost:8000/api/rules/fetch-chat-info")
        
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
                clients_status = {}
                
                if enhanced_bot:
                    # 获取运行时客户端状态
                    runtime_clients = enhanced_bot.get_client_status()
                    clients_status.update(runtime_clients)
                
                # 从数据库获取所有配置的客户端
                try:
                    from models import TelegramClient
                    from database import db_manager
                    from sqlalchemy import select
                    
                    async with db_manager.async_session() as session:
                        result = await session.execute(select(TelegramClient))
                        db_clients = result.scalars().all()
                        
                        # 为每个数据库客户端创建状态信息
                        for db_client in db_clients:
                            if db_client.client_id in clients_status:
                                # 运行时客户端已存在，只添加auto_start信息
                                clients_status[db_client.client_id]['auto_start'] = db_client.auto_start
                            else:
                                # 运行时客户端不存在，创建基础状态信息
                                clients_status[db_client.client_id] = {
                                    "client_id": db_client.client_id,
                                    "client_type": db_client.client_type,
                                    "running": False,
                                    "connected": False,
                                    "login_state": "idle",
                                    "user_info": None,
                                    "monitored_chats": [],
                                    "thread_alive": False,
                                    "auto_start": db_client.auto_start
                                }
                                
                except Exception as db_error:
                    logger.warning(f"获取数据库客户端信息失败: {db_error}")
                    # 如果数据库查询失败，给运行时客户端设置默认auto_start值
                    for client_id, client_info in clients_status.items():
                        if 'auto_start' not in client_info:
                            client_info['auto_start'] = False
                
                return JSONResponse(content={
                    "success": True,
                    "clients": clients_status
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
        
        # 日志管理API
        @app.get("/api/system/logs/stats")
        async def get_log_stats():
            """获取日志统计信息"""
            try:
                from log_manager import log_manager
                stats = log_manager.get_log_stats()
                return JSONResponse(content={
                    "success": True,
                    "data": stats
                })
            except Exception as e:
                logger.error(f"获取日志统计失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "error": str(e)
                }, status_code=500)
        
        @app.post("/api/system/logs/cleanup")
        async def trigger_log_cleanup():
            """手动触发日志清理"""
            try:
                from log_manager import log_manager
                await log_manager.cleanup_old_logs()
                return JSONResponse(content={
                    "success": True,
                    "message": "日志清理完成"
                })
            except Exception as e:
                logger.error(f"日志清理失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "error": str(e)
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
                
                # 提取参数，排除必需字段和已明确传递的字段
                excluded_fields = required_fields + ['source_chat_name', 'target_chat_name']
                kwargs = {k: v for k, v in data.items() if k not in excluded_fields}
                
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
        
        # 关键词管理API
        @app.get("/api/rules/{rule_id}/keywords")
        async def get_keywords(rule_id: int):
            """获取规则的关键词列表"""
            try:
                from models import Keyword
                from database import get_db
                from sqlalchemy import select
                
                async for db in get_db():
                    result = await db.execute(
                        select(Keyword).where(Keyword.rule_id == rule_id)
                    )
                    keywords = result.scalars().all()
                    
                    keywords_data = []
                    for kw in keywords:
                        keywords_data.append({
                            "id": kw.id,
                            "rule_id": kw.rule_id,
                            "keyword": kw.keyword,
                            "is_blacklist": getattr(kw, 'is_exclude', False),
                            "created_at": kw.created_at.isoformat() if kw.created_at else None
                        })
                    
                    return JSONResponse({
                        "success": True,
                        "keywords": keywords_data
                    })
                    
            except Exception as e:
                logger.error(f"获取关键词列表失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"获取关键词列表失败: {str(e)}"}
                )

        @app.post("/api/rules/{rule_id}/keywords")
        async def create_keyword(rule_id: int, request: Request):
            """创建关键词"""
            try:
                from models import Keyword
                from database import get_db
                
                data = await request.json()
                
                async for db in get_db():
                    keyword = Keyword(
                        rule_id=rule_id,
                        keyword=data.get('keyword'),
                        is_exclude=data.get('is_blacklist', False)
                    )
                    
                    db.add(keyword)
                    await db.commit()
                    await db.refresh(keyword)
                    
                    return JSONResponse({
                        "success": True,
                        "message": "关键词创建成功",
                        "keyword": {
                            "id": keyword.id,
                            "rule_id": keyword.rule_id,
                            "keyword": keyword.keyword,
                            "is_blacklist": keyword.is_exclude,
                            "created_at": keyword.created_at.isoformat() if keyword.created_at else None
                        }
                    })
                    
            except Exception as e:
                logger.error(f"创建关键词失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"创建关键词失败: {str(e)}"}
                )

        @app.put("/api/keywords/{keyword_id}")
        async def update_keyword(keyword_id: int, request: Request):
            """更新关键词"""
            try:
                from models import Keyword
                from database import get_db
                from sqlalchemy import select
                
                data = await request.json()
                
                async for db in get_db():
                    result = await db.execute(
                        select(Keyword).where(Keyword.id == keyword_id)
                    )
                    keyword = result.scalar_one_or_none()
                    
                    if not keyword:
                        return JSONResponse(
                            status_code=404,
                            content={"success": False, "message": "关键词不存在"}
                        )
                    
                    # 更新字段
                    if 'keyword' in data:
                        keyword.keyword = data['keyword']
                    if 'is_blacklist' in data:
                        keyword.is_exclude = data['is_blacklist']
                    
                    await db.commit()
                    await db.refresh(keyword)
                    
                    return JSONResponse({
                        "success": True,
                        "message": "关键词更新成功",
                        "keyword": {
                            "id": keyword.id,
                            "rule_id": keyword.rule_id,
                            "keyword": keyword.keyword,
                            "is_blacklist": keyword.is_exclude,
                            "created_at": keyword.created_at.isoformat() if keyword.created_at else None
                        }
                    })
                    
            except Exception as e:
                logger.error(f"更新关键词失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"更新关键词失败: {str(e)}"}
                )

        @app.delete("/api/keywords/{keyword_id}")
        async def delete_keyword(keyword_id: int):
            """删除关键词"""
            try:
                from models import Keyword
                from database import get_db
                from sqlalchemy import select, delete
                
                async for db in get_db():
                    result = await db.execute(
                        delete(Keyword).where(Keyword.id == keyword_id)
                    )
                    await db.commit()
                    
                    if result.rowcount > 0:
                        return JSONResponse({
                            "success": True,
                            "message": "关键词删除成功"
                        })
                    else:
                        return JSONResponse(
                            status_code=404,
                            content={"success": False, "message": "关键词不存在"}
                        )
                    
            except Exception as e:
                logger.error(f"删除关键词失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"删除关键词失败: {str(e)}"}
                )

        # 替换规则管理API
        @app.get("/api/rules/{rule_id}/replacements")
        async def get_replacements(rule_id: int):
            """获取规则的替换规则列表"""
            try:
                from models import ReplaceRule
                from database import get_db
                from sqlalchemy import select
                
                async for db in get_db():
                    result = await db.execute(
                        select(ReplaceRule).where(ReplaceRule.rule_id == rule_id)
                        .order_by(ReplaceRule.priority)
                    )
                    replacements = result.scalars().all()
                    
                    replacements_data = []
                    for rr in replacements:
                        replacements_data.append({
                            "id": rr.id,
                            "rule_id": rr.rule_id,
                            "name": rr.name,
                            "pattern": rr.pattern,
                            "replacement": rr.replacement,
                            "priority": rr.priority,
                            "is_regex": rr.is_regex,
                            "is_active": rr.is_active,
                            "created_at": rr.created_at.isoformat() if rr.created_at else None
                        })
                    
                    return JSONResponse({
                        "success": True,
                        "replacements": replacements_data
                    })
                    
            except Exception as e:
                logger.error(f"获取替换规则列表失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"获取替换规则列表失败: {str(e)}"}
                )

        @app.post("/api/rules/{rule_id}/replacements")
        async def create_replacement(rule_id: int, request: Request):
            """创建替换规则"""
            try:
                from models import ReplaceRule
                from database import get_db
                
                data = await request.json()
                
                async for db in get_db():
                    replacement = ReplaceRule(
                        rule_id=rule_id,
                        name=data.get('name'),
                        pattern=data.get('pattern'),
                        replacement=data.get('replacement'),
                        priority=data.get('priority', 1),
                        is_regex=data.get('is_regex', True),
                        is_active=data.get('is_active', True)
                    )
                    
                    db.add(replacement)
                    await db.commit()
                    await db.refresh(replacement)
                    
                    return JSONResponse({
                        "success": True,
                        "message": "替换规则创建成功",
                        "replacement": {
                            "id": replacement.id,
                            "rule_id": replacement.rule_id,
                            "name": replacement.name,
                            "pattern": replacement.pattern,
                            "replacement": replacement.replacement,
                            "priority": replacement.priority,
                            "is_regex": getattr(replacement, 'is_regex', True),
                            "is_active": replacement.is_active,
                            "created_at": replacement.created_at.isoformat() if replacement.created_at else None
                        }
                    })
                    
            except Exception as e:
                logger.error(f"创建替换规则失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"创建替换规则失败: {str(e)}"}
                )

        @app.put("/api/replacements/{replacement_id}")
        async def update_replacement(replacement_id: int, request: Request):
            """更新替换规则"""
            try:
                from models import ReplaceRule
                from database import get_db
                from sqlalchemy import select
                
                data = await request.json()
                
                async for db in get_db():
                    result = await db.execute(
                        select(ReplaceRule).where(ReplaceRule.id == replacement_id)
                    )
                    replacement = result.scalar_one_or_none()
                    
                    if not replacement:
                        return JSONResponse(
                            status_code=404,
                            content={"success": False, "message": "替换规则不存在"}
                        )
                    
                    # 更新字段
                    if 'name' in data:
                        replacement.name = data['name']
                    if 'pattern' in data:
                        replacement.pattern = data['pattern']
                    if 'replacement' in data:
                        replacement.replacement = data['replacement']
                    if 'priority' in data:
                        replacement.priority = data['priority']
                    if 'is_regex' in data:
                        replacement.is_regex = data['is_regex']
                    if 'is_active' in data:
                        replacement.is_active = data['is_active']
                    
                    await db.commit()
                    await db.refresh(replacement)
                    
                    return JSONResponse({
                        "success": True,
                        "message": "替换规则更新成功",
                        "replacement": {
                            "id": replacement.id,
                            "rule_id": replacement.rule_id,
                            "name": replacement.name,
                            "pattern": replacement.pattern,
                            "replacement": replacement.replacement,
                            "priority": replacement.priority,
                            "is_regex": getattr(replacement, 'is_regex', True),
                            "is_active": replacement.is_active,
                            "created_at": replacement.created_at.isoformat() if replacement.created_at else None
                        }
                    })
                    
            except Exception as e:
                logger.error(f"更新替换规则失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"更新替换规则失败: {str(e)}"}
                )

        @app.delete("/api/replacements/{replacement_id}")
        async def delete_replacement(replacement_id: int):
            """删除替换规则"""
            try:
                from models import ReplaceRule
                from database import get_db
                from sqlalchemy import select, delete
                
                async for db in get_db():
                    result = await db.execute(
                        delete(ReplaceRule).where(ReplaceRule.id == replacement_id)
                    )
                    await db.commit()
                    
                    if result.rowcount > 0:
                        return JSONResponse({
                            "success": True,
                            "message": "替换规则删除成功"
                        })
                    else:
                        return JSONResponse(
                            status_code=404,
                            content={"success": False, "message": "替换规则不存在"}
                        )
                    
            except Exception as e:
                logger.error(f"删除替换规则失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"删除替换规则失败: {str(e)}"}
                )
        
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

        @app.post("/api/chats/export")
        async def export_chats():
            """导出聊天列表"""
            try:
                from fastapi.responses import Response
                import json
                
                # 从增强版机器人获取聊天列表
                if enhanced_bot and enhanced_bot.multi_client_manager:
                    all_chats = []
                    
                    for client_id, client_wrapper in enhanced_bot.multi_client_manager.clients.items():
                        if client_wrapper.connected:
                            try:
                                # 使用线程安全方法获取聊天列表
                                client_chats = client_wrapper.get_chats_sync()
                                all_chats.extend(client_chats)
                            except Exception as e:
                                logger.warning(f"获取客户端 {client_id} 聊天列表失败: {e}")
                                continue
                    
                    # 返回JSON文件
                    json_str = json.dumps(all_chats, ensure_ascii=False, indent=2)
                    
                    return Response(
                        content=json_str,
                        media_type='application/json',
                        headers={
                            'Content-Disposition': f'attachment; filename="chats_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
                        }
                    )
                
                return JSONResponse({
                    "success": False,
                    "message": "无可用的客户端"
                }, status_code=503)
                
            except Exception as e:
                logger.error(f"导出聊天列表失败: {e}")
                return JSONResponse({
                    "success": False,
                    "message": f"导出失败: {str(e)}"
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
        
        @app.post("/api/rules/export")
        async def export_rules(request: Request):
            """导出规则"""
            try:
                from models import ForwardRule, Keyword, ReplaceRule
                from sqlalchemy import select
                from database import get_db
                import json
                
                # 获取请求参数
                try:
                    request_data = await request.json()
                    rule_ids = request_data.get('ids', [])
                except:
                    rule_ids = []
                
                async for db in get_db():
                    # 构建查询
                    query = select(ForwardRule)
                    if rule_ids:
                        query = query.where(ForwardRule.id.in_(rule_ids))
                    
                    # 获取规则
                    result = await db.execute(query)
                    rules = result.fetchall()
                    
                    export_data = []
                    for rule_tuple in rules:
                        rule = rule_tuple[0]
                        
                        # 获取关键词
                        keywords_result = await db.execute(
                            select(Keyword).where(Keyword.rule_id == rule.id)
                        )
                        keywords = [
                            {
                                'keyword': kw_tuple[0].keyword,
                                'keyword_type': kw_tuple[0].keyword_type,
                                'is_active': kw_tuple[0].is_active
                            }
                            for kw_tuple in keywords_result.fetchall()
                        ]
                        
                        # 获取替换规则
                        replacements_result = await db.execute(
                            select(ReplaceRule).where(ReplaceRule.rule_id == rule.id)
                        )
                        replacements = [
                            {
                                'pattern': rep_tuple[0].pattern,
                                'replacement': rep_tuple[0].replacement,
                                'is_regex': rep_tuple[0].is_regex,
                                'is_active': rep_tuple[0].is_active
                            }
                            for rep_tuple in replacements_result.fetchall()
                        ]
                        
                        # 构造规则数据
                        rule_data = {
                            'id': rule.id,
                            'name': rule.name,
                            'source_chat_id': rule.source_chat_id,
                            'source_chat_name': rule.source_chat_name,
                            'target_chat_id': rule.target_chat_id,
                            'target_chat_name': rule.target_chat_name,
                            'is_active': rule.is_active,
                            'enable_keyword_filter': rule.enable_keyword_filter,
                            'enable_regex_replace': rule.enable_regex_replace,
                            'client_id': rule.client_id,
                            'client_type': rule.client_type,
                            'enable_text': rule.enable_text,
                            'enable_media': rule.enable_media,
                            'enable_photo': rule.enable_photo,
                            'enable_video': rule.enable_video,
                            'enable_document': rule.enable_document,
                            'enable_audio': rule.enable_audio,
                            'enable_voice': rule.enable_voice,
                            'enable_sticker': rule.enable_sticker,
                            'enable_animation': rule.enable_animation,
                            'enable_webpage': rule.enable_webpage,
                            'forward_delay': rule.forward_delay,
                            'max_message_length': rule.max_message_length,
                            'enable_link_preview': rule.enable_link_preview,
                            'time_filter_type': rule.time_filter_type,
                            'start_time': rule.start_time.isoformat() if rule.start_time else None,
                            'end_time': rule.end_time.isoformat() if rule.end_time else None,
                            'created_at': rule.created_at.isoformat() if rule.created_at else None,
                            'updated_at': rule.updated_at.isoformat() if rule.updated_at else None,
                            'keywords': keywords,
                            'replacements': replacements
                        }
                        export_data.append(rule_data)
                    
                    return JSONResponse({
                        "success": True,
                        "data": export_data,
                        "count": len(export_data),
                        "filename": f"rules_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "message": f"成功导出 {len(export_data)} 个规则"
                    })
                    
            except Exception as e:
                logger.error(f"导出规则失败: {e}")
                return JSONResponse({
                    "success": False,
                    "message": f"导出失败: {str(e)}"
                }, status_code=500)

        @app.post("/api/rules/import")
        async def import_rules(request: Request):
            """导入规则"""
            try:
                from models import ForwardRule, Keyword, ReplaceRule
                from database import get_db
                from datetime import datetime
                import json
                
                # 获取导入数据
                try:
                    request_data = await request.json()
                    import_data = request_data.get('data', [])
                except Exception as e:
                    return JSONResponse({
                        "success": False,
                        "message": f"请求数据格式错误: {str(e)}"
                    }, status_code=400)
                
                if not isinstance(import_data, list):
                    return JSONResponse({
                        "success": False,
                        "message": "导入数据必须是数组格式"
                    }, status_code=400)
                
                async for db in get_db():
                    from sqlalchemy import select
                    imported_count = 0
                    failed_count = 0
                    errors = []
                    
                    for rule_data in import_data:
                        try:
                            # 检查是否已存在相同名称的规则
                            existing_rule = await db.execute(
                                select(ForwardRule).where(ForwardRule.name == rule_data.get('name'))
                            )
                            
                            if existing_rule.fetchone():
                                failed_count += 1
                                errors.append(f"规则 '{rule_data.get('name')}' 已存在，跳过导入")
                                continue
                            
                            # 创建新规则（不包括id字段）
                            new_rule = ForwardRule(
                                name=rule_data.get('name'),
                                source_chat_id=rule_data.get('source_chat_id'),
                                source_chat_name=rule_data.get('source_chat_name'),
                                target_chat_id=rule_data.get('target_chat_id'),
                                target_chat_name=rule_data.get('target_chat_name'),
                                is_active=rule_data.get('is_active', True),
                                enable_keyword_filter=rule_data.get('enable_keyword_filter', False),
                                enable_regex_replace=rule_data.get('enable_regex_replace', False),
                                client_id=rule_data.get('client_id'),
                                client_type=rule_data.get('client_type'),
                                enable_text=rule_data.get('enable_text', True),
                                enable_media=rule_data.get('enable_media', True),
                                enable_photo=rule_data.get('enable_photo', True),
                                enable_video=rule_data.get('enable_video', True),
                                enable_document=rule_data.get('enable_document', True),
                                enable_audio=rule_data.get('enable_audio', True),
                                enable_voice=rule_data.get('enable_voice', True),
                                enable_sticker=rule_data.get('enable_sticker', False),
                                enable_animation=rule_data.get('enable_animation', False),
                                enable_webpage=rule_data.get('enable_webpage', True),
                                forward_delay=rule_data.get('forward_delay', 0),
                                max_message_length=rule_data.get('max_message_length'),
                                enable_link_preview=rule_data.get('enable_link_preview', True),
                                time_filter_type=rule_data.get('time_filter_type', 'none'),
                                start_time=datetime.fromisoformat(rule_data['start_time'].replace('Z', '+00:00')) if rule_data.get('start_time') else None,
                                end_time=datetime.fromisoformat(rule_data['end_time'].replace('Z', '+00:00')) if rule_data.get('end_time') else None,
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            
                            db.add(new_rule)
                            await db.flush()  # 获取新规则的ID
                            
                            # 导入关键词
                            if rule_data.get('keywords'):
                                for keyword_data in rule_data['keywords']:
                                    new_keyword = Keyword(
                                        rule_id=new_rule.id,
                                        keyword=keyword_data.get('keyword'),
                                        keyword_type=keyword_data.get('keyword_type', 'contains'),
                                        is_active=keyword_data.get('is_active', True)
                                    )
                                    db.add(new_keyword)
                            
                            # 导入替换规则
                            if rule_data.get('replacements'):
                                for replacement_data in rule_data['replacements']:
                                    new_replacement = ReplaceRule(
                                        rule_id=new_rule.id,
                                        pattern=replacement_data.get('pattern'),
                                        replacement=replacement_data.get('replacement'),
                                        is_regex=replacement_data.get('is_regex', False),
                                        is_active=replacement_data.get('is_active', True)
                                    )
                                    db.add(new_replacement)
                            
                            imported_count += 1
                            
                        except Exception as e:
                            failed_count += 1
                            errors.append(f"导入规则 '{rule_data.get('name', '未知')}' 失败: {str(e)}")
                            logger.warning(f"导入单个规则失败: {e}")
                            continue
                    
                    await db.commit()
                    
                    return JSONResponse({
                        "success": True,
                        "message": f"导入完成：成功 {imported_count} 个，失败 {failed_count} 个",
                        "imported_count": imported_count,
                        "failed_count": failed_count,
                        "errors": errors
                    })
                    
            except Exception as e:
                logger.error(f"导入规则失败: {e}")
                return JSONResponse({
                    "success": False,
                    "message": f"导入失败: {str(e)}"
                }, status_code=500)

        @app.post("/api/rules/fetch-chat-info")
        async def fetch_chat_info():
            """触发聊天名称更新 - 简化版本"""
            try:
                from services import ForwardRuleService
                from database import get_db
                
                # 检查是否有可用的Telegram客户端
                if not enhanced_bot or not hasattr(enhanced_bot, 'multi_client_manager'):
                    return JSONResponse(content={
                        "success": False,
                        "message": "Telegram客户端未配置，无法获取聊天信息"
                    }, status_code=400)
                
                client_manager = enhanced_bot.multi_client_manager
                if not client_manager or not client_manager.clients:
                    return JSONResponse(content={
                        "success": False,
                        "message": "没有可用的Telegram客户端"
                    }, status_code=400)
                
                # 获取所有规则
                rules = await ForwardRuleService.get_all_rules()
                if not rules:
                    return JSONResponse(content={
                        "success": True,
                        "message": "没有规则需要更新",
                        "updated_rules": []
                    })
                
                # 重新运行自动更新聊天名称功能
                logger.info("🔄 手动触发聊天名称更新...")
                async for db in get_db():
                    await auto_update_chat_names(db, enhanced_bot)
                    break
                
                # 返回更新后的规则列表
                updated_rules = await ForwardRuleService.get_all_rules()
                
                return JSONResponse(content={
                    "success": True,
                    "message": f"聊天名称更新完成，处理了 {len(updated_rules)} 个规则",
                    "updated_rules": [
                        {
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "source_chat_name": rule.source_chat_name,
                            "target_chat_name": rule.target_chat_name
                        } for rule in updated_rules
                    ]
                })
                
            except Exception as e:
                logger.error(f"❌ 触发聊天名称更新失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"更新失败: {str(e)}"
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
        
        @app.post("/api/logs/export")
        async def export_logs(request: Request):
            """导出日志"""
            try:
                from models import MessageLog
                from sqlalchemy import select, and_, func
                from database import get_db
                from datetime import datetime
                import json
                from fastapi.responses import Response
                
                # 获取过滤条件
                try:
                    filters = await request.json()
                except:
                    filters = {}
                
                async for db in get_db():
                    # 构建查询
                    query = select(MessageLog)
                    
                    # 应用过滤条件
                    if filters.get('status'):
                        query = query.where(MessageLog.status == filters['status'])
                    
                    if filters.get('date'):
                        try:
                            target_date = datetime.strptime(filters['date'], '%Y-%m-%d').date()
                            query = query.where(func.date(MessageLog.created_at) == target_date)
                        except ValueError:
                            pass
                    
                    if filters.get('start_date') and filters.get('end_date'):
                        try:
                            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                            query = query.where(and_(
                                MessageLog.created_at >= start_date,
                                MessageLog.created_at <= end_date
                            ))
                        except ValueError:
                            pass
                    
                    # 执行查询
                    result = await db.execute(query)
                    logs = result.fetchall()
                    
                    # 转换为字典格式
                    export_data = []
                    for log_tuple in logs:
                        log = log_tuple[0]
                        export_data.append({
                            'id': log.id,
                            'rule_id': log.rule_id,
                            'rule_name': log.rule_name,
                            'source_chat_id': log.source_chat_id,
                            'source_chat_name': log.source_chat_name,
                            'target_chat_id': log.target_chat_id,
                            'target_chat_name': log.target_chat_name,
                            'source_message_id': log.source_message_id,
                            'target_message_id': log.target_message_id,
                            'original_text': log.original_text,
                            'processed_text': log.processed_text,
                            'media_type': log.media_type,
                            'status': log.status,
                            'error_message': log.error_message,
                            'processing_time': log.processing_time,
                            'created_at': log.created_at.isoformat() if log.created_at else None
                        })
                    
                    # 返回JSON文件
                    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                    
                    return Response(
                        content=json_str,
                        media_type='application/json',
                        headers={
                            'Content-Disposition': f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
                        }
                    )
                    
            except Exception as e:
                logger.error(f"导出日志失败: {e}")
                return JSONResponse({
                    "success": False,
                    "message": f"导出失败: {str(e)}"
                }, status_code=500)

        @app.post("/api/logs/import")
        async def import_logs(file: UploadFile = File(...)):
            """导入日志"""
            try:
                from models import MessageLog
                from database import get_db
                import json
                from datetime import datetime
                
                # 读取上传的文件
                content = await file.read()
                try:
                    import_data = json.loads(content.decode('utf-8'))
                except json.JSONDecodeError as e:
                    return JSONResponse({
                        "success": False,
                        "message": f"JSON格式错误: {str(e)}"
                    }, status_code=400)
                
                if not isinstance(import_data, list):
                    return JSONResponse({
                        "success": False,
                        "message": "导入数据必须是数组格式"
                    }, status_code=400)
                
                async for db in get_db():
                    from sqlalchemy import select, and_
                    imported_count = 0
                    skipped_count = 0
                    
                    for log_data in import_data:
                        try:
                            # 检查是否已存在相同的日志
                            existing_log = await db.execute(
                                select(MessageLog).where(
                                    and_(
                                        MessageLog.rule_id == log_data.get('rule_id'),
                                        MessageLog.source_message_id == log_data.get('source_message_id'),
                                        MessageLog.source_chat_id == log_data.get('source_chat_id')
                                    )
                                )
                            )
                            
                            if existing_log.fetchone():
                                skipped_count += 1
                                continue
                            
                            # 创建新的日志记录
                            new_log = MessageLog(
                                rule_id=log_data.get('rule_id'),
                                rule_name=log_data.get('rule_name'),
                                source_chat_id=log_data.get('source_chat_id'),
                                source_chat_name=log_data.get('source_chat_name'),
                                target_chat_id=log_data.get('target_chat_id'),
                                target_chat_name=log_data.get('target_chat_name'),
                                source_message_id=log_data.get('source_message_id'),
                                target_message_id=log_data.get('target_message_id'),
                                original_text=log_data.get('original_text'),
                                processed_text=log_data.get('processed_text'),
                                media_type=log_data.get('media_type'),
                                status=log_data.get('status', 'success'),
                                error_message=log_data.get('error_message'),
                                processing_time=log_data.get('processing_time'),
                                created_at=datetime.fromisoformat(log_data['created_at'].replace('Z', '+00:00')) if log_data.get('created_at') else datetime.now()
                            )
                            
                            db.add(new_log)
                            imported_count += 1
                            
                        except Exception as e:
                            logger.warning(f"导入单条日志失败: {e}")
                            skipped_count += 1
                            continue
                    
                    await db.commit()
                    
                    return JSONResponse({
                        "success": True,
                        "message": f"导入完成：成功 {imported_count} 条，跳过 {skipped_count} 条",
                        "imported": imported_count,
                        "skipped": skipped_count
                    })
                    
            except Exception as e:
                logger.error(f"导入日志失败: {e}")
                return JSONResponse({
                    "success": False,
                    "message": f"导入失败: {str(e)}"
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
        
        @app.post("/api/clients/{client_id}/auto-start")
        async def toggle_auto_start(client_id: str, request: Request):
            """切换客户端自动启动状态"""
            try:
                data = await request.json()
                auto_start = data.get('auto_start', False)
                
                # 更新数据库
                from models import TelegramClient
                from database import db_manager
                from sqlalchemy import select
                from config import Config
                
                async with db_manager.async_session() as session:
                    result = await session.execute(
                        select(TelegramClient).where(TelegramClient.client_id == client_id)
                    )
                    db_client = result.scalar_one_or_none()
                    
                    if not db_client:
                        # 如果客户端不存在，尝试创建一个默认记录
                        logger.info(f"💡 客户端 {client_id} 不存在，尝试创建默认记录")
                        
                        # 判断客户端类型并创建相应的配置
                        if client_id == 'main_user' or 'user' in client_id:
                            client_type = 'user'
                            # 创建用户客户端记录
                            db_client = TelegramClient(
                                client_id=client_id,
                                client_type=client_type,
                                api_id=str(Config.API_ID) if hasattr(Config, 'API_ID') and Config.API_ID else None,
                                api_hash=Config.API_HASH if hasattr(Config, 'API_HASH') else None,
                                phone=Config.PHONE_NUMBER if hasattr(Config, 'PHONE_NUMBER') else None,
                                is_active=True,
                                auto_start=auto_start
                            )
                        elif client_id == 'main_bot' or 'bot' in client_id:
                            client_type = 'bot'
                            # 创建机器人客户端记录
                            db_client = TelegramClient(
                                client_id=client_id,
                                client_type=client_type,
                                bot_token=Config.BOT_TOKEN if hasattr(Config, 'BOT_TOKEN') else None,
                                admin_user_id=Config.ADMIN_USER_IDS if hasattr(Config, 'ADMIN_USER_IDS') else None,
                                is_active=True,
                                auto_start=auto_start
                            )
                        else:
                            # 未知类型，默认创建用户类型
                            client_type = 'user'
                            db_client = TelegramClient(
                                client_id=client_id,
                                client_type=client_type,
                                is_active=True,
                                auto_start=auto_start
                            )
                        
                        session.add(db_client)
                        logger.info(f"✅ 已为客户端 {client_id} 创建数据库记录")
                    else:
                        # 更新现有记录
                        db_client.auto_start = auto_start
                    
                    await session.commit()
                    
                    logger.info(f"✅ 客户端 {client_id} 自动启动状态已更新: {auto_start}")
                
                # 根据自动启动状态控制客户端运行状态
                client_action_message = ""
                if enhanced_bot and hasattr(enhanced_bot, 'multi_client_manager') and auto_start:
                    # 只有启用自动启动时才启动客户端，禁用时不影响当前状态
                    client = enhanced_bot.multi_client_manager.get_client(client_id)
                    if not client:
                        # 客户端不存在，需要添加并启动
                        try:
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
                            
                            client = enhanced_bot.multi_client_manager.add_client_with_config(
                                client_id,
                                db_client.client_type,
                                config_data=config_data
                            )
                            client.add_status_callback(enhanced_bot._notify_status_change)
                            client.start()
                            client_action_message = "，并已启动客户端"
                            logger.info(f"🔄 启用自动启动，已启动客户端: {client_id}")
                        except Exception as start_error:
                            logger.error(f"❌ 启动客户端 {client_id} 失败: {start_error}")
                            client_action_message = f"，但启动客户端失败: {start_error}"
                    elif not client.running:
                        # 客户端存在但未运行，启动它
                        try:
                            client.start()
                            client_action_message = "，并已启动客户端"
                            logger.info(f"🔄 启用自动启动，已启动客户端: {client_id}")
                        except Exception as start_error:
                            logger.error(f"❌ 启动客户端 {client_id} 失败: {start_error}")
                            client_action_message = f"，但启动客户端失败: {start_error}"
                    else:
                        # 客户端已在运行，不需要操作
                        client_action_message = "，客户端已在运行"
                        logger.info(f"💡 启用自动启动，客户端 {client_id} 已在运行")
                elif not auto_start:
                    # 禁用自动启动时，不改变客户端当前状态
                    client_action_message = "，客户端当前状态保持不变"
                    logger.info(f"💡 禁用自动启动，客户端 {client_id} 当前状态保持不变")
                
                return JSONResponse(content={
                    "success": True,
                    "message": f"客户端 {client_id} 自动启动已{'启用' if auto_start else '禁用'}{client_action_message}"
                })
                
            except Exception as e:
                logger.error(f"切换自动启动状态失败: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"切换自动启动状态失败: {str(e)}"
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
        
        @app.post("/api/database/repair")
        async def repair_database():
            """修复数据库（重新创建表和迁移）"""
            try:
                from database import db_manager
                
                # 重新创建表
                await db_manager.create_tables()
                
                # 执行迁移
                await auto_database_migration(enhanced_bot)
                
                return JSONResponse(content={
                    "success": True,
                    "message": "数据库修复完成"
                })
                
            except Exception as e:
                logger.error(f"数据库修复失败: {str(e)}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"数据库修复失败: {str(e)}"
                }, status_code=500)

        @app.get("/api/proxy/status")
        async def get_proxy_status():
            """获取代理状态"""
            try:
                from proxy_utils import get_proxy_manager
                proxy_manager = get_proxy_manager()
                
                return JSONResponse(content={
                    "success": True,
                    "proxy_enabled": proxy_manager.enabled,
                    "proxy_type": proxy_manager.proxy_type if proxy_manager.enabled else None,
                    "proxy_host": proxy_manager.host if proxy_manager.enabled else None,
                    "proxy_port": proxy_manager.port if proxy_manager.enabled else None,
                    "has_credentials": bool(proxy_manager.username) if proxy_manager.enabled else False
                })
            except Exception as e:
                logger.error(f"获取代理状态失败: {str(e)}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"获取代理状态失败: {str(e)}"
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
                enable_proxy = data.get('enable_proxy', False)
                config_lines.append(f"ENABLE_PROXY={str(enable_proxy).lower()}")
                
                # 只有在启用代理时才写入代理参数
                if enable_proxy:
                    config_lines.append(f"PROXY_TYPE={data.get('proxy_type', 'http')}")
                    config_lines.append(f"PROXY_HOST={data.get('proxy_host', '127.0.0.1')}")
                    config_lines.append(f"PROXY_PORT={data.get('proxy_port', '7890')}")
                    config_lines.append(f"PROXY_USERNAME={data.get('proxy_username', '')}")
                    if data.get('proxy_password') and data.get('proxy_password') != '***':
                        config_lines.append(f"PROXY_PASSWORD={data.get('proxy_password', '')}")
                else:
                    # 代理禁用时，显式设置空值或注释掉
                    config_lines.append("# PROXY_TYPE=http")
                    config_lines.append("# PROXY_HOST=127.0.0.1") 
                    config_lines.append("# PROXY_PORT=7890")
                    config_lines.append("# PROXY_USERNAME=")
                    config_lines.append("# PROXY_PASSWORD=")
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
                    
                    # 重新加载代理管理器
                    try:
                        from proxy_utils import reload_proxy_manager
                        reload_proxy_manager()
                        logger.info("✅ 代理管理器已重新加载")
                    except Exception as e:
                        logger.error(f"⚠️ 代理管理器重新加载失败: {e}")
                    
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
