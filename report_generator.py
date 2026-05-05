import pandas as pd
from typing import Dict, Any
from tools import calculate_funnel, get_ab_conversion, run_ab_test, calculate_ab_roi, get_rfm_segment_stats
from datetime import datetime
from roi_calculator import generate_roi_report
from tracking import generate_performance_report

def generate_funnel_report(category: str = None) -> str:
    """
    生成转化漏斗分析报告
    
    Args:
        category: 可选的商品类别
    
    Returns:
        str: 分析报告
    """
    # 获取漏斗数据
    funnel_df = calculate_funnel(category)
    
    if 'error' in funnel_df.columns:
        return f"错误: {funnel_df['error'].iloc[0]}"
    
    # 生成报告
    report = f"# 转化漏斗分析报告\n\n"
    report += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    if category:
        report += f"**分析类别**: {category}\n\n"
    else:
        report += "**分析类别**: 全部\n\n"
    
    # 漏斗数据表格
    report += "## 漏斗数据\n\n"
    report += funnel_df.to_markdown(index=False) + "\n\n"
    
    # 分析洞察
    report += "## 分析洞察\n\n"
    if not funnel_df.empty:
        # 计算整体转化率
        total_views = funnel_df.iloc[0]['count']
        total_purchases = funnel_df[funnel_df['step'] == '购买']['count'].iloc[0] if '购买' in funnel_df['step'].values else 0
        overall_conversion = total_purchases / total_views * 100 if total_views > 0 else 0
        
        report += f"- **整体转化率**: {overall_conversion:.2f}%\n"
        
        # 识别瓶颈
        if len(funnel_df) >= 2:
            for i in range(1, len(funnel_df)):
                stage_conv = funnel_df.iloc[i]['stage_conversion_rate']
                if stage_conv < 20:  # 假设20%为阈值
                    report += f"- **瓶颈识别**: {funnel_df.iloc[i-1]['step']}到{funnel_df.iloc[i]['step']}的转化率较低 ({stage_conv:.2f}%)\n"
    
    # 业务建议
    report += "## 业务建议\n\n"
    report += "1. **优化产品页面**: 提高产品描述质量，增加高质量图片和视频\n"
    report += "2. **简化购买流程**: 减少结账步骤，优化支付体验\n"
    report += "3. **个性化推荐**: 根据用户浏览历史推荐相关产品\n"
    report += "4. **促销活动**: 针对加购未购买的用户发送优惠券\n"
    report += "5. **用户反馈**: 收集用户反馈，了解购买障碍\n"
    
    return report

def generate_ab_test_report(monthly_active_users: int = None) -> str:
    """
    生成A/B测试分析报告
    
    Args:
        monthly_active_users: 月活跃用户数，如果不提供则从数据中计算
    
    Returns:
        str: 分析报告
    """
    # 如果没有提供月活跃用户数，从数据中计算
    if monthly_active_users is None:
        try:
            from tools import run_sql_query
            query = """
            SELECT COUNT(DISTINCT user_id) as monthly_active_users
            FROM user_events
            WHERE timestamp >= datetime('now', '-30 days')
            """
            result = run_sql_query(query)
            if not result.empty and 'monthly_active_users' in result.columns:
                monthly_active_users = int(result['monthly_active_users'].iloc[0])
            else:
                monthly_active_users = 100000  # 默认值
        except:
            monthly_active_users = 100000  # 默认值
    
    # 获取A/B组数据
    ab_df = get_ab_conversion()
    
    if 'error' in ab_df.columns:
        return f"错误: {ab_df['error'].iloc[0]}"
    
    # 生成报告
    report = f"# A/B测试分析报告\n\n"
    report += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # A/B组数据表格
    report += "## A/B组数据\n\n"
    report += ab_df.to_markdown(index=False) + "\n\n"
    
    # 执行A/B测试
    if len(ab_df) == 2:
        control_row = ab_df[ab_df['group'] == 'A'].iloc[0]
        test_row = ab_df[ab_df['group'] == 'B'].iloc[0]
        
        # 运行统计检验
        test_result = run_ab_test(
            int(control_row['conversions']),
            int(control_row['total_users']),
            int(test_row['conversions']),
            int(test_row['total_users'])
        )
        
        # 计算ROI
        avg_order_value = (control_row['avg_order_value'] + test_row['avg_order_value']) / 2
        roi_result = calculate_ab_roi(
            int(control_row['conversions']),
            int(control_row['total_users']),
            int(test_row['conversions']),
            int(test_row['total_users']),
            avg_order_value,
            monthly_active_users
        )
        
        # 统计结果
        report += "## 统计结果\n\n"
        report += f"- **对照组转化率**: {test_result['control_rate']:.4f}\n"
        report += f"- **实验组转化率**: {test_result['test_rate']:.4f}\n"
        report += f"- **转化率差异**: {test_result['rate_diff']:.4f} ({test_result['rate_diff']*100:.2f}%)\n"
        report += f"- **P值**: {test_result['p_value']:.4f}\n"
        report += f"- **显著性**: {'显著' if test_result['is_significant'] else '不显著'}\n\n"
        
        # ROI分析
        report += "## ROI分析\n\n"
        report += f"- **额外转化数**: {roi_result['additional_conversions']:.2f}\n"
        report += f"- **额外收入**: ¥{roi_result['additional_revenue']:.2f}\n"
        report += f"- **测试成本**: ¥{roi_result['test_cost']:.2f}\n"
        report += f"- **ROI**: {roi_result['roi']:.2f}%\n\n"
    
    # 业务建议
    report += "## 业务建议\n\n"
    if len(ab_df) == 2:
        if test_result['is_significant'] and test_result['rate_diff'] > 0:
            report += "1. **全面推广**: 将实验组方案全面推广到所有用户\n"
            report += "2. **持续优化**: 基于实验组方案继续进行迭代优化\n"
            report += "3. **监控效果**: 密切监控全面推广后的效果\n"
        else:
            report += "1. **重新设计**: 重新设计测试方案，针对具体问题进行优化\n"
            report += "2. **增加样本**: 考虑增加样本量，提高测试的统计功效\n"
            report += "3. **分段测试**: 针对不同用户群体进行分段测试\n"
    
    return report

