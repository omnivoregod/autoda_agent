import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
from difflib import get_close_matches

# 语义表名映射 - 常见业务表名的同义词
TABLE_NAME_SYNONYMS = {
    'orders': ['orders', 'order', '订单', '订单表', '销售订单', 'purchase', 'sales_order'],
    'customers': ['customers', 'customer', '客户', '客户表', '用户', 'user', 'users'],
    'products': ['products', 'product', '产品', '商品', '商品表', '货品'],
    'events': ['events', 'event', '事件', '事件表', '行为', '用户行为', 'log', 'logs'],
    'sessions': ['sessions', 'session', '会话', '会话表', '访问', '访问记录'],
    'reviews': ['reviews', 'review', '评论', '评价', '反馈'],
    'order_items': ['order_items', 'order_item', '订单项', '订单明细', '商品明细', 'items']
}

# 语义字段名映射 - 常见字段名的同义词
FIELD_NAME_SYNONYMS = {
    # 通用字段
    'id': ['id', '编号', '标识', '唯一标识'],
    'name': ['name', '名称', '名字'],
    'time': ['time', '时间', '日期', 'timestamp', 'datetime', 'date'],
    'status': ['status', '状态', '状态码'],
    
    # orders 表字段
    'order_id': ['order_id', '订单id', '订单编号', 'order_no', '订单号'],
    'customer_id': ['customer_id', '客户id', '用户id', '用户编号', '买家id'],
    'total_usd': ['total_usd', '金额', '订单金额', '总价', '总金额', '销售额'],
    'order_time': ['order_time', '下单时间', '购买时间', '订单时间'],
    'status': ['status', '订单状态', '状态'],
    
    # customers 表字段
    'email': ['email', '邮箱', '电子邮件'],
    'phone': ['phone', '手机', '电话', '手机号码'],
    'register_time': ['register_time', '注册时间', '加入时间'],
    
    # products 表字段
    'product_id': ['product_id', '商品id', '产品id', '商品编号'],
    'price': ['price', '价格', '单价'],
    'category': ['category', '分类', '类别'],
    
    # events 表字段
    'event_type': ['event_type', '事件类型', '行为类型', '操作类型'],
    'session_id': ['session_id', '会话id', '访问id'],
    
    # sessions 表字段
    'start_time': ['start_time', '开始时间', '访问时间'],
    'end_time': ['end_time', '结束时间'],
    'page_views': ['page_views', '页面浏览量', '访问页数']
}

def get_available_tables(db_path):
    """获取数据库中可用的表名"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
    except Exception as e:
        print(f"获取表名失败: {e}")
        return []

def get_table_columns(db_path, table_name):
    """获取指定表的字段列表"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return columns
    except Exception as e:
        print(f"获取字段列表失败: {e}")
        return []

def match_field_name(query_field, available_fields):
    """使用语义分析和模糊匹配找到最相似的字段名"""
    if not available_fields:
        return None
    
    query_field_lower = query_field.lower()
    
    # 精确匹配
    for field in available_fields:
        if field.lower() == query_field_lower:
            return field
    
    # 语义匹配 - 使用同义词库
    for standard_name, synonyms in FIELD_NAME_SYNONYMS.items():
        if query_field_lower in [s.lower() for s in synonyms]:
            # 检查标准字段名是否在可用字段中
            if standard_name.lower() in [f.lower() for f in available_fields]:
                return next(f for f in available_fields if f.lower() == standard_name.lower())
            # 检查同义词是否在可用字段中
            for synonym in synonyms:
                if synonym.lower() in [f.lower() for f in available_fields]:
                    return next(f for f in available_fields if f.lower() == synonym.lower())
    
    # 模糊匹配 - 使用编辑距离
    matches = get_close_matches(query_field_lower, [f.lower() for f in available_fields], n=1, cutoff=0.6)
    if matches:
        return next(f for f in available_fields if f.lower() == matches[0])
    
    return None

