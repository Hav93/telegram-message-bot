import re
from typing import List, Optional
from loguru import logger
from models import Keyword, ReplaceRule

class KeywordFilter:
    """关键词过滤器"""
    
    def should_forward(self, text: str, keywords: List[Keyword]) -> bool:
        """
        判断消息是否应该被转发
        
        Args:
            text: 消息文本
            keywords: 关键词列表
            
        Returns:
            bool: True表示应该转发，False表示不转发
        """
        if not text or not keywords:
            return True
        
        text_lower = text.lower()
        
        # 分离包含和排除关键词
        include_keywords = [k for k in keywords if not k.is_exclude]
        exclude_keywords = [k for k in keywords if k.is_exclude]
        
        # 如果有排除关键词且匹配，则不转发
        if exclude_keywords and self._match_keywords(text_lower, exclude_keywords):
            logger.debug(f"消息被排除关键词过滤: {text[:50]}...")
            return False
        
        # 如果没有包含关键词，则转发
        if not include_keywords:
            return True
        
        # 检查是否匹配包含关键词
        if self._match_keywords(text_lower, include_keywords):
            logger.debug(f"消息匹配关键词，准备转发: {text[:50]}...")
            return True
        
        logger.debug(f"消息不匹配任何关键词，跳过转发: {text[:50]}...")
        return False
    
    def _match_keywords(self, text: str, keywords: List[Keyword]) -> bool:
        """检查文本是否匹配关键词列表中的任一关键词"""
        for keyword in keywords:
            if self._match_single_keyword(text, keyword):
                return True
        return False
    
    def _match_single_keyword(self, text: str, keyword: Keyword) -> bool:
        """检查文本是否匹配单个关键词"""
        try:
            if keyword.is_regex:
                # 正则表达式匹配
                pattern = re.compile(keyword.keyword, re.IGNORECASE | re.MULTILINE)
                return bool(pattern.search(text))
            else:
                # 普通字符串匹配
                return keyword.keyword.lower() in text
        except re.error as e:
            logger.error(f"正则表达式错误: {keyword.keyword}, 错误: {e}")
            return False
        except Exception as e:
            logger.error(f"关键词匹配错误: {e}")
            return False

class RegexReplacer:
    """正则表达式替换器"""
    
    def apply_replacements(self, text: str, replace_rules: List[ReplaceRule]) -> str:
        """
        应用替换规则到文本
        
        Args:
            text: 原始文本
            replace_rules: 替换规则列表
            
        Returns:
            str: 处理后的文本
        """
        if not text or not replace_rules:
            return text
        
        # 按优先级排序（数字越小优先级越高）
        sorted_rules = sorted(
            [rule for rule in replace_rules if rule.is_active],
            key=lambda x: x.priority
        )
        
        processed_text = text
        
        for rule in sorted_rules:
            try:
                processed_text = self._apply_single_replacement(processed_text, rule)
            except Exception as e:
                logger.error(f"替换规则应用失败: {rule.pattern}, 错误: {e}")
                continue
        
        return processed_text
    
    def _apply_single_replacement(self, text: str, rule: ReplaceRule) -> str:
        """应用单个替换规则"""
        try:
            pattern = re.compile(rule.pattern, re.MULTILINE | re.DOTALL)
            replaced_text = pattern.sub(rule.replacement, text)
            
            if replaced_text != text:
                logger.debug(f"应用替换规则: {rule.pattern[:50]}...")
            
            return replaced_text
            
        except re.error as e:
            logger.error(f"正则表达式错误: {rule.pattern}, 错误: {e}")
            return text
        except Exception as e:
            logger.error(f"替换操作错误: {e}")
            return text

class MessageProcessor:
    """消息处理器，整合过滤和替换功能"""
    
    def __init__(self):
        self.keyword_filter = KeywordFilter()
        self.regex_replacer = RegexReplacer()
    
    def process_message(self, text: str, keywords: List[Keyword], 
                       replace_rules: List[ReplaceRule]) -> Optional[str]:
        """
        处理消息
        
        Args:
            text: 原始消息文本
            keywords: 关键词列表
            replace_rules: 替换规则列表
            
        Returns:
            Optional[str]: 处理后的文本，如果应该过滤则返回None
        """
        if not text:
            return text
        
        # 关键词过滤
        if keywords and not self.keyword_filter.should_forward(text, keywords):
            return None
        
        # 文本替换
        processed_text = self.regex_replacer.apply_replacements(text, replace_rules)
        
        return processed_text