def generate_rfm_report() -> str:
    """
    生成RFM用户分层分析报告
    
    Returns:
        str: 分析报告
    """
    # 获取RFM分层统计
    segment_stats = get_rfm_segment_stats()
    
    if 'error' in segment_stats.columns:
        return f"错误: {segment_stats['error'].iloc[0]}"
    
    # 生成报告
    report = f"# RFM用户分层分析报告\n\n"
    report += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # RFM分层统计表格
    report += "## 用户分层统计\n\n"
    report += segment_stats.to_markdown(index=False) + "\n\n"
    
    # 分析洞察
    report += "## 分析洞察\n\n"
    if not segment_stats.empty:
        # 计算高价值用户占比
        high_value_segments = ['核心高频', '重要客户']
        high_value_users = segment_stats[segment_stats['segment'].isin(high_value_segments)]['user_count'].sum()
        total_users = segment_stats['user_count'].sum()
        high_value_percentage = high_value_users / total_users * 100 if total_users > 0 else 0
        
        # 计算高价值用户贡献的收入占比
        high_value_revenue = segment_stats[segment_stats['segment'].isin(high_value_segments)]['monetary'].sum()
        total_revenue = segment_stats['monetary'].sum()
        high_value_revenue_percentage = high_value_revenue / total_revenue * 100 if total_revenue > 0 else 0
        
        report += f"- **高价值用户占比**: {high_value_percentage:.2f}%\n"
        report += f"- **高价值用户收入贡献**: {high_value_revenue_percentage:.2f}%\n"
        
        # 识别需要关注的用户群体
        if '低价值' in segment_stats['segment'].values:
            low_value_users = segment_stats[segment_stats['segment'] == '低价值']['user_count'].iloc[0]
            low_value_percentage = low_value_users / total_users * 100 if total_users > 0 else 0
            report += f"- **低价值用户占比**: {low_value_percentage:.2f}%\n"
    
    # 业务建议
    report += "## 业务建议\n\n"
    report += "1. **高价值用户**: 提供VIP服务，专属优惠，个性化推荐\n"
    report += "2. **潜力用户**: 发送个性化促销，鼓励首次购买或增加购买频率\n"
    report += "3. **流失风险用户**: 发送召回邮件，提供专属折扣\n"
    report += "4. **低价值用户**: 尝试转化或适当放弃，降低营销成本\n"
    report += "5. **用户分层运营**: 针对不同层级用户制定差异化策略\n"
    
    return report

