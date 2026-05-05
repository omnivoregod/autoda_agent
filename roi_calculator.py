"""
ROI估算模块
实现投资回报率(ROI)估算功能，为商业决策提供数据支持
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ROIResult:
    """ROI计算结果"""
    roi: float  # 投资回报率
    net_return: float  # 净收益
    total_cost: float  # 总成本
    total_revenue: float  # 总收入
    payback_period: float  # 回收期（天）
    sensitivity_analysis: Dict[str, float]  # 敏感性分析

class ROICalculator:
    """ROI计算器"""
    
    def __init__(self):
        """初始化ROI计算器"""
        pass
    
    def calculate_roi(self, initial_investment: float, monthly_revenue: float, 
                     monthly_cost: float, time_horizon: int = 12) -> ROIResult:
        """
        计算基本ROI
        
        Args:
            initial_investment: 初始投资
            monthly_revenue: 月收入
            monthly_cost: 月成本
            time_horizon: 计算周期（月）
            
        Returns:
            ROIResult: ROI计算结果
        """
        # 计算总收益
        total_revenue = monthly_revenue * time_horizon
        
        # 计算总成本
        total_cost = initial_investment + (monthly_cost * time_horizon)
        
        # 计算净收益
        net_return = total_revenue - total_cost
        
        # 计算ROI
        if initial_investment > 0:
            roi = (net_return / initial_investment) * 100
        else:
            roi = 0
        
        # 计算回收期
        if (monthly_revenue - monthly_cost) > 0:
            payback_period = (initial_investment / (monthly_revenue - monthly_cost)) * 30  # 转换为天数
        else:
            payback_period = float('inf')
        
        # 敏感性分析
        sensitivity_analysis = {
            'revenue_increase_10%': self._calculate_sensitivity(
                initial_investment, monthly_revenue * 1.1, monthly_cost, time_horizon
            ),
            'revenue_decrease_10%': self._calculate_sensitivity(
                initial_investment, monthly_revenue * 0.9, monthly_cost, time_horizon
            ),
            'cost_increase_10%': self._calculate_sensitivity(
                initial_investment, monthly_revenue, monthly_cost * 1.1, time_horizon
            ),
            'cost_decrease_10%': self._calculate_sensitivity(
                initial_investment, monthly_revenue, monthly_cost * 0.9, time_horizon
            )
        }
        
        return ROIResult(
            roi=roi,
            net_return=net_return,
            total_cost=total_cost,
            total_revenue=total_revenue,
            payback_period=payback_period,
            sensitivity_analysis=sensitivity_analysis
        )
    
    def _calculate_sensitivity(self, initial_investment: float, monthly_revenue: float, 
                             monthly_cost: float, time_horizon: int) -> float:
        """计算敏感性分析"""
        total_revenue = monthly_revenue * time_horizon
        total_cost = initial_investment + (monthly_cost * time_horizon)
        net_return = total_revenue - total_cost
        
        if initial_investment > 0:
            return (net_return / initial_investment) * 100
        else:
            return 0
    
    def estimate_marketing_roi(self, ad_spend: float, conversion_rate: float, 
                             average_order_value: float, monthly_traffic: int, 
                             campaign_duration: int = 30) -> Dict[str, Any]:
        """
        估算营销活动ROI
        
        Args:
            ad_spend: 广告支出
            conversion_rate: 转化率（小数）
            average_order_value: 平均订单价值
            monthly_traffic: 月流量
            campaign_duration: 活动持续时间（天）
            
        Returns:
            dict: 营销ROI估算结果
        """
        # 计算活动期间的流量
        campaign_traffic = (monthly_traffic / 30) * campaign_duration
        
        # 计算预期转化数
        expected_conversions = campaign_traffic * conversion_rate
        
        # 计算预期收入
        expected_revenue = expected_conversions * average_order_value
        
        # 计算ROI
        if ad_spend > 0:
            roi = ((expected_revenue - ad_spend) / ad_spend) * 100
        else:
            roi = 0
        
        # 计算获客成本
        if expected_conversions > 0:
            cac = ad_spend / expected_conversions
        else:
            cac = float('inf')
        
        return {
            'roi': roi,
            'ad_spend': ad_spend,
            'expected_revenue': expected_revenue,
            'expected_conversions': expected_conversions,
            'cac': cac,
            'campaign_duration': campaign_duration,
            'message': f"营销活动预期ROI: {roi:.1f}%，获客成本: ¥{cac:.2f}"
        }
    
    def estimate_product_optimization_roi(self, implementation_cost: float, 
                                        current_conversion_rate: float, 
                                        expected_conversion_rate: float, 
                                        monthly_traffic: int, 
                                        average_order_value: float, 
                                        time_horizon: int = 12) -> Dict[str, Any]:
        """
        估算产品优化ROI
        
        Args:
            implementation_cost: 实施成本
            current_conversion_rate: 当前转化率（小数）
            expected_conversion_rate: 预期转化率（小数）
            monthly_traffic: 月流量
            average_order_value: 平均订单价值
            time_horizon: 计算周期（月）
            
        Returns:
            dict: 产品优化ROI估算结果
        """
        # 计算当前月收入
        current_monthly_revenue = monthly_traffic * current_conversion_rate * average_order_value
        
        # 计算预期月收入
        expected_monthly_revenue = monthly_traffic * expected_conversion_rate * average_order_value
        
        # 计算收入增长
        monthly_revenue_increase = expected_monthly_revenue - current_monthly_revenue
        total_revenue_increase = monthly_revenue_increase * time_horizon
        
        # 计算ROI
        if implementation_cost > 0:
            roi = ((total_revenue_increase - implementation_cost) / implementation_cost) * 100
        else:
            roi = 0
        
        # 计算回收期
        if monthly_revenue_increase > 0:
            payback_period = (implementation_cost / monthly_revenue_increase) * 30  # 转换为天数
        else:
            payback_period = float('inf')
        
        return {
            'roi': roi,
            'implementation_cost': implementation_cost,
            'current_monthly_revenue': current_monthly_revenue,
            'expected_monthly_revenue': expected_monthly_revenue,
            'monthly_revenue_increase': monthly_revenue_increase,
            'total_revenue_increase': total_revenue_increase,
            'payback_period': payback_period,
            'message': f"产品优化预期ROI: {roi:.1f}%，回收期: {payback_period:.0f}天"
        }
    
    def estimate_content_marketing_roi(self, content_cost: float, 
                                     expected_traffic_increase: int, 
                                     conversion_rate: float, 
                                     average_order_value: float, 
                                     content_lifespan: int = 365) -> Dict[str, Any]:
        """
        估算内容营销ROI
        
        Args:
            content_cost: 内容制作成本
            expected_traffic_increase: 预期流量增长
            conversion_rate: 转化率（小数）
            average_order_value: 平均订单价值
            content_lifespan: 内容生命周期（天）
            
        Returns:
            dict: 内容营销ROI估算结果
        """
        # 计算内容生命周期内的总流量增长
        total_traffic_increase = (expected_traffic_increase / 30) * content_lifespan
        
        # 计算预期转化数
        expected_conversions = total_traffic_increase * conversion_rate
        
        # 计算预期收入
        expected_revenue = expected_conversions * average_order_value
        
        # 计算ROI
        if content_cost > 0:
            roi = ((expected_revenue - content_cost) / content_cost) * 100
        else:
            roi = 0
        
        return {
            'roi': roi,
            'content_cost': content_cost,
            'expected_revenue': expected_revenue,
            'expected_conversions': expected_conversions,
            'content_lifespan': content_lifespan,
            'message': f"内容营销预期ROI: {roi:.1f}%，预期收入: ¥{expected_revenue:.2f}"
        }
    
    def generate_roi_report(self, roi_type: str, roi_result: Dict[str, Any]) -> str:
        """
        生成ROI分析报告
        
        Args:
            roi_type: ROI类型
            roi_result: ROI计算结果
            
        Returns:
            str: ROI分析报告
        """
        report = f"# {roi_type} ROI分析报告\n\n"
        
        if roi_type == "营销活动":
            report += f"## 基本信息\n"
            report += f"- 广告支出: ¥{roi_result.get('ad_spend', 0):.2f}\n"
            report += f"- 活动持续时间: {roi_result.get('campaign_duration', 0)}天\n"
            report += f"- 预期转化数: {roi_result.get('expected_conversions', 0):.0f}\n"
            report += f"- 预期收入: ¥{roi_result.get('expected_revenue', 0):.2f}\n"
            report += f"- 获客成本: ¥{roi_result.get('cac', 0):.2f}\n"
            report += f"- ROI: {roi_result.get('roi', 0):.1f}%\n\n"
            
            if roi_result.get('roi', 0) > 100:
                report += "## 建议\n"
                report += "- ROI高于100%，建议增加投放预算\n"
                report += "- 持续监控转化效果，及时调整策略\n"
            elif roi_result.get('roi', 0) > 0:
                report += "## 建议\n"
                report += "- ROI为正，建议继续执行\n"
                report += "- 尝试优化创意和定向，进一步提升ROI\n"
            else:
                report += "## 建议\n"
                report += "- ROI为负，建议重新评估活动策略\n"
                report += "- 考虑调整目标受众或创意内容\n"
        
        elif roi_type == "产品优化":
            report += f"## 基本信息\n"
            report += f"- 实施成本: ¥{roi_result.get('implementation_cost', 0):.2f}\n"
            report += f"- 当前月收入: ¥{roi_result.get('current_monthly_revenue', 0):.2f}\n"
            report += f"- 预期月收入: ¥{roi_result.get('expected_monthly_revenue', 0):.2f}\n"
            report += f"- 月收入增长: ¥{roi_result.get('monthly_revenue_increase', 0):.2f}\n"
            report += f"- 总收益增长: ¥{roi_result.get('total_revenue_increase', 0):.2f}\n"
            report += f"- 回收期: {roi_result.get('payback_period', 0):.0f}天\n"
            report += f"- ROI: {roi_result.get('roi', 0):.1f}%\n\n"
            
            if roi_result.get('roi', 0) > 200:
                report += "## 建议\n"
                report += "- ROI非常高，建议立即实施\n"
                report += "- 考虑扩大优化范围\n"
            elif roi_result.get('roi', 0) > 0:
                report += "## 建议\n"
                report += "- ROI为正，建议实施\n"
                report += "- 制定详细的实施计划和时间表\n"
            else:
                report += "## 建议\n"
                report += "- ROI为负，建议重新评估优化方案\n"
                report += "- 考虑降低实施成本或提高预期收益\n"
        
        elif roi_type == "内容营销":
            report += f"## 基本信息\n"
            report += f"- 内容制作成本: ¥{roi_result.get('content_cost', 0):.2f}\n"
            report += f"- 内容生命周期: {roi_result.get('content_lifespan', 0)}天\n"
            report += f"- 预期转化数: {roi_result.get('expected_conversions', 0):.0f}\n"
            report += f"- 预期收入: ¥{roi_result.get('expected_revenue', 0):.2f}\n"
            report += f"- ROI: {roi_result.get('roi', 0):.1f}%\n\n"
            
            if roi_result.get('roi', 0) > 300:
                report += "## 建议\n"
                report += "- ROI非常高，建议增加内容投入\n"
                report += "- 分析成功因素，复制到其他内容\n"
            elif roi_result.get('roi', 0) > 0:
                report += "## 建议\n"
                report += "- ROI为正，建议继续制作类似内容\n"
                report += "- 优化内容分发渠道，提高曝光\n"
            else:
                report += "## 建议\n"
                report += "- ROI为负，建议重新评估内容策略\n"
                report += "- 考虑调整内容主题或形式\n"
        
        return report

# 全局实例
roi_calculator = ROICalculator()

def calculate_roi(initial_investment: float, monthly_revenue: float, 
                 monthly_cost: float, time_horizon: int = 12) -> ROIResult:
    """计算基本ROI的便捷函数"""
    return roi_calculator.calculate_roi(initial_investment, monthly_revenue, monthly_cost, time_horizon)

def estimate_marketing_roi(ad_spend: float, conversion_rate: float, 
                         average_order_value: float, monthly_traffic: int, 
                         campaign_duration: int = 30) -> Dict[str, Any]:
    """估算营销活动ROI的便捷函数"""
    return roi_calculator.estimate_marketing_roi(ad_spend, conversion_rate, average_order_value, monthly_traffic, campaign_duration)

def estimate_product_optimization_roi(implementation_cost: float, 
                                    current_conversion_rate: float, 
                                    expected_conversion_rate: float, 
                                    monthly_traffic: int, 
                                    average_order_value: float, 
                                    time_horizon: int = 12) -> Dict[str, Any]:
    """估算产品优化ROI的便捷函数"""
    return roi_calculator.estimate_product_optimization_roi(implementation_cost, current_conversion_rate, expected_conversion_rate, monthly_traffic, average_order_value, time_horizon)

def estimate_content_marketing_roi(content_cost: float, 
                                 expected_traffic_increase: int, 
                                 conversion_rate: float, 
                                 average_order_value: float, 
                                 content_lifespan: int = 365) -> Dict[str, Any]:
    """估算内容营销ROI的便捷函数"""
    return roi_calculator.estimate_content_marketing_roi(content_cost, expected_traffic_increase, conversion_rate, average_order_value, content_lifespan)

def generate_roi_report(roi_type: str, roi_result: Dict[str, Any]) -> str:
    """生成ROI分析报告的便捷函数"""
    return roi_calculator.generate_roi_report(roi_type, roi_result)