def replace_field_names(query, db_path, table_name):
    """替换查询中的字段名为实际存在的字段名（不区分大小写）"""
    available_fields = get_table_columns(db_path, table_name)
    if not available_fields:
        return query, []
    
    select_pattern = r'SELECT\s+(.+?)(?=\s+FROM)'
    select_match = re.search(select_pattern, query, re.IGNORECASE | re.DOTALL)
    
    new_query = query
    replaced_fields = []
    
    if select_match:
        select_part = select_match.group(1)
        fields = [f.strip() for f in select_part.split(',')]
        
        for field in fields:
            has_alias = bool(re.search(r'\s+AS\s+\w+$', field, flags=re.IGNORECASE))
            field_for_match = re.sub(r'\s+AS\s+\w+$', '', field, flags=re.IGNORECASE).strip()
            field_after_func = re.sub(r'^(COUNT|SUM|AVG|MAX|MIN)\s*\(\s*(\*|\w+)\s*\)$', r'\2', field_for_match, flags=re.IGNORECASE).strip()
            
            if field_after_func == '*':
                continue
            
            if not field_after_func or '(' in field_after_func or ')' in field_after_func:
                continue
            
            # 如果字段是聚合函数的别名且不在表字段中，不进行替换（避免误替换 COUNT(*) as orders -> COUNT(*) as order_id）
            is_aggregate_alias = has_alias and field_for_match != field_after_func
            if is_aggregate_alias and field_after_func.lower() not in [f.lower() for f in available_fields]:
                # 聚合函数别名不在表字段中，跳过替换
                continue
            
            # 只有当字段名不在表字段列表中时才进行匹配
            if field_after_func.lower() not in [f.lower() for f in available_fields]:
                matched_field = match_field_name(field_after_func, available_fields)
                if matched_field and matched_field.lower() != field_after_func.lower():
                    if has_alias:
                        alias_match = re.search(r'(.+\s+AS\s+)(\w+)$', field, flags=re.IGNORECASE)
                        if alias_match:
                            new_field = alias_match.group(1) + matched_field
                            new_query = new_query.replace(field, new_field, 1)
                            replaced_fields.append(f"{field_after_func} -> {matched_field}")
                    else:
                        new_query = new_query.replace(field, matched_field, 1)
                        replaced_fields.append(f"{field_after_func} -> {matched_field}")
    
    return new_query, replaced_fields

def match_table_name(query_table, available_tables):
    """使用语义分析匹配最相似的表名"""
    if not available_tables:
        return None
    
    query_table_lower = query_table.lower()
    
    # 精确匹配
    for table in available_tables:
        if table.lower() == query_table_lower:
            return table
    
    # 检查带 temp_ 前缀的表名
    temp_table_name = f"temp_{query_table_lower}"
    for table in available_tables:
        if table.lower() == temp_table_name:
            return table
    
    # 语义匹配 - 使用同义词库
    for standard_name, synonyms in TABLE_NAME_SYNONYMS.items():
        if query_table_lower in [s.lower() for s in synonyms]:
            # 检查标准表名是否在可用表中
            if standard_name in available_tables:
                return standard_name
            # 检查带 temp_ 前缀的标准表名
            temp_standard = f"temp_{standard_name}"
            if temp_standard in available_tables:
                return temp_standard
            # 检查同义词是否在可用表中
            for synonym in synonyms:
                if synonym.lower() in [t.lower() for t in available_tables]:
                    return next(t for t in available_tables if t.lower() == synonym.lower())
                # 检查带 temp_ 前缀的同义词
                temp_synonym = f"temp_{synonym.lower()}"
                if temp_synonym in [t.lower() for t in available_tables]:
                    return next(t for t in available_tables if t.lower() == temp_synonym)
    
    # 模糊匹配 - 使用编辑距离
    matches = get_close_matches(query_table_lower, [t.lower() for t in available_tables], n=1, cutoff=0.6)
    if matches:
        return next(t for t in available_tables if t.lower() == matches[0])
    
    return None

def replace_table_name(query, available_tables):
    """替换查询中的表名为实际存在的表名（只替换 FROM 和 JOIN 子句中的表名）"""
    new_query = query
    replaced_tables = []
    
    # 只替换 FROM 和 JOIN 子句后的表名（不替换别名）
    from_join_pattern = r'(\bFROM\s+)(\w+)|(\bJOIN\s+)(\w+)'
    
    def replace_table(match):
        if match.group(1):  # FROM 匹配
            prefix = match.group(1)
            table_name = match.group(2)
        else:  # JOIN 匹配
            prefix = match.group(3)
            table_name = match.group(4)
        matched_table = match_table_name(table_name, available_tables)
        if matched_table and matched_table.lower() != table_name.lower():
            replaced_tables.append(f"{table_name} -> {matched_table}")
            return f"{prefix}{matched_table}"
        return match.group(0)
    
    new_query = re.sub(from_join_pattern, replace_table, new_query, flags=re.IGNORECASE)
    
    return new_query, replaced_tables

