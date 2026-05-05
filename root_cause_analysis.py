"""
深度诊断与根因分析模块
实现根因分析、多维交叉分析和漏斗分析功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any

class RootCauseAnalyzer:
    """根因分析器"""
    
    def __init__(self):
        """初始化根因分析器"""
        pass
    
    def analyze_root_causes(self, data_results: Dict[str, Any]) -> List[str]:
        """
        分析根因
        
        Args:
            data_results: 数据结果
            
        Returns:
            list: 根因洞察
        """
        insights = []
        
        # 1. 分析漏斗数据
        if 'funnel_data' in data_results:
            funnel_insights = self._analyze_funnel(data_results['funnel_data'])
            insights.extend(funnel_insights)
        
        # 2. 分析用户行为数据
        if 'user_behavior_data' in data_results:
            behavior_insights = self._analyze_user_behavior(data_results['user_behavior_data'])
            insights.extend(behavior_insights)
        
        # 3. 分析销售数据
        if 'sales_data' in data_results:
            sales_insights = self._analyze_sales(data_results['sales_data'])
            insights.extend(sales_insights)
        
        # 4. 分析产品数据
        if 'product_data' in data_results:
            product_insights = self._analyze_products(data_results['product_data'])
            insights.extend(product_insights)
        
        # 5. 分析营销数据
        if 'marketing_data' in data_results:
            marketing_insights = self._analyze_marketing(data_results['marketing_data'])
            insights.extend(marketing_insights)
        
        # 限制洞察数量
        return insights[:10]
    
    def _analyze_funnel(self, funnel_data: pd.DataFrame) -> List[str]:
        """分析漏斗数据"""
        insights = []
        
        try:
            # 计算各阶段转化率
            if len(funnel_data) > 1:
                conversion_rates = []
                for i in range(1, len(funnel_data)):
                    prev_count = funnel_data.iloc[i-1]['count']
                    curr_count = funnel_data.iloc[i]['count']
                    if prev_count > 0:
                        rate = (curr_count / prev_count) * 100
                        conversion_rates.append({
                            'from_stage': funnel_data.iloc[i-1]['step'],
                            'to_stage': funnel_data.iloc[i]['step'],
                            'rate': rate
                        })
                
                # 识别转化率低的环节
                low_conversion = [cr for cr in conversion_rates if cr['rate'] < 30]
                if low_conversion:
                    for item in low_conversion:
                        insights.append(
                            f"🔍 **漏斗断点**：{item['from_stage']}到{item['to_stage']}的转化率仅为{item['rate']:.1f}%，"  
                            f"可能存在用户体验问题"
                        )
                
                # 识别最大的转化率下降
                if conversion_rates:
                    max_drop = min(conversion_rates, key=lambda x: x['rate'])
                    insights.append(
                        f"📉 **关键断点**：{max_drop['from_stage']}到{max_drop['to_stage']}的转化率最低，"  
                        f"仅为{max_drop['rate']:.1f}%，建议重点优化此环节"
                    )
        except Exception as e:
            insights.append(f"⚠️ 漏斗分析失败: {str(e)}")
        
        return insights
    
    def _analyze_user_behavior(self, behavior_data: pd.DataFrame) -> List[str]:
        """分析用户行为数据"""
        insights = []
        
        try:
            # 分析用户停留时间
            if 'session_duration' in behavior_data.columns:
                avg_duration = behavior_data['session_duration'].mean()
                median_duration = behavior_data['session_duration'].median()
                
                if avg_duration < 60:  # 小于1分钟
                    insights.append(
                        "⏱️ **用户停留时间短**：平均会话时长仅{avg_duration:.1f}秒，"  
                        "可能是内容吸引力不足或页面加载缓慢"
                    )
                
                # 分析停留时间分布
                if 'page' in behavior_data.columns:
                    page_duration = behavior_data.groupby('page')['session_duration'].mean().sort_values()
                    if len(page_duration) > 0:
                        shortest_page = page_duration.index[0]
                        shortest_duration = page_duration.iloc[0]
                        if shortest_duration < 30:
                            insights.append(
                                f"📄 **页面跳出率高**：{shortest_page}页面平均停留时间仅{shortest_duration:.1f}秒，"  
                                "可能存在页面设计问题"
                            )
            
            # 分析跳出率
            if 'bounce' in behavior_data.columns:
                bounce_rate = (behavior_data['bounce'].sum() / len(behavior_data)) * 100
                if bounce_rate > 60:
                    insights.append(
                        f"💨 **跳出率高**：整体跳出率{rate:.1f}%，"  
                        "可能是着陆页体验差或流量质量低"
                    )
        except Exception as e:
            insights.append(f"⚠️ 用户行为分析失败: {str(e)}")
        
        return insights
    
    def _analyze_sales(self, sales_data: pd.DataFrame) -> List[str]:
        """分析销售数据"""
        insights = []
        
        try:
            # 分析销售趋势
            if 'date' in sales_data.columns and 'revenue' in sales_data.columns:
                sales_data['date'] = pd.to_datetime(sales_data['date'])
                sales_data = sales_data.sort_values('date')
                
                # 计算日销售额
                daily_sales = sales_data.groupby('date')['revenue'].sum()
                
                # 分析趋势
                if len(daily_sales) > 7:
                    recent_7_days = daily_sales.tail(7)
                    previous_7_days = daily_sales.tail(14).head(7)
                    
                    recent_avg = recent_7_days.mean()
                    previous_avg = previous_7_days.mean()
                    
                    if previous_avg > 0:
                        change = ((recent_avg - previous_avg) / previous_avg) * 100
                        if change < -10:
                            insights.append(
                                f"📉 **销售额下降**：近7天销售额相比前7天下降{abs(change):.1f}%，"  
                                "需要分析原因并采取措施"
                            )
                        elif change > 10:
                            insights.append(
                                f"📈 **销售额上升**：近7天销售额相比前7天增长{change:.1f}%，"  
                                "建议分析成功因素并复制"
                            )
            
            # 分析客单价
            if 'order_value' in sales_data.columns:
                avg_order_value = sales_data['order_value'].mean()
                median_order_value = sales_data['order_value'].median()
                
                # 分析客单价分布
                high_value_orders = sales_data[sales_data['order_value'] > avg_order_value * 2]
                if len(high_value_orders) / len(sales_data) < 0.1:
                    insights.append(
                        "💎 **高价值订单占比低**：高价值订单（客单价高于平均值2倍）占比不足10%，"  
                        "建议优化产品组合或向上销售策略"
                    )
        except Exception as e:
            insights.append(f"⚠️ 销售分析失败: {str(e)}")
        
        return insights
    
    def _analyze_products(self, product_data: pd.DataFrame) -> List[str]:
        """分析产品数据"""
        insights = []
        
        try:
            # 分析产品表现
            if 'sales' in product_data.columns and 'stock' in product_data.columns:
                # 分析滞销产品
                low_sales_products = product_data[product_data['sales'] < 10]
                if len(low_sales_products) > 0:
                    insights.append(
                        f"📦 **滞销产品**：发现{len(low_sales_products)}个产品销量低于10，"  
                        "建议清理库存或优化营销策略"
                    )
                
                # 分析库存不足产品
                low_stock_products = product_data[product_data['stock'] < 5]
                if len(low_stock_products) > 0:
                    insights.append(
                        f"⚠️ **库存不足**：发现{len(low_stock_products)}个产品库存不足5，"  
                        "建议及时补货避免缺货"
                    )
            
            # 分析产品评分
            if 'rating' in product_data.columns:
                low_rated_products = product_data[product_data['rating'] < 3.0]
                if len(low_rated_products) > 0:
                    insights.append(
                        f"⭐ **低评分产品**：发现{len(low_rated_products)}个产品评分低于3.0，"  
                        "建议改进产品质量或客户服务"
                    )
        except Exception as e:
            insights.append(f"⚠️ 产品分析失败: {str(e)}")
        
        return insights
    
    def _analyze_marketing(self, marketing_data: pd.DataFrame) -> List[str]:
        """分析营销数据"""
        insights = []
        
        try:
            # 分析渠道效果
            if 'channel' in marketing_data.columns and 'conversion_rate' in marketing_data.columns:
                channel_performance = marketing_data.groupby('channel')['conversion_rate'].mean().sort_values()
                
                # 识别低效渠道
                low_performing_channels = channel_performance[channel_performance < 0.01]  # 转化率低于1%
                if len(low_performing_channels) > 0:
                    insights.append(
                        f"📺 **低效渠道**：{len(low_performing_channels)}个渠道转化率低于1%，"  
                        "建议优化或停止这些渠道的投放"
                    )
                
                # 识别高效渠道
                high_performing_channels = channel_performance[channel_performance > 0.05]  # 转化率高于5%
                if len(high_performing_channels) > 0:
                    insights.append(
                        f"🚀 **高效渠道**：{len(high_performing_channels)}个渠道转化率高于5%，"  
                        "建议增加这些渠道的投放预算"
                    )
            
            # 分析活动效果
            if 'campaign' in marketing_data.columns and 'roi' in marketing_data.columns:
                campaign_roi = marketing_data.groupby('campaign')['roi'].mean().sort_values()
                
                # 识别负ROI活动
                negative_roi_campaigns = campaign_roi[campaign_roi < 0]
                if len(negative_roi_campaigns) > 0:
                    insights.append(
                        f"💸 **负ROI活动**：{len(negative_roi_campaigns)}个活动ROI为负，"  
                        "建议调整活动策略或停止"
                    )
        except Exception as e:
            insights.append(f"⚠️ 营销分析失败: {str(e)}")
        
        return insights
    
    def perform_multivariate_analysis(self, df: pd.DataFrame, target_col: str, 
                                    feature_cols: List[str]) -> Dict[str, Any]:
        """
        执行多维交叉分析
        
        Args:
            df: 数据框
            target_col: 目标列
            feature_cols: 特征列列表
            
        Returns:
            dict: 分析结果
        """
        try:
            analysis_results = {}
            
            for feature_col in feature_cols:
                if feature_col in df.columns:
                    # 计算每个特征值的目标值统计
                    feature_stats = df.groupby(feature_col)[target_col].agg(['mean', 'count', 'std']).reset_index()
                    feature_stats = feature_stats.sort_values('mean', ascending=False)
                    
                    analysis_results[feature_col] = {
                        'stats': feature_stats.to_dict('records'),
                        'top_performer': feature_stats.iloc[0][feature_col] if len(feature_stats) > 0 else None,
                        'bottom_performer': feature_stats.iloc[-1][feature_col] if len(feature_stats) > 0 else None
                    }
            
            return {
                'success': True,
                'results': analysis_results,
                'message': '多维交叉分析完成'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'多维交叉分析失败: {str(e)}'
            }
    
    def generate_insights_from_analysis(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        从分析结果生成洞察
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            list: 生成的洞察
        """
        insights = []
        
        # 从多维分析结果生成洞察
        if 'results' in analysis_results:
            for feature, result in analysis_results['results'].items():
                if 'top_performer' in result and 'bottom_performer' in result:
                    if result['top_performer'] and result['bottom_performer']:
                        insights.append(
                            f"🎯 **{feature}优化机会**：{result['top_performer']}表现最佳，"  
                            f"而{result['bottom_performer']}表现最差，建议向最佳实践靠拢"
                        )
        
        return insights

# 全局实例
root_cause_analyzer = RootCauseAnalyzer()

def analyze_root_causes(data_results: Dict[str, Any]) -> List[str]:
    """分析根因的便捷函数"""
    return root_cause_analyzer.analyze_root_causes(data_results)

def perform_multivariate_analysis(df: pd.DataFrame, target_col: str, 
                                feature_cols: List[str]) -> Dict[str, Any]:
    """执行多维交叉分析的便捷函数"""
    return root_cause_analyzer.perform_multivariate_analysis(df, target_col, feature_cols)

def generate_insights_from_analysis(analysis_results: Dict[str, Any]) -> List[str]:
    """从分析结果生成洞察的便捷函数"""
    return root_cause_analyzer.generate_insights_from_analysis(analysis_results)
