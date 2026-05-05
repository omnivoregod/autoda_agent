# data_connector/__init__.py
"""
数据连接器模块
支持多种数据源的统一接入
"""

from .base_connector import BaseConnector, QueryExecutionError
from .sqlite_connector import SQLiteConnector

__all__ = ['BaseConnector', 'QueryExecutionError', 'SQLiteConnector']
