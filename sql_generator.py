"""
SQL生成器模块
将DSL语句转换为可执行的SQL查询
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SQLQuery:
    """SQL查询数据结构"""
    sql: str
    params: tuple
    description: str
    risk_level: str  # 'low', 'medium', 'high'


class SQLGenerator:
    """SQL生成器 - 将DSL语句转换为SQL查询"""

    def __init__(self):
        self.table_schemas = self._init_table_schemas()

    def _init_table_schemas(self) -> Dict[str, Dict[str, Any]]:
        """初始化表schema信息"""
        return {
            'customers': {
                'columns': ['customer_id', 'name', 'email', 'country', 'age', 'signup_date', 'marketing_opt_in'],
                'primary_key': 'customer_id',
                'joins': {
                    'orders': 'customer_id'
                }
            },
            'orders': {
                'columns': ['order_id', 'customer_id', 'order_time', 'payment_method', 'discount_pct', 'subtotal_usd', 'total_usd', 'country', 'device', 'source'],
                'primary_key': 'order_id',
                'joins': {
                    'customers': 'customer_id',
                    'order_items': 'order_id'
                }
            },
            'products': {
                'columns': ['product_id', 'category', 'name', 'price_usd', 'cost_usd', 'margin_usd'],
                'primary_key': 'product_id',
                'joins': {
                    'order_items': 'product_id'
                }
            },
            'order_items': {
                'columns': ['order_id', 'product_id', 'unit_price_usd', 'quantity', 'line_total_usd'],
                'primary_key': None,
                'joins': {
                    'orders': 'order_id',
                    'products': 'product_id'
                }
            },
            'events': {
                'columns': ['event_id', 'session_id', 'timestamp', 'event_type', 'product_id', 'qty', 'cart_size', 'payment', 'discount_pct', 'amount_usd'],
                'primary_key': 'event_id',
                'joins': {
                    'sessions': 'session_id'
                }
            },
            'reviews': {
                'columns': ['review_id', 'order_id', 'product_id', 'rating', 'review_text', 'review_time'],
                'primary_key': 'review_id',
                'joins': {
                    'orders': 'order_id',
                    'products': 'product_id'
                }
            },
            'sessions': {
                'columns': ['session_id', 'customer_id', 'start_time', 'device', 'source', 'country'],
                'primary_key': 'session_id',
                'joins': {
                    'customers': 'customer_id',
                    'events': 'session_id'
                }
            }
        }

    def generate(self, dsl, db_schema: Optional[Dict[str, Any]] = None) -> SQLQuery:
        """
        生成SQL查询

        Args:
            dsl: DSL语句对象
            db_schema: 数据库schema信息（可选）

        Returns:
            SQLQuery: SQL查询对象
        """
        if dsl.dsl_type == 'funnel':
            return self._generate_funnel_sql(dsl)
        elif dsl.dsl_type == 'rfm':
            return self._generate_rfm_sql(dsl)
        elif dsl.dsl_type == 'ab_test':
            return self._generate_ab_test_sql(dsl)
        elif dsl.dsl_type == 'trend':
            return self._generate_trend_sql(dsl)
        elif dsl.dsl_type == 'distribution':
            return self._generate_distribution_sql(dsl)
        elif dsl.dsl_type == 'comparison':
            return self._generate_comparison_sql(dsl)
        else:
            return self._generate_custom_sql(dsl)

    def _generate_funnel_sql(self, dsl) -> SQLQuery:
        """生成漏斗分析SQL"""
        sql = """
SELECT 
    event_type,
    COUNT(DISTINCT session_id) as step_count,
    COUNT(DISTINCT session_id) * 1.0 / (SELECT COUNT(DISTINCT session_id) FROM events WHERE event_type IN ('Page View', 'View')) as conversion_rate
FROM events
WHERE session_id IS NOT NULL
  AND event_type IN ('Page View', 'View', 'Add to Cart', 'Cart', 'Purchase')
GROUP BY event_type
ORDER BY CASE 
    WHEN event_type IN ('Page View', 'View') THEN 1
    WHEN event_type IN ('Add to Cart', 'Cart') THEN 2
    WHEN event_type = 'Purchase' THEN 3
    ELSE 4
END
"""
        return SQLQuery(
            sql=sql.strip(),
            params=(),
            description="转化漏斗分析查询",
            risk_level='low'
        )

    def _generate_rfm_sql(self, dsl) -> SQLQuery:
        """生成RFM分析SQL"""
        sql = """
