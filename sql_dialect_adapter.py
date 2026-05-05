# sql_dialect_adapter.py
"""
SQL方言适配器
处理不同数据库的SQL语法差异
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class SQLDialect(Enum):
    """支持的SQL方言"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    CLICKHOUSE = "clickhouse"

class SQLDialectAdapter:
    """
    SQL方言适配器
    
    处理不同数据库的SQL语法差异：
    - LIMIT/OFFSET
    - 字符串函数（IFNULL vs COALESCE）
    - 日期函数（NOW vs NOW()）
    - 字符串拼接
    - 类型转换
    """
    
    DIALECT_FUNCTIONS = {
        'mysql': {
            'ifnull': 'IFNULL',
            'now': 'NOW()',
            'date_format': 'DATE_FORMAT',
            'concat': 'CONCAT',
            'substring': 'SUBSTRING',
            'length': 'LENGTH',
            'upper': 'UPPER',
            'lower': 'LOWER',
            'round': 'ROUND',
            'cast': 'CAST',
            'limit': 'LIMIT',
            'top': 'LIMIT'
        },
        'postgresql': {
            'ifnull': 'COALESCE',
            'now': 'NOW()',
            'date_format': 'TO_CHAR',
            'concat': 'CONCAT',
            'substring': 'SUBSTRING',
            'length': 'LENGTH',
            'upper': 'UPPER',
            'lower': 'LOWER',
            'round': 'ROUND',
            'cast': 'CAST',
            'limit': 'LIMIT',
            'top': 'LIMIT'
        },
        'sqlite': {
            'ifnull': 'IFNULL',
            'now': "datetime('now')",
            'date_format': 'STRFTIME',
            'concat': '||',
            'substring': 'SUBSTR',
            'length': 'LENGTH',
            'upper': 'UPPER',
            'lower': 'LOWER',
            'round': 'ROUND',
            'cast': 'CAST',
            'limit': 'LIMIT',
            'top': 'LIMIT'
        },
        'clickhouse': {
            'ifnull': 'ifNull',
            'now': 'now()',
            'date_format': 'formatDateTime',
            'concat': 'concat',
            'substring': 'substring',
            'length': 'length',
            'upper': 'upper',
            'lower': 'lower',
            'round': 'round',
            'cast': 'CAST',
            'limit': 'LIMIT',
            'top': 'LIMIT'
        }
    }
    
    def __init__(self, dialect: str = 'sqlite'):
        """
        初始化适配器
        
        Args:
            dialect: 目标数据库类型
        """
        self.dialect = dialect.lower()
        if self.dialect not in [d.value for d in SQLDialect]:
            logger.warning(f"未知的方言: {dialect}，使用sqlite作为默认值")
            self.dialect = 'sqlite'
        self.functions = self.DIALECT_FUNCTIONS.get(self.dialect, self.DIALECT_FUNCTIONS['sqlite'])
    
    def adapt_sql(self, sql: str) -> str:
        """
        转换SQL以适配目标方言
        
        Args:
            sql: 原始SQL语句
            
        Returns:
            适配后的SQL语句
        """
        adapted_sql = sql
        
        adapted_sql = self._adapt_limit(adapted_sql)
        adapted_sql = self._adapt_string_functions(adapted_sql)
        adapted_sql = self._adapt_date_functions(adapted_sql)
        adapted_sql = self._adapt_concat(adapted_sql)
        adapted_sql = self._adapt_type_cast(adapted_sql)
        
        logger.debug(f"SQL适配完成 ({self.dialect}): {self._truncate_sql(adapted_sql)}")
        return adapted_sql
    
    def _adapt_limit(self, sql: str) -> str:
        """处理LIMIT/OFFSET"""
        limit_match = re.search(r'LIMIT\s+(\d+)(?:\s+OFFSET\s+(\d+))?', sql, re.IGNORECASE)
        if limit_match:
            limit = limit_match.group(1)
            offset = limit_match.group(2) or '0'
            
            if self.dialect == 'sqlite':
                new_clause = f'LIMIT {limit} OFFSET {offset}'
            elif self.dialect == 'mysql':
                new_clause = f'LIMIT {offset}, {limit}'
            elif self.dialect == 'postgresql':
                new_clause = f'LIMIT {limit} OFFSET {offset}'
            elif self.dialect == 'clickhouse':
                new_clause = f'LIMIT {limit} OFFSET {offset}'
            else:
                new_clause = limit_match.group(0)
            
            sql = re.sub(r'LIMIT\s+\d+(?:\s+OFFSET\s+\d+)?', new_clause, sql, flags=re.IGNORECASE)
        
        return sql
    
    def _adapt_string_functions(self, sql: str) -> str:
        """转换字符串函数"""
        if self.dialect == 'postgresql':
            sql = re.sub(r'IFNULL\s*\(', 'COALESCE(', sql, flags=re.IGNORECASE)
        elif self.dialect == 'sqlite':
            pass
        elif self.dialect == 'clickhouse':
            sql = re.sub(r'IFNULL\s*\(', 'ifNull(', sql, flags=re.IGNORECASE)
        
        return sql
    
    def _adapt_date_functions(self, sql: str) -> str:
        """转换日期函数"""
        if self.dialect == 'sqlite':
            sql = re.sub(r'NOW\(\)', "datetime('now')", sql, flags=re.IGNORECASE)
            sql = re.sub(r"DATE_FORMAT\s*\(\s*([^,]+),\s*'([^']+)'\s*\)",
                        lambda m: self._sqlite_strftime(m.group(1), m.group(2)), sql, flags=re.IGNORECASE)
        elif self.dialect == 'postgresql':
            sql = re.sub(r"DATE_FORMAT\s*\(\s*([^,]+),\s*'([^']+)'\s*\)",
                        lambda m: f"TO_CHAR({m.group(1)}, '{m.group(2)}')", sql, flags=re.IGNORECASE)
        
        return sql
    
    def _sqlite_strftime(self, date_expr: str, format_str: str) -> str:
        """将MySQL DATE_FORMAT转换为SQLite STRFTIME"""
        format_map = {
            '%Y': '%Y',
            '%m': '%m',
            '%d': '%d',
            '%H': '%H',
            '%i': '%M',
            '%s': '%S',
            '%Y-%m-%d': '%Y-%m-%d',
            '%Y-%m-%d %H:%i:%s': '%Y-%m-%d %H:%M:%S'
        }
        sqlite_format = format_map.get(format_str, format_str)
        return f"STRFTIME('{sqlite_format}', {date_expr})"
    
    def _adapt_concat(self, sql: str) -> str:
        """处理字符串拼接"""
        if self.dialect == 'sqlite':
            sql = re.sub(r"CONCAT\s*\(([^)]+)\)",
                        lambda m: self._sqlite_concat(m.group(1)), sql, flags=re.IGNORECASE)
        return sql
    
    def _sqlite_concat(self, args: str) -> str:
        """将CONCAT转换为SQLite的||语法"""
        parts = [p.strip() for p in args.split(',')]
        return '(' + ' || '.join(parts) + ')'
    
    def _adapt_type_cast(self, sql: str) -> str:
        """处理类型转换"""
        if self.dialect == 'postgresql':
            sql = re.sub(r"CAST\s*\(\s*([^ ]+)\s+AS\s+VARCHAR\s*\)",
                        r'CAST(\1 AS TEXT)', sql, flags=re.IGNORECASE)
            sql = re.sub(r"CAST\s*\(\s*([^ ]+)\s+AS\s+INT\s*\)",
                        r'CAST(\1 AS INTEGER)', sql, flags=re.IGNORECASE)
        elif self.dialect == 'sqlite':
            sql = re.sub(r"CAST\s*\(\s*([^ ]+)\s+AS\s+INT\s*\)",
                        r'CAST(\1 AS INTEGER)', sql, flags=re.IGNORECASE)
        return sql
    
    def _truncate_sql(self, sql: str, max_length: int = 100) -> str:
        """截断SQL（用于日志）"""
        sql = re.sub(r'\s+', ' ', sql).strip()
        if len(sql) > max_length:
            return sql[:max_length] + "..."
        return sql
    
    def get_dialect(self) -> str:
        """获取当前方言"""
        return self.dialect


