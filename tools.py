import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# SQL执行器
def run_sql_query(query: str) -> pd.DataFrame:
    """
    执行SQL查询并返回结果

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
        
        # 使用with语句管理数据库连接
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        return df
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
            'avg_order_value': [],
            'segment': []
        })
        return empty_df
    
    # 计算Recency（最近购买天数）
    today = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'], format='mixed')
    df['recency'] = (today - df['last_purchase_date']).dt.days
    
    # 计算RFM得分（1-5分，5分最高）
    try:
        df['r_score'] = pd.qcut(df['recency'], 5, labels=[5, 4, 3, 2, 1])
    except:
        df['r_score'] = 3  # 默认给3分
    
    # 处理frequency值相同的情况
    if df['frequency'].nunique() <= 1:
        df['f_score'] = 3  # 默认给3分
    else:
        try:
            df['f_score'] = pd.qcut(df['frequency'], 5, labels=[1, 2, 3, 4, 5])
        except:
            df['f_score'] = 3
    
    # 处理monetary值相同的情况
    if df['monetary'].nunique() <= 1:
        df['m_score'] = 3  # 默认给3分
    else:
        try:
            df['m_score'] = pd.qcut(df['monetary'], 5, labels=[1, 2, 3, 4, 5])
        except:
            df['m_score'] = 3
    
    # 计算总得分
    df['rfm_score'] = df['r_score'].astype(int) + df['f_score'].astype(int) + df['m_score'].astype(int)
    
    # 计算平均订单价值
    df['avg_order_value'] = df['monetary'] / df['frequency']
    
    # 用户分层
    def get_user_segment(row):
        r = int(row['r_score'])
        f = int(row['f_score'])
        m = int(row['m_score'])
        
        if r >= 4 and f >= 4 and m >= 4:
            return '核心高频'
        elif r >= 3 and f >= 3 and m >= 3:
            return '重要客户'
        elif r >= 4 and (f <= 2 or m <= 2):
            return '重要挽留'
        elif r <= 2 and f >= 3 and m >= 3:
            return '重要发展'
        elif r <= 2 and f <= 2 and m >= 3:
            return '重要价值'
        elif r <= 2 and f <= 2 and m <= 2:
            return '低价值'
        else:
            return '一般客户'
    
    df['segment'] = df.apply(get_user_segment, axis=1)
    
    return df

# 获取RFM分层统计
def get_rfm_segment_stats() -> pd.DataFrame:
    """
    获取RFM分层统计数据
    
    Returns:
        DataFrame: RFM分层统计
    """
    rfm_df = calculate_rfm()
    
    if 'error' in rfm_df.columns:
        return rfm_df
    
    # 检查数据是否为空
    if rfm_df.empty:
        # 返回空DataFrame，包含必要的列
        empty_df = pd.DataFrame({
            'segment': [],
            'user_count': [],
            'rfm_score': [],
            'monetary': [],
            'frequency': [],
            'recency': [],
            'avg_order_value': [],
            'monetary_percentage': []
        })
        return empty_df
    
    # 统计各分层的用户数、平均RFM得分、平均消费金额
    segment_stats = rfm_df.groupby('segment').agg({
        'user_id': 'count',
        'rfm_score': 'mean',
        'monetary': 'sum',
        'frequency': 'mean',
        'recency': 'mean',
        'avg_order_value': 'mean'
    }).reset_index()
    
    segment_stats.rename(columns={'user_id': 'user_count'}, inplace=True)
    
    # 检查monetary总和是否为0，避免除零错误
    if segment_stats['monetary'].sum() > 0:
        segment_stats['monetary_percentage'] = segment_stats['monetary'] / segment_stats['monetary'].sum() * 100
    else:
        segment_stats['monetary_percentage'] = 0
    
    return segment_stats

# A/B统计检验
def run_ab_test(control_conv: int, control_n: int, test_conv: int, test_n: int) -> dict:
    """
    计算A/B测试的统计显著性
    
    Args:
        control_conv: 对照组转化人数
        control_n: 对照组总人数
        test_conv: 实验组转化人数
        test_n: 实验组总人数
    
    Returns:
        dict: 包含转化率、差异、p值等统计结果
    """
    # 计算转化率
    control_rate = control_conv / control_n if control_n > 0 else 0
    test_rate = test_conv / test_n if test_n > 0 else 0
    rate_diff = test_rate - control_rate
    
    # 执行Z检验
    try:
        _, p_value = stats.proportions_ztest(
            [test_conv, control_conv],
            [test_n, control_n]
        )
    except:
        p_value = 1.0
    
    # 计算置信区间（95%）
    se = np.sqrt(test_rate * (1 - test_rate) / test_n + control_rate * (1 - control_rate) / control_n)
    ci_lower = rate_diff - 1.96 * se
    ci_upper = rate_diff + 1.96 * se
    
    # 判断显著性
    is_significant = p_value < 0.05
    
    return {
        'control_rate': round(control_rate, 4),
        'test_rate': round(test_rate, 4),
        'rate_diff': round(rate_diff, 4),
        'p_value': round(p_value, 4),
        'ci_lower': round(ci_lower, 4),
        'ci_upper': round(ci_upper, 4),
        'is_significant': is_significant
    }

# Plotly绘图 - 漏斗图
def plot_funnel(data: pd.DataFrame) -> go.Figure:
    """
    绘制漏斗图
    
    Args:
        data: 包含阶段和人数的DataFrame，需要有'step'和'count'列
    
    Returns:
        go.Figure: 漏斗图对象
    """
    fig = px.funnel(data, x='count', y='step')
    fig.update_layout(
        title='转化漏斗',
        xaxis_title='人数',
        yaxis_title='转化阶段'
    )
    return fig

# Plotly绘图 - 柱状图
def plot_bar(data: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """
    绘制柱状图
    
    Args:
        data: 数据源
        x: x轴字段
        y: y轴字段
        title: 图表标题
    
    Returns:
        go.Figure: 柱状图对象
    """
    fig = px.bar(data, x=x, y=y)
    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y
    )
    return fig

# Plotly绘图 - 折线图
def plot_line(data: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """
    绘制折线图（时间序列）
    
    Args:
        data: 数据源
        x: x轴字段（通常是日期）
        y: y轴字段
        title: 图表标题
    
    Returns:
        go.Figure: 折线图对象
    """
    fig = px.line(data, x=x, y=y)
    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y
    )
    return fig

# Plotly绘图 - 饼图
def plot_pie(data: pd.DataFrame, values: str, names: str, title: str) -> go.Figure:
    """
    绘制饼图（占比分析）
    
    Args:
        data: 数据源
        values: 值字段
        names: 名称字段
        title: 图表标题
    
    Returns:
        go.Figure: 饼图对象
    """
    fig = px.pie(data, values=values, names=names)
    fig.update_layout(
        title=title
    )
    return fig

# Plotly绘图 - 散点图
def plot_scatter(data: pd.DataFrame, x: str, y: str, title: str, color=None, size=None) -> go.Figure:
    """
    绘制散点图（相关性分析）
    
    Args:
        data: 数据源
        x: x轴字段
        y: y轴字段
        title: 图表标题
        color: 颜色分组字段（可选）
        size: 大小映射字段（可选）
    
    Returns:
        go.Figure: 散点图对象
    """
    fig = px.scatter(data, x=x, y=y, color=color, size=size)
    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y
    )
    return fig

# Plotly绘图 - 箱线图
def plot_box(data: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """
    绘制箱线图（分布分析）
    
    Args:
        data: 数据源
        x: x轴字段（分组）
        y: y轴字段（数值）
        title: 图表标题
    
    Returns:
        go.Figure: 箱线图对象
    """
    fig = px.box(data, x=x, y=y)
    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y
    )
    return fig

# Plotly绘图 - 热力图
def plot_heatmap(data: pd.DataFrame, x: str, y: str, z: str, title: str) -> go.Figure:
    """
    绘制热力图
    
    Args:
        data: 数据源
        x: x轴字段
        y: y轴字段
        z: 值字段
        title: 图表标题
    
    Returns:
        go.Figure: 热力图对象
    """
    # 检查数据是否为空
    if data.empty:
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title=x,
            yaxis_title=y,
            annotations=[{
                'text': 'No data available for heatmap',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
        return fig
    
    # 尝试转换时间字段
    for col in [x, y]:
        if col in data.columns:
            try:
                data[col] = pd.to_datetime(data[col])
            except:
                pass
    
    # 检查z字段是否存在且有值
    if z not in data.columns or data[z].isnull().all():
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title=x,
            yaxis_title=y,
            annotations=[{
                'text': 'No valid data for heatmap values',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
        return fig
    
    fig = px.density_heatmap(data, x=x, y=y, z=z)
    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y
    )
    
    # 确保时间轴显示正确
    for axis in ['xaxis', 'yaxis']:
        if axis in fig.layout:
            fig.layout[axis].type = 'date'
    
    return fig

# 计算漏斗转化率
def calculate_funnel(category: str = None) -> pd.DataFrame:
    """
    计算转化漏斗数据
    
    Args:
        category: 可选的商品类别过滤
    
    Returns:
        DataFrame: 包含各阶段人数和转化率的漏斗数据
    """
    # 统计各事件类型的用户数，使用events表
    query = """
    SELECT event_type, COUNT(DISTINCT session_id) as count
    FROM events
    WHERE session_id IS NOT NULL
    GROUP BY event_type
    ORDER BY CASE 
        WHEN event_type = 'Page View' THEN 1
        WHEN event_type = 'View' THEN 1
        WHEN event_type = 'Add to Cart' THEN 2
        WHEN event_type = 'Cart' THEN 2
        WHEN event_type = 'Purchase' THEN 3
        ELSE 4
    END
    """
    
    df = run_sql_query(query)
    
    if 'error' in df.columns:
        return df
    
    # 检查数据是否为空
    if df.empty:
        # 返回空DataFrame，包含必要的列
        empty_df = pd.DataFrame({
            'step': [],
            'count': [],
            'conversion_rate': [],
            'stage_conversion_rate': []
        })
        return empty_df
    
    # 重命名事件为更友好的名称，并合并相似事件
    event_map = {
        'Page View': '浏览',
        'View': '浏览',
        'Add to Cart': '加购',
        'Cart': '加购',
        'Purchase': '购买'
    }
    df['step'] = df['event_type'].map(event_map)
    
    # 移除未映射的事件
    df = df.dropna(subset=['step'])
    
    # 检查数据是否为空
    if df.empty:
        # 返回空DataFrame，包含必要的列
        empty_df = pd.DataFrame({
            'step': [],
            'count': [],
            'conversion_rate': [],
            'stage_conversion_rate': []
        })
        return empty_df
    
    # 合并相同步骤的数据
    df_grouped = df.groupby('step')['count'].sum().reset_index()
    
    # 重新排序步骤
    step_order = {'浏览': 0, '加购': 1, '购买': 2}
    df_grouped = df_grouped.sort_values(by='step', key=lambda x: x.map(step_order))
    
    # 重置索引以确保正确的顺序
    df_grouped = df_grouped.reset_index(drop=True)
    
    # 计算转化率
    if not df_grouped.empty:
        # 找到浏览阶段的用户数作为基数
        if '浏览' in df_grouped['step'].values:
            total_views = df_grouped[df_grouped['step'] == '浏览']['count'].iloc[0]
            df_grouped['conversion_rate'] = df_grouped['count'] / total_views * 100
            
            # 计算阶段间转化率
            df_grouped['stage_conversion_rate'] = 0.0
            for i in range(1, len(df_grouped)):
                if df_grouped['count'].iloc[i-1] > 0:
                    df_grouped.loc[df_grouped.index[i], 'stage_conversion_rate'] = df_grouped['count'].iloc[i] / df_grouped['count'].iloc[i-1] * 100
        else:
            # 如果没有浏览数据，不计算转化率，显示N/A
            df_grouped['conversion_rate'] = None
            df_grouped['stage_conversion_rate'] = None
    
    return df_grouped[['step', 'count', 'conversion_rate', 'stage_conversion_rate']]

# 计算A/B组转化率
def get_ab_conversion(category: str = None) -> pd.DataFrame:
    """
    获取A/B组的转化率数据
    
    Args:
        category: 可选的商品类别过滤
    
    Returns:
        DataFrame: 包含A/B组转化率数据
    """
    # 由于数据库中没有user_events表，使用events表
    # 并基于discount_pct字段模拟A/B组（有折扣为A组，无折扣为B组）
    query = """
    SELECT 
        CASE 
            WHEN discount_pct > 0 THEN 'A' -- 有折扣组
            ELSE 'B' -- 无折扣组
        END as "group",
        COUNT(DISTINCT session_id) as total_users,
        SUM(CASE WHEN event_type = 'Purchase' THEN 1 ELSE 0 END) as conversions,
        SUM(CASE WHEN event_type = 'Purchase' THEN 1 ELSE 0 END) * 1.0 / COUNT(DISTINCT session_id) as conversion_rate
    FROM events
    WHERE session_id IS NOT NULL
    GROUP BY "group"
    """
    
    return run_sql_query(query)

# 计算A/B测试ROI
def calculate_ab_roi(control_conv: int, control_n: int, test_conv: int, test_n: int, avg_order_value: float, monthly_active_users: int) -> dict:
    """
    计算A/B测试的ROI
    
    Args:
        control_conv: 对照组转化人数
        control_n: 对照组总人数
        test_conv: 实验组转化人数
        test_n: 实验组总人数
        avg_order_value: 平均订单价值
        monthly_active_users: 月活跃用户数
    
    Returns:
        dict: 包含ROI计算结果
    """
    # 计算转化率
    control_rate = control_conv / control_n if control_n > 0 else 0
    test_rate = test_conv / test_n if test_n > 0 else 0
    rate_diff = test_rate - control_rate
    
    # 计算额外转化数
    additional_conversions = monthly_active_users * rate_diff
    
    # 计算额外收入
    additional_revenue = additional_conversions * avg_order_value
    
    # 假设测试成本（可根据实际情况调整）
    test_cost = 10000  # 示例值
    
    # 计算ROI
    roi = (additional_revenue - test_cost) / test_cost * 100 if test_cost > 0 else 0
    
    return {
        'additional_conversions': round(additional_conversions, 2),
        'additional_revenue': round(additional_revenue, 2),
        'test_cost': test_cost,
        'roi': round(roi, 2)
    }