WITH rfm_base AS (
    SELECT 
        session_id as user_id,
        MAX(timestamp) as last_event_date,
        COUNT(*) as frequency,
        SUM(amount_usd) as monetary
    FROM events
    WHERE event_type = 'Purchase'
    GROUP BY session_id
)
SELECT 
    user_id,
    last_event_date,
    frequency,
    monetary,
    DATE('now') - DATE(last_event_date) as recency_days,
    CASE 
        WHEN DATE('now') - DATE(last_event_date) <= 7 THEN 5
        WHEN DATE('now') - DATE(last_event_date) <= 14 THEN 4
        WHEN DATE('now') - DATE(last_event_date) <= 30 THEN 3
        WHEN DATE('now') - DATE(last_event_date) <= 60 THEN 2
        ELSE 1
    END as r_score,
    CASE 
        WHEN frequency >= 10 THEN 5
        WHEN frequency >= 5 THEN 4
        WHEN frequency >= 3 THEN 3
        WHEN frequency >= 2 THEN 2
        ELSE 1
    END as f_score,
    CASE 
        WHEN monetary >= 1000 THEN 5
        WHEN monetary >= 500 THEN 4
        WHEN monetary >= 200 THEN 3
        WHEN monetary >= 100 THEN 2
        ELSE 1
    END as m_score
FROM rfm_base
"""
        return SQLQuery(
            sql=sql.strip(),
            params=(),
            description="RFM分析查询",
            risk_level='low'
        )

    def _generate_ab_test_sql(self, dsl) -> SQLQuery:
        """生成A/B测试SQL"""
        sql = """
SELECT 
    CASE 
        WHEN discount_pct > 0 THEN 'A'  -- 有折扣组
        ELSE 'B'  -- 无折扣组
    END as group_name,
    COUNT(DISTINCT session_id) as total_users,
    SUM(CASE WHEN event_type = 'Purchase' THEN 1 ELSE 0 END) as conversions,
    SUM(CASE WHEN event_type = 'Purchase' THEN 1 ELSE 0 END) * 1.0 / COUNT(DISTINCT session_id) as conversion_rate
FROM events
WHERE session_id IS NOT NULL
GROUP BY CASE 
    WHEN discount_pct > 0 THEN 'A'
    ELSE 'B'
END
"""
        return SQLQuery(
            sql=sql.strip(),
            params=(),
            description="A/B组转化率分析查询",
            risk_level='low'
        )

    def _generate_trend_sql(self, dsl) -> SQLQuery:
        """生成趋势分析SQL"""
        table_name = dsl.source if dsl.source in self.table_schemas else 'orders'
        time_field = 'order_time' if table_name == 'orders' else 'timestamp'
        
        # 确定时间聚合粒度
        granularity = 'day'
        if hasattr(dsl, 'granularity'):
            granularity = dsl.granularity

        # 构建聚合函数
        agg_expressions = []
        for measure in dsl.measures:
            if measure == 'count':
                agg_expressions.append('COUNT(*) as total_count')
            elif measure == 'sum':
                agg_expressions.append('SUM(total_usd) as total_amount')
            elif measure == 'avg':
                agg_expressions.append('AVG(total_usd) as avg_amount')

        if not agg_expressions:
            agg_expressions = ['COUNT(*) as total_count']

        agg_clause = ', '.join(agg_expressions)
        
        # 构建GROUP BY子句
        if granularity == 'day':
            group_by_expr = f"DATE({time_field})"
            select_expr = f"DATE({time_field}) as time_period"
        elif granularity == 'week':
            group_by_expr = f"strftime('%Y-%W', {time_field})"
            select_expr = f"strftime('%Y-%W', {time_field}) as time_period"
        elif granularity == 'month':
            group_by_expr = f"strftime('%Y-%m', {time_field})"
            select_expr = f"strftime('%Y-%m', {time_field}) as time_period"
        else:
            group_by_expr = f"DATE({time_field})"
            select_expr = f"DATE({time_field}) as time_period"

        # 构建过滤条件
        where_conditions = ['1=1']
        if dsl.filters:
            for filter_expr in dsl.filters:
                if '=' in filter_expr:
                    where_conditions.append(filter_expr)

        where_clause = ' AND '.join(where_conditions)

        sql = f"""
SELECT 
    {select_expr},
    {agg_clause}
