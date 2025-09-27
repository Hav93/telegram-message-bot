import os
from dotenv import load_dotenv
from pathlib import Path

# 统一配置文件加载器
class ConfigLoader:
    """统一配置文件加载器，支持多种配置文件格式"""
    
    @staticmethod
    def load_config():
        """按优先级加载配置文件，环境变量优先"""
        # 配置文件搜索路径（按优先级排序）
        config_files = [
            'config/app.config',    # 持久化主配置文件（推荐）
            'app.config',           # 根目录主配置文件（兼容）
            'config/config.env',    # 持久化环境变量文件
            'config.env',           # 根目录环境变量文件（兼容）
            'config/.env',          # 持久化开发环境文件
            '.env'                  # 根目录开发环境文件（兼容）
        ]
        
        # 加载所有存在的配置文件，按优先级顺序（后加载的覆盖先加载的）
        loaded_files = []
        for config_file in reversed(config_files):  # 反向加载，让高优先级的文件最后加载
            if os.path.exists(config_file):
                print(f"[CONFIG] 加载配置文件: {config_file}")
                load_dotenv(config_file, override=True)  # 允许覆盖，实现优先级
                loaded_files.append(config_file)
        
        if not loaded_files:
            print("[WARNING] 未找到配置文件，使用默认配置")
        else:
            print(f"[CONFIG] 已加载 {len(loaded_files)} 个配置文件，最终优先级: {' > '.join(reversed(loaded_files))}")
        
        # 环境变量已经在系统中，优先级最高

# 加载配置
ConfigLoader.load_config()