class ContentExtractor:
    """内容提取器，用于提取标题和内容"""
    
    def __init__(self):
        # 预设的标题提取正则表达式
        self.title_patterns = [
            r'^(.{1,50}?)[\n\r]',  # 第一行作为标题
            r'【(.+?)】',  # 【标题】格式
            r'\*\*(.+?)\*\*',  # **标题**格式
            r'^\s*(.{1,50}?)\s*[:：]',  # 标题: 格式
        ]
        
        # 预设的内容提取正则表达式
        self.content_patterns = [
            r'[\n\r](.+)',  # 第一行之后的内容
            r'】(.+)',  # 】后的内容
            r'\*\*.*?\*\*(.+)',  # **标题**后的内容
        ]
    
    def extract_title(self, text: str, custom_patterns: List[str] = None) -> str:
        """提取标题"""
        if not text:
            return ""
        
        patterns = custom_patterns or self.title_patterns
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                if match:
                    title = match.group(1).strip()
                    if title:
                        return title[:100]  # 限制标题长度
            except re.error as e:
                logger.error(f"标题提取正则错误: {pattern}, 错误: {e}")
                continue
        
        # 如果没有匹配到，返回前20个字符作为标题
        return text[:20].strip()
    
    def extract_content(self, text: str, custom_patterns: List[str] = None) -> str:
        """提取内容"""
        if not text:
            return ""
        
        patterns = custom_patterns or self.content_patterns
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if content:
                        return content
            except re.error as e:
                logger.error(f"内容提取正则错误: {pattern}, 错误: {e}")
                continue
        
        # 如果没有匹配到，返回原文
        return text
    
    def auto_extract(self, text: str, extract_title: bool = True, 
                    extract_content: bool = True,
                    title_patterns: List[str] = None,
                    content_patterns: List[str] = None) -> dict:
        """
        自动提取标题和内容
        
        Returns:
            dict: {'title': str, 'content': str}
        """
        result = {'title': '', 'content': ''}
        
        if not text:
            return result
        
        if extract_title:
            result['title'] = self.extract_title(text, title_patterns)
        
        if extract_content:
            result['content'] = self.extract_content(text, content_patterns)
        else:
            result['content'] = text
        
        return result

class MediaFilter:
    """媒体文件过滤器"""
    
    def __init__(self):
        # 支持的媒体类型
        self.supported_media_types = {
            'photo': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
            'video': ['mp4', 'avi', 'mov', 'mkv', 'webm'],
            'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac'],
            'document': ['pdf', 'doc', 'docx', 'txt', 'zip', 'rar']
        }
        
        # 文件大小限制（字节）
        self.size_limits = {
            'photo': 20 * 1024 * 1024,  # 20MB
            'video': 50 * 1024 * 1024,  # 50MB
            'audio': 50 * 1024 * 1024,  # 50MB
            'document': 20 * 1024 * 1024,  # 20MB
        }
    
    def should_forward_media(self, media, media_type: str = None) -> bool:
        """判断媒体文件是否应该转发"""
        if not media:
            return False
        
        try:
            # 检查文件大小
            if hasattr(media, 'size') and media.size:
                if media_type and media_type in self.size_limits:
                    if media.size > self.size_limits[media_type]:
                        logger.debug(f"媒体文件过大，跳过转发: {media.size} bytes")
                        return False
            
            # 检查文件类型
            if hasattr(media, 'mime_type') and media.mime_type:
                if not self._is_supported_mime_type(media.mime_type):
                    logger.debug(f"不支持的媒体类型: {media.mime_type}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"媒体过滤检查错误: {e}")
            return False
    
    def _is_supported_mime_type(self, mime_type: str) -> bool:
        """检查是否为支持的MIME类型"""
        supported_mimes = [
            'image/', 'video/', 'audio/', 'application/pdf',
            'text/', 'application/zip', 'application/x-rar'
        ]
        
        return any(mime_type.startswith(prefix) for prefix in supported_mimes)
