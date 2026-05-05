# data_connector/sqlite_connector.py
"""
SQLite连接器
用于本地SQLite数据库的连接和查询
"""
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path

from .base_connector import BaseConnector, QueryExecutionError

class SQLiteConnector(BaseConnector):
    """
    SQLite数据库连接器
    
    支持：
    - 自动创建数据库文件
    - 内存数据库
    - 查询重试
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化SQLite连接器
        
        Args:
            config: 连接配置，包含：
                - path: 数据库文件路径（默认：ecommerce.db）
                - timeout: 连接超时时间（默认：30）
                - check_same_thread: 是否检查同一线程（默认：False）
        """
        if config is None:
            config = {}
        
        default_config = {
            'path': 'ecommerce.db',
            'timeout': 30,
            'check_same_thread': False
        }
        
        merged_config = {**default_config, **config}
        super().__init__(merged_config)
        
        self.db_path = self.config.get('path', 'ecommerce.db')
        self.timeout = self.config.get('timeout', 30)
        self.check_same_thread = self.config.get('check_same_thread', False)
    
    def _connect_impl(self):
        """建立SQLite连接"""
        self.connection = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=self.check_same_thread
        )
        self.connection.row_factory = sqlite3.Row
    
    def _disconnect_impl(self):
        """关闭SQLite连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def _execute_impl(self, query: str) -> pd.DataFrame:
        """执行SQL查询"""
        if not self.connection:
            raise QueryExecutionError("数据库未连接")
        
        query = query.strip()
        is_select = query.upper().startswith('SELECT')
        
        if is_select:
            return pd.read_sql_query(query, self.connection)
        else:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            return pd.DataFrame({'affected_rows': [cursor.rowcount]})
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构
        
        Args:
            table_name: 表名
            
        Returns:
            字段列表，每个字段包含name、type、nullable、default、pk信息
        """
        if not self.connection:
            raise QueryExecutionError("数据库未连接")
        
        query = f"PRAGMA table_info({table_name})"
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[1],
                'type': row[2],
                'nullable': not row[3],
                'default': row[4],
                'pk': row[5] == 1
            })
        
        return columns
    
    def get_all_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            表名列表
        """
        if not self.connection:
            raise QueryExecutionError("数据库未连接")
        
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        return [row[0] for row in cursor.fetchall()]
    
    def execute_script(self, script: str) -> List[pd.DataFrame]:
        """
        执行SQL脚本（支持多条语句）
        
        Args:
            script: SQL脚本
            
        Returns:
            每个SELECT语句的结果列表
        """
        if not self.connection:
            raise QueryExecutionError("数据库未连接")
        
        results = []
        cursor = self.connection.cursor()
        
        for statement in script.split(';'):
            statement = statement.strip()
            if statement.upper().startswith('SELECT'):
                df = pd.read_sql_query(statement, self.connection)
                results.append(df)
            elif statement:
                cursor.execute(statement)
                self.connection.commit()
        
        return results
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            表是否存在
        """
        if not self.connection:
            raise QueryExecutionError("数据库未连接")
        
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        return cursor.fetchone() is not None
    
    def get_row_count(self, table_name: str) -> int:
        """
        获取表的行数
        
        Args:
            table_name: 表名
            
        Returns:
            行数
        """
        if not self.connection:
            raise QueryExecutionError("数据库未连接")
        
        query = f"SELECT COUNT(*) FROM {table_name}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        return cursor.fetchone()[0]