class Config:
    """统一配置类 - Telegram消息转发机器人"""
    
    # === 应用信息 ===
    APP_NAME = os.getenv('APP_NAME', 'telegram-message')
    APP_VERSION = os.getenv('APP_VERSION', '3.9.0')
    APP_DESCRIPTION = os.getenv('APP_DESCRIPTION', 'Telegram消息转发机器人v3.6')
    
    # === Telegram API 配置 ===
    try:
        API_ID = int(os.getenv('API_ID', '0')) if os.getenv('API_ID', '0').isdigit() else 0
    except (ValueError, TypeError):
        API_ID = 0
        
    API_HASH = os.getenv('API_HASH', '')
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    
    # === 管理员配置 ===
    @staticmethod
    def _parse_admin_ids(ids_str):
        try:
            return [int(x.strip()) for x in ids_str.split(',') if x.strip() and x.strip().isdigit()]
        except (ValueError, AttributeError):
            return []
    
    ADMIN_USER_IDS = _parse_admin_ids(os.getenv('ADMIN_USER_IDS', ''))
    
    # === 数据库配置 ===
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/bot.db')
    
    # === 文件路径配置 ===
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    LOGS_DIR = os.getenv('LOGS_DIR', 'logs') 
    TEMP_DIR = os.getenv('TEMP_DIR', 'temp')
    SESSIONS_DIR = os.getenv('SESSIONS_DIR', 'sessions')
    
    # === 日志配置 ===
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    ENABLE_LOG_CLEANUP = os.getenv('ENABLE_LOG_CLEANUP', 'true').lower() == 'true'
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '30'))
    LOG_CLEANUP_TIME = os.getenv('LOG_CLEANUP_TIME', '02:00')
    MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', '100'))
    
    # === 转发配置 ===
    MAX_FORWARD_DELAY = int(os.getenv('MAX_FORWARD_DELAY', '5'))
    ENABLE_MEDIA_FORWARD = os.getenv('ENABLE_MEDIA_FORWARD', 'true').lower() == 'true'
    ENABLE_KEYWORD_FILTER = os.getenv('ENABLE_KEYWORD_FILTER', 'true').lower() == 'true'
    ENABLE_REGEX_REPLACE = os.getenv('ENABLE_REGEX_REPLACE', 'true').lower() == 'true'
    
    # === Web界面配置 ===
    WEB_PORT = int(os.getenv('WEB_PORT', '9393'))
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    
    # === 权限配置（Docker用户映射） ===
    PUID = int(os.getenv('PUID', '1000'))
    PGID = int(os.getenv('PGID', '1000'))
    
    # === 代理配置 ===
    # 支持标准HTTP_PROXY环境变量
    HTTP_PROXY = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    HTTPS_PROXY = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    
    # 代理启用状态检查
    # 优先检查显式的 ENABLE_PROXY 设置
    enable_proxy_env = os.getenv('ENABLE_PROXY', '').lower()
    if enable_proxy_env in ['true', 'false']:
        # 如果明确设置了 ENABLE_PROXY，使用该设置
        ENABLE_PROXY = enable_proxy_env == 'true'
    else:
        # 如果没有明确设置，则检查是否有代理URL环境变量
        ENABLE_PROXY = HTTP_PROXY is not None or HTTPS_PROXY is not None
    
    # 解析代理URL或使用传统配置
    PROXY_TYPE = 'http'
    PROXY_HOST = '127.0.0.1'
    PROXY_PORT = 1080
    PROXY_USERNAME = ''
    PROXY_PASSWORD = ''
    
    # 只有在启用代理的情况下才设置代理参数
    if ENABLE_PROXY:
        if HTTP_PROXY or HTTPS_PROXY:
            # 优先使用HTTPS_PROXY，fallback到HTTP_PROXY
            proxy_url = HTTPS_PROXY or HTTP_PROXY
            try:
                from urllib.parse import urlparse
                parsed = urlparse(proxy_url)
                if parsed.hostname:
                    PROXY_TYPE = parsed.scheme or 'http'
                    PROXY_HOST = parsed.hostname
                    PROXY_PORT = parsed.port or (1080 if PROXY_TYPE in ['socks4', 'socks5'] else 8080)
                    PROXY_USERNAME = parsed.username or ''
                    PROXY_PASSWORD = parsed.password or ''
            except Exception:
                # 解析失败，使用传统配置
                pass
        else:
            # 使用传统配置方式（仅在启用代理时）
            PROXY_TYPE = os.getenv('PROXY_TYPE', 'http').lower()
            PROXY_HOST = os.getenv('PROXY_HOST', '127.0.0.1')
            PROXY_PORT = int(os.getenv('PROXY_PORT', '1080'))
            PROXY_USERNAME = os.getenv('PROXY_USERNAME', '')
            PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '')
    
    # === Docker配置 ===
    TZ = os.getenv('TZ', 'Asia/Shanghai')
    MEMORY_LIMIT = os.getenv('MEMORY_LIMIT', '512M')
    CPU_LIMIT = float(os.getenv('CPU_LIMIT', '0.5'))
    
    # === 安全配置 ===
    SESSION_SECRET = os.getenv('SESSION_SECRET', 'your_random_session_secret_key_here')
    
    # === 高级配置 ===
    ENABLE_HISTORY_CRAWL = os.getenv('ENABLE_HISTORY_CRAWL', 'false').lower() == 'true'
    HISTORY_CRAWL_LIMIT = int(os.getenv('HISTORY_CRAWL_LIMIT', '100'))
    MESSAGE_BATCH_SIZE = int(os.getenv('MESSAGE_BATCH_SIZE', '10'))
    MESSAGE_PROCESSING_DELAY = int(os.getenv('MESSAGE_PROCESSING_DELAY', '1'))
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))
    
    # === 监控配置 ===
    HEALTH_CHECK_ENABLED = os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
    ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'false').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9394'))
    
    @classmethod
    def reload(cls):
        """重新加载配置"""
        print("🔄 重新加载配置...")
        ConfigLoader.load_config()
        
        # 重新设置所有属性
        api_id_str = os.getenv('API_ID', '0').strip()
        cls.API_ID = int(api_id_str) if api_id_str and api_id_str.isdigit() else 0
        cls.API_HASH = os.getenv('API_HASH', '')
        cls.BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        cls.PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
        cls.ADMIN_USER_IDS = cls._parse_admin_ids(os.getenv('ADMIN_USER_IDS', ''))
        
        # 更新其他配置
        cls.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/bot.db')
        cls.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        cls.LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
        
        # 安全的int转换
        max_delay = os.getenv('MAX_FORWARD_DELAY', '5').strip()
        cls.MAX_FORWARD_DELAY = int(max_delay) if max_delay and max_delay.isdigit() else 5
        
        cls.ENABLE_MEDIA_FORWARD = os.getenv('ENABLE_MEDIA_FORWARD', 'true').lower() == 'true'
        cls.ENABLE_KEYWORD_FILTER = os.getenv('ENABLE_KEYWORD_FILTER', 'true').lower() == 'true'
        cls.ENABLE_REGEX_REPLACE = os.getenv('ENABLE_REGEX_REPLACE', 'true').lower() == 'true'
        
        web_port = os.getenv('WEB_PORT', '9393').strip()
        cls.WEB_PORT = int(web_port) if web_port and web_port.isdigit() else 9393
        cls.WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
        
        # 重载代理配置
        cls.ENABLE_PROXY = os.getenv('ENABLE_PROXY', 'false').lower() == 'true'
        cls.PROXY_TYPE = os.getenv('PROXY_TYPE', 'http')
        cls.PROXY_HOST = os.getenv('PROXY_HOST', '127.0.0.1')
        
        proxy_port = os.getenv('PROXY_PORT', '1080').strip()
        cls.PROXY_PORT = int(proxy_port) if proxy_port and proxy_port.isdigit() else 1080
        cls.PROXY_USERNAME = os.getenv('PROXY_USERNAME', '')
        cls.PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '')
        
        # 重载日志管理配置
        cls.ENABLE_LOG_CLEANUP = os.getenv('ENABLE_LOG_CLEANUP', 'true').lower() == 'true'
        
        retention_days = os.getenv('LOG_RETENTION_DAYS', '30').strip()
        cls.LOG_RETENTION_DAYS = int(retention_days) if retention_days and retention_days.isdigit() else 30
        cls.LOG_CLEANUP_TIME = os.getenv('LOG_CLEANUP_TIME', '02:00')
        
        max_log_size = os.getenv('MAX_LOG_SIZE', '100').strip()
        cls.MAX_LOG_SIZE = int(max_log_size) if max_log_size and max_log_size.isdigit() else 100
        
        # 重载Session配置
        cls.SESSION_SECRET = os.getenv('SESSION_SECRET', 'default-secret-key-change-in-production')
        
        print("✅ 配置重载完成")
    
    @staticmethod
    def create_directories():
        """创建必要的目录"""
        directories = [Config.DATA_DIR, Config.LOGS_DIR, Config.TEMP_DIR, Config.SESSIONS_DIR]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            
    @classmethod
    def get_config_summary(cls):
        """获取配置摘要（隐藏敏感信息）"""
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.APP_VERSION,
            'web_port': cls.WEB_PORT,
            'web_host': cls.WEB_HOST,
            'database_type': 'sqlite' if 'sqlite' in cls.DATABASE_URL else 'postgresql',
            'proxy_enabled': cls.ENABLE_PROXY,
            'proxy_type': cls.PROXY_TYPE if cls.ENABLE_PROXY else None,
            'admin_count': len(cls.ADMIN_USER_IDS),
            'features': {
                'media_forward': cls.ENABLE_MEDIA_FORWARD,
                'keyword_filter': cls.ENABLE_KEYWORD_FILTER,
                'regex_replace': cls.ENABLE_REGEX_REPLACE,
                'history_crawl': cls.ENABLE_HISTORY_CRAWL,
                'performance_monitoring': cls.ENABLE_PERFORMANCE_MONITORING
            }
        }