FROM {table_name}
WHERE {where_clause}
GROUP BY {group_by_expr}
ORDER BY {group_by_expr}
LIMIT 100
"""
        return SQLQuery(
            sql=sql.strip(),
            params=(),
            description=f"趋势分析查询（按{granularity}聚合）",
            risk_level='low'
        )

    def _generate_distribution_sql(self, dsl) -> SQLQuery:
        """生成分布分析SQL"""
        table_name = dsl.source if dsl.source in self.table_schemas else 'orders'
        field_name = dsl.dimensions[0] if dsl.dimensions else 'age'

        # 检查字段是否存在
        if field_name not in self.table_schemas.get(table_name, {}).get('columns', []):
            # 使用备用字段
            if table_name == 'orders':
                field_name = 'total_usd'
            elif table_name == 'customers':
                field_name = 'age'

        # 构建聚合表达式
        agg_expressions = []
        for measure in dsl.measures:
            if measure == 'count':
                agg_expressions.append(f'COUNT(*) as count')
            elif measure == 'avg':
                agg_expressions.append(f'AVG({field_name}) as avg_value')
            elif measure == 'sum':
                agg_expressions.append(f'SUM({field_name}) as sum_value')

        if not agg_expressions:
            agg_expressions = ['COUNT(*) as count']

        agg_clause = ', '.join(agg_expressions)

        # 构建GROUP BY子句
        if field_name == 'age':
            group_by_expr = """
                CASE 
                    WHEN age < 20 THEN '20岁以下'
                    WHEN age >= 20 AND age < 30 THEN '20-29岁'
                    WHEN age >= 30 AND age < 40 THEN '30-39岁'
                    WHEN age >= 40 AND age < 50 THEN '40-49岁'
                    WHEN age >= 50 AND age < 60 THEN '50-59岁'
                    ELSE '60岁以上'
                END as age_group
            """
            select_expr = f"""
                CASE 
                    WHEN age < 20 THEN '20岁以下'
                    WHEN age >= 20 AND age < 30 THEN '20-29岁'
                    WHEN age >= 30 AND age < 40 THEN '30-39岁'
                    WHEN age >= 40 AND age < 50 THEN '40-49岁'
                    WHEN age >= 50 AND age < 60 THEN '50-59岁'
                    ELSE '60岁以上'
                END as age_group
            """
        else:
            group_by_expr = field_name
            select_expr = field_name

        # 构建过滤条件
        where_conditions = ['1=1']
        if dsl.filters:
            for filter_expr in dsl.filters:
                if '=' in filter_expr:
                    where_conditions.append(filter_expr)

        where_clause = ' AND '.join(where_conditions)

        sql = f"""
SELECT 
    {select_expr},
    {agg_clause}
FROM {table_name}
WHERE {where_clause}
GROUP BY {group_by_expr}
ORDER BY count DESC
LIMIT 20
"""
        return SQLQuery(
            sql=sql.strip(),
            params=(),
            description="分布分析查询",
            risk_level='low'
        )

    def _generate_comparison_sql(self, dsl) -> SQLQuery:
        """生成比较分析SQL"""
        table_name = dsl.source if dsl.source in self.table_schemas else 'orders'
        
        # 构建GROUP BY子句
        group_by_field = dsl.dimensions[0] if dsl.dimensions else 'category'

        # 构建聚合表达式
        agg_expressions = []
        for measure in dsl.measures:
            if measure == 'count':
                agg_expressions.append('COUNT(*) as total_count')
            elif measure == 'sum':
                agg_expressions.append('SUM(total_usd) as total_amount')
            elif measure == 'avg':
                agg_expressions.append('AVG(total_usd) as avg_amount')

        if not agg_expressions:
            agg_expressions = ['COUNT(*) as total_count']

        agg_clause = ', '.join(agg_expressions)

        # 构建ORDER BY子句
        order_by_clause = f"ORDER BY total_count DESC" if 'count' in agg_clause else ""

        # 构建过滤条件
        where_conditions = ['1=1']
        if dsl.filters:
            for filter_expr in dsl.filters:
                if '=' in filter_expr:
                    where_conditions.append(filter_expr)

        where_clause = ' AND '.join(where_conditions)

        sql = f"""
SELECT 
    {group_by_field},
    {agg_clause}
