"""
数据库配置和管理模块 - 增强版
"""
import os
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pathlib import Path
from config import Config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器 - 支持SQLite优化配置"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        
    async def init_db(self):
        """初始化数据库连接"""
        try:
            # 确保数据目录存在
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # 数据库URL配置
            database_url = Config.DATABASE_URL
            if database_url.startswith('sqlite:'):
                # SQLite优化配置
                database_url = database_url.replace('sqlite:', 'sqlite+aiosqlite:')
                
                # 提取数据库文件路径进行优化
                db_file = database_url.replace('sqlite+aiosqlite:///', '')
                self._optimize_sqlite_database(db_file)
                
                # 创建引擎（SQLite特殊配置）
                self.engine = create_async_engine(
                    database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30
                    },
                    echo=False
                )
            else:
                # PostgreSQL或其他数据库
                self.engine = create_async_engine(
                    database_url,
                    echo=False
                )
            
            # 创建Session工厂
            self.async_session = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info(f"✅ 数据库初始化成功: {database_url}")
            
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    def _optimize_sqlite_database(self, db_file: str):
        """优化SQLite数据库配置"""
        try:
            # 确保文件存在
            Path(db_file).parent.mkdir(parents=True, exist_ok=True)
            
            # 使用同步连接进行优化配置
            conn = sqlite3.connect(db_file, timeout=30.0)
            cursor = conn.cursor()
            
            # WAL模式 - 提高并发性能
            cursor.execute("PRAGMA journal_mode=WAL;")
            
            # 同步模式优化
            cursor.execute("PRAGMA synchronous=NORMAL;")
            
            # 缓存大小优化
            cursor.execute("PRAGMA cache_size=10000;")
            
            # 临时存储优化
            cursor.execute("PRAGMA temp_store=memory;")
            
            # 锁定超时
            cursor.execute("PRAGMA busy_timeout=30000;")
            
            # 自动清理模式
            cursor.execute("PRAGMA auto_vacuum=INCREMENTAL;")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ SQLite数据库优化完成: {db_file}")
            
        except Exception as e:
            logger.warning(f"⚠️ SQLite优化失败: {e}")
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ 数据库连接已关闭")

# 全局数据库管理器实例
db_manager = DatabaseManager()

async def init_database():
    """初始化数据库"""
    await db_manager.init_db()

async def get_db():
    """获取数据库会话"""
    if not db_manager.async_session:
        await db_manager.init_db()
    
    async with db_manager.async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()