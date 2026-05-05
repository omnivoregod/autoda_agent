"""
图表规划模块
根据分析结果决定绘制什么图表
"""

from typing import Dict, List, Any, Optional
import pandas as pd


class VisualizationPlanner:
    """图表规划器 - 决定绘制什么图表"""

    def __init__(self):
        """初始化图表规划器"""
        self.chart_templates = {
            'bar': {
                'type': 'bar',
                'description': '适合比较不同类别的数据'
            },
            'line': {
                'type': 'line',
                'description': '适合展示时间趋势数据'
            },
            'funnel': {
                'type': 'funnel',
                'description': '适合展示转化漏斗数据'
            },
            'pie': {
                'type': 'pie',
                'description': '适合展示占比数据'
            },
            'scatter': {
                'type': 'scatter',
                'description': '适合展示两个变量之间的关系'
            }
        }

    def plan(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        """
        规划图表

        Args:
            analysis_output: 分析结果
            data: 分析数据

        Returns:
            Dict: 图表规划结果
        """
        charts = []

        # 根据分析类型规划图表
        analysis_type = analysis_output.get('analysis_type', 'auto')

        if analysis_type == 'ab_test':
            charts.extend(self._plan_ab_test_charts(analysis_output, data))
        elif analysis_type == 'funnel':
            charts.extend(self._plan_funnel_charts(analysis_output, data))
        elif analysis_type == 'rfm':
            charts.extend(self._plan_rfm_charts(analysis_output, data))
        elif analysis_type == 'revenue_tree':
            charts.extend(self._plan_revenue_tree_charts(analysis_output, data))
        elif analysis_type == 'channel':
            charts.extend(self._plan_channel_charts(analysis_output, data))
        elif analysis_type == 'ltv_roi':
            charts.extend(self._plan_ltv_roi_charts(analysis_output, data))
        elif analysis_type == 'trend':
            charts.extend(self._plan_trend_charts(analysis_output, data))
        elif analysis_type == 'distribution':
            charts.extend(self._plan_distribution_charts(analysis_output, data))
        elif analysis_type == 'comparison':
            charts.extend(self._plan_comparison_charts(analysis_output, data))
        else:
            # 自动分析数据并规划图表
            charts.extend(self._plan_auto_charts(data))

        # 确保图表数量合理，只保留核心图表
        charts = self._filter_core_charts(charts)

        return {"charts": charts}

    def _plan_ab_test_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划A/B测试图表"""
        charts = []

        # 转化率对比柱状图
        charts.append({
            "type": "bar",
            "x": ["Group A", "Group B"],
            "y": [
                analysis_output.get("conversion_A", 0),
                analysis_output.get("conversion_B", 0)
            ],
            "title": "A/B测试转化率对比"
        })

        return charts

    def _plan_funnel_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划漏斗分析图表"""
        charts = []

        # 漏斗图
        if 'funnel_stages' in analysis_output:
            stages = analysis_output['funnel_stages']
            steps = [stage['name'] for stage in stages]
            counts = [stage['count'] for stage in stages]

            charts.append({
                "type": "funnel",
                "x": steps,
                "y": counts,
                "title": "转化漏斗分析"
            })

        return charts

    def _plan_rfm_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划RFM分析图表"""
        charts = []

        # 用户分群饼图
        if 'segments' in analysis_output:
            segments = analysis_output['segments']
            if data is not None and not data.empty:
                # 假设数据中有segment列
                if 'segment' in data.columns:
                    segment_counts = data['segment'].value_counts()
                    charts.append({
                        "type": "pie",
                        "x": segment_counts.index.tolist(),
                        "y": segment_counts.values.tolist(),
                        "title": "用户分群分布"
                    })

        return charts

    def _plan_revenue_tree_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划收入拆解图表"""
        charts = []

        # 收入贡献柱状图
        if 'revenue_breakdown' in analysis_output:
            breakdown = analysis_output['revenue_breakdown'].get('breakdown', [])
            if breakdown:
                categories = [item['category'] for item in breakdown]
                revenues = [item['revenue'] for item in breakdown]

                charts.append({
                    "type": "bar",
                    "x": categories,
                    "y": revenues,
                    "title": "收入贡献分析"
                })

        return charts

    def _plan_channel_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划渠道分析图表"""
        charts = []

        # 渠道表现柱状图
        if 'channel_performance' in analysis_output:
            performance = analysis_output['channel_performance']
            if performance:
                channels = [item['channel'] for item in performance]
                # 假设第一个指标是主要指标
                metric_name = list(performance[0].keys())[1] if len(performance[0]) > 1 else 'value'
                metrics = [item.get(metric_name, 0) for item in performance]

                charts.append({
                    "type": "bar",
                    "x": channels,
                    "y": metrics,
                    "title": f"渠道{metric_name}表现"
                })

        return charts

    def _plan_ltv_roi_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划LTV/ROI分析图表"""
        charts = []

        # LTV和ROI指标展示
        if 'metrics' in analysis_output:
            metrics = analysis_output['metrics']
            if metrics:
                # 简单的指标展示
                chart_data = []
                if 'average_ltv' in metrics:
                    chart_data.append({"name": "平均LTV", "value": metrics['average_ltv']})
                if 'roi' in metrics:
                    chart_data.append({"name": "ROI", "value": metrics['roi'] * 100})

                if chart_data:
                    charts.append({
                        "type": "bar",
                        "x": [item['name'] for item in chart_data],
                        "y": [item['value'] for item in chart_data],
                        "title": "LTV/ROI分析"
                    })

        return charts

    def _plan_trend_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划趋势分析图表"""
        charts = []

        # 趋势线图
        if 'trend_summary' in analysis_output:
            summary = analysis_output['trend_summary']
            if data is not None and not data.empty:
                # 假设数据中有时间列和值列
                time_col = summary.get('time_column')
                value_col = summary.get('value_column')
                if time_col and value_col and time_col in data.columns and value_col in data.columns:
                    charts.append({
                        "type": "line",
                        "x": data[time_col].tolist(),
                        "y": data[value_col].tolist(),
                        "title": "趋势分析"
                    })

        return charts

    def _plan_distribution_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划分布分析图表"""
        charts = []

        # 分布饼图或柱状图
        if 'distribution_summary' in analysis_output:
            summary = analysis_output['distribution_summary']
            distribution = summary.get('distribution', [])
            if distribution:
                categories = [item['category'] for item in distribution]
                values = [item['value'] for item in distribution]

                # 根据类别数量选择图表类型
                if len(categories) <= 7:
                    charts.append({
                        "type": "pie",
                        "x": categories,
                        "y": values,
                        "title": "分布分析"
                    })
                else:
                    charts.append({
                        "type": "bar",
                        "x": categories,
                        "y": values,
                        "title": "分布分析"
                    })

        return charts

    def _plan_comparison_charts(self, analysis_output: Dict[str, Any], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """规划比较分析图表"""
        charts = []

        # 比较柱状图
        if 'comparison_summary' in analysis_output:
            summary = analysis_output['comparison_summary']
            groups = summary.get('groups', [])
            if groups:
                group_names = [item['name'] for item in groups]
                # 假设使用sum作为比较指标
                values = [item['sum'] for item in groups]

                charts.append({
                    "type": "bar",
                    "x": group_names,
                    "y": values,
                    "title": "比较分析"
                })

        return charts

    def _plan_auto_charts(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """自动规划图表"""
        charts = []

        if data is None or data.empty:
            return charts

        # 分析数据特征
        numeric_cols = data.select_dtypes(include=['number']).columns
        categorical_cols = data.select_dtypes(include=['object']).columns
        time_cols = []

        # 识别时间列
        for col in data.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['date', 'time', 'day', 'week', 'month', 'year', 'period']):
                time_cols.append(col)

        # 根据数据特征规划图表
        if len(time_cols) > 0 and len(numeric_cols) > 0:
            # 时间趋势图
            charts.append({
                "type": "line",
                "x": data[time_cols[0]].tolist(),
                "y": data[numeric_cols[0]].tolist(),
                "title": f"{numeric_cols[0]}趋势分析"
            })
        elif len(categorical_cols) > 0 and len(numeric_cols) > 0:
            # 类别比较图
            if len(data[categorical_cols[0]].unique()) <= 10:
                # 聚合数据
                aggregated = data.groupby(categorical_cols[0])[numeric_cols[0]].sum().reset_index()
                charts.append({
                    "type": "bar",
                    "x": aggregated[categorical_cols[0]].tolist(),
                    "y": aggregated[numeric_cols[0]].tolist(),
                    "title": f"{categorical_cols[0]}对比分析"
                })
        elif len(numeric_cols) >= 2:
            # 散点图
            charts.append({
                "type": "scatter",
                "x": data[numeric_cols[0]].tolist(),
                "y": data[numeric_cols[1]].tolist(),
                "title": f"{numeric_cols[0]} vs {numeric_cols[1]}"
            })

        return charts

    def _filter_core_charts(self, charts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤核心图表，只保留相关的核心图表

        Args:
            charts: 原始图表列表

        Returns:
            List: 过滤后的核心图表列表
        """
        # 限制图表数量，只保留前3个核心图表
        return charts[:3]


# 测试代码
if __name__ == "__main__":
    planner = VisualizationPlanner()
    
    # 测试A/B测试图表规划
    ab_data = {
        "conversion_A": 0.1234,
        "conversion_B": 0.1567,
        "uplift": 0.2698,
        "p_value": 0.0234,
        "significant": True,
        "confidence_level": "95%"
    }
    
    print("A/B测试图表规划:")
    print(planner.plan(ab_data, None))
    
    # 测试漏斗分析图表规划
    funnel_data = {
        "funnel_stages": [
            {"name": "浏览", "count": 1000},
            {"name": "加购", "count": 500},
            {"name": "购买", "count": 200}
        ]
    }
    
    print("\n漏斗分析图表规划:")
    print(planner.plan(funnel_data, None))
