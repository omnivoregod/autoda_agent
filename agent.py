from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langsmith import traceable
from langsmith.wrappers import wrap_openai
import pandas as pd
import os
from tools import run_sql_query, calculate_rfm, run_ab_test, calculate_funnel, get_ab_conversion
from datetime import datetime
from field_semantic import analyze_field_semantics, get_chart_recommendations, generate_semantic_insights, generate_field_semantic_report_section

# 格式化工具结果
def format_funnel_result():
    """格式化转化漏斗结果"""
    from tools import calculate_funnel
    try:
        df = calculate_funnel()
        
        result = "## 🔄 转化漏斗分析\n"
        result += "-" * 60 + "\n\n"
        
        # 检查数据是否为空
        if df.empty:
            result += "- 暂无转化数据，无法生成漏斗分析\n"
            result += "\n**分析建议**:\n"
            result += "- 上传包含用户行为数据的文件\n"
            result += "- 确保数据中包含浏览、加购和购买等事件类型\n"
            return result
        
        # 检查是否有错误
        if 'error' in df.columns:
            error_message = df['error'].iloc[0]
            result += f"- 数据获取失败: {error_message}\n"
            result += "\n**分析建议**:\n"
            result += "- 确保数据库连接正常\n"
            result += "- 确保temp_events表存在且包含必要的字段\n"
            result += "- 检查数据是否完整\n"
            return result
        
        # 检查是否有浏览数据
        has_view_data = '浏览' in df['step'].values
        
        for idx, row in df.iterrows():
            step = row['step']
            count = row['count']
            conv_rate = row['conversion_rate']
            stage_rate = row['stage_conversion_rate']
            
            result += f"### {step}\n"
            result += f"- **用户数**: {count:,}\n"
            if conv_rate is not None:
                result += f"- **整体转化率**: {conv_rate:.2f}%\n"
            else:
                result += f"- **整体转化率**: N/A (缺少浏览数据)\n"
            if idx > 0 and stage_rate is not None:
                result += f"- **阶段转化率**: {stage_rate:.2f}%\n"
            elif idx > 0:
                result += f"- **阶段转化率**: N/A (缺少前一阶段数据)\n"
            result += "\n"
        
        # 生成转化路径
        steps = list(df['step'])
        if len(steps) > 1:
            result += f"**转化路径**: {' → '.join(steps)}\n"
        else:
            result += "**转化路径**: 数据不完整，无法生成转化路径\n"
        
        result += "\n**分析建议**:\n"
        if has_view_data:
            result += "- 识别转化率下降的关键环节\n"
            result += "- 针对低转化率步骤优化用户体验\n"
            result += "- 制定相应的营销策略提高转化\n"
        else:
            result += "- 建议收集完整的用户行为数据，包括浏览、加购和购买等事件\n"
            result += "- 数据不完整时，无法准确分析转化漏斗\n"
        
        return result
    except Exception as e:
        result = "## 🔄 转化漏斗分析\n"
        result += "-" * 60 + "\n\n"
        result += f"- 分析失败: {str(e)}\n"
        result += "\n**分析建议**:\n"
        result += "- 确保数据库连接正常\n"
        result += "- 确保temp_events表存在且包含必要的字段\n"
        result += "- 检查数据是否完整\n"
        return result

def format_rfm_result():
    """格式化RFM分析结果"""
    from tools import calculate_rfm, get_rfm_segment_stats
    try:
        df = calculate_rfm()
        
        # 检查数据是否为空
        if df.empty:
            result = "## 🎯 RFM用户分层分析\n"
            result += "-" * 60 + "\n\n"
            result += "- 暂无RFM数据，无法生成用户分层分析\n"
            result += "\n**分析建议**:\n"
            result += "- 上传包含用户购买数据的文件\n"
            result += "- 确保数据中包含用户ID、购买时间和金额等字段\n"
            return result
        
        # 检查是否有错误
        if 'error' in df.columns:
            error_message = df['error'].iloc[0]
            result = "## 🎯 RFM用户分层分析\n"
            result += "-" * 60 + "\n\n"
            result += f"- 数据获取失败: {error_message}\n"
            result += "\n**分析建议**:\n"
            result += "- 确保数据库连接正常\n"
            result += "- 确保temp_events表存在且包含必要的字段\n"
            result += "- 检查数据是否完整\n"
            return result
        
        segment_df = get_rfm_segment_stats()
        
        result = "## 🎯 RFM用户分层分析\n"
        result += "-" * 60 + "\n\n"
        
        result += "### 用户分层统计\n"
        result += "-" * 50 + "\n"
        
        for idx, row in segment_df.iterrows():
            result += f"- **{row['segment']}**: {row['user_count']:,} 用户 (RFM得分: {row['rfm_score']:.2f})\n"
        
        result += "\n### 分层说明\n"
        result += "-" * 50 + "\n"
        result += "- **高价值用户(重要客户)**: 消费金额高、频率高、最近购买\n"
        result += "- **潜力用户(重要发展用户)**: 消费金额高、频率低、有发展潜力\n"
        result += "- **流失风险用户(重要挽留用户)**: 频率低、最近购买时间久远\n"
        result += "- **低价值用户**: 消费金额低、频率低、很久未购买\n"
        
        result += "\n### TOP 5 高价值用户\n"
        result += "-" * 50 + "\n"
        top_users = df.nlargest(5, 'rfm_score')
        for idx, row in top_users.iterrows():
            result += f"- 用户 {row['user_id']}: RFM得分 {row['rfm_score']:.2f}\n"
        
        result += "\n**营销策略建议**:\n"
        result += "- **高价值用户**: 提供VIP服务、专属优惠\n"
        result += "- **潜力用户**: 个性化推荐、促销活动\n"
        result += "- **流失风险用户**: 召回活动、专属优惠\n"
        result += "- **低价值用户**: 尝试转化或适当放弃\n"
        
        return result
    except Exception as e:
        result = "## 🎯 RFM用户分层分析\n"
        result += "-" * 60 + "\n\n"
        result += f"- 分析失败: {str(e)}\n"
        result += "\n**分析建议**:\n"
        result += "- 确保数据库连接正常\n"
        result += "- 确保temp_events表存在且包含必要的字段\n"
        result += "- 检查数据是否完整\n"
        return result

