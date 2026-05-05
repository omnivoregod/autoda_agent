# data_connector/base_connector.py
"""
数据连接器基类
提供统一的接口和通用功能（重试机制、错误处理、日志）
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
import time
import logging
import re

logger = logging.getLogger(__name__)

class QueryExecutionError(Exception):
    """查询执行错误"""
    pass

class ConnectionError(Exception):
    """连接错误"""
    pass

class BaseConnector(ABC):
    """
    数据连接器基类
    
    提供：
    - 重试机制
    - 统一错误处理
    - 日志记录
    - SQL方言适配
    """
    
    DEFAULT_RETRY_CONFIG = {
        'max_attempts': 3,
        'wait_multiplier': 1,
        'wait_min': 2,
        'wait_max': 10
    }
    
    def __init__(self, config: Dict[str, Any], retry_config: Optional[Dict[str, Any]] = None):
        """
        初始化连接器
        
        Args:
            config: 连接配置
            retry_config: 重试配置，覆盖默认配置
        """
        self.config = config
        self.retry_config = {**self.DEFAULT_RETRY_CONFIG, **(retry_config or {})}
        self.connection = None
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.getLogger(__name__).setLevel(getattr(logging, log_level))
    
    @abstractmethod
    def _connect_impl(self):
        """子类实现实际连接逻辑"""
        pass
    
    @abstractmethod
    def _disconnect_impl(self):
        """子类实现实际断开连接逻辑"""
        pass
    
    @abstractmethod
    def _execute_impl(self, query: str) -> pd.DataFrame:
        """子类实现实际查询逻辑"""
        pass
    
    @abstractmethod
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构"""
        pass
    
    def connect(self) -> bool:
        """
        带重试的连接方法
        
        Returns:
            是否连接成功
        """
        max_attempts = self.retry_config.get('max_attempts', 3)
        wait_multiplier = self.retry_config.get('wait_multiplier', 1)
        wait_min = self.retry_config.get('wait_min', 2)
        wait_max = self.retry_config.get('wait_max', 10)
        
        for attempt in range(max_attempts):
            try:
                self._connect_impl()
                logger.info(f"数据库连接成功")
                return True
            except Exception as e:
                wait_time = min(wait_min * (wait_multiplier ** attempt), wait_max)
                logger.warning(f"连接失败 (尝试 {attempt + 1}/{max_attempts}): {str(e)}")
                if attempt < max_attempts - 1:
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"数据库连接最终失败")
                    raise ConnectionError(f"连接失败: {str(e)}")
        
        return False
    
    def disconnect(self):
        """断开连接"""
        try:
            self._disconnect_impl()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.warning(f"关闭连接时出现警告: {str(e)}")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        执行查询（带错误日志）
        
        Args:
            query: SQL查询语句
            
        Returns:
            查询结果DataFrame
        """
        try:
            logger.info(f"执行查询: {self._truncate_query(query)}...")
            result = self._execute_impl(query)
            logger.info(f"查询成功，返回 {len(result)} 行数据")
            return result
        except Exception as e:
            logger.error(f"查询失败: {self._truncate_query(query)}, 错误: {str(e)}")
            raise QueryExecutionError(f"查询执行失败: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        测试连接是否正常
        
        Returns:
            连接是否正常
        """
        try:
            self.connect()
            self.disconnect()
            return True
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            return False
    
    def _truncate_query(self, query: str, max_length: int = 100) -> str:
        """截断查询语句（用于日志）"""
        query = re.sub(r'\s+', ' ', query).strip()
        if len(query) > max_length:
            return query[:max_length] + "..."
        return query
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
        return False
