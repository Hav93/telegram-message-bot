import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from config import Config

def setup_logging():
    """设置日志"""
    import os
    
    # 配置loguru
    logger.remove()  # 移除默认处理器
    
    # 尝试添加文件处理器
    try:
        # 创建日志目录
        log_file = Path(Config.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 尝试创建日志文件并设置权限
        if not log_file.exists():
            log_file.touch()
            os.chmod(log_file, 0o666)  # 设置文件权限
        
        # 添加文件处理器
        logger.add(
            Config.LOG_FILE,
            rotation="10 MB",
            retention="7 days",
            level=Config.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            encoding="utf-8"
        )
        print(f"📄 日志文件: {Config.LOG_FILE}")
    except (PermissionError, OSError) as e:
        print(f"⚠️  无法创建日志文件 {Config.LOG_FILE}: {e}")
        print("📝 日志将仅输出到控制台")
    
    # 添加控制台处理器
    logger.add(
        lambda msg: print(msg, end=""),
        level=Config.LOG_LEVEL,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    return logger

def is_admin(user_id: int) -> bool:
    """检查用户是否为管理员"""
    return user_id in Config.ADMIN_USER_IDS

def parse_chat_link(link: str) -> Optional[Dict[str, Any]]:
    """解析Telegram聊天链接"""
    patterns = [
        r'https?://t\.me/([a-zA-Z0-9_]+)',
        r'https?://telegram\.me/([a-zA-Z0-9_]+)',
        r'@([a-zA-Z0-9_]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            username = match.group(1)
            return {
                'username': username,
                'type': 'username'
            }
    
    # 尝试解析私有群组链接
    private_pattern = r'https?://t\.me/c/(\d+)/(\d+)'
    match = re.search(private_pattern, link)
    if match:
        chat_id = int(match.group(1))
        message_id = int(match.group(2))
        return {
            'chat_id': -1000000000000 - chat_id,  # 转换为实际的chat_id
            'message_id': message_id,
            'type': 'private_group'
        }
    
    return None

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    # 移除或替换不安全的字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # 移除多余的空格和点
    filename = re.sub(r'\s+', ' ', filename).strip()
    filename = filename.strip('.')
    
    # 确保文件名不为空
    if not filename:
        filename = "unnamed_file"
    
    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_len] + ('.' + ext if ext else '')
    
    return filename

def extract_message_entities(message):
    """提取消息实体信息"""
    entities = {
        'urls': [],
        'mentions': [],
        'hashtags': [],
        'bold': [],
        'italic': [],
        'code': []
    }
    
    if not message.entities:
        return entities
    
    text = message.text or ""
    
    for entity in message.entities:
        start = entity.offset
        end = entity.offset + entity.length
        entity_text = text[start:end]
        
        entity_type = type(entity).__name__
        
        if 'Url' in entity_type:
            entities['urls'].append(entity_text)
        elif 'Mention' in entity_type:
            entities['mentions'].append(entity_text)
        elif 'Hashtag' in entity_type:
            entities['hashtags'].append(entity_text)
        elif 'Bold' in entity_type:
            entities['bold'].append(entity_text)
        elif 'Italic' in entity_type:
            entities['italic'].append(entity_text)
        elif 'Code' in entity_type:
            entities['code'].append(entity_text)
    
    return entities

def validate_regex(pattern: str) -> bool:
    """验证正则表达式是否有效"""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False

def escape_markdown(text: str) -> str:
    """转义Markdown特殊字符"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def truncate_text(text: str, max_length: int = 4096) -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    
    # 尝试在单词边界截断
    if max_length > 10:
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # 如果最后一个空格位置合理
            return truncated[:last_space] + "..."
    
    return text[:max_length-3] + "..."

class RateLimiter:
    """简单的速率限制器"""
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, key: str) -> bool:
        """检查是否允许请求"""
        import time
        now = time.time()
        
        # 清理过期记录
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < self.time_window
            ]
        
        # 检查当前请求数
        current_requests = len(self.requests.get(key, []))
        if current_requests >= self.max_requests:
            return False
        
        # 记录当前请求
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key].append(now)
        
        return True