def format_ab_test_result(ab_result):
    """格式化A/B测试结果"""
    result = "## 🧪 A/B测试分析\n"
    result += "-" * 60 + "\n\n"
    
    result += "### 测试结果\n"
    result += "-" * 50 + "\n"
    result += f"- **对照组转化率**: {ab_result.get('control_rate', 0):.2f}%\n"
    result += f"- **实验组转化率**: {ab_result.get('test_rate', 0):.2f}%\n"
    result += f"- **P值**: {ab_result.get('p_value', 0):.4f}\n"
    result += f"- **统计显著性**: {'[显著]' if ab_result.get('p_value', 1) < 0.05 else '[不显著]'}\n"
    
    if 'ci' in ab_result:
        result += f"- **置信区间**: [{ab_result['ci'][0]:.4f}, {ab_result['ci'][1]:.4f}]\n"
    
    if 'roi' in ab_result:
        result += f"- **ROI**: {ab_result['roi']:.2f}%\n"
    
    result += "\n**分析建议**:\n"
    if ab_result.get('p_value', 1) < 0.05:
        if ab_result.get('test_rate', 0) > ab_result.get('control_rate', 0):
            result += "- 实验成功！可以考虑在全量用户中推广\n"
        else:
            result += "- 实验失败，建议保留原有方案\n"
    else:
        result += "- 结果不显著，建议延长测试时间或调整实验方案\n"
    
    return result

def format_ab_conversion_result():
    """格式化A/B组转化率结果"""
    from tools import get_ab_conversion
    df = get_ab_conversion()
    
    result = "## 📈 A/B组转化率对比\n"
    result += "-" * 60 + "\n\n"
    
    for idx, row in df.iterrows():
        group = row['group']
        conv_rate = row['conversion_rate'] * 100
        total = row['total_users']
        conv = row['conversions']
        avg_order = row.get('avg_order_value', 0)
        
        result += f"### 组别: {group}\n"
        result += f"- **总用户数**: {total:,}\n"
        result += f"- **转化人数**: {conv:,}\n"
        result += f"- **转化率**: {conv_rate:.2f}%\n"
        if avg_order > 0:
            result += f"- **平均订单价值**: ${avg_order:.2f}\n"
        result += "\n"
    
    if len(df) == 2:
        rate_a = df[df['group'] == 'A']['conversion_rate'].iloc[0] * 100
        rate_b = df[df['group'] == 'B']['conversion_rate'].iloc[0] * 100
        diff = rate_b - rate_a
        result += f"### 转化率差异: {diff:+.2f}%\n"
        if diff > 0:
            result += "**实验组表现更优**\n"
        else:
            result += "**对照组表现更优**\n"
    
    result += "\n**优化建议**:\n"
    result += "- 分析表现更优组别的具体差异\n"
    result += "- 结合用户行为数据深入分析原因\n"
    result += "- 制定针对性的优化策略\n"
    
    return result

def format_sql_result(df):
    """格式化SQL查询结果"""
    if df.empty:
        return "查询结果为空"

    # 检查是否是错误结果
    if 'error' in df.columns and len(df) == 1:
        error_message = str(df['error'].iloc[0])
        # 检查是否有查询语句
        query = df.get('query', [None])[0]

        # 构建错误信息
        result = "**查询执行失败**\n\n"
        result += f"- 错误信息: {error_message}\n"
        if query:
            result += f"- SQL查询: {query}\n"
        result += "- 建议：检查SQL语句格式或确认表结构"
        return result

    result = "**数据概览**\n"
    result += "-" * 60 + "\n"
    result += f"**记录数**: {len(df)}\n"
    result += f"**字段数**: {len(df.columns)}\n"
    result += f"**字段名称**: {', '.join(df.columns)}\n"
    result += "-" * 60 + "\n\n"

    # 如果只有很少的行（聚合查询结果），直接返回不做进一步分析
    if len(df) <= 3:
        result += "**数据统计**\n"
        result += "-" * 60 + "\n"
        result += "（聚合查询结果，仅展示数据）\n"
        for col in df.columns:
            result += f"- **{col}**: {df[col].iloc[0]}\n"
        return result

    # 移除数据预览部分，根据用户需求

    # 添加基本统计信息
    result += "**数据统计**\n"
    result += "-" * 60 + "\n"

    # 对数值字段进行统计
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        result += "**数值字段统计**\n"
        stats_df = df[numeric_cols].describe().round(2)
        result += stats_df.to_markdown()

    # 对类别字段进行统计
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        result += "\n\n**类别字段统计**\n"
        for col in categorical_cols:
            unique_count = df[col].nunique()
            top_values = df[col].value_counts().head(5)
            result += f"- **{col}**: 唯一值={unique_count}\n"
            if unique_count > 0:
                result += "  前5个值：\n"
                for val, count in top_values.items():
                    result += f"    - {val}: {count}次\n"

    # 添加数据质量评估
    result += "\n\n**数据质量评估**\n"
    result += "-" * 60 + "\n"
    
    for col in df.columns:
        non_null_count = df[col].count()
        null_count = len(df) - non_null_count
        completeness = (non_null_count / len(df) * 100) if len(df) > 0 else 0
        result += f"- **{col}**: 完整度 {completeness:.2f}% (非空值: {non_null_count}, 空值: {null_count})\n"
    
    # 添加字段分析洞察
    result += "\n\n**字段分析洞察**\n"
    result += "-" * 60 + "\n"
    
    # 分析数值字段
    for col in numeric_cols:
        if len(df[col].dropna()) > 0:
            mean_val = df[col].mean()
            min_val = df[col].min()
            max_val = df[col].max()
            std_val = df[col].std()
            
            result += f"- **{col}**:\n"
            result += f"  - 均值: {mean_val:.2f}\n"
            result += f"  - 范围: {min_val} 到 {max_val}\n"
            result += f"  - 标准差: {std_val:.2f}\n"
            
            # 简单的业务洞察
            if std_val > mean_val * 0.5:
                result += f"  - 洞察: 该字段值波动较大，可能需要进一步分析其分布原因\n"
            if max_val > mean_val * 2:
                result += f"  - 洞察: 存在较大值，可能包含异常值\n"
    
    # 分析类别字段
    for col in categorical_cols:
        unique_count = df[col].nunique()
        total_count = len(df[col].dropna())
        
        if total_count > 0:
            top_value = df[col].value_counts().index[0]
            top_value_count = df[col].value_counts().iloc[0]
            top_value_percent = (top_value_count / total_count) * 100
            
            result += f"- **{col}**:\n"
            result += f"  - 唯一值数量: {unique_count}\n"
            result += f"  - 最常见值: {top_value} (占比 {top_value_percent:.2f}%)\n"
            
            # 简单的业务洞察
            if unique_count == 1:
                result += f"  - 洞察: 该字段值单一，可能不需要作为分析维度\n"
            elif unique_count > total_count * 0.8:
                result += f"  - 洞察: 该字段值高度分散，可能需要进行分组或归类\n"
    
    return result

