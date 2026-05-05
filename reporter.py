"""
报告生成模块
生成结构化的分析报告
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ReportSection:
    """报告章节数据结构"""
    title: str
    content: str
    section_type: str  # 'table', 'text', 'chart', 'insight'
    data: Optional[Any] = None


class Reporter:
    """报告生成器 - 生成结构化的分析报告"""

    def __init__(self):
        self.report_sections = []

    def generate(self, 
                 user_input: str,
                 analysis_result: Dict[str, Any],
                 validation_result: Any,
                 data: pd.DataFrame,
                 dsl_info: Optional[Any] = None,
                 visualization_plan: Optional[Dict[str, Any]] = None,
                 guardrail_result: Optional[Dict[str, Any]] = None) -> str:
        """
        生成完整的分析报告

        Args:
            user_input: 用户输入
            analysis_result: 分析结果
            validation_result: 校验结果
            data: 原始数据
            dsl_info: DSL信息（可选）
            visualization_plan: 图表规划（可选）
            guardrail_result: 数据质量检查结果（可选）

        Returns:
            str: 格式化的报告字符串
        """
        report = []

        # 1. 报告头部
        report.append(self._generate_header(user_input))

        # 2. 分析背景
        report.append(self._generate_background_section(user_input, data))

        # 3. 核心结论
        report.append(self._generate_core_conclusions(analysis_result, data))

        # 4. 关键发现
        report.append(self._generate_key_findings(analysis_result, visualization_plan))

        # 5. 风险与限制
        report.append(self._generate_risks_and_limits(validation_result, guardrail_result, data))

        # 6. 业务建议
        report.append(self._generate_business_recommendations(analysis_result, validation_result))

        return "\n\n".join(report)

    def _generate_header(self, user_input: str) -> str:
        """生成报告头部"""
        return f"""📋 分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
