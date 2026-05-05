# redis_cache.py
"""
Redis缓存模块
缓存高频分析结果，提升查询效率
"""
import os
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Redis缓存管理器
    
    支持：
    - 自动连接管理
    - DataFrame缓存
    - 过期时间设置
    - 键名前缀
    - 连接池
    """
    
    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 6379
    DEFAULT_DB = 0
    DEFAULT_EXPIRE = 3600
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 db: int = DEFAULT_DB, password: Optional[str] = None,
                 key_prefix: str = 'autoda:', default_expire: int = DEFAULT_EXPIRE):
        """
        初始化Redis缓存
        
        Args:
            host: Redis主机
            port: Redis端口
            db: 数据库编号
            password: 密码
            key_prefix: 键名前缀
            default_expire: 默认过期时间（秒）
        """
        self.host = host or os.getenv('REDIS_HOST', self.DEFAULT_HOST)
        self.port = port or int(os.getenv('REDIS_PORT', str(self.DEFAULT_PORT)))
        self.db = db
        self.password = password or os.getenv('REDIS_PASSWORD')
        self.key_prefix = key_prefix
        self.default_expire = default_expire
        self._client = None
        self._connected = False
    
    def _get_client(self):
        """获取Redis客户端（延迟连接）"""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            except ImportError:
                logger.warning("redis模块未安装，缓存功能不可用")
                return None
        return self._client
    
    def connect(self) -> bool:
        """
        测试连接
        
        Returns:
            连接是否成功
        """
        try:
            client = self._get_client()
            if client is None:
                return False
            client.ping()
            self._connected = True
            logger.info(f"Redis连接成功: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.warning(f"Redis连接失败: {str(e)}，缓存功能将不可用")
            self._connected = False
            return False
    
    def disconnect(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._connected = False
            logger.info("Redis连接已关闭")
    
    def _ensure_connected(self) -> bool:
        """确保已连接"""
        if not self._connected:
            return self.connect()
        return True
    
    def _make_key(self, key: str) -> str:
        """生成带前缀的键名"""
        return f"{self.key_prefix}{key}"
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 键名
            value: 值（支持DataFrame、Dict、List等）
            expire: 过期时间（秒），None使用默认值
            
        Returns:
            是否设置成功
        """
        if not self._ensure_connected():
            return False
        
        try:
            full_key = self._make_key(key)
            expire = expire or self.default_expire
            
            if isinstance(value, pd.DataFrame):
                serialized = value.to_json(orient='records', date_format='iso')
            elif isinstance(value, (dict, list)):
                serialized = json.dumps(value, ensure_ascii=False, default=str)
            else:
                serialized = str(value)
            
            self._client.setex(full_key, expire, serialized)
            logger.debug(f"缓存已设置: {full_key} (过期: {expire}s)")
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False
    
    def get(self, key: str, as_dataframe: bool = False) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 键名
            as_dataframe: 是否转换为DataFrame
            
        Returns:
            缓存的值，不存在返回None
        """
        if not self._ensure_connected():
            return None
        
        try:
            full_key = self._make_key(key)
            value = self._client.get(full_key)
            
            if value is None:
                logger.debug(f"缓存不存在: {full_key}")
                return None
            
            if as_dataframe:
                return pd.DataFrame(json.loads(value))
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键名
            
        Returns:
            是否存在
        """
        if not self._ensure_connected():
            return False
        
        try:
            full_key = self._make_key(key)
            return self._client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 键名
            
        Returns:
            是否删除成功
        """
        if not self._ensure_connected():
            return False
        
        try:
            full_key = self._make_key(key)
            self._client.delete(full_key)
            logger.debug(f"缓存已删除: {full_key}")
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {str(e)}")
            return False
    
    def clear_prefix(self) -> int:
        """
        清除所有带前缀的键
        
        Returns:
            删除的键数量
        """
        if not self._ensure_connected():
            return 0
        
        try:
            pattern = f"{self.key_prefix}*"
            keys = self._client.keys(pattern)
            if keys:
                count = self._client.delete(*keys)
                logger.info(f"已清除 {count} 个缓存键")
                return count
            return 0
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return 0
    
    def get_ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间
        
        Args:
            key: 键名
            
        Returns:
            剩余秒数，-1表示永久，-2表示不存在
        """
        if not self._ensure_connected():
            return -2
        
        try:
            full_key = self._make_key(key)
            return self._client.ttl(full_key)
        except Exception:
            return -2
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取缓存状态信息
        
        Returns:
            状态信息字典
        """
        info = {
            'connected': self._connected,
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'key_prefix': self.key_prefix,
            'default_expire': self.default_expire
        }
        
        if self._ensure_connected():
            try:
                info['keys_count'] = len(self._client.keys(f"{self.key_prefix}*"))
                info['memory_usage'] = self._client.info('memory').get('used_memory_human', 'unknown')
            except Exception:
                pass
        
        return info
    
    def cache_query_result(self, query: str, result: pd.DataFrame, 
                          expire: Optional[int] = None) -> bool:
        """
        缓存查询结果（便捷方法）
        
        Args:
            query: SQL查询语句
            result: 查询结果DataFrame
            expire: 过期时间
            
        Returns:
            是否缓存成功
        """
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self.set(f"query:{query_hash}", result, expire)
    
    def get_cached_query_result(self, query: str) -> Optional[pd.DataFrame]:
        """
        获取缓存的查询结果（便捷方法）
        
        Args:
            query: SQL查询语句
            
        Returns:
            缓存的查询结果，不存在返回None
        """
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self.get(f"query:{query_hash}", as_dataframe=True)
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
        return False


def get_cache(config: Optional[Dict[str, Any]] = None) -> RedisCache:
    """
    便捷函数：从配置获取缓存实例
    
    Args:
        config: 配置字典，如果为None则从配置文件加载
        
    Returns:
        RedisCache实例
    """
    if config is None:
        from config_loader import get_cache_config
        config = get_cache_config()
    
    if not config.get('enabled', False):
        logger.info("缓存功能未启用，返回空实现")
        return NoOpCache()
    
    return RedisCache(
        host=config.get('host', 'localhost'),
        port=config.get('port', 6379),
        db=config.get('db', 0),
        key_prefix=config.get('key_prefix', 'autoda:'),
        default_expire=config.get('expire_seconds', 3600)
    )


class NoOpCache:
    """
    空缓存实现（缓存禁用时使用）
    
    提供与RedisCache相同的接口，但不执行任何操作
    """
    
    def __init__(self):
        self._connected = False
    
    def connect(self) -> bool:
        return False
    
    def disconnect(self):
        pass
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        return True
    
    def get(self, key: str, as_dataframe: bool = False) -> Optional[Any]:
        return None
    
    def exists(self, key: str) -> bool:
        return False
    
    def delete(self, key: str) -> bool:
        return True
    
    def clear_prefix(self) -> int:
        return 0
    
    def get_info(self) -> Dict[str, Any]:
        return {'connected': False, 'enabled': False}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