def generate_comprehensive_report(workflow_output: Dict[str, Any]) -> str:
    """
    生成综合商业分析报告
    
    Args:
        workflow_output: 工作流输出结果
        
    Returns:
        str: 综合分析报告
    """
    # 生成报告
    report = f"# 企业级商业分析报告\n\n"
    report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 1. 需求诊断
    if 'business_context' in workflow_output:
        business_context = workflow_output['business_context']
        report += "## 🎯 需求诊断\n"
        report += "-" * 60 + "\n"
        report += "| 项目 | 内容 |\n"
        report += "|------|------|\n"
        report += f"| 原始需求 | {business_context.get('original_input', '未提供')} |\n"
        report += f"| 业务目标 | {business_context.get('business_goal', '未提供')} |\n"
        report += f"| 时间范围 | {business_context.get('time_range', '未提供')} |\n"
        report += f"| 产品周期 | {business_context.get('product_cycle', '未提供')} |\n"
        report += f"| 分析类型 | {business_context.get('analysis_type', '未提供')} |\n"
        report += f"| 业务领域 | {business_context.get('business_domain', '未提供')} |\n\n"
    
    # 2. 指标体系
    if 'metric_tree' in workflow_output:
        metric_tree = workflow_output['metric_tree']
        report += "## 📊 指标体系\n"
        report += "-" * 60 + "\n"
        
        # OSM框架
        if 'osm' in metric_tree:
            osm = metric_tree['osm']
            report += f"**目标**: {osm.get('objective', '未提供')}\n\n"
            
            report += "**策略与度量**:\n"
            report += "| 策略 | 度量指标 |\n"
            report += "|------|----------|\n"
            for strategy in osm.get('strategies', []):
                report += f"| {strategy.get('strategy', '未提供')} | {', '.join(strategy.get('metrics', []))} |\n"
        
        # 核心指标
        if 'core_metrics' in metric_tree:
            report += "\n**核心指标**:\n"
            report += "| 核心指标 |\n"
            report += "|----------|\n"
            for metric in metric_tree['core_metrics']:
                report += f"| {metric} |\n"
        
        # 分析角度
        if 'analysis_angles' in metric_tree:
            report += "\n**分析角度**:\n"
            report += "| 分析角度 |\n"
            report += "|----------|\n"
            for angle in metric_tree['analysis_angles']:
                report += f"| {angle} |\n"
        report += "\n"
    
    # 3. 数据质量
    if 'data_results' in workflow_output:
        data_results = workflow_output['data_results']
        report += "## 📋 数据质量\n"
        report += "-" * 60 + "\n"
        report += "**数据获取完成**\n\n"
        
        # 数据质量表格
        if 'qa_result' in data_results:
            qa_result = data_results['qa_result']
            report += "| 数据质量指标 | 结果 |\n"
            report += "|--------------|------|\n"
            report += f"| 数据质量评分 | {qa_result.get('data_quality_score', '未提供')}/100 |\n"
            report += f"| 行数 | {qa_result.get('basic_info', {}).get('rows', '未提供')} |\n"
            report += f"| 列数 | {qa_result.get('basic_info', {}).get('columns', '未提供')} |\n"
            report += f"| 缺失值 | {qa_result.get('missing_values', {}).get('total_missing', '未提供')} |\n"
            report += f"| 异常值 | {qa_result.get('anomalies', {}).get('total_anomalies', '未提供')} |\n"
        report += "\n"
    
    # 4. 深度分析
    if 'insights' in workflow_output:
        insights = workflow_output['insights']
        report += "## 🔍 深度分析\n"
        report += "-" * 60 + "\n"
        if insights:
            report += "| 序号 | 分析洞察 |\n"
            report += "|------|----------|\n"
            for i, insight in enumerate(insights, 1):
                report += f"| {i} | {insight} |\n"
        else:
            report += "- 暂无分析洞察\n"
        report += "\n"
    
    # 5. 业务决策
    if 'action_plan' in workflow_output:
        action_plan = workflow_output['action_plan']
        report += "## 🎯 业务决策\n"
        report += "-" * 60 + "\n"
        
        # 建议
        if 'suggestions' in action_plan:
            suggestions = action_plan['suggestions']
            report += "**可执行建议**:\n"
            if suggestions:
                report += "| 序号 | 建议内容 |\n"
                report += "|------|----------|\n"
                for i, suggestion in enumerate(suggestions, 1):
                    report += f"| {i} | {suggestion} |\n"
            else:
                report += "- 暂无建议\n"
        
        # ROI分析
        if 'roi_estimation' in action_plan:
            roi_estimation = action_plan['roi_estimation']
            report += "\n**ROI估算**:\n"
            report += "| 建议 | ROI |\n"
            report += "|------|-----|\n"
            for key, value in roi_estimation.items():
                report += f"| {key} | {value} |\n"
        
        # 优先级排序
        if 'priority' in action_plan:
            priority = action_plan['priority']
            report += "\n**优先级排序**:\n"
            report += "| 优先级 | 建议内容 |\n"
            report += "|--------|----------|\n"
            for i, item in enumerate(priority, 1):
                report += f"| {i} | {item} |\n"
        report += "\n"
    
    # 6. 数据可视化
    if 'visualizations' in workflow_output and workflow_output['visualizations']:
        visualizations = workflow_output['visualizations']
        report += "## 📊 数据可视化\n"
        report += "-" * 60 + "\n"
        
        report += "**生成的图表**:\n"
        report += "| 序号 | 图表类型 | 图表标题 |\n"
        report += "|------|----------|----------|\n"
        for i, viz in enumerate(visualizations, 1):
            report += f"| {i} | {viz.get('type', '未知')} | {viz.get('title', '未命名')} |\n"
        
        report += "\n**图表说明**:\n"
        report += "- 柱状图：适合比较不同类别的数据\n"
        report += "- 折线图：适合展示时间趋势数据\n"
        report += "- 饼图：适合展示占比数据\n"
        report += "- 漏斗图：适合展示转化漏斗数据\n"
        report += "- 散点图：适合展示变量之间的关系\n\n"
    
    # 7. 效果追踪
    if 'tracking_config' in workflow_output:
        tracking_config = workflow_output['tracking_config']
        report += "## 📈 效果追踪\n"
        report += "-" * 60 + "\n"
        
        # 追踪指标
        if 'metrics' in tracking_config:
            metrics = tracking_config['metrics']
            report += "**追踪指标**:\n"
            report += "| 指标名称 | 目标值 | 单位 |\n"
            report += "|----------|--------|------|\n"
            for metric in metrics:
                report += f"| {metric.get('display_name', '未提供')} | {metric.get('target', 0)} | {metric.get('unit', '')} |\n"
        
        # 预警规则
        if 'alert_rules' in tracking_config:
            alert_rules = tracking_config['alert_rules']
            report += "\n**预警规则**:\n"
            report += "| 指标 | 预警信息 | 严重程度 |\n"
            report += "|------|----------|----------|\n"
            for rule in alert_rules[:3]:  # 只显示前3个规则
                report += f"| {rule.get('metric', '未提供')} | {rule.get('message', '未提供')} | {rule.get('severity', '未提供')} |\n"
        report += "\n"
    
    # 7. 总结
    report += "## 📝 总结\n"
    report += "-" * 60 + "\n"
    report += "**报告摘要**\n"
    report += "- 本次分析基于企业级标准操作流程(SOP)完成\n"
    report += "- 涵盖了需求诊断、数据获取、深度分析、业务决策和效果追踪五个阶段\n"
    report += "- 提供了基于数据的可执行建议和ROI估算\n"
    report += "- 建立了完整的效果追踪机制，确保策略执行效果\n\n"
    
    report += "**下一步建议**\n"
    report += "| 序号 | 建议 |\n"
    report += "|------|------|\n"
    report += "| 1 | 优先实施高ROI的建议 |\n"
    report += "| 2 | 建立定期分析机制，持续优化策略 |\n"
    report += "| 3 | 基于效果追踪结果，及时调整策略 |\n"
    report += "| 4 | 深入分析关键问题，挖掘更多业务机会 |\n"
    
    return report