# 配置LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "AutoDA-Agent"
# 注意：在实际部署时，应该通过环境变量或配置文件设置API密钥
# os.environ["LANGCHAIN_API_KEY"] = "your-api-key"

# 配置LLM
def get_llm(api_key, model_type="deepseek", base_url=None):
    """
    获取LLM实例
    
    Args:
        api_key: API密钥
        model_type: 模型类型，支持 "deepseek", "wenxin", "xinghuo", "qwen"
        base_url: 可选的API基础URL
    
    Returns:
        ChatOpenAI: LLM实例
    """
    # 模型配置
    model_configs = {
        "deepseek": {
            "model": "deepseek-chat",
            "base_url": base_url or "https://api.deepseek.com/v1"
        },
        "wenxin": {
            "model": "ERNIE-Bot-4",
            "base_url": base_url or "https://ark.cn-beijing.volces.com/api/v3"
        },
        "xinghuo": {
            "model": "spark-pro-2.0",
            "base_url": base_url or "https://spark-api.xf-yun.com/v3"
        },
        "qwen": {
            "model": "qwen-plus",
            "base_url": base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
        "kimi": {
            "model": "kimi-k2.5",
            "base_url": base_url or "https://api.moonshot.cn/v1"
        }
    }
    
    # 获取模型配置
    config = model_configs.get(model_type, model_configs["deepseek"])
    
    # 根据模型类型设置temperature
    if model_type == "kimi":
        temperature = 1.0  # Kimi模型只允许temperature=1
    else:
        temperature = 0.1  # 其他模型降低随机性，提高稳定性
    
    llm = ChatOpenAI(
        model=config["model"],
        api_key=api_key,
        base_url=config["base_url"],
        temperature=temperature
    )
    
    # 使用LangSmith包装LLM
    return llm

# 定义工具
@tool
async def execute_sql(query: str) -> str:
    """
    执行SQL查询并返回结果
    
    Args:
        query: SQL查询语句
    
    Returns:
        str: 查询结果的字符串表示
    """
    try:
        df = run_sql_query(query)
        return df.to_string()
    except Exception as e:
        return f"错误: {str(e)}"

@tool
async def calculate_rfm_scores() -> str:
    """
    计算用户RFM指标并进行分层
    
    Returns:
        str: RFM计算结果的字符串表示，包含用户分层统计
    """
    try:
        df = calculate_rfm()
        
        # 检查数据是否为空
        if df.empty:
            return "RFM计算结果:\n暂无购买数据，无法进行RFM分析\n\n用户分层统计:\n无数据"
        
        segment_stats = df['segment'].value_counts().to_string()
        return f"RFM计算结果:\n{df.head().to_string()}\n\n用户分层统计:\n{segment_stats}"
    except Exception as e:
        return f"错误: {str(e)}"

@tool
async def perform_ab_test(control_conv: int, control_n: int, test_conv: int, test_n: int) -> str:
    """
    执行A/B测试统计检验
    
    Args:
        control_conv: 对照组转化人数
        control_n: 对照组总人数
        test_conv: 实验组转化人数
        test_n: 实验组总人数
    
    Returns:
        str: A/B测试结果的字符串表示
    """
    try:
        result = run_ab_test(control_conv, control_n, test_conv, test_n)
        return str(result)
    except Exception as e:
        return f"错误: {str(e)}"

@tool
async def get_funnel_data() -> str:
    """
    获取转化漏斗数据
    
    Returns:
        str: 漏斗数据的字符串表示
    """
    try:
        df = calculate_funnel()
        
        # 检查数据是否为空
        if df.empty:
            return "转化漏斗分析结果:\n暂无转化数据，无法生成漏斗分析\n\n建议：\n- 上传包含用户行为数据的文件\n- 确保数据中包含浏览、加购和购买等事件类型"
        
        # 检查是否有错误
        if 'error' in df.columns:
            error_message = df['error'].iloc[0]
            return f"转化漏斗分析结果:\n数据获取失败: {error_message}\n\n建议：\n- 确保数据库连接正常\n- 确保temp_events表存在且包含必要的字段\n- 检查数据是否完整"
        
        return df.to_string()
    except Exception as e:
        return f"错误: {str(e)}"

@tool
async def get_ab_conversion_data() -> str:
    """
    获取A/B组转化率数据
    
    Returns:
        str: A/B组转化率数据的字符串表示
    """
    try:
        df = get_ab_conversion()
        return df.to_string()
    except Exception as e:
        return f"错误: {str(e)}"

# 定义工具列表
tools = [
    execute_sql,
    calculate_rfm_scores,
    perform_ab_test,
    get_funnel_data,
    get_ab_conversion_data
]

# 定义Prompt模板
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个资深的数据工程师。你的任务是将用户的自然语言需求转化为精确的 SQL 查询或 Pandas 聚合操作。"),
    ("system", "当前数据库/数据集的信息如下（Schema）："),
    ("system", "- temp_customers (客户表): customer_id, name, email, country, age, signup_date, marketing_opt_in\n"),
    ("system", "- temp_orders (订单表): order_id, customer_id, order_time, payment_method, discount_pct, subtotal_usd, total_usd, country, device, source\n"),
    ("system", "- temp_products (产品表): product_id, category, name, price_usd, cost_usd, margin_usd\n"),
    ("system", "- temp_order_items (订单项表): order_id, product_id, unit_price_usd, quantity, line_total_usd\n"),
    ("system", "- temp_events (事件表): event_id, session_id, timestamp, event_type, product_id, qty, cart_size, payment, discount_pct, amount_usd\n"),
    ("system", "- temp_reviews (评论表): review_id, order_id, product_id, rating, review_text, review_time\n"),
    ("system", "- temp_sessions (会话表): session_id, customer_id, start_time, device, source, country\n"),
    ("system", "数据样例 (Top 3 rows)："),
    ("system", "temp_orders 表样例：\n"),
    ("system", "| order_id | customer_id | order_time | payment_method | discount_pct | subtotal_usd | total_usd | country | device | source |\n"),
    ("system", "|---------|-------------|------------|----------------|--------------|--------------|-----------|---------|--------|--------|\n"),
    ("system", "| 1 | 101 | 2024-01-01 10:00:00 | Credit Card | 0.05 | 100.0 | 95.0 | USA | Desktop | Organic |\n"),
    ("system", "| 2 | 102 | 2024-01-01 11:00:00 | PayPal | 0.10 | 200.0 | 180.0 | UK | Mobile | Social |\n"),
    ("system", "| 3 | 103 | 2024-01-01 12:00:00 | Credit Card | 0.00 | 150.0 | 150.0 | Canada | Desktop | Referral |\n"),
    ("system", "temp_events 表样例：\n"),
    ("system", "| event_id | session_id | timestamp | event_type | product_id | qty | cart_size | payment | discount_pct | amount_usd |\n"),
    ("system", "|---------|------------|------------|------------|------------|-----|-----------|---------|--------------|------------|\n"),
    ("system", "| 1 | S001 | 2024-01-01 10:00:00 | View | P001 | 1 | 0 | NULL | 0.0 | 0.0 |\n"),
    ("system", "| 2 | S001 | 2024-01-01 10:05:00 | Add to Cart | P001 | 1 | 1 | NULL | 0.0 | 0.0 |\n"),
    ("system", "| 3 | S001 | 2024-01-01 10:10:00 | Purchase | P001 | 1 | 1 | 1 | 0.05 | 95.0 |\n"),
    ("system", "## 重要提醒：表结构关系\n"),
    ("system", "- temp_orders 表中没有 session_id 字段，只能通过 customer_id 与其他表关联\n"),
    ("system", "- temp_sessions 表中没有 order_id 字段，只能通过 customer_id 与其他表关联\n"),
    ("system", "## 字段格式说明\n"),
    ("system", "用户选择的字段格式为'表名.字段名'，例如'temp_orders.order_time'，在SQL中使用时保持这种格式。\n"),
    ("system", "## SQL语法限制（重要！）\n"),
    ("system", "数据库使用SQLite，不支持以下语法：\n"),
    ("system", "- PERCENTILE_CONT、PERCENTILE_DISC（不支持的窗口函数）\n"),
    ("system", "- WITH AS（CTE语法不支持）\n"),
    ("system", "- OVER(PARTITION BY)（窗口函数不支持）\n"),
    ("system", "- CROSS JOIN LATERAL（LATERAL不支持）\n"),
    ("system", "请使用简单的SQL查询，如：SELECT field1, field2 FROM table_name LIMIT 100\n"),
    ("system", "## 正确的SQL查询示例\n"),
    ("system", "如果用户选择temp_orders.order_time和temp_orders.total_usd，应该生成：\n"),
    ("system", "SELECT temp_orders.order_time, temp_orders.total_usd FROM temp_orders LIMIT 100\n"),
    ("system", "注意：SQL中表名和字段名之间用点号分隔，但FROM子句中只写表名。\n"),
    ("system", "## 分析流程要求\n"),
    ("system", "1. 分析用户的商业问题\n"),
    ("system", "2. 确定需要的数据和分析方法\n"),
    ("system", "3. 选择合适的工具进行分析\n"),
    ("system", "4. 执行分析并收集结果\n"),
    ("system", "5. 生成有洞察力的分析报告\n"),
    ("system", "## 重要规则\n"),
    ("system", "- 请根据以上数据集的实际结构，提取分析所需的数据。\n"),
    ("system", "- 如果用户的需求（例如漏斗分析）在当前数据结构中无法直接实现（例如缺失 'event_type' 等字段），请不要胡编乱造，直接返回错误信息：\"当前数据集缺乏支持该分析的必要字段：[列出缺失字段]\"。\n"),
    ("system", "- 确保生成的SQL查询只包含实际存在的表和字段。\n"),
    ("system", "- 对于复杂分析，确保使用正确的表关联和聚合函数。\n"),
    ("system", "## 工具使用建议\n"),
    ("system", "- 对于一般数据查询和分析，使用execute_sql工具\n"),
    ("system", "- 对于用户价值分析，使用calculate_rfm_scores工具\n"),
    ("system", "- 对于A/B测试分析，使用perform_ab_test工具\n"),
    ("system", "- 对于转化漏斗分析，使用get_funnel_data工具\n"),
    ("system", "- 对于A/B组转化率分析，使用get_ab_conversion_data工具\n"),
    ("user", "{input}"),
    ("assistant", "我需要分析用户的商业问题，确定需要的数据和分析方法，然后选择合适的工具执行分析。")
])