def validate_config():
    """验证配置的完整性"""
    errors = []
    warnings = []
    
    # 必需配置检查
    if not Config.API_ID or Config.API_ID == 0:
        errors.append("❌ API_ID 未设置或无效")
    
    if not Config.API_HASH:
        errors.append("❌ API_HASH 未设置")
    
    if not Config.BOT_TOKEN:
        errors.append("❌ BOT_TOKEN 未设置")
    
    if not Config.PHONE_NUMBER:
        errors.append("❌ PHONE_NUMBER 未设置")
    
    # 可选配置警告
    if not Config.ADMIN_USER_IDS:
        warnings.append("⚠️  ADMIN_USER_IDS 未设置，所有用户都可以管理")
    
    if Config.SESSION_SECRET == 'your_random_session_secret_key_here':
        warnings.append("⚠️  SESSION_SECRET 使用默认值，建议修改")
    
    if Config.ENABLE_PROXY and not Config.PROXY_HOST:
        warnings.append("⚠️  启用了代理但未设置 PROXY_HOST")
    
    # 输出结果
    if warnings:
        print("配置警告:")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    if errors:
        error_msg = "配置错误:\n" + "\n".join(f"  {error}" for error in errors)
        raise ValueError(error_msg)
    
    print("✅ 配置验证通过")
    return True

def print_config_info():
    """打印配置信息"""
    print(f"""
🔧 配置信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 应用名称: {Config.APP_NAME}
📊 版本号: {Config.APP_VERSION}
🌐 Web端口: {Config.WEB_PORT}
🗄️  数据库: {"SQLite" if "sqlite" in Config.DATABASE_URL else "PostgreSQL"}
🔌 代理状态: {"启用" if Config.ENABLE_PROXY else "禁用"}
👥 管理员数量: {len(Config.ADMIN_USER_IDS)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)