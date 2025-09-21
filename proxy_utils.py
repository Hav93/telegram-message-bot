# -*- coding: utf-8 -*-
"""
简化的代理配置工具
"""
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class SimpleProxyManager:
    """简化的代理管理器"""
    
    def __init__(self):
        self.enabled = Config.ENABLE_PROXY
        self.proxy_type = Config.PROXY_TYPE
        self.host = Config.PROXY_HOST
        self.port = Config.PROXY_PORT
        self.username = Config.PROXY_USERNAME
        self.password = Config.PROXY_PASSWORD
    
    def get_telethon_proxy(self) -> Optional[Dict[str, Any]]:
        """获取Telethon格式的代理配置"""
        if not self.enabled or not self.host or not self.port:
            return None
        
        try:
            # Telethon需要特定的代理格式
            proxy_type_map = {
                'http': 'http',
                'socks4': 'socks4', 
                'socks5': 'socks5'
            }
            
            telethon_proxy_type = proxy_type_map.get(self.proxy_type.lower(), 'http')
            
            # Telethon代理配置格式
            if telethon_proxy_type == 'http':
                # HTTP代理格式
                proxy_config = (
                    'http',          # 协议类型
                    self.host,       # 代理地址
                    int(self.port),  # 代理端口
                    True,            # rdns
                    self.username if self.username else None,  # 用户名
                    self.password if self.password else None   # 密码
                )
            else:
                # SOCKS代理格式
                proxy_config = (
                    telethon_proxy_type,  # 协议类型 
                    self.host,            # 代理地址
                    int(self.port),       # 代理端口
                    True,                 # rdns
                    self.username if self.username else None,  # 用户名
                    self.password if self.password else None   # 密码
                )
            
            logger.info(f"Telethon代理配置: {self.proxy_type}://{self.host}:{self.port}")
            logger.info(f"代理元组格式: {proxy_config}")
            return proxy_config
            
        except Exception as e:
            logger.error(f"代理配置错误: {e}")
            return None
    
    def get_proxy_info(self) -> Dict[str, Any]:
        """获取代理信息"""
        return {
            'enabled': self.enabled,
            'type': self.proxy_type if self.enabled else None,
            'host': self.host if self.enabled else None,
            'port': self.port if self.enabled else None,
            'status': 'enabled' if self.enabled else 'disabled'
        }
    
    def test_connection(self) -> bool:
        """测试代理连接"""
        if not self.enabled:
            return True
        
        if not self.host or not self.port:
            logger.warning("代理配置不完整")
            return False
            
        try:
            import socket
            import time
            
            # 创建socket连接测试
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # 5秒超时
            
            result = sock.connect_ex((self.host, int(self.port)))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ 代理连接测试成功: {self.host}:{self.port}")
                return True
            else:
                logger.warning(f"❌ 代理连接测试失败: {self.host}:{self.port} (错误码: {result})")
                return False
                
        except Exception as e:
            logger.warning(f"❌ 代理连接测试异常: {e}")
            return False

class ProxyValidator:
    """代理验证器（兼容性类）"""
    
    @staticmethod
    def validate_proxy_config(config: Dict[str, Any]) -> bool:
        """验证代理配置"""
        try:
            required_fields = ['addr', 'port']
            return all(field in config for field in required_fields)
        except:
            return False

# 全局实例缓存
_proxy_manager_instance = None
_config_timestamp = None

def get_proxy_manager():
    """获取代理管理器实例（支持配置更新后重新初始化）"""
    global _proxy_manager_instance, _config_timestamp
    
    # 检查配置文件是否有更新
    import os
    config_file = '.env'
    current_timestamp = None
    
    try:
        if os.path.exists(config_file):
            current_timestamp = os.path.getmtime(config_file)
    except Exception:
        pass
    
    # 如果没有实例或者配置文件已更新，重新创建
    if (_proxy_manager_instance is None or 
        current_timestamp != _config_timestamp):
        
        # 重新加载配置模块
        import importlib
        import config
        importlib.reload(config)
        
        _proxy_manager_instance = SimpleProxyManager()
        _config_timestamp = current_timestamp
        
        proxy_status = "启用" if _proxy_manager_instance.enabled else "禁用"
        logger.info(f"✅ 代理管理器已初始化 - 状态: {proxy_status}")
        
        if _proxy_manager_instance.enabled:
            logger.info(f"🌐 代理配置: {_proxy_manager_instance.proxy_type}://{_proxy_manager_instance.host}:{_proxy_manager_instance.port}")
        else:
            logger.info("🚫 代理已禁用")
    
    return _proxy_manager_instance

def reload_proxy_manager():
    """重新加载代理管理器（配置更新后调用）"""
    global _proxy_manager_instance, _config_timestamp
    _proxy_manager_instance = None
    _config_timestamp = None
    logger.info("🔄 代理管理器已重置，下次获取时将重新初始化")
    return get_proxy_manager()

def validate_and_test_proxy():
    """验证并测试代理配置"""
    manager = get_proxy_manager()
    return manager.test_connection()