# SQL执行器
def run_sql_query(query: str) -> pd.DataFrame:
    """
    执行SQL查询并返回结果（支持表名和字段名的语义匹配）
    
    Args:
        query: SQL查询语句
        
    Returns:
        DataFrame: 查询结果
    """
    try:
        # 尝试从session_state获取数据库路径
        db_path = 'ecommerce.db'  # 默认数据库路径
        try:
            import streamlit as st
            if hasattr(st, 'session_state'):
                db_path = st.session_state.get('db_path', 'ecommerce.db')
        except ImportError:
            # 非Streamlit环境，使用默认路径
            pass
        
        # 检查数据库文件是否存在
        import os
        if not os.path.exists(db_path):
            error_df = pd.DataFrame({'error': ['数据库文件不存在，请先上传数据文件并处理']})
            error_df['query'] = [query]
            return error_df
        
        # 获取可用表名
        available_tables = get_available_tables(db_path)
        
        # 使用语义匹配替换表名
        new_query, replaced_tables = replace_table_name(query, available_tables)
        
        # 提取查询中的表名，用于字段匹配
        table_pattern = r'\bFROM\s+(\w+)\b'
        table_matches = re.findall(table_pattern, new_query, re.IGNORECASE)
        
        # 对每个表进行字段名替换
        replaced_fields = []
        for table_name in table_matches:
            new_query, replaced = replace_field_names(new_query, db_path, table_name)
            replaced_fields.extend(replaced)
        
        # 使用with语句管理数据库连接
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(new_query, conn)
        
        # 如果有表名替换，添加提示信息
        all_replacements = []
        if replaced_tables:
            all_replacements.extend([f"表: {r}" for r in replaced_tables])
        if replaced_fields:
            all_replacements.extend([f"字段: {r}" for r in replaced_fields])
        
        if all_replacements:
            df['_replacements'] = ', '.join(all_replacements)
        
        return df
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            # 表不存在时提供更友好的错误信息
            available_tables = get_available_tables(db_path)
            if available_tables:
                error_msg = f"表不存在。可用表名: {', '.join(available_tables)}"
            else:
                error_msg = "数据库中没有表，请先上传数据文件"
            error_df = pd.DataFrame({'error': [error_msg]})
            error_df['query'] = [query]
            return error_df
        else:
            error_df = pd.DataFrame({'error': [str(e)]})
            error_df['query'] = [query]
            return error_df
    except Exception as e:
        # 返回更详细的错误信息
        error_df = pd.DataFrame({'error': [str(e)]})
        error_df['query'] = [query]  # 添加查询语句到错误信息中
        return error_df