# 构建Agent
def create_agent(api_key, model_type="deepseek", base_url=None):
    """
    创建Agent实例
    
    Args:
        api_key: API密钥
        model_type: 模型类型，支持 "deepseek", "wenxin", "xinghuo", "qwen"
        base_url: 可选的API基础URL
    
    Returns:
        RunnableSequence: Agent实例
    """
    llm = get_llm(api_key, model_type, base_url)
    
    # 绑定工具
    llm_with_tools = llm.bind_tools(tools)
    
    # 构建序列
    agent = RunnableSequence(
        prompt_template,
        llm_with_tools
    )
    
    return agent

# 运行Agent
@traceable
async def run_agent(input_text, api_key, model_type="deepseek", base_url=None):
    """
    运行Agent处理用户输入
    
    Args:
        input_text: 用户输入
        api_key: API密钥
        model_type: 模型类型，支持 "deepseek", "wenxin", "xinghuo", "qwen"
        base_url: 可选的API基础URL
    
    Returns:
        tuple: (响应文本, 图表对象)
    """
    agent = create_agent(api_key, model_type, base_url)
    
    try:
        response = await agent.ainvoke({"input": input_text})
        
        # 处理工具调用结果
        if response.tool_calls:
            # 这里简化处理，实际应该根据工具调用结果进行相应的处理
            tool_results = []
            all_data = {}
            
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                
                # 根据工具名称执行相应的函数
                try:
                    if tool_name == "execute_sql":
                        from tools import run_sql_query
                        # 记录SQL查询
                        print(f"执行SQL查询: {tool_args}")
                        df = run_sql_query(**tool_args)
                        result = format_sql_result(df)
                        all_data["sql_result"] = df
                    elif tool_name == "calculate_rfm_scores":
                        result = format_rfm_result()
                        all_data["rfm_result"] = result
                    elif tool_name == "perform_ab_test":
                        from tools import run_ab_test
                        ab_result = run_ab_test(**tool_args)
                        result = format_ab_test_result(ab_result)
                        all_data["ab_test_result"] = ab_result
                    elif tool_name == "get_funnel_data":
                        result = format_funnel_result()
                        all_data["funnel_result"] = result
                    elif tool_name == "get_ab_conversion_data":
                        result = format_ab_conversion_result()
                        all_data["ab_conversion_result"] = result
                    else:
                        result = f"未知工具: {tool_name}"
                except Exception as e:
                    result = f"执行工具时出错: {str(e)}"
                
                # 直接添加工具结果，标题已经在格式化函数中包含
                tool_results.append(result)
            
            # 生成企业级分析报告
            final_response = generate_enterprise_report(tool_results, all_data, input_text, api_key, model_type)
            return final_response, None
        else:
            # 直接使用模型的响应
            response_content = response.content
            # 确保响应符合企业级分析标准
            if not response_content.startswith("# 企业级探索性数据分析报告"):
                response_content = f"# 企业级探索性数据分析报告\n\n{response_content}"
            return response_content, None
    except Exception as e:
        return f"错误: {str(e)}", None

