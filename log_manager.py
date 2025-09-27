#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器 - 统一的日志轮转和清理机制
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import gzip
import shutil
import asyncio
from typing import Optional

# 确保能找到配置文件 - Docker和本地环境兼容
import os
if os.path.exists('app/backend/config.py'):
    # 本地开发环境
    sys.path.append('app/backend')
elif os.path.exists('config.py'):
    # Docker环境或根目录运行
    pass
else:
    # 尝试添加可能的路径
    sys.path.append('app/backend')

try:
    from config import Config
except ImportError as e:
    print(f"无法导入配置文件: {e}")
    # 提供默认配置
    class Config:
        MAX_LOG_SIZE = 100
        ENABLE_LOG_CLEANUP = True
        LOG_RETENTION_DAYS = 30
        LOG_CLEANUP_TIME = "02:00"
        LOG_LEVEL = "INFO"
        LOGS_DIR = "logs"


class LogRotationHandler(logging.handlers.RotatingFileHandler):
    """自定义日志轮转处理器，支持压缩"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, 
                 encoding=None, delay=False, compress=True):
        self.compress = compress
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
    
    def doRollover(self):
        """执行日志轮转并压缩旧文件"""
        if self.stream:
            self.stream.close()
            self.stream = None
            
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            dfn = self.rotation_filename(self.baseFilename + ".1")
            if os.path.exists(dfn):
                os.remove(dfn)
                
            # 移动当前文件到 .1
            if os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dfn)
                
                # 压缩轮转的文件
                if self.compress and dfn.endswith('.1'):
                    self._compress_file(dfn)
        
        if not self.delay:
            self.stream = self._open()
    
    def _compress_file(self, filename):
        """压缩日志文件"""
        try:
            compressed_filename = f"{filename}.gz"
            with open(filename, 'rb') as f_in:
                with gzip.open(compressed_filename, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(filename)
            print(f"📦 日志文件已压缩: {compressed_filename}")
        except Exception as e:
            print(f"⚠️ 压缩日志文件失败 {filename}: {e}")


class LogManager:
    """统一日志管理器"""
    
    def __init__(self):
        self.loggers = {}
        self.setup_directories()
    
    def setup_directories(self):
        """创建日志目录"""
        log_dir = Path(Config.LOGS_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_logger(self, name: str, log_file: Optional[str] = None, 
                   max_bytes: int = 10*1024*1024, backup_count: int = 5) -> logging.Logger:
        """
        获取配置好的日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径（可选）
            max_bytes: 单个日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（如果指定了日志文件）
        if log_file:
            log_path = Path(Config.LOGS_DIR) / log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                file_handler = LogRotationHandler(
                    filename=str(log_path),
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8',
                    compress=True
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
                print(f"📄 日志文件配置: {log_path} (最大: {max_bytes//1024//1024}MB, 备份: {backup_count}个)")
                
            except (PermissionError, OSError) as e:
                print(f"⚠️ 无法创建日志文件 {log_path}: {e}")
                print("📝 日志将仅输出到控制台")
        
        self.loggers[name] = logger
        return logger
    
    def setup_main_loggers(self):
        """设置主要的日志记录器"""
        # 主应用日志
        main_logger = self.get_logger(
            'main', 
            'bot.log',
            max_bytes=Config.MAX_LOG_SIZE * 1024 * 1024,  # MB转换为字节
            backup_count=7
        )
        
        # Web服务日志
        web_logger = self.get_logger(
            'web',
            'web_enhanced_clean.log',
            max_bytes=Config.MAX_LOG_SIZE * 1024 * 1024,
            backup_count=7
        )
        
        # Telegram客户端日志
        telegram_logger = self.get_logger(
            'telegram',
            'telegram_client.log',
            max_bytes=50 * 1024 * 1024,  # 50MB
            backup_count=5
        )
        
        # 数据库日志
        db_logger = self.get_logger(
            'database',
            'database.log',
            max_bytes=20 * 1024 * 1024,  # 20MB
            backup_count=3
        )
        
        return {
            'main': main_logger,
            'web': web_logger,
            'telegram': telegram_logger,
            'database': db_logger
        }
    
    async def cleanup_old_logs(self):
        """清理过期的日志文件"""
        if not Config.ENABLE_LOG_CLEANUP:
            return
        
        log_dir = Path(Config.LOGS_DIR)
        if not log_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=Config.LOG_RETENTION_DAYS)
        cleaned_count = 0
        
        try:
            for log_file in log_dir.glob('*.log*'):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        log_file.unlink()
                        cleaned_count += 1
                        print(f"🗑️ 清理过期日志: {log_file.name}")
                    except Exception as e:
                        print(f"⚠️ 清理日志文件失败 {log_file}: {e}")
            
            if cleaned_count > 0:
                print(f"✅ 清理完成，删除了 {cleaned_count} 个过期日志文件")
            else:
                print("📋 没有发现过期的日志文件")
                
        except Exception as e:
            print(f"❌ 日志清理失败: {e}")
    
    def get_log_stats(self):
        """获取日志统计信息"""
        log_dir = Path(Config.LOGS_DIR)
        if not log_dir.exists():
            return {"total_files": 0, "total_size": 0}
        
        total_files = 0
        total_size = 0
        
        try:
            for log_file in log_dir.glob('*.log*'):
                if log_file.is_file():
                    total_files += 1
                    total_size += log_file.stat().st_size
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            print(f"⚠️ 获取日志统计失败: {e}")
            return {"total_files": 0, "total_size": 0, "error": str(e)}


# 全局日志管理器实例
log_manager = LogManager()

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return log_manager.get_logger(name, log_file)

def setup_logging():
    """设置应用程序日志"""
    return log_manager.setup_main_loggers()

async def schedule_log_cleanup():
    """定时日志清理任务"""
    while True:
        try:
            # 解析清理时间
            cleanup_time = Config.LOG_CLEANUP_TIME.split(':')
            cleanup_hour = int(cleanup_time[0])
            cleanup_minute = int(cleanup_time[1]) if len(cleanup_time) > 1 else 0
            
            now = datetime.now()
            next_cleanup = now.replace(hour=cleanup_hour, minute=cleanup_minute, second=0, microsecond=0)
            
            # 如果今天的清理时间已过，设置为明天
            if next_cleanup <= now:
                next_cleanup += timedelta(days=1)
            
            wait_seconds = (next_cleanup - now).total_seconds()
            print(f"📅 下次日志清理时间: {next_cleanup.strftime('%Y-%m-%d %H:%M:%S')}")
            
            await asyncio.sleep(wait_seconds)
            await log_manager.cleanup_old_logs()
            
        except Exception as e:
            print(f"❌ 日志清理调度失败: {e}")
            # 出错时等待1小时后重试
            await asyncio.sleep(3600)
