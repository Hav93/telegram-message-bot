"""
数据库连接管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
from config import Config
from models import Base

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def init_db(self):
        """初始化数据库"""
        # 创建异步引擎
        if Config.DATABASE_URL.startswith('sqlite'):
            # 对于SQLite，需要特殊处理
            db_url = Config.DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///')
        else:
            db_url = Config.DATABASE_URL
        
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # 创建表
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self):
        """获取数据库会话"""
        async with self.async_session() as session:
            yield session
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()

# 全局数据库管理器实例
db_manager = DatabaseManager()

# 依赖注入函数
async def get_db():
    async with db_manager.async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_database():
    """初始化数据库"""
    await db_manager.init_db()