def generate_enterprise_report(tool_results, all_data, input_text, api_key=None, model_type="deepseek"):
    """
    生成企业级分析报告（精简版）

    Args:
        tool_results: 工具执行结果列表
        all_data: 所有数据结果
        input_text: 用户输入
        api_key: API密钥（可选）
        model_type: 模型类型（可选）

    Returns:
        str: 企业级分析报告
    """
    # 解析用户输入，直接从原始输入中识别分析意图
    import re
    
    # 尝试从各种格式中提取字段信息
    fields_match = re.search(r'请对以下字段进行企业级探索性数据分析：(.*?)。', input_text)
    if not fields_match:
        fields_match = re.search(r'字段：(.*?)[。\n]', input_text)
    if not fields_match:
        fields_match = re.search(r'选择字段[：:](.*?)[。\n]', input_text)
    
    fields = fields_match.group(1) if fields_match else ""
    
    # 解析分析深度
    depth_match = re.search(r'分析深度：(.*?)\n', input_text)
    analysis_depth = depth_match.group(1) if depth_match else "标准分析"

    # 解析字段列表
    field_list = [f.strip() for f in fields.split(',')] if fields else []
    
    # 如果field_list为空但用户提到了年龄和折扣相关的内容
    if not field_list:
        input_lower = input_text.lower()
        # 检查用户输入中是否包含年龄和折扣相关的关键词
        if '年龄' in input_text or 'age' in input_lower:
            field_list.append('age')
        if '折扣' in input_text or 'discount' in input_lower:
            field_list.append('discount_pct')
        
        # 如果仍然为空，从数据库中获取一些常见字段
        if not field_list:
            # 添加一些常见的电商分析字段
            field_list = ['age', 'discount_pct', 'total_usd', 'order_time', 'category']

    # 分析字段语义
    field_semantics = analyze_field_semantics(field_list)

    # 构建精简报告
    report = f"# 企业级探索性数据分析报告\n"
    report += f"\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += f"**分析字段**: {fields}\n"
    report += "\n" + "="*60 + "\n"

    # 1. 字段语义分析
    report += "\n## 📋 字段语义分析\n"
    if field_semantics:
        report += generate_field_semantic_report_section(field_semantics)
    else:
        report += "- 暂无字段语义分析结果\n"

    # 2. 数据查询结果
    # 过滤并收集有效的工具结果
    valid_tool_results = []
    has_funnel_analysis = False
    has_connection_error = False
    
    for tool_result in tool_results:
        if "查询执行失败" in tool_result:
            valid_tool_results.append(tool_result)
        elif "数据库文件不存在" in tool_result:
            valid_tool_results.append(tool_result)
            has_connection_error = True
        elif "Connection error" in tool_result:
            valid_tool_results.append(tool_result)
            has_connection_error = True
        elif tool_result.strip():
            valid_tool_results.append(tool_result)
            if "转化漏斗分析" in tool_result:
                has_funnel_analysis = True

    if valid_tool_results:
        report += "\n## 📊 数据查询结果\n"
        # 直接添加工具结果，标题已经在工具结果中包含
        for tool_result in valid_tool_results:
            report += tool_result
    # 否则不显示数据查询结果部分

    # 3. 关键洞察（最多5条）
    report += "\n## 💡 关键洞察\n"

    insights = []
    
    # 如果有连接错误，添加相关洞察
    if has_connection_error:
        insights.append("- **数据连接错误**：数据库文件不存在或连接失败")
        insights.append("- **解决方案**：请先上传数据文件并处理，确保数据库文件存在")
        insights.append("- **建议**：检查数据文件格式是否正确，确保文件未被其他程序占用")
    else:
        # 分析用户的商业问题，生成针对性的洞察
        input_lower = input_text.lower()
        
        # 检查是否是转化漏斗分析
        is_funnel_analysis = '转化漏斗' in input_text or 'funnel' in input_lower or '漏斗' in input_text
        
        # 检查是否是渠道分析
        is_channel_analysis = '渠道' in input_text or 'channel' in input_lower or '营销' in input_text
    
    # 如果是转化漏斗分析，添加相关洞察
    if is_funnel_analysis and has_funnel_analysis:
        insights.append("- **转化漏斗分析**：通过分析用户行为转化路径，识别转化瓶颈")
        insights.append("- **优化机会**：针对转化率较低的环节，制定相应的优化策略")
        insights.append("- **用户体验**：改善用户体验，提高整体转化率")
    elif is_channel_analysis:
        # 渠道分析
        # 获取SQL查询结果数据
        sql_result = all_data.get("sql_result")
        
        # 基于实际数据生成渠道洞察
        if sql_result is not None:
            df = sql_result
            if not df.empty and 'error' not in df.columns:
                # 检查是否包含渠道字段
                channel_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['channel', '渠道', 'source', '来源'])]
                
                if channel_cols:
                    channel_col = channel_cols[0]
                    
                    # 分析各渠道的订单量
                    order_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['order', '订单'])]
                    sales_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['sales', '销售', 'revenue', '收入'])]
                    conversion_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['conversion', '转化'])]
                    
                    # 分析渠道订单量
                    if order_cols:
                        order_col = order_cols[0]
                        channel_orders = df.groupby(channel_col)[order_col].sum().sort_values(ascending=False)
                        if not channel_orders.empty:
                            top_channel = channel_orders.index[0]
                            insights.append(f"- **订单量最高的渠道**：{top_channel}，订单量 {channel_orders.iloc[0]:,}")
                    
                    # 分析渠道销售额
                    if sales_cols:
                        sales_col = sales_cols[0]
                        channel_sales = df.groupby(channel_col)[sales_col].sum().sort_values(ascending=False)
                        if not channel_sales.empty:
                            top_sales_channel = channel_sales.index[0]
                            insights.append(f"- **销售额最高的渠道**：{top_sales_channel}，销售额 {channel_sales.iloc[0]:,.2f}")
                    
                    # 分析渠道转化率
                    if conversion_cols:
                        conversion_col = conversion_cols[0]
                        channel_conversion = df.groupby(channel_col)[conversion_col].mean().sort_values(ascending=False)
                        if not channel_conversion.empty:
                            top_conversion_channel = channel_conversion.index[0]
                            insights.append(f"- **转化率最高的渠道**：{top_conversion_channel}，转化率 {channel_conversion.iloc[0]:.2f}%")
        
        # 如果没有针对性的洞察，添加渠道相关的通用洞察
        if not insights:
            insights.append("- **渠道洞察**：通过分析不同营销渠道的效果，识别最有效的获客渠道")
            insights.append("- **分析建议**：对比各渠道的ROI，优化渠道投放策略")
            insights.append("- **优化机会**：针对表现不佳的渠道，分析原因并制定改进策略")
    else:
        # 获取SQL查询结果数据
        sql_result = all_data.get("sql_result")
        
        # 检查是否是年龄对折扣偏好的分析
        has_age = any('age' in field.lower() for field in field_list)
        has_discount = any('discount' in field.lower() for field in field_list)
        has_total_usd = any('total_usd' in field.lower() for field in field_list)
        has_order_time = any('order_time' in field.lower() for field in field_list)
        has_category = any('category' in field.lower() for field in field_list)
        
        # 基于实际数据生成洞察
        if sql_result is not None:
            df = sql_result
            if not df.empty and 'error' not in df.columns:
                # 分析年龄对折扣偏好的关系
                if has_age and has_discount:
                    # 检查是否包含年龄和折扣字段
                    age_cols = [col for col in df.columns if 'age' in col.lower()]
                    discount_cols = [col for col in df.columns if 'discount' in col.lower()]
                    
                    if age_cols and discount_cols:
                        age_col = age_cols[0]
                        discount_col = discount_cols[0]
                        
                        # 按年龄分组分析折扣情况
                        age_groups = df.groupby(pd.cut(df[age_col], bins=[0, 20, 30, 40, 50, 60, 100])).agg({
                            discount_col: ['mean', 'std', 'count']
                        })
                        
                        # 找出折扣偏好最高和最低的年龄段
                        age_groups_flat = age_groups.reset_index()
                        age_groups_flat.columns = ['age_group', 'avg_discount', 'std_discount', 'count']
                        
                        if not age_groups_flat.empty:
                            max_discount_age = age_groups_flat.loc[age_groups_flat['avg_discount'].idxmax()]
                            min_discount_age = age_groups_flat.loc[age_groups_flat['avg_discount'].idxmin()]
                            
                            insights.append(f"- **折扣偏好最高的年龄段**：{max_discount_age['age_group']}，平均折扣率 {max_discount_age['avg_discount']:.2f}%")
                            insights.append(f"- **折扣偏好最低的年龄段**：{min_discount_age['age_group']}，平均折扣率 {min_discount_age['avg_discount']:.2f}%")
                
                # 分析交易金额分布
                if has_total_usd:
                    total_cols = [col for col in df.columns if 'total' in col.lower() or 'amount' in col.lower()]
                    if total_cols:
                        total_col = total_cols[0]
                        avg_total = df[total_col].mean()
                        max_total = df[total_col].max()
                        min_total = df[total_col].min()
                        
                        insights.append(f"- **交易金额分析**：平均交易金额 {avg_total:.2f} USD，最高 {max_total:.2f} USD，最低 {min_total:.2f} USD")
                
                # 分析时间趋势
                if has_order_time:
                    time_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['time', 'date', 'day'])]
                    if time_cols:
                        time_col = time_cols[0]
                        if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                            # 按时间分组
                            df[time_col] = pd.to_datetime(df[time_col])
                            trend_df = df.groupby(df[time_col].dt.date).size().reset_index(name='order_count')
                            
                            if len(trend_df) > 1:
                                insights.append(f"- **时间趋势分析**：共分析 {len(trend_df)} 天的订单数据，订单量波动较大")
                
                # 分析品类分布
                if has_category:
                    category_cols = [col for col in df.columns if 'category' in col.lower()]
                    if category_cols:
                        category_col = category_cols[0]
                        top_categories = df[category_col].value_counts().head(3)
                        if not top_categories.empty:
                            insights.append(f"- **品类分析**：Top 3 品类分别是 {top_categories.index[0]}、{top_categories.index[1]} 和 {top_categories.index[2]}")
        
        # 如果没有针对性的洞察，添加基于实际数据的洞察
        if not insights:
            # 基于实际数据生成洞察
            if sql_result is not None:
                df = sql_result
                if not df.empty and 'error' not in df.columns:
                    # 分析数据中的关键指标
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    
                    # 基于数值字段生成洞察
                    for col in numeric_cols:
                        if df[col].nunique() > 1:
                            avg_val = df[col].mean()
                            max_val = df[col].max()
                            min_val = df[col].min()
                            insights.append(f"- **{col}分析**：平均值 {avg_val:.2f}，最大值 {max_val:.2f}，最小值 {min_val:.2f}")
                    
                    # 基于分类字段生成洞察
                    for col in categorical_cols:
                        if df[col].nunique() > 1:
                            top_values = df[col].value_counts().head(3)
                            if not top_values.empty:
                                insights.append(f"- **{col}分析**：Top 3 值分别是 {top_values.index[0]}、{top_values.index[1]} 和 {top_values.index[2]}")
            
            # 如果仍然没有洞察，使用基于字段语义的洞察
            if not insights:
                semantic_insights = generate_semantic_insights(field_semantics)
                insights = semantic_insights[:5]

    # 确保最多5条洞察
    for insight in insights[:5]:
        report += f"{insight}\n"

    # 4. 业务建议（最多3条）
    report += "\n## 🎯 业务建议\n"

    suggestions = []
    
    # 基于实际数据生成业务建议
    if sql_result is not None:
        df = sql_result
        if not df.empty and 'error' not in df.columns:
            # 分析数据中的关键指标
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # 基于数值字段生成建议
            for col in numeric_cols:
                if df[col].nunique() > 1:
                    avg_val = df[col].mean()
                    max_val = df[col].max()
                    min_val = df[col].min()
                    
                    # 基于平均值和最大值的差异生成建议
                    if max_val > avg_val * 1.5:
                        suggestions.append(f"- **{col}优化**：针对{col}值较高的用户或产品，制定专属策略，提高整体表现")
                    elif min_val < avg_val * 0.5:
                        suggestions.append(f"- **{col}提升**：关注{col}值较低的用户或产品，分析原因并制定改进方案")
            
            # 基于分类字段生成建议
            for col in categorical_cols:
                if df[col].nunique() > 1:
                    top_values = df[col].value_counts()
                    if not top_values.empty:
                        # 针对占比最高的类别生成建议
                        top_category = top_values.index[0]
                        top_ratio = top_values.iloc[0] / len(df) * 100
                        suggestions.append(f"- **{col}策略**：针对{top_category}（占比{top_ratio:.2f}%）制定重点策略，同时关注其他类别")
    
    # 如果没有基于数据的建议，使用基于字段语义和用户输入的建议
    if not suggestions:
        # 基于用户输入和字段语义生成建议
        if is_funnel_analysis and has_funnel_analysis:
            suggestions.append("- **优化转化路径**：识别转化漏斗中的瓶颈环节，优化用户体验")
            suggestions.append("- **提高加购率**：通过推荐系统、促销活动等方式提高用户加购率")
            suggestions.append("- **降低购买环节流失**：简化购买流程，减少购买环节的用户流失")
        elif is_channel_analysis:
            # 渠道分析的业务建议 - 调用大模型生成具体建议
            if api_key:
                channel_suggestions = generate_channel_suggestions_with_llm(sql_result, input_text, api_key, model_type)
                suggestions.extend(channel_suggestions)
            else:
                # 如果没有API密钥，使用模板建议
                suggestions.append("- **渠道优化**：增加对高ROI渠道的投入，减少对低效能渠道的资源分配")
                suggestions.append("- **渠道整合**：整合线上线下渠道，实现全渠道营销闭环")
                suggestions.append("- **渠道差异化**：针对不同渠道的用户特点，制定差异化的营销策略")
        elif has_age and has_discount:
            suggestions.append("- **差异化折扣策略**：针对不同年龄段制定不同的折扣策略，如对折扣敏感度高的年龄段提供更多优惠")
            suggestions.append("- **精准营销**：根据年龄段的折扣偏好，定向推送相应的促销活动")
            suggestions.append("- **优化定价**：结合年龄分布和折扣偏好，优化产品定价策略，提高转化率")
        elif has_total_usd:
            suggestions.append("- **客单价优化**：分析交易金额分布，制定价格策略提高客单价")
            suggestions.append("- **促销策略**：针对不同交易金额区间的用户制定差异化促销方案")
            suggestions.append("- **会员体系**：建立会员等级制度，鼓励用户增加消费金额")
        elif has_order_time:
            suggestions.append("- **时间策略**：根据时间趋势，合理安排促销活动和库存")
            suggestions.append("- **高峰期营销**：在订单高峰期加大营销力度，提高整体销售额")
            suggestions.append("- **季节性规划**：根据季节性波动，提前做好库存和营销准备")
        elif has_category:
            suggestions.append("- **品类优化**：分析品类表现，调整产品结构和促销策略")
            suggestions.append("- **交叉销售**：基于品类关联分析，制定交叉销售策略")
            suggestions.append("- **库存管理**：根据品类销售情况，优化库存水平，减少库存成本")
        else:
            # 通用建议
            for field, sem in field_semantics.items():
                if sem['category'] == '交易金额' and not any('交易金额' in suggestion for suggestion in suggestions):
                    suggestions.append(f"- **{field}优化**：分析{field}的分布和趋势，制定相应的业务策略")
                elif sem['category'] == '用户维度' and not any('用户' in suggestion for suggestion in suggestions):
                    suggestions.append(f"- **用户分析**：基于{field}进行用户画像和分层分析，制定精准营销策略")
                elif sem['category'] == '时间维度' and not any('时间' in suggestion for suggestion in suggestions):
                    suggestions.append(f"- **时间策略**：分析{field}的时间趋势，合理安排业务活动")
                elif sem['category'] == '商品维度' and not any('商品' in suggestion for suggestion in suggestions):
                    suggestions.append(f"- **商品策略**：分析{field}的表现，优化产品结构和促销策略")
                elif sem['category'] == '促销维度' and not any('促销' in suggestion for suggestion in suggestions):
                    suggestions.append(f"- **促销优化**：分析{field}的效果，优化促销策略")
                elif sem['category'] == '渠道维度' and not any('渠道' in suggestion for suggestion in suggestions):
                    suggestions.append(f"- **渠道策略**：分析{field}的表现，优化渠道投放策略")
                
                # 最多3条建议
                if len(suggestions) >= 3:
                    break
    
    # 确保最多3条建议
    for recommendation in suggestions[:3]:
        report += f"{recommendation}\n"
    
    # 如果没有建议，添加默认建议
    if not suggestions:
        report += "- 建议结合业务场景深入分析相关维度\n"

    return report