FROM {table_name}
WHERE {where_clause}
GROUP BY {group_by_field}
{order_by_clause}
LIMIT 20
"""
        return SQLQuery(
            sql=sql.strip(),
            params=(),
            description="比较分析查询",
            risk_level='low'
        )

    def _generate_custom_sql(self, dsl) -> SQLQuery:
        """生成自定义分析SQL"""
        table_name = dsl.source if dsl.source in self.table_schemas else 'orders'

        # 构建SELECT子句
        select_fields = []
        if dsl.dimensions:
            select_fields.extend(dsl.dimensions)
        if dsl.measures:
            for measure in dsl.measures:
                if measure == 'count':
                    select_fields.append('COUNT(*) as total_count')
                elif measure == 'sum':
                    select_fields.append('SUM(total_usd) as total_amount')
                elif measure == 'avg':
                    select_fields.append('AVG(total_usd) as avg_amount')
                else:
                    select_fields.append(measure)

        if not select_fields:
            select_fields = ['*']

        select_clause = ', '.join(select_fields)

        # 构建WHERE子句
        where_conditions = ['1=1']
        if dsl.filters:
            for filter_expr in dsl.filters:
                if '=' in filter_expr:
                    where_conditions.append(filter_expr)

        where_clause = ' AND '.join(where_conditions)

        # 构建ORDER BY子句
        order_by_clause = ""
        if dsl.order_by:
            order_by_clause = f"ORDER BY {', '.join(dsl.order_by)}"

        # 构建LIMIT子句
        limit_clause = f"LIMIT {dsl.limit}" if dsl.limit else "LIMIT 1000"

        sql = f"""
SELECT {select_clause}
FROM {table_name}
WHERE {where_clause}
{order_by_clause}
{limit_clause}
"""
        return SQLQuery(
            sql=sql.strip(),
            params=(),
            description="自定义分析查询",
            risk_level='medium'
        )

    def validate_sql(self, sql: str) -> tuple:
        """
        验证SQL的安全性

        Args:
            sql: SQL查询字符串

        Returns:
            tuple: (is_valid, error_message)
        """
        # 检查是否包含危险关键字
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE',
            'INSERT', 'UPDATE', 'GRANT', 'REVOKE'
        ]

        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                return False, f"禁止使用关键字: {keyword}"

        # 检查SQL长度
        if len(sql) > 5000:
            return False, "SQL语句过长"

        return True, ""

    def generate_from_standard_dsl(self, standard_dsl: Dict[str, Any], db_schema: Dict[str, Any]) -> Dict[str, str]:
        """
        从标准DSL生成SQL查询

        Args:
            standard_dsl: 标准DSL格式
            db_schema: 数据库schema信息

        Returns:
            Dict: 包含SQL查询的字典
        """
        # 确定数据源
        analysis_type = standard_dsl.get('analysis_type', '')
        # 检查是否有用户指定的表名
        table_name = standard_dsl.get('source', '')
        if not table_name or table_name not in db_schema.get('tables', {}):
            table_name = self._get_table_name(analysis_type, standard_dsl, db_schema)

        # 获取表的实际字段
        table_columns = db_schema.get('tables', {}).get(table_name, {}).get('columns', [])

        # 构建SELECT子句
        select_clause = self._build_select_clause(standard_dsl, table_name)

        # 构建WHERE子句（包含时间过滤）
        where_clause = self._build_where_clause(standard_dsl, table_name)

        # 构建GROUP BY子句
        group_by_clause = self._build_group_by_clause(standard_dsl)

        # 构建ORDER BY子句
        order_by_clause = self._build_order_by_clause(standard_dsl)

        # 构建完整的SQL
        sql = f"""