def generate_combined_report(monthly_active_users: int = None) -> str:
    """
    生成综合分析报告
    
    Args:
        monthly_active_users: 月活跃用户数，如果不提供则从数据中计算
    
    Returns:
        str: 综合分析报告
    """
    report = f"# 电商数据分析综合报告\n\n"
    report += f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 1. 转化漏斗分析
    report += "## 1. 转化漏斗分析\n\n"
    report += generate_funnel_report() + "\n\n"
    
    # 2. A/B测试分析
    report += "## 2. A/B测试分析\n\n"
    report += generate_ab_test_report(monthly_active_users) + "\n\n"
    
    # 3. RFM用户分层分析
    report += "## 3. RFM用户分层分析\n\n"
    report += generate_rfm_report() + "\n\n"
    
    # 4. 总结与建议
    report += "## 4. 总结与建议\n\n"
    report += "### 关键发现\n"
    report += "- 识别转化漏斗中的关键瓶颈\n"
    report += "- 评估A/B测试的效果和ROI\n"
    report += "- 了解用户分层结构和价值分布\n\n"
    
    report += "### 行动建议\n"
    report += "| 序号 | 建议 |\n"
    report += "|------|------|\n"
    report += "| 1 | **优化转化路径**: 针对漏斗瓶颈进行优化 |\n"
    report += "| 2 | **数据驱动决策**: 基于A/B测试结果调整策略 |\n"
    report += "| 3 | **精细化运营**: 根据RFM分层实施差异化运营策略 |\n"
    report += "| 4 | **持续监测**: 建立数据监测机制，及时发现问题 |\n"
    report += "| 5 | **迭代优化**: 持续进行小范围测试和优化 |\n"
    
    return report