def generate_channel_suggestions_with_llm(sql_result, input_text, api_key, model_type="deepseek"):
    """
    使用大模型生成具体的渠道建议
    
    Args:
        sql_result: SQL查询结果DataFrame
        input_text: 用户输入
        api_key: API密钥
        model_type: 模型类型
        
    Returns:
        list: 渠道建议列表
    """
    try:
        # 准备数据摘要
        data_summary = ""
        if sql_result is not None and not sql_result.empty and 'error' not in sql_result.columns:
            # 提取渠道数据
            channel_cols = [col for col in sql_result.columns if any(keyword in col.lower() for keyword in ['channel', '渠道', 'source', '来源'])]
            if channel_cols:
                channel_col = channel_cols[0]
                
                # 提取关键指标
                order_cols = [col for col in sql_result.columns if any(keyword in col.lower() for keyword in ['order', '订单'])]
                sales_cols = [col for col in sql_result.columns if any(keyword in col.lower() for keyword in ['sales', '销售', 'revenue', '收入'])]
                conversion_cols = [col for col in sql_result.columns if any(keyword in col.lower() for keyword in ['conversion', '转化'])]
                user_cols = [col for col in sql_result.columns if any(keyword in col.lower() for keyword in ['user', '用户', 'customer', '客户'])]
                avg_price_cols = [col for col in sql_result.columns if any(keyword in col.lower() for keyword in ['avg', '平均', '客单价', 'aov'])]
                
                # 构建数据摘要
                data_summary += "\n渠道数据摘要：\n"
                for idx, row in sql_result.iterrows():
                    channel_name = row[channel_col]
                    data_summary += f"- {channel_name}: "
                    if order_cols:
                        data_summary += f"订单量={row[order_cols[0]]:,} "
                    if sales_cols:
                        data_summary += f"销售额={row[sales_cols[0]]:,.2f} "
                    if user_cols:
                        data_summary += f"用户数={row[user_cols[0]]:,} "
                    if avg_price_cols:
                        data_summary += f"客单价={row[avg_price_cols[0]]:.2f} "
                    if conversion_cols:
                        data_summary += f"转化率={row[conversion_cols[0]]:.2f}% "
                    data_summary += "\n"
                
                # 添加数据分析
                data_summary += "\n数据分析：\n"
                if sales_cols:
                    max_sales_channel = sql_result.loc[sql_result[sales_cols[0]].idxmax(), channel_col]
                    min_sales_channel = sql_result.loc[sql_result[sales_cols[0]].idxmin(), channel_col]
                    max_sales_value = sql_result[sales_cols[0]].max()
                    min_sales_value = sql_result[sales_cols[0]].min()
                    data_summary += f"- 销售额最高：{max_sales_channel}（{max_sales_value:,.2f}）\n"
                    data_summary += f"- 销售额最低：{min_sales_channel}（{min_sales_value:,.2f}）\n"
                if conversion_cols:
                    max_conv_channel = sql_result.loc[sql_result[conversion_cols[0]].idxmax(), channel_col]
                    min_conv_channel = sql_result.loc[sql_result[conversion_cols[0]].idxmin(), channel_col]
                    max_conv_value = sql_result[conversion_cols[0]].max()
                    min_conv_value = sql_result[conversion_cols[0]].min()
                    data_summary += f"- 转化率最高：{max_conv_channel}（{max_conv_value:.2f}%）\n"
                    data_summary += f"- 转化率最低：{min_conv_channel}（{min_conv_value:.2f}%）\n"
        
        # 构建提示词
        prompt = f"""你是一位资深的营销策略专家。请基于以下数据，为用户提供具体的、可执行的营销渠道优化建议。

用户需求：{input_text}

{data_summary}

分析要求：
1. 仔细分析各渠道的数据表现，识别表现最好和最差的渠道
2. 基于实际数据（订单量、销售额、用户数、客单价、转化率）提出具体建议
3. 建议必须包含具体的行动步骤和可量化的预期效果
4. 每条建议应该针对特定渠道，避免泛泛而谈
5. 建议应该基于数据事实，不要使用模板化的表述
6. 每条建议应该简洁明了，不超过120字
7. 最多提供3条建议

注意事项：
- 不要使用"增加对高ROI渠道的投入"这种模板化表述
- 不要使用"整合线上线下渠道"这种泛泛而谈的建议
- 建议必须包含具体的数据支撑和可执行的步骤
- 预期效果应该包含具体的数字（如"提升40%"、"ROI提升至1:15"）

请直接输出建议，每条建议以"- "开头，不要添加其他说明。"""
        
        # 调用大模型
        llm = get_llm(api_key, model_type)
        response = llm.invoke(prompt)
        
        # 解析响应
        suggestions = []
        lines = response.content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                suggestion_text = line[2:].strip()
                # 验证建议长度
                if len(suggestion_text) <= 120:
                    suggestions.append(f"- **渠道优化建议**：{suggestion_text}")
            elif line and not line.startswith('-'):
                suggestion_text = line.strip()
                # 验证建议长度
                if len(suggestion_text) <= 120:
                    suggestions.append(f"- **渠道优化建议**：{suggestion_text}")
        
        # 如果没有生成建议，返回默认建议
        if not suggestions:
            suggestions = [
                "- **渠道优化**：增加对高ROI渠道的投入，减少对低效能渠道的资源分配",
                "- **渠道整合**：整合线上线下渠道，实现全渠道营销闭环",
                "- **渠道差异化**：针对不同渠道的用户特点，制定差异化的营销策略"
            ]
        
        return suggestions[:3]
        
    except Exception as e:
        # 如果调用失败，返回默认建议
        return [
            "- **渠道优化**：增加对高ROI渠道的投入，减少对低效能渠道的资源分配",
            "- **渠道整合**：整合线上线下渠道，实现全渠道营销闭环",
            "- **渠道差异化**：针对不同渠道的用户特点，制定差异化的营销策略"
        ]