SELECT {select_clause}
FROM {table_name}
WHERE {where_clause}
{group_by_clause}
{order_by_clause}
LIMIT 1000
""".strip()

        # 验证SQL
        is_valid, error_msg = self.validate_sql(sql)
        if not is_valid:
            raise ValueError(f"SQL验证失败: {error_msg}")

        return {"sql": sql}

    def _get_table_name(self, analysis_type: str, standard_dsl: Dict[str, Any], db_schema: Dict[str, Any]) -> str:
        """
        获取表名

        Args:
            analysis_type: 分析类型
            standard_dsl: 标准DSL格式
            db_schema: 数据库schema信息

        Returns:
            str: 表名
        """
        # 根据分析类型选择表
        table_mapping = {
            '漏斗分析': 'events',
            'A/B测试': 'events',
            'RFM分析': 'events',
            '趋势分析': 'orders',
            '分布分析': 'orders',
            '比较分析': 'orders'
        }

        table_name = table_mapping.get(analysis_type, 'orders')

        # 确保表存在于schema中
        if table_name not in db_schema.get('tables', {}):
            table_name = 'orders'  # 默认表

        return table_name

    def _build_select_clause(self, standard_dsl: Dict[str, Any], table_name: str) -> str:
        """
        构建SELECT子句

        Args:
            standard_dsl: 标准DSL格式
            table_name: 表名

        Returns:
            str: SELECT子句
        """
        select_fields = []

        # 获取表的实际字段
        table_columns = self.table_schemas.get(table_name, {}).get('columns', [])

        # 如果没有指定字段，根据表名添加默认字段
        if not standard_dsl.get('dimensions') and not standard_dsl.get('metrics'):
            if table_name == 'orders':
                # 订单表的默认字段
                default_fields = ['order_id', 'customer_id', 'order_time', 'total_usd', 'payment_method', 'country']
                select_fields = [field for field in default_fields if field in table_columns]
            else:
                # 其他表的默认字段
                select_fields = table_columns[:5]  # 取前5个字段

        # 添加维度字段
        for dimension in standard_dsl.get('dimensions', []):
            # 确保字段存在于表中
            if dimension in table_columns:
                select_fields.append(dimension)

        # 添加指标字段
        for metric in standard_dsl.get('metrics', []):
            metric_name = metric.get('name', '')
            metric_formula = metric.get('formula', '')
            
            # 确保公式中的字段存在于表中
            if self._validate_formula_fields(metric_formula, table_name):
                select_fields.append(f"{metric_formula} as {metric_name}")

        if not select_fields:
            select_fields = ['*']

        return ', '.join(select_fields)

    def _validate_formula_fields(self, formula: str, table_name: str) -> bool:
        """
        验证公式中的字段是否存在于表中

        Args:
            formula: 指标计算公式
            table_name: 表名

        Returns:
            bool: 是否有效
        """
        # 提取公式中的字段名
        field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        fields = re.findall(field_pattern, formula)

        # 过滤掉SQL关键字和函数
        sql_keywords = {'COUNT', 'SUM', 'AVG', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'NULL'}
        table_columns = set(self.table_schemas.get(table_name, {}).get('columns', []))

        for field in fields:
            if field not in sql_keywords and field not in table_columns:
                return False

        return True

    def _build_where_clause(self, standard_dsl: Dict[str, Any], table_name: str) -> str:
        """
        构建WHERE子句（包含时间过滤）

        Args:
            standard_dsl: 标准DSL格式
            table_name: 表名

        Returns:
            str: WHERE子句
        """
        conditions = ['1=1']

        # 添加时间过滤
        time_field = self._get_time_field(table_name)
        if time_field:
            # 默认最近30天
            conditions.append(f"{time_field} >= date('now', '-30 days')")

        # 添加其他过滤条件
        for filter_expr in standard_dsl.get('filters', []):
            conditions.append(filter_expr)

        return ' AND '.join(conditions)

    def _get_time_field(self, table_name: str) -> str:
        """
        获取表的时间字段

        Args:
            table_name: 表名

        Returns:
            str: 时间字段名
        """
        time_fields = {
            'orders': 'order_time',
            'events': 'timestamp',
            'customers': 'signup_date',
            'reviews': 'review_time',
            'sessions': 'start_time'
        }

        return time_fields.get(table_name, '')

    def _build_group_by_clause(self, standard_dsl: Dict[str, Any]) -> str:
        """
        构建GROUP BY子句

        Args:
            standard_dsl: 标准DSL格式

        Returns:
            str: GROUP BY子句
        """
        group_by = standard_dsl.get('group_by', '')
        if group_by:
            return f"GROUP BY {group_by}"
        return ""

    def _build_order_by_clause(self, standard_dsl: Dict[str, Any]) -> str:
        """
        构建ORDER BY子句

        Args:
            standard_dsl: 标准DSL格式

        Returns:
            str: ORDER BY子句
        """
        # 简单默认排序
        return "ORDER BY 1"



def execute_workflow(user_input: str, db_schema: Dict[str, Any], user_answers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    执行SQL生成工作流

    Args:
        user_input: 用户输入
        db_schema: 数据库schema信息
        user_answers: 用户的补充回答（可选）

    Returns:
        Dict: 工作流执行结果
    """
    # 导入workflow_core模块
    from workflow_core import execute_workflow as core_execute_workflow

    # 1. 执行核心工作流（Planner -> Clarifier -> DSL Generator）
    core_result = core_execute_workflow(user_input, db_schema, user_answers)

    if not core_result.get('success', False):
        return core_result

    # 2. SQL Generator - 生成SQL查询
    dsl = core_result.get('dsl')
    if not dsl:
        return {
            'success': False,
            'message': 'DSL生成失败',
            'stage': 'sql_generator'
        }

    sql_generator = SQLGenerator()
    sql_query = sql_generator.generate(dsl, db_schema)

    # 验证SQL
    is_valid, error_msg = sql_generator.validate_sql(sql_query.sql)
    if not is_valid:
        return {
            'success': False,
            'message': f'SQL验证失败: {error_msg}',
            'stage': 'sql_generator'
        }

    return {
        'success': True,
        'stage': 'sql_generator',
        'sql_query': sql_query.sql,
        'dsl': dsl,
        'description': sql_query.description,
        'risk_level': sql_query.risk_level,
        'message': 'SQL生成完成'
    }