# RFM计算
def calculate_rfm() -> pd.DataFrame:
    """
    计算RFM指标并对用户进行分层
    
    Returns:
        DataFrame: 包含用户RFM指标和分层结果
    """
    # 读取购买数据，使用orders表
    query = """
    SELECT customer_id as user_id, MAX(order_time) as last_purchase_date, 
           COUNT(*) as frequency, SUM(total_usd) as monetary
    FROM orders
    GROUP BY customer_id
    """
    
    df = run_sql_query(query)
    
    if 'error' in df.columns:
        return df
    
    # 检查数据是否为空
    if df.empty:
        # 返回空DataFrame，包含必要的列
        empty_df = pd.DataFrame({
            'user_id': [],
            'last_purchase_date': [],
            'frequency': [],
            'monetary': [],
            'recency': [],
            'r_score': [],
            'f_score': [],
            'm_score': [],
            'rfm_score': [],
            'rfm_level': []
        })
        return empty_df
    
    # 计算RFM指标
    current_date = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    df['recency'] = (current_date - df['last_purchase_date']).dt.days
    
    # 计算RFM得分（1-5分）
    df['r_score'] = pd.qcut(df['recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    df['f_score'] = pd.qcut(df['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df['m_score'] = pd.qcut(df['monetary'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # 计算RFM总分
    df['rfm_score'] = df['r_score'] * 100 + df['f_score'] * 10 + df['m_score']
    
    # RFM分层
    def get_rfm_level(row):
        if row['rfm_score'] >= 444:
            return '重要价值客户'
        elif row['rfm_score'] >= 333:
            return '潜力客户'
        elif row['rfm_score'] >= 222:
            return '一般客户'
        else:
            return '流失客户'
    
    df['rfm_level'] = df.apply(get_rfm_level, axis=1)
    
    return df

# 销售漏斗计算
def calculate_funnel() -> pd.DataFrame:
    """
    计算销售漏斗数据
    
    Returns:
        DataFrame: 包含漏斗各阶段的数据
    """
    # 查询各阶段数据
    queries = [
        ("浏览", "SELECT COUNT(DISTINCT session_id) as count FROM events WHERE event_type='view'"),
        ("加购", "SELECT COUNT(DISTINCT session_id) as count FROM events WHERE event_type='add_to_cart'"),
        ("下单", "SELECT COUNT(DISTINCT session_id) as count FROM events WHERE event_type='purchase'"),
        ("支付", "SELECT COUNT(DISTINCT order_id) as count FROM orders WHERE status='completed'")
    ]
    
    funnel_data = []
    for stage, query in queries:
        df = run_sql_query(query)
        if 'error' in df.columns:
            # 如果events表不存在，尝试从orders表获取数据
            if stage == '浏览':
                count = 0
            elif stage == '加购':
                count = 0
            elif stage == '下单':
                df = run_sql_query("SELECT COUNT(DISTINCT session_id) as count FROM orders")
                count = df['count'].iloc[0] if not df.empty else 0
            else:
                df = run_sql_query("SELECT COUNT(*) as count FROM orders WHERE status='completed'")
                count = df['count'].iloc[0] if not df.empty else 0
        else:
            count = df['count'].iloc[0] if not df.empty else 0
        funnel_data.append({'stage': stage, 'count': count})
    
    df_funnel = pd.DataFrame(funnel_data)
    
    # 计算转化率
    df_funnel['conversion_rate'] = 0.0
    for i in range(1, len(df_funnel)):
        if df_funnel.loc[i-1, 'count'] > 0:
            df_funnel.loc[i, 'conversion_rate'] = df_funnel.loc[i, 'count'] / df_funnel.loc[i-1, 'count']
    
    return df_funnel

# 统计检验
def ab_test_metrics(metric_name: str, group_a: str, group_b: str) -> dict:
    """
    执行AB测试统计检验
    
    Args:
        metric_name: 指标名称（如转化率、平均订单金额等）
        group_a: A组过滤条件
        group_b: B组过滤条件
        
    Returns:
        dict: 包含统计检验结果
    """
    # 查询A组数据
    query_a = f"SELECT {metric_name} FROM orders WHERE {group_a}"
    df_a = run_sql_query(query_a)
    
    # 查询B组数据
    query_b = f"SELECT {metric_name} FROM orders WHERE {group_b}"
    df_b = run_sql_query(query_b)
    
    if 'error' in df_a.columns or 'error' in df_b.columns:
        return {'error': '数据查询失败'}
    
    # 执行t检验
    t_stat, p_value = stats.ttest_ind(df_a[metric_name], df_b[metric_name], equal_var=False)
    
    # 计算均值和标准差
    result = {
        'group_a_mean': df_a[metric_name].mean(),
        'group_a_std': df_a[metric_name].std(),
        'group_a_count': len(df_a),
        'group_b_mean': df_b[metric_name].mean(),
        'group_b_std': df_b[metric_name].std(),
        'group_b_count': len(df_b),
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
    
    return result

def run_ab_test(group_a_filter: str, group_b_filter: str, metric: str = 'total_usd') -> dict:
    """
    执行AB测试分析
    
    Args:
        group_a_filter: A组过滤条件
        group_b_filter: B组过滤条件
        metric: 测试指标（如 total_usd, order_count 等）
        
    Returns:
        dict: AB测试结果
    """
    # 查询A组数据
    query_a = f"SELECT {metric} FROM orders WHERE {group_a_filter}"
    df_a = run_sql_query(query_a)
    
    # 查询B组数据
    query_b = f"SELECT {metric} FROM orders WHERE {group_b_filter}"
    df_b = run_sql_query(query_b)
    
    if 'error' in df_a.columns or 'error' in df_b.columns:
        return {
            'error': '数据查询失败',
            'group_a_count': 0,
            'group_b_count': 0,
            'group_a_mean': 0,
            'group_b_mean': 0,
            'lift': 0,
            'p_value': 1.0,
            'significant': False
        }
    
    # 计算统计指标
    group_a_count = len(df_a)
    group_b_count = len(df_b)
    group_a_mean = df_a[metric].mean()
    group_b_mean = df_b[metric].mean()
    
    # 计算提升率
    if group_a_mean > 0:
        lift = (group_b_mean - group_a_mean) / group_a_mean * 100
    else:
        lift = 0
    
    # 执行t检验
    if group_a_count >= 30 and group_b_count >= 30:
        t_stat, p_value = stats.ttest_ind(df_a[metric], df_b[metric], equal_var=False)
        significant = p_value < 0.05
    else:
        p_value = 1.0
        significant = False
    
    return {
        'group_a_filter': group_a_filter,
        'group_b_filter': group_b_filter,
        'metric': metric,
        'group_a_count': group_a_count,
        'group_b_count': group_b_count,
        'group_a_mean': round(group_a_mean, 2),
        'group_b_mean': round(group_b_mean, 2),
        'lift': round(lift, 2),
        'p_value': round(p_value, 4),
        'significant': significant
    }

def get_ab_conversion(group_a_filter: str, group_b_filter: str) -> dict:
    """
    计算AB测试的转化率
    
    Args:
        group_a_filter: A组过滤条件
        group_b_filter: B组过滤条件
        
    Returns:
        dict: 转化率对比结果
    """
    # 查询A组转化数据
    query_a = f"SELECT COUNT(*) as conversions FROM orders WHERE {group_a_filter} AND status='completed'"
    df_a_conv = run_sql_query(query_a)
    
    query_a_total = f"SELECT COUNT(*) as total FROM orders WHERE {group_a_filter}"
    df_a_total = run_sql_query(query_a_total)
    
    # 查询B组转化数据
    query_b = f"SELECT COUNT(*) as conversions FROM orders WHERE {group_b_filter} AND status='completed'"
    df_b_conv = run_sql_query(query_b)
    
    query_b_total = f"SELECT COUNT(*) as total FROM orders WHERE {group_b_filter}"
    df_b_total = run_sql_query(query_b_total)
    
    if 'error' in df_a_conv.columns or 'error' in df_b_conv.columns:
        return {
            'error': '数据查询失败',
            'group_a_conversion': 0,
            'group_b_conversion': 0,
            'lift': 0
        }
    
    group_a_conv = df_a_conv['conversions'].iloc[0] if not df_a_conv.empty else 0
    group_a_total = df_a_total['total'].iloc[0] if not df_a_total.empty else 1
    group_a_rate = group_a_conv / group_a_total * 100
    
    group_b_conv = df_b_conv['conversions'].iloc[0] if not df_b_conv.empty else 0
    group_b_total = df_b_total['total'].iloc[0] if not df_b_total.empty else 1
    group_b_rate = group_b_conv / group_b_total * 100
    
    lift = (group_b_rate - group_a_rate) / group_a_rate * 100 if group_a_rate > 0 else 0
    
    return {
        'group_a_filter': group_a_filter,
        'group_b_filter': group_b_filter,
        'group_a_conversions': group_a_conv,
        'group_a_total': group_a_total,
        'group_a_conversion': round(group_a_rate, 2),
        'group_b_conversions': group_b_conv,
        'group_b_total': group_b_total,
        'group_b_conversion': round(group_b_rate, 2),
        'lift': round(lift, 2)
    }

def calculate_ab_roi(group_a_filter: str, group_b_filter: str, cost_b: float = 0) -> dict:
    """
    计算AB测试的ROI
    
    Args:
        group_a_filter: A组过滤条件
        group_b_filter: B组过滤条件
        cost_b: B组成本（如营销费用）
        
    Returns:
        dict: ROI计算结果
    """
    # 获取两组数据
    ab_result = run_ab_test(group_a_filter, group_b_filter, 'total_usd')
    
    if 'error' in ab_result:
        return {
            'error': '数据查询失败',
            'roi': 0,
            'net_gain': 0
        }
    
    # 计算收入差异
    group_a_revenue = ab_result['group_a_mean'] * ab_result['group_a_count']
    group_b_revenue = ab_result['group_b_mean'] * ab_result['group_b_count']
    revenue_diff = group_b_revenue - group_a_revenue
    
    # 计算ROI
    if cost_b > 0:
        roi = (revenue_diff - cost_b) / cost_b * 100
    else:
        roi = 0
    
    return {
        'group_a_filter': group_a_filter,
        'group_b_filter': group_b_filter,
        'group_a_revenue': round(group_a_revenue, 2),
        'group_b_revenue': round(group_b_revenue, 2),
        'revenue_diff': round(revenue_diff, 2),
        'cost_b': cost_b,
        'net_gain': round(revenue_diff - cost_b, 2),
        'roi': round(roi, 2),
        'significant': ab_result.get('significant', False)
    }

def get_rfm_segment_stats() -> pd.DataFrame:
    """
    获取RFM分段的统计信息
    
    Returns:
        DataFrame: 各RFM分段的统计数据
    """
    df = calculate_rfm()
    
    if 'error' in df.columns:
        return df
    
    if df.empty:
        return pd.DataFrame({
            'segment': [],
            'customer_count': [],
            'avg_recency': [],
            'avg_frequency': [],
            'avg_monetary': [],
            'total_revenue': []
        })
    
    # 按RFM分层分组统计
    segment_stats = df.groupby('rfm_level').agg({
        'user_id': 'count',
        'recency': 'mean',
        'frequency': 'mean',
        'monetary': ['mean', 'sum']
    }).reset_index()
    
    segment_stats.columns = ['segment', 'customer_count', 'avg_recency', 'avg_frequency', 'avg_monetary', 'total_revenue']
    
    # 计算百分比
    segment_stats['revenue_percentage'] = (segment_stats['total_revenue'] / segment_stats['total_revenue'].sum() * 100).round(2)
    
    # 排序
    segment_order = ['重要价值客户', '潜力客户', '一般客户', '流失客户']
    segment_stats['segment'] = pd.Categorical(segment_stats['segment'], categories=segment_order, ordered=True)
    segment_stats = segment_stats.sort_values('segment')
    
    return segment_stats

# 图表生成
def generate_chart(data: pd.DataFrame, chart_type: str, x_column: str, y_column: str = None, 
                   title: str = "", color_column: str = None) -> go.Figure:
    """
    生成图表
    
    Args:
        data: 数据
        chart_type: 图表类型（bar, line, pie, histogram, scatter）
        x_column: X轴列名
        y_column: Y轴列名
        title: 图表标题
        color_column: 颜色分组列名
        
    Returns:
        Figure: Plotly图表对象
    """
    if data.empty:
        fig = go.Figure()
        fig.update_layout(title="暂无数据")
        return fig
    
    try:
        if chart_type == 'bar':
            fig = px.bar(data, x=x_column, y=y_column, color=color_column, title=title)
        elif chart_type == 'line':
            fig = px.line(data, x=x_column, y=y_column, color=color_column, title=title)
        elif chart_type == 'pie':
            fig = px.pie(data, values=y_column, names=x_column, title=title)
        elif chart_type == 'histogram':
            fig = px.histogram(data, x=x_column, color=color_column, title=title)
        elif chart_type == 'scatter':
            fig = px.scatter(data, x=x_column, y=y_column, color=color_column, title=title)
        else:
            fig = px.bar(data, x=x_column, y=y_column, title=title)
        
        # 设置中文显示
        fig.update_layout(font=dict(family="SimHei, sans-serif"))
        
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"图表生成失败: {str(e)}")
        return fig

def plot_bar(data: pd.DataFrame, x: str, y: str = None, title: str = "", color: str = None) -> go.Figure:
    """绘制柱状图"""
    return generate_chart(data, 'bar', x, y, title, color)

def plot_line(data: pd.DataFrame, x: str, y: str = None, title: str = "", color: str = None) -> go.Figure:
    """绘制折线图"""
    return generate_chart(data, 'line', x, y, title, color)

def plot_pie(data: pd.DataFrame, names: str, values: str, title: str = "") -> go.Figure:
    """绘制饼图"""
    return generate_chart(data, 'pie', names, values, title)

def plot_scatter(data: pd.DataFrame, x: str, y: str, title: str = "", color: str = None) -> go.Figure:
    """绘制散点图"""
    return generate_chart(data, 'scatter', x, y, title, color)

def plot_box(data: pd.DataFrame, x: str, y: str = None, title: str = "", color: str = None) -> go.Figure:
    """绘制箱线图"""
    if data.empty:
        fig = go.Figure()
        fig.update_layout(title="暂无数据")
        return fig
    
    try:
        fig = px.box(data, x=x, y=y, color=color, title=title)
        fig.update_layout(font=dict(family="SimHei, sans-serif"))
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"图表生成失败: {str(e)}")
        return fig

def plot_heatmap(data: pd.DataFrame, x: str, y: str, color: str, title: str = "") -> go.Figure:
    """绘制热力图"""
    if data.empty:
        fig = go.Figure()
        fig.update_layout(title="暂无数据")
        return fig
    
    try:
        fig = px.density_heatmap(data, x=x, y=y, z=color, title=title)
        fig.update_layout(font=dict(family="SimHei, sans-serif"))
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"图表生成失败: {str(e)}")
        return fig

def plot_funnel(data: pd.DataFrame, stage: str, value: str, title: str = "") -> go.Figure:
    """绘制漏斗图"""
    if data.empty:
        fig = go.Figure()
        fig.update_layout(title="暂无数据")
        return fig
    
    try:
        fig = go.Figure(go.Funnel(
            y=data[stage],
            x=data[value],
            textinfo="value+percent previous",
            textposition="inside"
        ))
        fig.update_layout(title=title, font=dict(family="SimHei, sans-serif"))
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"图表生成失败: {str(e)}")
        return fig

# 指标计算
def calculate_metrics(metric_list: list) -> pd.DataFrame:
    """
    计算指定的指标列表
    
    Args:
        metric_list: 指标名称列表
        
    Returns:
        DataFrame: 包含指标值
    """
    metrics_data = []
    
    for metric in metric_list:
        if metric == 'total_orders':
            df = run_sql_query("SELECT COUNT(*) as value FROM orders")
            value = df['value'].iloc[0] if not df.empty else 0
            metrics_data.append({'metric': '订单总数', 'value': value})
        elif metric == 'total_revenue':
            df = run_sql_query("SELECT SUM(total_usd) as value FROM orders")
            value = df['value'].iloc[0] if not df.empty else 0
            metrics_data.append({'metric': '总销售额', 'value': round(value, 2)})
        elif metric == 'avg_order_value':
            df = run_sql_query("SELECT AVG(total_usd) as value FROM orders")
            value = df['value'].iloc[0] if not df.empty else 0
            metrics_data.append({'metric': '平均订单金额', 'value': round(value, 2)})
        elif metric == 'customer_count':
            df = run_sql_query("SELECT COUNT(DISTINCT customer_id) as value FROM orders")
            value = df['value'].iloc[0] if not df.empty else 0
            metrics_data.append({'metric': '客户总数', 'value': value})
        elif metric == 'conversion_rate':
            df_events = run_sql_query("SELECT COUNT(DISTINCT session_id) as views FROM events WHERE event_type='view'")
            df_orders = run_sql_query("SELECT COUNT(DISTINCT session_id) as orders FROM orders")
            views = df_events['views'].iloc[0] if not df_events.empty else 1
            orders = df_orders['orders'].iloc[0] if not df_orders.empty else 0
            metrics_data.append({'metric': '转化率', 'value': round(orders / views * 100, 2)})
        elif metric == 'active_sessions':
            df = run_sql_query("SELECT COUNT(DISTINCT session_id) as value FROM sessions")
            value = df['value'].iloc[0] if not df.empty else 0
            metrics_data.append({'metric': '活跃会话数', 'value': value})
        else:
            metrics_data.append({'metric': metric, 'value': '未知指标'})
    
    return pd.DataFrame(metrics_data)