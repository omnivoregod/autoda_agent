"""
字段语义分析模块
此脚本包含字段语义分析的所有功能，用于增强探索性数据分析报告。
使用方法：将此文件保存为 field_semantic.py，然后在 agent.py 中导入使用。
"""

import re
from typing import Dict, List, Any

def analyze_field_semantics(fields: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    分析字段语义

    Args:
        fields: 字段列表

    Returns:
        dict: 字段语义映射
    """
    semantics = {}

    # 预定义的字段语义模式（按优先级排序）
    patterns = [
        # 时间相关（优先匹配）
        (r'(order|purchase|transaction|trade|create|register|signup)_?(date|time|at|day)', {
            'category': '时间维度',
            'description': '交易或行为发生时间',
            'analysis_angle': '趋势分析、季节性分析、周期性分析',
            'main_dimension': '时间维度',
            'type': 'datetime'
        }),

        # 评分相关
        (r'(rating|score|stars|likes|favorites)', {
            'category': '评价维度',
            'description': '用户评分或评价',
            'analysis_angle': '质量分析、满意度分析',
            'main_dimension': '评价维度',
            'type': 'numeric'
        }),

        # 促销相关（优先于数量）
        (r'(discount|coupon|reduce)', {
            'category': '促销维度',
            'description': '折扣或优惠金额',
            'analysis_angle': '促销效果分析、价格敏感度分析',
            'main_dimension': '促销维度',
            'type': 'numeric'
        }),

        # 用户相关
        (r'(user|customer|member|client)_?id', {
            'category': '用户标识',
            'description': '唯一识别用户身份',
            'analysis_angle': '用户行为追踪、用户分层、用户价值评估',
            'main_dimension': '用户维度',
            'type': 'identifier'
        }),
        (r'(user|customer|member|client)_?(name|email|phone)', {
            'category': '用户属性',
            'description': '用户基本信息',
            'analysis_angle': '用户画像、联系方式',
            'main_dimension': '用户维度',
            'type': 'user_info'
        }),
        (r'(age|birth|year)', {
            'category': '用户属性',
            'description': '用户年龄或出生年份',
            'analysis_angle': '用户画像、年龄段分析',
            'main_dimension': '用户维度',
            'type': 'numeric'
        }),
        (r'(gender|sex)', {
            'category': '用户属性',
            'description': '用户性别',
            'analysis_angle': '性别差异分析、用户画像',
            'main_dimension': '用户维度',
            'type': 'categorical'
        }),
        (r'(location|city|region|province|country|address)', {
            'category': '地域维度',
            'description': '用户所在地域',
            'analysis_angle': '地域分析、区域市场策略',
            'main_dimension': '地域维度',
            'type': 'categorical'
        }),

        # 订单相关
        (r'(order|transaction|purchase|trade)_?(id|number|no)', {
            'category': '订单标识',
            'description': '唯一识别订单',
            'analysis_angle': '订单分析、转化漏斗',
            'main_dimension': '交易维度',
            'type': 'identifier'
        }),

        # 商品相关
        (r'(product|item|goods|sku|commodity)_?(id|no|code)', {
            'category': '商品标识',
            'description': '唯一识别商品',
            'analysis_angle': '商品分析、SKU分析',
            'main_dimension': '商品维度',
            'type': 'identifier'
        }),
        (r'(product|item|goods|sku|commodity|category)', {
            'category': '品类维度',
            'description': '商品所属品类',
            'analysis_angle': '品类结构分析、品类贡献分析',
            'main_dimension': '商品维度',
            'type': 'categorical'
        }),

        # 营销相关
        (r'(campaign|activity|promotion)', {
            'category': '营销维度',
            'description': '营销活动',
            'analysis_angle': '营销效果分析、活动ROI分析',
            'main_dimension': '营销维度',
            'type': 'categorical'
        }),
        (r'(channel|source|platform|medium)', {
            'category': '渠道维度',
            'description': '用户来源或渠道',
            'analysis_angle': '渠道效果分析、渠道ROI分析',
            'main_dimension': '渠道维度',
            'type': 'categorical'
        }),

        # 状态相关
        (r'(status|state|step|phase)', {
            'category': '状态维度',
            'description': '订单或流程状态',
            'analysis_angle': '流程分析、转化漏斗分析',
            'main_dimension': '状态维度',
            'type': 'categorical'
        }),

        # 行为相关
        (r'(frequency|recency|tenure|duration)', {
            'category': '行为维度',
            'description': '用户行为指标',
            'analysis_angle': '用户活跃度分析、用户留存分析',
            'main_dimension': '行为维度',
            'type': 'numeric'
        }),

        # 交易相关（放在后面，避免误匹配）
        (r'(amount|gmv|revenue|sales|price|total|cost)', {
            'category': '交易金额',
            'description': '订单或交易金额',
            'analysis_angle': '营收分析、客单价分析、GMV分析',
            'main_dimension': '交易维度',
            'type': 'numeric'
        }),
        (r'(quantity|count|num|qty)', {
            'category': '数量',
            'description': '商品数量',
            'analysis_angle': '销量分析、客单价分析',
            'main_dimension': '交易维度',
            'type': 'numeric'
        }),
        
        # 事件相关
        (r'(event|action|behavior)', {
            'category': '事件类型',
            'description': '用户行为事件类型',
            'analysis_angle': '用户行为分析、转化漏斗分析',
            'main_dimension': '行为维度',
            'type': 'categorical'
        }),
        
        # 会话相关
        (r'(session|visitor)', {
            'category': '会话标识',
            'description': '用户会话或访客标识',
            'analysis_angle': '流量分析、会话分析',
            'main_dimension': '渠道维度',
            'type': 'identifier'
        }),
        
        # 时间戳相关
        (r'(timestamp|time|date)', {
            'category': '时间维度',
            'description': '时间戳',
            'analysis_angle': '时间序列分析、趋势分析',
            'main_dimension': '时间维度',
            'type': 'datetime'
        }),
    ]

    for field in fields:
        # 处理"表名.字段名"格式，提取字段名
        field_name = field.split('.')[-1] if '.' in field else field
        field_lower = field_name.lower()
        matched = False

        for pattern, semantic in patterns:
            if re.search(pattern, field_lower):
                semantics[field] = semantic
                matched = True
                break

        if not matched:
            # 默认语义
            semantics[field] = {
                'category': '其他',
                'description': '需进一步确认业务含义',
                'analysis_angle': '待分析',
                'main_dimension': '待定',
                'type': 'unknown'
            }

    return semantics

def get_chart_recommendations(field_semantics: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    根据字段语义获取推荐的图表

    Args:
        field_semantics: 字段语义映射

    Returns:
        list: 推荐的图表列表
    """
    recommendations = []
    seen = set()

    for field, semantics in field_semantics.items():
        field_type = semantics['type']
        category = semantics['category']

        # 数值字段推荐分布图
        if field_type == 'numeric' and 'numeric' not in seen:
            recommendations.append({
                'purpose': '分布分析',
                'chart': '直方图、箱线图',
                'fields': ', '.join([f for f, s in field_semantics.items() if s['type'] == 'numeric'])
            })
            seen.add('numeric')

        # 时间字段推荐趋势图
        if field_type == 'datetime' and 'datetime' not in seen:
            recommendations.append({
                'purpose': '趋势分析',
                'chart': '折线图、面积图',
                'fields': ', '.join([f for f, s in field_semantics.items() if s['type'] == 'datetime'])
            })
            seen.add('datetime')

        # 类别字段推荐构成图
        if field_type == 'categorical' and 'categorical' not in seen:
            recommendations.append({
                'purpose': '构成分析',
                'chart': '饼图、堆叠柱状图',
                'fields': ', '.join([f for f, s in field_semantics.items() if s['type'] == 'categorical'])
            })
            seen.add('categorical')

    # 如果没有特定推荐，添加通用推荐
    if not recommendations:
        recommendations.append({
            'purpose': '综合分析',
            'chart': '根据数据类型选择合适图表',
            'fields': ', '.join(field_semantics.keys())
        })

    return recommendations

def generate_semantic_insights(field_semantics: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    基于字段语义生成业务洞察

    Args:
        field_semantics: 字段语义映射

    Returns:
        list: 业务洞察列表
    """
    insights = []

    # 检查主维度
    dimensions = [s['main_dimension'] for s in field_semantics.values()]

    # 用户维度洞察
    if '用户维度' in dimensions:
        insights.append("- **用户洞察**：通过用户标识和属性字段，可以进行用户画像、用户分层和用户价值分析")
        insights.append("- **分析建议**：结合用户年龄、性别、地域等属性，识别核心用户群体特征")

    # 交易维度洞察
    if '交易维度' in dimensions:
        insights.append("- **交易洞察**：通过交易金额和数量字段，可以分析营收、客单价和购买频次")
        insights.append("- **分析建议**：关注交易金额的分布和趋势，识别异常交易和增长机会")

    # 时间维度洞察
    if '时间维度' in dimensions:
        insights.append("- **时间洞察**：通过时间字段，可以分析销售趋势、季节性波动和营销活动效果")
        insights.append("- **分析建议**：结合时间维度进行同比、环比分析，识别周期性规律")

    # 商品维度洞察
    if '商品维度' in dimensions:
        insights.append("- **商品洞察**：通过品类字段，可以分析商品结构、品类贡献和商品表现")
        insights.append("- **分析建议**：关注品类销售额占比，识别主力品类和潜力品类")

    # 促销维度洞察
    if '促销维度' in dimensions:
        insights.append("- **促销洞察**：通过折扣字段，可以分析促销效果和价格敏感度")
        insights.append("- **分析建议**：评估折扣力度与销量的关系，优化促销策略")

    # 渠道维度洞察
    if '渠道维度' in dimensions:
        insights.append("- **渠道洞察**：通过渠道字段，可以分析不同渠道的用户获取和转化效果")
        insights.append("- **分析建议**：对比渠道ROI，优化渠道投放策略")

    # 状态维度洞察
    if '状态维度' in dimensions:
        insights.append("- **流程洞察**：通过状态字段，可以分析转化漏斗和各环节流失情况")
        insights.append("- **分析建议**：识别转化瓶颈，优化用户体验")

    # 评价维度洞察
    if '评价维度' in dimensions:
        insights.append("- **质量洞察**：通过评分字段，可以分析用户满意度和产品质量")
        insights.append("- **分析建议**：关注低评分商品或用户，制定改进措施")

    # 行为维度洞察
    if '行为维度' in dimensions:
        insights.append("- **行为洞察**：通过行为指标字段，可以分析用户活跃度和留存情况")
        insights.append("- **分析建议**：识别高活跃用户特征，制定用户激活策略")

    return insights

def generate_field_semantic_report_section(field_semantics: Dict[str, Dict[str, Any]]) -> str:
    """
    生成字段语义分析报告部分

    Args:
        field_semantics: 字段语义映射

    Returns:
        str: 字段语义分析报告部分
    """
    report = ""

    # 生成字段语义表格
    report += "| 字段名称 | 语义类别 | 业务含义 | 分析角度 |\n"
    report += "|---------|---------|---------|---------|\n"

    for field, semantics in field_semantics.items():
        report += f"| {field} | {semantics['category']} | {semantics['description']} | {semantics['analysis_angle']} |\n"

    # 核心分析维度
    report += "\n### 🎯 核心分析维度\n\n"
    report += "基于字段语义分析，系统识别以下核心分析维度：\n\n"

    dimensions = set([s['main_dimension'] for s in field_semantics.values()])
    for dim in dimensions:
        report += f"- **{dim}**：{', '.join([f for f, s in field_semantics.items() if s['main_dimension'] == dim])}\n"

    # 推荐图表
    report += "\n### 📊 推荐图表\n\n"
    report += "| 分析目的 | 推荐图表 | 适用字段 |\n"
    report += "|---------|---------|---------|\n"

    chart_recommendations = get_chart_recommendations(field_semantics)
    for rec in chart_recommendations:
        report += f"| {rec['purpose']} | {rec['chart']} | {rec['fields']} |\n"

    return report

if __name__ == "__main__":
    # 测试字段语义分析
    test_fields = [
        "user_id", "customer_age", "gender", "location",
        "order_amount", "quantity", "discount",
        "order_date", "product_category",
        "campaign_name", "channel"
    ]

    print("测试字段语义分析：")
    print("=" * 60)

    semantics = analyze_field_semantics(test_fields)

    for field, sem in semantics.items():
        print(f"\n字段: {field}")
        print(f"  类别: {sem['category']}")
        print(f"  描述: {sem['description']}")
        print(f"  分析角度: {sem['analysis_angle']}")
        print(f"  主维度: {sem['main_dimension']}")

    print("\n" + "=" * 60)
    print("\n推荐图表：")
    for rec in get_chart_recommendations(semantics):
        print(f"  {rec['purpose']}: {rec['chart']} (适用字段: {rec['fields']})")

    print("\n" + "=" * 60)
    print("\n业务洞察：")
    for insight in generate_semantic_insights(semantics):
        print(f"  {insight}")