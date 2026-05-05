"""
分析执行器模块
执行SQL查询并进行数据分析
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    success: bool
    data: Optional[pd.DataFrame]
    error_message: Optional[str]
    execution_time: float
    row_count: int
    column_count: int


class AnalysisExecutor:
    """分析执行器 - 执行SQL查询并处理分析结果"""

    def __init__(self):
        self.execution_history = []

    def execute(self, sql_query: str, db_path: str = "ecommerce.db") -> AnalysisResult:
        """
        执行SQL查询（使用语义表名匹配）

        Args:
            sql_query: SQL查询字符串
            db_path: 数据库路径

        Returns:
            AnalysisResult: 分析结果对象
        """
        from tools import run_sql_query
        import time

        start_time = time.time()

        try:
            # 使用语义表名匹配执行SQL查询
            df = run_sql_query(sql_query)

            # 检查是否有错误
            if 'error' in df.columns:
                execution_time = time.time() - start_time
                
                # 记录错误
                self.execution_history.append({
                    'sql': sql_query,
                    'execution_time': execution_time,
                    'error': df['error'].iloc[0],
                    'timestamp': datetime.now().isoformat()
                })

                return AnalysisResult(
                    success=False,
                    data=None,
                    error_message=df['error'].iloc[0],
                    execution_time=execution_time,
                    row_count=0,
                    column_count=0
                )

            execution_time = time.time() - start_time

            # 记录执行历史
            self.execution_history.append({
                'sql': sql_query,
                'execution_time': execution_time,
                'row_count': len(df),
                'timestamp': datetime.now().isoformat()
            })

            return AnalysisResult(
                success=True,
                data=df,
                error_message=None,
                execution_time=execution_time,
                row_count=len(df),
                column_count=len(df.columns)
            )

        except Exception as e:
            execution_time = time.time() - start_time

            # 记录错误
            self.execution_history.append({
                'sql': sql_query,
                'execution_time': execution_time,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

            return AnalysisResult(
                success=False,
                data=None,
                error_message=str(e),
                execution_time=execution_time,
                row_count=0,
                column_count=0
            )

    def analyze(self, df: pd.DataFrame, analysis_type: str = 'auto') -> Dict[str, Any]:
        """
        对数据进行深度分析

        Args:
            df: 数据DataFrame
            analysis_type: 分析类型 ('auto', 'funnel', 'rfm', 'comparison', 'trend', 'distribution')

        Returns:
            Dict: 分析结果字典
        """
        if df is None or df.empty:
            return {
                'success': False,
                'error': '数据为空'
            }

        result = {
            'success': True,
            'data_shape': {
                'rows': len(df),
                'columns': len(df.columns)
            },
            'columns': list(df.columns)
        }

        if analysis_type == 'auto':
            # 自动识别分析类型并分析
            if self._is_funnel_data(df):
                result.update(self._analyze_funnel(df))
            elif self._is_rfm_data(df):
                result.update(self._analyze_rfm(df))
            elif self._is_comparison_data(df):
                result.update(self._analyze_comparison(df))
            elif self._is_trend_data(df):
                result.update(self._analyze_trend(df))
            else:
                result.update(self._analyze_distribution(df))

        elif analysis_type == 'funnel':
            result.update(self._analyze_funnel(df))

        elif analysis_type == 'rfm':
            result.update(self._analyze_rfm(df))

        elif analysis_type == 'comparison':
            result.update(self._analyze_comparison(df))

        elif analysis_type == 'trend':
            result.update(self._analyze_trend(df))

        elif analysis_type == 'distribution':
            result.update(self._analyze_distribution(df))

        return result

    def _is_funnel_data(self, df: pd.DataFrame) -> bool:
        """判断是否为漏斗数据"""
        funnel_indicators = ['step', 'stage', 'count', 'conversion_rate', 'rate']
        columns_lower = [col.lower() for col in df.columns]
        return any(indicator in col for indicator in funnel_indicators for col in columns_lower)

    def _is_rfm_data(self, df: pd.DataFrame) -> bool:
        """判断是否为RFM数据"""
        rfm_indicators = ['recency', 'frequency', 'monetary', 'rfm', 'segment', 'r_score', 'f_score', 'm_score']
        columns_lower = [col.lower() for col in df.columns]
        return any(indicator in col for indicator in rfm_indicators for col in columns_lower)

    def _is_comparison_data(self, df: pd.DataFrame) -> bool:
        """判断是否为比较数据"""
        # 比较数据通常有分组字段和数值字段
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        return len(numeric_cols) > 0 and len(categorical_cols) > 0

    def _is_trend_data(self, df: pd.DataFrame) -> bool:
        """判断是否为趋势数据"""
        trend_indicators = ['date', 'time', 'day', 'week', 'month', 'year', 'period']
        columns_lower = [col.lower() for col in df.columns]
        return any(indicator in col for indicator in trend_indicators for col in columns_lower)

    def _analyze_funnel(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析漏斗数据"""
        result = {
            'analysis_type': 'funnel',
            'funnel_stages': []
        }

        # 查找关键列
        step_col = None
        count_col = None
        rate_col = None

        for col in df.columns:
            col_lower = col.lower()
            if step_col is None and ('step' in col_lower or 'stage' in col_lower):
                step_col = col
            if count_col is None and 'count' in col_lower:
                count_col = col
            if rate_col is None and ('rate' in col_lower or 'rate' in col_lower.replace('_', '')):
                rate_col = col

        if step_col is None:
            step_col = df.columns[0]
        if count_col is None and len(df.columns) > 1:
            count_col = df.columns[1]

        # 构建漏斗阶段数据
        total_count = 0
        for idx, row in df.iterrows():
            if count_col and pd.notna(row[count_col]):
                total_count = max(total_count, row[count_col])

        for idx, row in df.iterrows():
            stage_data = {
                'name': str(row.get(step_col, f'Stage {idx+1}')),
                'count': int(row[count_col]) if count_col and count_col in row and pd.notna(row[count_col]) else 0,
                'conversion_rate': 0.0
            }

            # 计算转化率
            if total_count > 0 and stage_data['count'] > 0:
                stage_data['conversion_rate'] = round(stage_data['count'] / total_count * 100, 2)

            result['funnel_stages'].append(stage_data)

        # 计算阶段间转化率
        for i in range(1, len(result['funnel_stages'])):
            prev_count = result['funnel_stages'][i-1]['count']
            curr_count = result['funnel_stages'][i]['count']
            if prev_count > 0:
                result['funnel_stages'][i]['stage_conversion_rate'] = round(curr_count / prev_count * 100, 2)
            else:
                result['funnel_stages'][i]['stage_conversion_rate'] = 0.0

        # 生成洞察
        result['insights'] = self._generate_funnel_insights(result['funnel_stages'])

        return result

    def _generate_funnel_insights(self, funnel_stages: List[Dict]) -> List[str]:
        """生成漏斗洞察"""
        insights = []

        if len(funnel_stages) < 2:
            return ['数据不足，无法生成有效洞察']

        # 找出流失最大的阶段
        max_drop_idx = 1
        max_drop_rate = 0

        for i in range(1, len(funnel_stages)):
            if 'stage_conversion_rate' in funnel_stages[i]:
                drop_rate = 100 - funnel_stages[i]['stage_conversion_rate']
                if drop_rate > max_drop_rate:
                    max_drop_rate = drop_rate
                    max_drop_idx = i

        if max_drop_idx > 0:
            insights.append(
                f"从「{funnel_stages[max_drop_idx-1]['name']}」到「{funnel_stages[max_drop_idx]['name']}」流失率最高，达{max_drop_rate:.1f}%，建议重点优化该环节"
            )

        # 找出转化率最高的阶段
        best_idx = 1
        best_rate = 100

        for i in range(1, len(funnel_stages)):
            if 'stage_conversion_rate' in funnel_stages[i]:
                if funnel_stages[i]['stage_conversion_rate'] < best_rate:
                    best_rate = funnel_stages[i]['stage_conversion_rate']
                    best_idx = i

        if best_idx > 0:
            insights.append(
                f"「{funnel_stages[best_idx]['name']}」环节转化率最高，达{100-best_rate:.1f}%，可作为其他阶段的优化参考"
            )

        return insights

    def _analyze_rfm(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析RFM数据"""
        result = {
            'analysis_type': 'rfm',
            'rfm_summary': {}
        }

        # 识别RFM列
        rfm_cols = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'recency' in col_lower or 'r_score' in col_lower:
                rfm_cols['recency'] = col
            elif 'frequency' in col_lower or 'f_score' in col_lower:
                rfm_cols['frequency'] = col
            elif 'monetary' in col_lower or 'm_score' in col_lower:
                rfm_cols['monetary'] = col

        # 计算各维度统计
        for key, col in rfm_cols.items():
            if col in df.columns:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_values) > 0:
                    result['rfm_summary'][key] = {
                        'mean': round(numeric_values.mean(), 2),
                        'median': round(numeric_values.median(), 2),
                        'min': round(numeric_values.min(), 2),
                        'max': round(numeric_values.max(), 2)
                    }

        # 生成洞察
        result['insights'] = self._generate_rfm_insights(df, rfm_cols)

        return result

    def _generate_rfm_insights(self, df: pd.DataFrame, rfm_cols: Dict[str, str]) -> List[str]:
        """生成RFM洞察"""
        insights = []

        # 分析用户价值分布
        if 'segment' in df.columns:
            segment_counts = df['segment'].value_counts()
            if len(segment_counts) > 0:
                top_segment = segment_counts.index[0]
                top_pct = segment_counts.iloc[0] / len(df) * 100
                insights.append(f"当前最多用户属于「{top_segment}」群体，占比{top_pct:.1f}%")

        # 分析RFM得分
        if 'rfm_score' in df.columns:
            avg_rfm = pd.to_numeric(df['rfm_score'], errors='coerce').mean()
            if not pd.isna(avg_rfm):
                if avg_rfm >= 12:
                    insights.append("用户整体RFM得分较高，客户质量优良")
                elif avg_rfm >= 8:
                    insights.append("用户整体RFM得分中等，有提升空间")
                else:
                    insights.append("用户整体RFM得分较低，需要重点关注用户激活和留存")

        return insights if insights else ['数据不足，无法生成有效洞察']

    def _analyze_comparison(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析比较数据"""
        result = {
            'analysis_type': 'comparison',
            'comparison_summary': {}
        }

        # 识别分组列和数值列
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            group_col = categorical_cols[0]
            value_col = numeric_cols[0]

            # 计算各组统计
            grouped_stats = df.groupby(group_col)[value_col].agg(['sum', 'mean', 'count'])
            result['comparison_summary'] = {
                'group_column': group_col,
                'value_column': value_col,
                'groups': []
            }

            for group_name in grouped_stats.index:
                group_data = grouped_stats.loc[group_name]
                result['comparison_summary']['groups'].append({
                    'name': str(group_name),
                    'sum': round(group_data['sum'], 2) if pd.notna(group_data['sum']) else 0,
                    'mean': round(group_data['mean'], 2) if pd.notna(group_data['mean']) else 0,
                    'count': int(group_data['count'])
                })

            # 按sum排序，找出最大和最小的组
            sorted_groups = sorted(result['comparison_summary']['groups'], key=lambda x: x['sum'], reverse=True)
            if len(sorted_groups) > 0:
                result['comparison_summary']['top_group'] = sorted_groups[0]['name']
                result['comparison_summary']['bottom_group'] = sorted_groups[-1]['name']

        # 生成洞察
        result['insights'] = self._generate_comparison_insights(result['comparison_summary'])

        return result

    def _generate_comparison_insights(self, comparison_summary: Dict) -> List[str]:
        """生成比较洞察"""
        insights = []

        if 'groups' in comparison_summary and len(comparison_summary['groups']) > 0:
            groups = comparison_summary['groups']

            # 找出贡献最大的组
            total_sum = sum(g['sum'] for g in groups)
            if total_sum > 0:
                top_groups = sorted(groups, key=lambda x: x['sum'], reverse=True)[:2]
                for g in top_groups:
                    pct = g['sum'] / total_sum * 100
                    if pct > 20:
                        insights.append(f"「{g['name']}」贡献了总值的{pct:.1f}%，是最重要的{comparison_summary.get('group_column', '类别')}群体")

        return insights if insights else ['数据不足，无法生成有效洞察']

    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析趋势数据"""
        result = {
            'analysis_type': 'trend',
            'trend_summary': {}
        }

        # 识别时间列和数值列
        time_cols = []
        numeric_cols = []

        for col in df.columns:
            col_lower = col.lower()
            if any(indicator in col_lower for indicator in ['date', 'time', 'day', 'week', 'month', 'period']):
                time_cols.append(col)
            elif df[col].dtype in ['int64', 'float64']:
                numeric_cols.append(col)

        if len(time_cols) > 0 and len(numeric_cols) > 0:
            time_col = time_cols[0]
            value_col = numeric_cols[0]

            try:
                # 转换时间列
                df_sorted = df.copy()
                df_sorted[time_col] = pd.to_datetime(df_sorted[time_col], errors='coerce')
                df_sorted = df_sorted.dropna(subset=[time_col])
                df_sorted = df_sorted.sort_values(time_col)

                result['trend_summary'] = {
                    'time_column': time_col,
                    'value_column': value_col,
                    'start_value': float(df_sorted[value_col].iloc[0]) if len(df_sorted) > 0 else 0,
                    'end_value': float(df_sorted[value_col].iloc[-1]) if len(df_sorted) > 0 else 0,
                    'total_change': 0,
                    'change_rate': 0
                }

                # 计算变化
                if result['trend_summary']['start_value'] > 0:
                    change = result['trend_summary']['end_value'] - result['trend_summary']['start_value']
                    result['trend_summary']['total_change'] = round(change, 2)
                    result['trend_summary']['change_rate'] = round(change / result['trend_summary']['start_value'] * 100, 2)

            except Exception as e:
                result['trend_summary'] = {'error': str(e)}

        # 生成洞察
        result['insights'] = self._generate_trend_insights(result['trend_summary'])

        return result

    def _generate_trend_insights(self, trend_summary: Dict) -> List[str]:
        """生成趋势洞察"""
        insights = []

        if 'error' in trend_summary:
            return ['时间序列数据解析失败，无法生成趋势洞察']

        if 'change_rate' in trend_summary:
            change_rate = trend_summary['change_rate']
            if change_rate > 0:
                insights.append(f"指标整体呈上升趋势，增长率为{change_rate:.1f}%")
            elif change_rate < 0:
                insights.append(f"指标整体呈下降趋势，下降率为{abs(change_rate):.1f}%")
            else:
                insights.append("指标整体保持稳定")

        return insights if insights else ['数据不足，无法生成有效洞察']

    def _analyze_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析分布数据"""
        result = {
            'analysis_type': 'distribution',
            'distribution_summary': {}
        }

        # 获取所有列
        if len(df.columns) >= 2:
            category_col = df.columns[0]
            value_col = df.columns[1]

            # 计算分布
            total = df[value_col].sum() if value_col in df.columns else 0

            if total > 0:
                distribution_data = []
                for idx, row in df.iterrows():
                    value = row[value_col] if value_col in row and pd.notna(row[value_col]) else 0
                    distribution_data.append({
                        'category': str(row[category_col]) if category_col in row else f'Category {idx}',
                        'value': float(value),
                        'percentage': round(float(value) / float(total) * 100, 2)
                    })

                result['distribution_summary'] = {
                    'category_column': category_col,
                    'value_column': value_col,
                    'distribution': distribution_data
                }

        # 生成洞察
        result['insights'] = self._generate_distribution_insights(result['distribution_summary'])

        return result

    def _generate_distribution_insights(self, distribution_summary: Dict) -> List[str]:
        """生成分布洞察"""
        insights = []

        if 'distribution' in distribution_summary and len(distribution_summary['distribution']) > 0:
            dist = distribution_summary['distribution']

            # 找出占比最大的类别
            top_categories = sorted(dist, key=lambda x: x['percentage'], reverse=True)[:2]
            for cat in top_categories:
                if cat['percentage'] > 30:
                    insights.append(f"「{cat['category']}」占比最高，达{cat['percentage']:.1f}%，需要重点关注")

            # 检查是否集中度过高
            top3_pct = sum(c['percentage'] for c in dist[:3])
            if top3_pct > 80:
                insights.append(f"前3个类别合计占比达{top3_pct:.1f}%，存在集中风险，建议关注长尾品类")

        return insights if insights else ['数据不足，无法生成有效洞察']

    def analyze_ab_test(self, ab_data: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """
        A/B测试分析

        Args:
            ab_data: A/B测试数据

        Returns:
            Dict: A/B测试分析结果
        """
        import math

        # 提取数据
        group_a = ab_data.get('group_A', {})
        group_b = ab_data.get('group_B', {})

        users_a = group_a.get('users', 0)
        conversions_a = group_a.get('conversions', 0)
        users_b = group_b.get('users', 0)
        conversions_b = group_b.get('conversions', 0)

        # 计算转化率
        conversion_a = conversions_a / users_a if users_a > 0 else 0
        conversion_b = conversions_b / users_b if users_b > 0 else 0

        # 计算uplift
        uplift = (conversion_b - conversion_a) / conversion_a if conversion_a > 0 else 0

        # 计算Z检验
        p_value = 0.0
        significant = False

        if users_a > 0 and users_b > 0:
            # 合并转化率
            p_hat = (conversions_a + conversions_b) / (users_a + users_b)
            # 标准误
            se = math.sqrt(p_hat * (1 - p_hat) * (1/users_a + 1/users_b))
            # Z统计量
            z = (conversion_b - conversion_a) / se if se > 0 else 0
            # 近似计算p值（双侧检验）
            # 简化版Z检验，实际应用中应使用更精确的统计库
            if abs(z) > 1.96:  # 95%置信水平
                p_value = 0.05
                significant = True
            else:
                p_value = 0.1

        return {
            "conversion_A": round(conversion_a, 4),
            "conversion_B": round(conversion_b, 4),
            "uplift": round(uplift, 4),
            "p_value": round(p_value, 4),
            "significant": significant,
            "confidence_level": "95%"
        }

    def analyze_funnel(self, funnel_data: Dict[str, List]) -> Dict[str, Any]:
        """
        漏斗分析

        Args:
            funnel_data: 漏斗数据

        Returns:
            Dict: 漏斗分析结果
        """
        steps = funnel_data.get('steps', [])
        counts = funnel_data.get('counts', [])

        conversion_rates = []
        drop_off_rates = []
        biggest_drop_step = ""

        if steps and counts and len(steps) == len(counts):
            total = counts[0]
            max_drop = 0

            for i, count in enumerate(counts):
                # 计算转化率
                conversion_rate = count / total if total > 0 else 0
                conversion_rates.append(round(conversion_rate, 4))

                # 计算流失率
                if i > 0:
                    drop_off_rate = 1 - (count / counts[i-1]) if counts[i-1] > 0 else 0
                    drop_off_rates.append(round(drop_off_rate, 4))

                    # 找出最大流失环节
                    if drop_off_rate > max_drop:
                        max_drop = drop_off_rate
                        biggest_drop_step = f"{steps[i-1]} → {steps[i]}"
                else:
                    drop_off_rates.append(0.0)

        return {
            "conversion_rates": conversion_rates,
            "drop_off_rates": drop_off_rates,
            "biggest_drop_step": biggest_drop_step
        }

    def analyze_rfm(self, rfm_data: Dict[str, List]) -> Dict[str, Any]:
        """
        RFM分析

        Args:
            rfm_data: RFM数据

        Returns:
            Dict: RFM分析结果
        """
        recency = rfm_data.get('recency', [])
        frequency = rfm_data.get('frequency', [])
        monetary = rfm_data.get('monetary', [])

        segments = []

        if recency and frequency and monetary and len(recency) == len(frequency) == len(monetary):
            # 计算分位数
            import numpy as np

            r_percentiles = np.percentile(recency, [33, 66])
            f_percentiles = np.percentile(frequency, [33, 66])
            m_percentiles = np.percentile(monetary, [33, 66])

            # 定义用户分群
            segments = [
                {
                    "name": "高价值用户",
                    "criteria": f"最近购买时间 <= {r_percentiles[0]:.1f}, 购买频次 >= {f_percentiles[1]:.1f}, 购买金额 >= {m_percentiles[1]:.1f}"
                },
                {
                    "name": "流失风险用户",
                    "criteria": f"最近购买时间 >= {r_percentiles[1]:.1f}, 购买频次 <= {f_percentiles[0]:.1f}, 购买金额 <= {m_percentiles[0]:.1f}"
                },
                {
                    "name": "潜在价值用户",
                    "criteria": f"最近购买时间 <= {r_percentiles[1]:.1f}, 购买频次 >= {f_percentiles[0]:.1f}, 购买金额 >= {m_percentiles[0]:.1f}"
                },
                {
                    "name": "新用户",
                    "criteria": f"最近购买时间 <= {r_percentiles[0]:.1f}, 购买频次 <= {f_percentiles[0]:.1f}, 购买金额 <= {m_percentiles[0]:.1f}"
                }
            ]

        return {
            "segments": segments
        }

    def analyze_revenue_tree(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        收入拆解分析

        Args:
            df: 数据DataFrame

        Returns:
            Dict: 收入拆解分析结果
        """
        result = {
            'analysis_type': 'revenue_tree',
            'revenue_breakdown': {}
        }

        # 识别收入相关列
        revenue_cols = []
        category_cols = []

        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['revenue', 'sales', 'amount', 'total']):
                revenue_cols.append(col)
            elif any(term in col_lower for term in ['category', 'channel', 'product', 'region']):
                category_cols.append(col)

        if revenue_cols and category_cols:
            revenue_col = revenue_cols[0]
            category_col = category_cols[0]

            # 计算各分类的收入贡献
            revenue_by_category = df.groupby(category_col)[revenue_col].sum()
            total_revenue = revenue_by_category.sum()

            breakdown = []
            for category, revenue in revenue_by_category.items():
                breakdown.append({
                    'category': str(category),
                    'revenue': round(revenue, 2),
                    'percentage': round(revenue / total_revenue * 100, 2)
                })

            result['revenue_breakdown'] = {
                'total_revenue': round(total_revenue, 2),
                'breakdown': sorted(breakdown, key=lambda x: x['revenue'], reverse=True)
            }

        return result

    def analyze_channel(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        渠道分析

        Args:
            df: 数据DataFrame

        Returns:
            Dict: 渠道分析结果
        """
        result = {
            'analysis_type': 'channel',
            'channel_performance': {}
        }

        # 识别渠道和指标列
        channel_cols = []
        metric_cols = []

        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['channel', 'source', 'medium']):
                channel_cols.append(col)
            elif any(term in col_lower for term in ['revenue', 'conversion', 'cost', 'roi']):
                metric_cols.append(col)

        if channel_cols and metric_cols:
            channel_col = channel_cols[0]

            # 计算各渠道的指标
            performance = []
            for channel in df[channel_col].unique():
                channel_data = df[df[channel_col] == channel]
                channel_metrics = {'channel': str(channel)}

                for metric_col in metric_cols:
                    try:
                        channel_metrics[metric_col] = round(channel_data[metric_col].sum(), 2)
                    except:
                        pass

                performance.append(channel_metrics)

            result['channel_performance'] = sorted(performance, key=lambda x: x.get(metric_cols[0], 0), reverse=True)

        return result

    def analyze_ltv_roi(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        LTV/ROI分析

        Args:
            df: 数据DataFrame

        Returns:
            Dict: LTV/ROI分析结果
        """
        result = {
            'analysis_type': 'ltv_roi',
            'metrics': {}
        }

        # 识别相关列
        user_col = None
        revenue_col = None
        cost_col = None
        date_col = None

        for col in df.columns:
            col_lower = col.lower()
            if user_col is None and any(term in col_lower for term in ['user', 'customer', 'id']):
                user_col = col
            elif revenue_col is None and any(term in col_lower for term in ['revenue', 'sales', 'amount']):
                revenue_col = col
            elif cost_col is None and any(term in col_lower for term in ['cost', 'expense']):
                cost_col = col
            elif date_col is None and any(term in col_lower for term in ['date', 'time']):
                date_col = col

        if user_col and revenue_col:
            # 计算LTV
            user_revenue = df.groupby(user_col)[revenue_col].sum()
            ltv = user_revenue.mean()

            # 计算ROI
            roi = 0
            if cost_col in df.columns:
                total_revenue = df[revenue_col].sum()
                total_cost = df[cost_col].sum()
                if total_cost > 0:
                    roi = (total_revenue - total_cost) / total_cost

            result['metrics'] = {
                'average_ltv': round(ltv, 2),
                'roi': round(roi, 4) if roi != 0 else 0
            }

        return result

    def analyze_anomaly(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        异常检测分析

        Args:
            df: 数据DataFrame

        Returns:
            Dict: 异常检测分析结果
        """
        result = {
            'analysis_type': 'anomaly',
            'anomalies': []
        }

        # 对数值列进行异常检测
        numeric_cols = df.select_dtypes(include=['number']).columns

        for col in numeric_cols:
            try:
                values = df[col].dropna()
                if len(values) > 0:
                    # 使用简单的3sigma方法检测异常
                    mean = values.mean()
                    std = values.std()
                    threshold = 3 * std

                    anomalies = df[(df[col] > mean + threshold) | (df[col] < mean - threshold)]
                    
                    for idx, row in anomalies.iterrows():
                        result['anomalies'].append({
                            'column': col,
                            'value': round(row[col], 2),
                            'expected_range': f"[{mean - threshold:.2f}, {mean + threshold:.2f}]",
                            'row_index': idx
                        })
            except:
                pass

        return result

    def analyze_generic(self, df: pd.DataFrame, analysis_type: str, analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        通用分析方法，支持各种分析类型

        Args:
            df: 数据DataFrame
            analysis_type: 分析类型
            analysis_config: 分析配置

        Returns:
            Dict: 分析结果
        """
        if analysis_type == 'ab_test' or analysis_type == 'A/B测试':
            # 从DataFrame中提取A/B测试数据
            ab_data = {
                'group_A': {'users': 0, 'conversions': 0},
                'group_B': {'users': 0, 'conversions': 0}
            }
            # 简单实现：假设数据中有group和conversion列
            if 'group' in df.columns and 'conversion' in df.columns:
                for group in ['A', 'B']:
                    group_data = df[df['group'] == group]
                    ab_data[f'group_{group}']['users'] = len(group_data)
                    ab_data[f'group_{group}']['conversions'] = int(group_data['conversion'].sum())
            return self.analyze_ab_test(ab_data)

        elif analysis_type == 'funnel' or analysis_type == '漏斗分析':
            # 从DataFrame中提取漏斗数据
            funnel_data = {'steps': [], 'counts': []}
            # 简单实现：假设数据中有step和count列
            if 'step' in df.columns and 'count' in df.columns:
                for _, row in df.iterrows():
                    funnel_data['steps'].append(row['step'])
                    funnel_data['counts'].append(int(row['count']))
            return self.analyze_funnel(funnel_data)

        elif analysis_type == 'rfm' or analysis_type == 'RFM分析':
            # 从DataFrame中提取RFM数据
            rfm_data = {'recency': [], 'frequency': [], 'monetary': []}
            # 支持多种RFM字段命名
            field_mapping = {
                'recency': ['recency', 'recency_days', 'r_score'],
                'frequency': ['frequency', 'f_score'],
                'monetary': ['monetary', 'm_score']
            }
            
            for key, possible_fields in field_mapping.items():
                for field in possible_fields:
                    if field in df.columns:
                        rfm_data[key] = df[field].tolist()
                        break
            
            # 如果直接从DataFrame提取失败，尝试从原始数据计算
            if not rfm_data['recency'] and 'order_time' in df.columns and 'customer_id' in df.columns:
                # 计算RFM值
                customer_groups = df.groupby('customer_id')
                recency = []
                frequency = []
                monetary = []
                
                for _, group in customer_groups:
                    # 计算最近购买时间（天数）
                    last_purchase = pd.to_datetime(group['order_time']).max()
                    days_since_last = (pd.Timestamp.now() - last_purchase).days
                    recency.append(days_since_last)
                    
                    # 计算购买频次
                    frequency.append(len(group))
                    
                    # 计算累计消费
                    monetary.append(group['total_usd'].sum())
                
                rfm_data['recency'] = recency
                rfm_data['frequency'] = frequency
                rfm_data['monetary'] = monetary
            
            return self.analyze_rfm(rfm_data)

        elif analysis_type == 'revenue_tree':
            return self.analyze_revenue_tree(df)

        elif analysis_type == 'channel':
            return self.analyze_channel(df)

        elif analysis_type == 'ltv_roi':
            return self.analyze_ltv_roi(df)

        elif analysis_type == 'anomaly':
            return self.analyze_anomaly(df)

        else:
            # 默认分析
            return self.analyze(df, analysis_type)


    def get_execution_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.execution_history

    def clear_history(self):
        """清空执行历史"""
        self.execution_history = []


def execute_analysis_workflow(sql_query: str, db_path: str = "ecommerce.db", analysis_type: str = 'auto') -> Dict[str, Any]:
    """
    执行分析工作流

    Args:
        sql_query: SQL查询字符串
        db_path: 数据库路径
        analysis_type: 分析类型

    Returns:
        Dict: 分析结果
    """
    executor = AnalysisExecutor()

    # 执行SQL查询
    result = executor.execute(sql_query, db_path)

    if not result.success:
        return {
            'success': False,
            'stage': 'executor',
            'error': result.error_message
        }

    # 执行数据分析
    analysis_result = executor.analyze(result.data, analysis_type)

    return {
        'success': True,
        'stage': 'executor',
        'data': result.data,
        'analysis': analysis_result,
        'execution_time': result.execution_time,
        'row_count': result.row_count,
        'column_count': result.column_count
    }