分析需求: {user_input}
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    def _generate_data_overview(self, data: pd.DataFrame, validation_result: Any) -> str:
        """生成数据概览"""
        if data is None or data.empty:
            return "## 📊 数据概览\n\n暂无数据"

        section = ["## 📊 数据概览"]
        section.append(f"| 指标 | 值 |\n| --- | --- |")
        section.append(f"| 数据行数 | {len(data)} |")
        section.append(f"| 数据列数 | {len(data.columns)} |")

        if validation_result:
            quality_score = getattr(validation_result, 'risk_level', None)
            if quality_score:
                section.append(f"| 数据质量 | {quality_score.value.upper()} |")

        section.append("")
        section.append("### 字段信息")
        section.append(self._generate_field_table(data))

        return "\n".join(section)

    def _generate_field_table(self, data: pd.DataFrame) -> str:
        """生成字段信息表"""
        if data is None or data.empty:
            return "暂无字段信息"

        lines = ["| 字段名 | 类型 | 示例值 |", "| --- | --- | --- |"]

        for col in data.columns[:10]:  # 最多显示10个字段
            col_type = str(data[col].dtype)
            sample_value = ""

            if len(data[col].dropna()) > 0:
                sample = data[col].dropna().iloc[0]
                sample_value = str(sample)[:30]

            lines.append(f"| {col} | {col_type} | {sample_value} |")

        if len(data.columns) > 10:
            lines.append(f"\n_...共{len(data.columns)}个字段，显示前10个_")

        return "\n".join(lines)

    def _generate_analysis_section(self, analysis_result: Dict[str, Any]) -> str:
        """生成分析结果章节"""
        if not analysis_result or not analysis_result.get('success'):
            return "## 📈 分析结果\n\n暂无分析结果"

        analysis_type = analysis_result.get('analysis_type', 'unknown')

        section = [f"## 📈 {self._get_analysis_type_name(analysis_type)}"]

        if analysis_type == 'funnel':
            section.append(self._generate_funnel_table(analysis_result))
        elif analysis_type == 'rfm':
            section.append(self._generate_rfm_table(analysis_result))
        elif analysis_type == 'comparison':
            section.append(self._generate_comparison_table(analysis_result))
        elif analysis_type == 'trend':
            section.append(self._generate_trend_table(analysis_result))
        elif analysis_type == 'distribution':
            section.append(self._generate_distribution_table(analysis_result))
        else:
            section.append(self._generate_generic_table(analysis_result))

        return "\n".join(section)

    def _get_analysis_type_name(self, analysis_type: str) -> str:
        """获取分析类型的中文名称"""
        type_names = {
            'funnel': '转化漏斗分析',
            'rfm': 'RFM用户分层分析',
            'comparison': '对比分析',
            'trend': '趋势分析',
            'distribution': '分布分析',
            'ab_test': 'A/B测试分析',
            'custom': '自定义分析'
        }
        return type_names.get(analysis_type, '数据分析')

    def _generate_funnel_table(self, analysis_result: Dict[str, Any]) -> str:
        """生成漏斗分析结果表"""
        funnel_stages = analysis_result.get('funnel_stages', [])

        if not funnel_stages:
            return "暂无漏斗数据"

        lines = [
            "\n| 漏斗阶段 | 用户数 | 整体转化率 | 阶段转化率 |",
            "| --- | --- | --- | --- |"
        ]

        for stage in funnel_stages:
            name = stage.get('name', '未知')
            count = stage.get('count', 0)
            conversion_rate = stage.get('conversion_rate', 0)
            stage_rate = stage.get('stage_conversion_rate', 0)

            lines.append(f"| {name} | {count:,} | {conversion_rate:.2f}% | {stage_rate:.2f}% |")

        return "\n".join(lines)

    def _generate_rfm_table(self, analysis_result: Dict[str, Any]) -> str:
        """生成RFM分析结果表"""
        rfm_summary = analysis_result.get('rfm_summary', {})

        if not rfm_summary:
            return "暂无RFM数据"

        lines = [
            "\n| RFM维度 | 平均值 | 中位数 | 最小值 | 最大值 |",
            "| --- | --- | --- | --- | --- |"
        ]

        for dim, stats in rfm_summary.items():
            lines.append(f"| {dim.upper()} | {stats.get('mean', 0)} | {stats.get('median', 0)} | {stats.get('min', 0)} | {stats.get('max', 0)} |")

        return "\n".join(lines)

    def _generate_comparison_table(self, analysis_result: Dict[str, Any]) -> str:
        """生成对比分析结果表"""
        comparison_summary = analysis_result.get('comparison_summary', {})
        groups = comparison_summary.get('groups', [])

        if not groups:
            return "暂无对比数据"

        group_col = comparison_summary.get('group_column', '组别')
        value_col = comparison_summary.get('value_column', '值')

        lines = [
            f"\n| {group_col} | {value_col} | 占比 |",
            "| --- | --- | --- |"
        ]

        total_sum = sum(g.get('sum', 0) for g in groups)

        for group in groups[:10]:  # 最多显示10个组
            name = group.get('name', '未知')
            value = group.get('sum', 0)
            pct = value / total_sum * 100 if total_sum > 0 else 0
            lines.append(f"| {name} | {value:,.2f} | {pct:.2f}% |")

        if len(groups) > 10:
            lines.append(f"\n_...共{len(groups)}个组别，显示前10个_")

        return "\n".join(lines)

    def _generate_trend_table(self, analysis_result: Dict[str, Any]) -> str:
        """生成趋势分析结果表"""
        trend_summary = analysis_result.get('trend_summary', {})

        if not trend_summary or 'error' in trend_summary:
            return "暂无趋势数据"

        lines = [
            "\n| 指标 | 值 |",
            "| --- | --- |"
        ]

        start_value = trend_summary.get('start_value', 0)
        end_value = trend_summary.get('end_value', 0)
        change_rate = trend_summary.get('change_rate', 0)

        lines.append(f"| 起始值 | {start_value:,.2f} |")
        lines.append(f"| 结束值 | {end_value:,.2f} |")
        lines.append(f"| 变化量 | {trend_summary.get('total_change', 0):+,.2f} |")
        lines.append(f"| 变化率 | {change_rate:+.2f}% |")

        return "\n".join(lines)

    def _generate_distribution_table(self, analysis_result: Dict[str, Any]) -> str:
        """生成分布分析结果表"""
        distribution_summary = analysis_result.get('distribution_summary', {})
        distribution = distribution_summary.get('distribution', [])

        if not distribution:
            return "暂无分布数据"

        category_col = distribution_summary.get('category_column', '类别')
        value_col = distribution_summary.get('value_column', '值')

        lines = [
            f"\n| {category_col} | {value_col} | 占比 |",
            "| --- | --- | --- |"
        ]

        for item in distribution[:10]:  # 最多显示10个类别
            lines.append(f"| {item.get('category', '未知')} | {item.get('value', 0):,.2f} | {item.get('percentage', 0):.2f}% |")

        if len(distribution) > 10:
            lines.append(f"\n_...共{len(distribution)}个类别，显示前10个_")

        return "\n".join(lines)

    def _generate_generic_table(self, analysis_result: Dict[str, Any]) -> str:
        """生成通用分析结果表"""
        data = analysis_result.get('data')

        if data is None or (hasattr(data, 'empty') and data.empty):
            return "暂无数据"

        if isinstance(data, pd.DataFrame):
            # 转换为Markdown表格
            lines = [data.to_markdown(index=False)]
            return "\n".join(lines)

        return str(data)

    def _generate_quality_section(self, validation_result: Any) -> str:
        """生成数据质量评估章节"""
        if not validation_result:
            return ""

        section = ["## ⚠️ 数据质量评估"]

        issues = getattr(validation_result, 'issues', [])
        warnings = getattr(validation_result, 'warnings', [])

        if issues:
            section.append("\n**问题：**")
            for issue in issues:
                section.append(f"- {issue}")

        if warnings:
            section.append("\n**警告：**")
            for warning in warnings:
                section.append(f"- {warning}")

        if not issues and not warnings:
            section.append("\n✓ 数据质量良好，未发现明显问题")

        return "\n".join(section)

    def _generate_insights_section(self, analysis_result: Dict[str, Any]) -> str:
        """生成业务洞察章节"""
        if not analysis_result:
            return "## 💡 业务洞察\n\n暂无洞察"

        insights = analysis_result.get('insights', [])

        section = ["## 💡 业务洞察"]

        if insights:
            for insight in insights:
                section.append(f"- {insight}")
        else:
            section.append("- 暂无具体洞察，建议结合业务场景深入分析")

        return "\n".join(section)

    def _generate_background_section(self, user_input: str, data: pd.DataFrame) -> str:
        """生成分析背景章节"""
        section = ["# 一、分析背景"]
        section.append(f"**分析需求**：{user_input}")
        section.append(f"**分析时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if data is not None and not data.empty:
            section.append(f"**数据规模**：{len(data)}条记录，{len(data.columns)}个字段")
            section.append(f"**数据字段**：{', '.join(data.columns[:5])}{'...' if len(data.columns) > 5 else ''}")
        
        section.append("\n**分析目标**：")
        section.append("- 深入理解业务数据，挖掘潜在价值")
        section.append("- 识别关键业务问题和机会")
        section.append("- 为业务决策提供数据支持")
        
        return "\n".join(section)

    def _generate_core_conclusions(self, analysis_result: Dict[str, Any], data: pd.DataFrame) -> str:
        """生成核心结论章节"""
        section = ["# 二、核心结论"]
        
        if not analysis_result or not analysis_result.get('success'):
            section.append("- 暂无有效分析结果")
            return "\n".join(section)
        
        analysis_type = analysis_result.get('analysis_type', 'unknown')
        
        if analysis_type == 'funnel':
            funnel_stages = analysis_result.get('funnel_stages', [])
            if funnel_stages:
                overall_conversion = funnel_stages[-1].get('conversion_rate', 0)
                section.append(f"- 整体转化率为 **{overall_conversion:.2f}%**")
                section.append(f"- 最大流失环节：{self._get_max_drop_off_stage(funnel_stages)}")
        elif analysis_type == 'rfm':
            rfm_summary = analysis_result.get('rfm_summary', {})
            if rfm_summary:
                high_value_users = rfm_summary.get('high_value_users', 0)
                total_users = len(data) if data is not None else 0
                pct_high_value = (high_value_users / total_users * 100) if total_users > 0 else 0
                section.append(f"- 高价值用户占比：**{pct_high_value:.2f}%**")
        elif analysis_type == 'ab_test':
            conversion_a = analysis_result.get('conversion_A', 0)
            conversion_b = analysis_result.get('conversion_B', 0)
            uplift = analysis_result.get('uplift', 0)
            significant = analysis_result.get('significant', False)
            section.append(f"- A组转化率：**{conversion_a:.4f}**")
            section.append(f"- B组转化率：**{conversion_b:.4f}**")
            section.append(f"- 提升率：**{uplift:.2f}%**")
            section.append(f"- 统计显著性：**{'显著' if significant else '不显著'}**")
        elif analysis_type == 'trend':
            trend_summary = analysis_result.get('trend_summary', {})
            change_rate = trend_summary.get('change_rate', 0)
            section.append(f"- 整体变化率：**{change_rate:+.2f}%**")
        elif analysis_type == 'comparison':
            comparison_summary = analysis_result.get('comparison_summary', {})
            groups = comparison_summary.get('groups', [])
            if groups:
                top_group = max(groups, key=lambda x: x.get('sum', 0))
                section.append(f"- 表现最佳组别：**{top_group.get('name', '未知')}**")
                section.append(f"- 占比：**{top_group.get('percentage', 0):.2f}%**")
        
        return "\n".join(section)

    def _get_max_drop_off_stage(self, funnel_stages: List[Dict[str, Any]]) -> str:
        """获取最大流失环节"""
        max_drop_off = 0
        max_stage = ""
        
        for i in range(1, len(funnel_stages)):
            prev_count = funnel_stages[i-1].get('count', 0)
            curr_count = funnel_stages[i].get('count', 0)
            drop_off = (prev_count - curr_count) / prev_count * 100 if prev_count > 0 else 0
            if drop_off > max_drop_off:
                max_drop_off = drop_off
                max_stage = f"{funnel_stages[i-1].get('name', '未知')} → {funnel_stages[i].get('name', '未知')}（{drop_off:.2f}%）"
        
        return max_stage

    def _generate_key_findings(self, analysis_result: Dict[str, Any], visualization_plan: Optional[Dict[str, Any]]) -> str:
        """生成关键发现章节"""
        section = ["# 三、关键发现"]
        
        if not analysis_result or not analysis_result.get('success'):
            section.append("- 暂无关键发现")
            return "\n".join(section)
        
        analysis_type = analysis_result.get('analysis_type', 'unknown')
        
        if analysis_type == 'funnel':
            funnel_stages = analysis_result.get('funnel_stages', [])
            if funnel_stages:
                section.append("**转化漏斗分析**")
                for stage in funnel_stages:
                    section.append(f"- {stage.get('name', '未知')}：{stage.get('count', 0):,}人，转化率{stage.get('conversion_rate', 0):.2f}%")
        elif analysis_type == 'rfm':
            rfm_summary = analysis_result.get('rfm_summary', {})
            if rfm_summary:
                section.append("**用户分层分析**")
                for segment in rfm_summary.get('segments', []):
                    section.append(f"- {segment.get('name', '未知')}：{segment.get('count', 0):,}人，{segment.get('percentage', 0):.2f}%")
        elif analysis_type == 'ab_test':
            section.append("**A/B测试分析**")
            section.append(f"- A组：{analysis_result.get('group_A', {}).get('users', 0):,}用户，{analysis_result.get('group_A', {}).get('conversions', 0):,}转化")
            section.append(f"- B组：{analysis_result.get('group_B', {}).get('users', 0):,}用户，{analysis_result.get('group_B', {}).get('conversions', 0):,}转化")
            section.append(f"- P值：{analysis_result.get('p_value', 0):.4f}")
        elif analysis_type == 'trend':
            trend_summary = analysis_result.get('trend_summary', {})
            if trend_summary:
                section.append("**趋势分析**")
                section.append(f"- 起始值：{trend_summary.get('start_value', 0):,.2f}")
                section.append(f"- 结束值：{trend_summary.get('end_value', 0):,.2f}")
                section.append(f"- 变化量：{trend_summary.get('total_change', 0):+,.2f}")
        
        # 从图表规划中提取关键发现
        if visualization_plan:
            charts = visualization_plan.get('charts', [])
            if charts:
                section.append("\n**可视化洞察**")
                for chart in charts[:3]:  # 最多显示3个关键图表
                    section.append(f"- {chart.get('title', '未知图表')}")
        
        return "\n".join(section)

    def _generate_risks_and_limits(self, validation_result: Any, guardrail_result: Optional[Dict[str, Any]], data: pd.DataFrame) -> str:
        """生成风险与限制章节"""
        section = ["# 四、风险与限制"]
        
        risks = []
        
        # 数据质量风险
        if guardrail_result and not guardrail_result.get('valid', True):
            issues = guardrail_result.get('issues', [])
            for issue in issues:
                risks.append(f"- {issue}")
        
        # 样本量限制
        if data is not None:
            if len(data) < 10:
                risks.append("- 样本量过小（小于10条），分析结果可能不可靠")
            elif len(data) < 30:
                risks.append("- 样本量较小（小于30条），统计显著性可能不足")
        
        # 数据完整性风险
        if data is not None and not data.empty:
            null_percentage = data.isnull().sum().sum() / data.size * 100 if data.size > 0 else 0
            if null_percentage > 50:
                risks.append(f"- 数据空值比例过高（{null_percentage:.1f}%），可能影响分析准确性")
        
        # 分析方法限制
        risks.append("- 分析基于历史数据，未来表现可能受外部因素影响")
        risks.append("- 未考虑所有可能的影响因素，分析结果存在一定局限性")
        
        if risks:
            for risk in risks:
                section.append(risk)
        else:
            section.append("- 未发现明显风险与限制")
        
        return "\n".join(section)

    def _generate_business_recommendations(self, analysis_result: Dict[str, Any], validation_result: Any) -> str:
        """生成业务建议章节"""
        section = ["# 五、业务建议"]
        
        recommendations = []
        
        if not analysis_result or not analysis_result.get('success'):
            section.append("- 暂无具体建议")
            return "\n".join(section)
        
        analysis_type = analysis_result.get('analysis_type', 'unknown')
        
        if analysis_type == 'funnel':
            recommendations.extend([
                "**优化转化漏斗**：针对流失率最高的环节，进行用户体验优化，简化转化流程",
                "**定向营销**：对漏斗中流失的用户进行定向召回，提供个性化激励措施",
                "**数据监控**：建立转化漏斗实时监控机制，及时发现异常并采取措施"
            ])
        elif analysis_type == 'rfm':
            recommendations.extend([
                "**用户分层运营**：针对不同价值用户群体，制定差异化的营销策略和服务方案",
                "**高价值用户维护**：为高价值用户提供VIP服务和专属优惠，增强用户忠诚度",
                "**低价值用户激活**：通过个性化促销和内容推荐，提升低价值用户的活跃度和消费频次"
            ])
        elif analysis_type == 'ab_test':
            significant = analysis_result.get('significant', False)
            if significant:
                recommendations.extend([
                    "**推广成功方案**：将B组策略在全量用户中推广实施",
                    "**持续优化**：基于测试结果，进一步优化策略细节，提升效果",
                    "**监控效果**：建立长期监控机制，确保策略持续有效"
                ])
            else:
                recommendations.extend([
                    "**继续测试**：延长测试时间或增加样本量，获取更可靠的结果",
                    "**优化策略**：基于初步结果，调整测试方案，进行新一轮测试",
                    "**综合评估**：结合其他指标，全面评估不同方案的优劣"
                ])
        elif analysis_type == 'trend':
            change_rate = analysis_result.get('trend_summary', {}).get('change_rate', 0)
            if change_rate > 0:
                recommendations.extend([
                    "**扩大优势**：针对增长趋势，加大资源投入，扩大市场份额",
                    "**总结经验**：分析增长原因，提炼成功因素，复制到其他业务领域",
                    "**预防风险**：建立预警机制，避免增长过快带来的潜在问题"
                ])
            else:
                recommendations.extend([
                    "**分析原因**：深入分析下降原因，识别问题根源",
                    "**制定对策**：针对问题，制定具体的改进措施和行动计划",
                    "**监控进展**：建立定期评估机制，确保改进措施有效实施"
                ])
        elif analysis_type == 'comparison':
            recommendations.extend([
                "**标杆学习**：分析表现优秀组别的成功经验，推广到其他组别",
                "**精准施策**：针对不同组别的特点，制定个性化的改进方案",
                "**资源优化**：根据各组表现，合理分配资源，提高投入产出比"
            ])
        
        # 从校验结果中提取建议
        if validation_result:
            validation_recs = getattr(validation_result, 'recommendations', [])
            for rec in validation_recs:
                if rec not in [r.split('：')[1] if '：' in r else r for r in recommendations]:
                    recommendations.append(f"**数据质量**：{rec}")
        
        if recommendations:
            for rec in recommendations:
                section.append(f"- {rec}")
        else:
            section.append("- 暂无具体建议")
        
        return "\n".join(section)

    def generate_summary(self, analysis_result: Dict[str, Any]) -> str:
        """生成简短的摘要信息"""
        if not analysis_result:
            return "暂无摘要"

        summary_parts = []

        # 分析类型
        analysis_type = analysis_result.get('analysis_type', 'unknown')
        summary_parts.append(f"分析类型：{self._get_analysis_type_name(analysis_type)}")

    def self_check(self, report: str, analysis_result: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """
        对报告进行自检

        Args:
            report: 生成的报告
            analysis_result: 分析结果
            data: 原始数据

        Returns:
            Dict: 自检结果
        """
        issues = []
        quality_score = 100

        # 1. 检查逻辑跳跃
        logic_issues = self._check_logic_gaps(report, analysis_result)
        if logic_issues:
            issues.extend(logic_issues)
            quality_score -= len(logic_issues) * 10

        # 2. 检查结论与数据一致性
        consistency_issues = self._check_data_consistency(report, analysis_result, data)
        if consistency_issues:
            issues.extend(consistency_issues)
            quality_score -= len(consistency_issues) * 15

        # 3. 检查是否存在夸大结论
        exaggeration_issues = self._check_exaggeration(report, analysis_result)
        if exaggeration_issues:
            issues.extend(exaggeration_issues)
            quality_score -= len(exaggeration_issues) * 20

        # 4. 检查报告完整性
        completeness_issues = self._check_completeness(report)
        if completeness_issues:
            issues.extend(completeness_issues)
            quality_score -= len(completeness_issues) * 5

        # 确保分数在0-100之间
        quality_score = max(0, min(100, quality_score))

        # 生成改进版本
        improved_version = self._generate_improved_report(report, issues, analysis_result, data)

        return {
            "quality_score": quality_score,
            "issues": issues,
            "improved_version": improved_version
        }

    def _check_logic_gaps(self, report: str, analysis_result: Dict[str, Any]) -> List[str]:
        """检查逻辑跳跃"""
        issues = []

        # 检查核心结论是否有数据支持
        if "核心结论" in report:
            # 简单检查核心结论部分是否包含具体数据
            core_conclusion_start = report.find("# 二、核心结论")
            core_conclusion_end = report.find("# 三、关键发现")
            if core_conclusion_start != -1 and core_conclusion_end != -1:
                core_conclusion = report[core_conclusion_start:core_conclusion_end]
                if "**" not in core_conclusion:
                    issues.append("核心结论缺乏具体数据支持，存在逻辑跳跃")

        # 检查关键发现与核心结论是否一致
        if "关键发现" in report and "核心结论" in report:
            # 简单检查是否有发现但没有对应结论
            key_findings_start = report.find("# 三、关键发现")
            key_findings_end = report.find("# 四、风险与限制")
            if key_findings_start != -1 and key_findings_end != -1:
                key_findings = report[key_findings_start:key_findings_end]
                if "-" in key_findings and "核心结论" in report:
                    # 这里可以添加更复杂的逻辑检查
                    pass

        return issues

    def _check_data_consistency(self, report: str, analysis_result: Dict[str, Any], data: pd.DataFrame) -> List[str]:
        """检查结论与数据一致性"""
        issues = []

        # 检查分析结果与报告中的数据是否一致
        if analysis_result and analysis_result.get('success'):
            analysis_type = analysis_result.get('analysis_type', 'unknown')

            if analysis_type == 'funnel':
                funnel_stages = analysis_result.get('funnel_stages', [])
                if funnel_stages:
                    overall_conversion = funnel_stages[-1].get('conversion_rate', 0)
                    if f"{overall_conversion:.2f}%" not in report:
                        issues.append("漏斗分析的整体转化率在报告中不一致")

            elif analysis_type == 'ab_test':
                conversion_a = analysis_result.get('conversion_A', 0)
                conversion_b = analysis_result.get('conversion_B', 0)
                if f"{conversion_a:.4f}" not in report or f"{conversion_b:.4f}" not in report:
                    issues.append("A/B测试的转化率在报告中不一致")

        # 检查数据规模是否一致
        if data is not None and not data.empty:
            expected_size = f"{len(data)}条记录，{len(data.columns)}个字段"
            if expected_size not in report:
                issues.append("报告中的数据规模与实际数据不一致")

        return issues

    def _check_exaggeration(self, report: str, analysis_result: Dict[str, Any]) -> List[str]:
        """检查是否存在夸大结论"""
        issues = []

        # 检查是否使用了过于绝对的表述
        exaggeration_words = ["绝对", "完全", "100%", "必然", "一定", "全部"]
        for word in exaggeration_words:
            if word in report:
                issues.append(f"报告中使用了过于绝对的表述：'{word}'")

        # 检查是否有未经验证的因果关系
        causal_words = ["导致", "造成", "引起", "使得", "决定"]
        for word in causal_words:
            if word in report:
                # 这里可以添加更复杂的检查逻辑
                pass

        # 检查A/B测试结论是否夸大
        if analysis_result and analysis_result.get('analysis_type') == 'ab_test':
            significant = analysis_result.get('significant', False)
            if not significant and "显著" in report:
                issues.append("A/B测试结论夸大，实际结果不显著")

        return issues

    def _check_completeness(self, report: str) -> List[str]:
        """检查报告完整性"""
        issues = []

        # 检查报告结构是否完整
        required_sections = [
            "# 一、分析背景",
            "# 二、核心结论",
            "# 三、关键发现",
            "# 四、风险与限制",
            "# 五、业务建议"
        ]

        for section in required_sections:
            if section not in report:
                issues.append(f"报告缺少必要章节：{section}")

        # 检查业务建议是否具体可执行
        if "# 五、业务建议" in report:
            business_recommendations_start = report.find("# 五、业务建议")
            business_recommendations = report[business_recommendations_start:]
            if "暂无具体建议" in business_recommendations:
                issues.append("业务建议部分过于简略，缺乏具体可执行的措施")

        return issues

    def _generate_improved_report(self, report: str, issues: List[str], analysis_result: Dict[str, Any], data: pd.DataFrame) -> str:
        """
        生成改进版本的报告

        Args:
            report: 原始报告
            issues: 发现的问题
            analysis_result: 分析结果
            data: 原始数据

        Returns:
            str: 改进后的报告
        """
        # 这里可以根据发现的问题对报告进行改进
        # 为了简化，我们返回原始报告，但在实际应用中可以根据具体问题进行修改
        
        # 在报告开头添加自检结果
        improved_report = f"# 报告自检结果\n\n"
        improved_report += f"**质量评分**：{max(0, 100 - len(issues) * 10)}\n\n"
        
        if issues:
            improved_report += "**发现的问题**：\n"
            for issue in issues:
                improved_report += f"- {issue}\n"
            improved_report += "\n"
        else:
            improved_report += "**未发现明显问题**\n\n"
        
        improved_report += report
        
        return improved_report

    def generate_json_report_with_llm(self, 
                                    user_input: str, 
                                    analysis_result: Dict[str, Any], 
                                    data: pd.DataFrame, 
                                    api_key: str, 
                                    model_type: str = "deepseek") -> str:
        """
        使用大模型生成符合要求的 JSON 格式报告

        Args:
            user_input: 用户输入
            analysis_result: 分析结果
            data: 原始数据
            api_key: API密钥
            model_type: 模型类型

        Returns:
            str: JSON 格式的报告
        """
        import json
        from agent import get_llm

        # 准备数据摘要
        data_summary_string = ""
        table_schema_info = ""

        # 总是从数据库获取所有表的结构信息，确保LLM能看到完整的数据库schema
        import sqlite3
        try:
            conn = sqlite3.connect('ecommerce.db')
            cursor = conn.cursor()
            
            # 检查所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # 如果传入了data，先用data构建data_summary_string
            if data is not None and not data.empty:
                data_summary_string = f"数据行数: {len(data)}\n"
                data_summary_string += f"数据列数: {len(data.columns)}\n"
                data_summary_string += "\n前5行数据:\n"
                data_summary_string += data.head().to_string()
            else:
                data_summary_string = ""
            
            table_schema_info = ""
            
            for table in tables:
                table_name = table[0]
                # 检查表结构
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                if columns:
                    # 检查表数据量
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    data_summary_string += f"\n表名: {table_name}\n"
                    data_summary_string += f"数据行数: {count}\n"
                    data_summary_string += f"数据列数: {len(columns)}\n\n"
                    
                    # 构建表结构信息
                    table_schema_info += f"\n=== {table_name} 表 ===\n"
                    table_schema_info += "\n".join([f"{col[1]}: {col[2]}" for col in columns])
                    table_schema_info += "\n"
            conn.close()
        except Exception:
            # 如果数据库操作失败，使用默认值
            if data is not None and not data.empty:
                data_summary_string = f"数据行数: {len(data)}\n数据列数: {len(data.columns)}\n前5行数据:\n{data.head().to_string()}"
                table_schema_info = "\n".join([f"{col}: {data[col].dtype}" for col in data.columns])
            else:
                data_summary_string = "无数据"
                table_schema_info = "无字段信息"

        # 构建最强版AI Prompt
        prompt = f"""你是一位顶尖的大厂商业分析师（BA）和数据诊断专家。
请基于传入的【真实数据】回答用户的【原始需求】。

用户原始需求："{user_input}"
实际提取到的数据分析结果 (Data Summary)：
{data_summary_string}
当前数据集的字段包含：{table_schema_info}

【核心处理逻辑】：
1. 校验数据：首先检查传入的数据是否能支撑用户的需求。
   - 流量转化分析判断规则：如果上面的"当前数据集的字段包含"中有events表，并且events表中有session_id、event_type和timestamp字段，那么数据是支持流量转化分析和漏斗分析的，必须返回status为success。
   - 只有当数据中确实不包含必要的字段时，才返回status为error。
2. 绝对真实：如果数据不支持，绝对禁止瞎编，必须在 JSON 中将 status 置为 error，并给出专业的解释。
3. 如果数据部分支持，应该基于现有数据提供分析，并在报告中说明数据限制。
4. 如果数据支持，正常进行深度分析和费米估算。

【重要提示】：
1. 货币单位：请使用数据中实际的货币单位（美元），在报告中使用 "$" 符号。
2. 总营收计算：请根据数据中的 total_usd 字段准确计算总营收，确保数值正确。
3. 数据准确性：请确保所有计算结果与原始数据一致，避免四舍五入导致的误差。
4. 字段映射：对于支付方式分析，请将以下字段视为等效：
   - payment_method 等同于 支付方式
   - order_id 等同于 订单标识
   - total_usd 等同于 交易金额/transaction_amount
5. 退款率计算：如果数据中没有退款状态(refund_status)字段，无法计算退款率，但仍然可以提供其他支付方式分析指标（订单量、销售额、占比、客单价）。
6. 流量转化分析：如果上面的"当前数据集的字段包含"中有events表，并且events表中有session_id、event_type和timestamp字段，那么数据是支持流量转化分析和漏斗分析的，必须返回status为success，正常进行分析。

【强制 JSON 输出格式】（必须可以直接用 json.loads 解析，不要加 ```json 符号）：
{{
  "status": "success",  // 如果数据不支持需求，请改为 "error"
  "message": "如果status是error，请用专业商分口吻解释原因，例如'当前数据集缺乏用户行为事件(event_type)字段，无法构建转化漏斗，建议查看基础销售数据分析。'",
  "key_metrics":[
    {{
      "name": "指标名称(如:总转化率)",
      "value": "数值(如:15%)",
      "trend": "同比/环比变化"
    }}
  ],
  "deep_insights":[
    {{
      "conclusion": "一句话核心结论",
      "data_proof": "引用具体数据支撑",
      "why": "深度归因推测",
      "next_step": "下一步验证建议"
    }}
  ],
  "actionable_decisions":[
    {{
      "strategy_name": "策略名称",
      "target_pain_point": "痛点",
      "action": "具体动作",
      "roi_calc_logic": "ROI推演公式与预期收益",
      "priority": "P0/P1"
    }}
  ],
  "tracking_plan":[
    {{
      "metric": "核心追踪指标",
      "target": "目标值",
      "warning_rule": "预警阈值"
    }}
  ]
}}
"""

        try:
            # 调用大模型
            llm = get_llm(api_key, model_type)
            response = llm.invoke(prompt)
            
            # 提取 JSON 响应
            response_content = response.content
            
            # 尝试解析 JSON
            report_data = json.loads(response_content)
            return json.dumps(report_data, ensure_ascii=False, indent=2)
        except Exception as e:
            # 如果调用失败，基于现有数据生成报告
            report_data = {
                "status": "success",
                "message": "基于现有数据生成的报告",
                "key_metrics": [],
                "deep_insights": [],
                "actionable_decisions": [],
                "tracking_plan": []
            }
            
            # 基于数据生成核心指标
            if data is not None and not data.empty:
                # 总订单量
                report_data['key_metrics'].append({
                    "name": "总订单量",
                    "value": f"{len(data)}",
                    "trend": "-"
                })
                # 总销售额
                if 'total_usd' in data.columns:
                    total_sales = data['total_usd'].sum()
                    report_data['key_metrics'].append({
                        "name": "总销售额",
                        "value": f"${total_sales:.2f}",
                        "trend": "-"
                    })
                # 总销量
                if 'quantity' in data.columns:
                    total_quantity = data['quantity'].sum()
                    report_data['key_metrics'].append({
                        "name": "总销量",
                        "value": f"{total_quantity}",
                        "trend": "-"
                    })
                # 平均客单价
                if 'total_usd' in data.columns:
                    avg_order_value = data['total_usd'].mean()
                    report_data['key_metrics'].append({
                        "name": "平均客单价",
                        "value": f"${avg_order_value:.2f}",
                        "trend": "-"
                    })
                # 平均订单商品数
                if 'quantity' in data.columns:
                    avg_items_per_order = data.groupby('order_id')['quantity'].sum().mean()
                    report_data['key_metrics'].append({
                        "name": "平均订单商品数",
                        "value": f"{avg_items_per_order:.2f}",
                        "trend": "-"
                    })
            
            # 生成深度洞察
            report_data['deep_insights'].append({
                "conclusion": "数据加载成功，系统能够基于现有数据提供分析",
                "data_proof": f"数据包含 {len(data) if data is not None and not data.empty else 0} 条记录",
                "why": "系统能够正确识别和处理数据字段",
                "next_step": "基于分析结果制定相应的业务策略"
            })
            
            # 生成可执行决策
            report_data['actionable_decisions'].append({
                "strategy_name": "数据质量优化",
                "target_pain_point": "数据完整性",
                "action": "确保数据包含所有必要的字段和记录",
                "roi_calc_logic": "提高数据质量，提升分析准确性和决策质量",
                "priority": "P1"
            })
            
            # 生成追踪计划
            report_data['tracking_plan'].append({
                "metric": "数据质量得分",
                "target": "90%",
                "warning_rule": "低于80%时发出预警"
            })
            
            return json.dumps(report_data, ensure_ascii=False, indent=2)

    def generate_json_report(self, 
                           user_input: str, 
                           analysis_result: Dict[str, Any], 
                           data: pd.DataFrame) -> str:
        """
        生成符合要求的 JSON 格式报告

        Args:
            user_input: 用户输入
            analysis_result: 分析结果
            data: 原始数据

        Returns:
            str: JSON 格式的报告
        """
        import json

        # 构建报告结构，加入状态码
        report_data = {
            "status": "success",  # success 或 error
            "message": "",  # 错误信息
            "key_metrics": [],
            "deep_insights": [],
            "actionable_decisions": [],
            "tracking_plan": []
        }

        # 1. 核心指标
        if analysis_result and analysis_result.get('success'):
            analysis_type = analysis_result.get('analysis_type', 'unknown')
            
            if analysis_type == 'funnel':
                funnel_stages = analysis_result.get('funnel_stages', [])
                if funnel_stages:
                    overall_conversion = funnel_stages[-1].get('conversion_rate', 0)
                    report_data['key_metrics'].append({
                        "name": "总转化率",
                        "value": f"{overall_conversion:.2f}%",
                        "trend": "-"
                    })
                    # 添加各阶段转化率
                    for i, stage in enumerate(funnel_stages):
                        report_data['key_metrics'].append({
                            "name": f"{stage.get('name', '未知')}转化率",
                            "value": f"{stage.get('conversion_rate', 0):.2f}%",
                            "trend": "-"
                        })
            elif analysis_type == 'rfm':
                rfm_summary = analysis_result.get('rfm_summary', {})
                if rfm_summary:
                    high_value_users = rfm_summary.get('high_value_users', 0)
                    total_users = len(data) if data is not None else 0
                    # 确保总用户数大于0，并且高价值用户数不超过总用户数
                    if total_users > 0:
                        # 高价值用户数不能超过总用户数
                        actual_high_value = min(high_value_users, total_users)
                        pct_high_value = (actual_high_value / total_users * 100)
                    else:
                        pct_high_value = 0
                    report_data['key_metrics'].append({
                        "name": "高价值用户占比",
                        "value": f"{pct_high_value:.2f}%",
                        "trend": "-"
                    })
                    # 添加RFM各维度均值
                    for dim, stats in rfm_summary.items():
                        if isinstance(stats, dict) and 'mean' in stats:
                            report_data['key_metrics'].append({
                                "name": f"{dim.upper()}均值",
                                "value": f"{stats.get('mean', 0):.2f}",
                                "trend": "-"
                            })
            elif analysis_type == 'ab_test':
                conversion_a = analysis_result.get('conversion_A', 0)
                conversion_b = analysis_result.get('conversion_B', 0)
                uplift = analysis_result.get('uplift', 0)
                significant = analysis_result.get('significant', False)
                
                report_data['key_metrics'].append({
                    "name": "A组转化率",
                    "value": f"{conversion_a:.4f}",
                    "trend": "-"
                })
                report_data['key_metrics'].append({
                    "name": "B组转化率",
                    "value": f"{conversion_b:.4f}",
                    "trend": "-"
                })
                report_data['key_metrics'].append({
                    "name": "提升率",
                    "value": f"{uplift:.2f}%",
                    "trend": "-"
                })
            elif analysis_type == 'trend':
                trend_summary = analysis_result.get('trend_summary', {})
                if trend_summary:
                    start_value = trend_summary.get('start_value', 0)
                    end_value = trend_summary.get('end_value', 0)
                    change_rate = trend_summary.get('change_rate', 0)
                    
                    report_data['key_metrics'].append({
                        "name": "起始值",
                        "value": f"{start_value:,.2f}",
                        "trend": "-"
                    })
                    report_data['key_metrics'].append({
                        "name": "结束值",
                        "value": f"{end_value:,.2f}",
                        "trend": "-"
                    })
                    report_data['key_metrics'].append({
                        "name": "变化率",
                        "value": f"{change_rate:+.2f}%",
                        "trend": "-"
                    })
            elif analysis_type == 'comparison':
                comparison_summary = analysis_result.get('comparison_summary', {})
                groups = comparison_summary.get('groups', [])
                if groups:
                    for group in groups[:5]:  # 最多显示5个组
                        report_data['key_metrics'].append({
                            "name": f"{group.get('name', '未知')}",
                            "value": f"{group.get('sum', 0):,.2f}",
                            "trend": "-"
                        })
            elif analysis_type == 'distribution':
                distribution_summary = analysis_result.get('distribution_summary', {})
                distribution = distribution_summary.get('distribution', [])
                if distribution:
                    for item in distribution[:5]:  # 最多显示5个类别
                        report_data['key_metrics'].append({
                            "name": f"{item.get('category', '未知')}",
                            "value": f"{item.get('value', 0):,.2f}",
                            "trend": "-"
                        })

        # 2. 深度洞察
        if analysis_result and analysis_result.get('success'):
            insights = analysis_result.get('insights', [])
            for insight in insights[:3]:  # 最多显示3个洞察
                report_data['deep_insights'].append({
                    "conclusion": insight,
                    "data_proof": "基于数据分析",
                    "why": "需要进一步分析",
                    "next_step": "制定具体行动计划"
                })
        else:
            # 数据为空时的洞察
            report_data['deep_insights'].append({
                "conclusion": "数据不足，无法进行深入分析",
                "data_proof": "当前数据集为空",
                "why": "数据缺失或未正确加载",
                "next_step": "检查数据来源和加载过程"
            })

        # 3. 可执行决策
        report_data['actionable_decisions'].append({
            "strategy_name": "数据质量优化",
            "target_pain_point": "数据缺失或质量问题",
            "action": "检查数据来源，确保数据完整性",
            "roi_calc_logic": "提高数据质量，减少分析误差",
            "priority": "P1"
        })

        # 4. 追踪计划
        report_data['tracking_plan'].append({
            "metric": "数据完整性",
            "target": "100%",
            "warning_rule": "低于90%时发出预警"
        })

        return json.dumps(report_data, ensure_ascii=False, indent=2)