class QueryBuilder:
    """
    SQL查询构建器
    根据目标方言构建跨数据库兼容的SQL
    """
    
    def __init__(self, dialect: str = 'sqlite'):
        self.adapter = SQLDialectAdapter(dialect)
    
    def select(self, table: str, columns: List[str] = None,
               where: Optional[str] = None, order_by: Optional[str] = None,
               limit: Optional[int] = None, offset: Optional[int] = None) -> str:
        """
        构建SELECT查询
        
        Args:
            table: 表名
            columns: 列名列表，None表示所有列
            where: WHERE条件
            order_by: 排序字段
            limit: 限制返回行数
            offset: 偏移量
            
        Returns:
            SQL语句
        """
        cols = ', '.join(columns) if columns else '*'
        sql = f"SELECT {cols} FROM {table}"
        
        if where:
            sql += f" WHERE {where}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit is not None:
            if offset is not None:
                sql += f" LIMIT {limit} OFFSET {offset}"
            else:
                sql += f" LIMIT {limit}"
        
        return self.adapter.adapt_sql(sql)
    
    def count(self, table: str, where: Optional[str] = None) -> str:
        """构建COUNT查询"""
        sql = f"SELECT COUNT(*) FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return self.adapter.adapt_sql(sql)
    
    def insert(self, table: str, data: Dict[str, any]) -> str:
        """构建INSERT语句"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return sql
    
    def update(self, table: str, data: Dict[str, any], where: str) -> str:
        """构建UPDATE语句"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        return sql
    
    def delete(self, table: str, where: str) -> str:
        """构建DELETE语句"""
        sql = f"DELETE FROM {table} WHERE {where}"
        return sql


def adapt_sql_for_dialect(sql: str, dialect: str) -> str:
    """
    便捷函数：转换SQL到指定方言
    
    Args:
        sql: 原始SQL
        dialect: 目标方言
        
    Returns:
        适配后的SQL
    """
    adapter = SQLDialectAdapter(dialect)
    return adapter.adapt_sql(sql)
