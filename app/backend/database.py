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
            
            # 创建所有表
            await self.create_tables()
            
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
    
    async def create_tables(self):
        """创建所有数据库表"""
        try:
            from models import Base
            
            # 使用 SQLAlchemy 创建所有表
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ 数据库表创建成功")
            
            # 验证表是否正确创建
            await self.verify_tables()
            
        except Exception as e:
            logger.error(f"❌ 数据库表创建失败: {e}")
            raise
    
    async def verify_tables(self):
        """验证数据库表完整性"""
        try:
            from models import DatabaseHelper
            from sqlalchemy import text
            
            expected_tables = DatabaseHelper.get_table_names()
            
            async with self.engine.begin() as conn:
                # 获取实际存在的表
                if 'sqlite' in str(self.engine.url):
                    result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                else:
                    result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                
                existing_tables = [row[0] for row in result.fetchall()]
                
                # 检查缺失的表
                missing_tables = set(expected_tables) - set(existing_tables)
                if missing_tables:
                    logger.warning(f"⚠️ 缺失的数据库表: {missing_tables}")
                else:
                    logger.info(f"✅ 数据库表完整性验证通过，共 {len(existing_tables)} 个表")
                    
        except Exception as e:
            logger.warning(f"⚠️ 数据库表验证失败: {e}")
    
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
    # 确保所有表都被创建
    await db_manager.create_tables()
    # 执行自动数据库迁移
    await _auto_migrate_database()

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

async def _auto_migrate_database():
    """自动数据库迁移 - 添加缺失的字段"""
    try:
        from sqlalchemy import text
        logger.info("🔄 开始自动数据库迁移...")
        
        async with db_manager.async_session() as session:
            # 检查replace_rules表是否存在is_regex字段
            try:
                result = await session.execute(text("PRAGMA table_info(replace_rules)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'is_regex' not in columns:
                    logger.info("🔧 添加is_regex字段到replace_rules表...")
                    await session.execute(text("ALTER TABLE replace_rules ADD COLUMN is_regex BOOLEAN DEFAULT 1"))
                    await session.commit()
                    logger.info("✅ is_regex字段已添加")
                else:
                    logger.debug("✅ is_regex字段已存在")
                    
            except Exception as e:
                # 如果表不存在，跳过迁移（表会在create_tables中创建）
                if "no such table" in str(e).lower():
                    logger.debug("replace_rules表不存在，跳过迁移")
                else:
                    logger.warning(f"⚠️ 迁移replace_rules表时出错: {e}")
            
            # 可以在这里添加更多的迁移逻辑
            # 例如：添加其他缺失的字段、索引等
            
            logger.info("✅ 自动数据库迁移完成")
            
    except Exception as e:
        logger.error(f"❌ 自动数据库迁移失败: {e}")
        # 不抛出异常，避免影响正常启动