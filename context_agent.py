"""
需求诊断模块
用于澄清用户需求，填充业务上下文，生成结构化的分析任务需求书
"""

from typing import Dict, List, Any
import re
from datetime import datetime

class ContextAgent:
    """需求诊断代理"""
    
    def __init__(self):
        """初始化需求诊断代理"""
        self.business_goals = [
            '提升GMV',
            '提高转化率',
            '增加用户留存',
            '降低获客成本',
            '优化库存管理',
            '提升用户体验',
            '增加客单价',
            '提高复购率'
        ]
        
        self.product_cycles = [
            '探索期',
            '增长期',
            '成熟期',
            '衰退期'
        ]
        
        self.time_ranges = [
            '7天',
            '30天',
            '90天',
            '半年',
            '一年',
            '同比',
            '环比'
        ]
    
    def clarify_requirement(self, user_input: str) -> Dict[str, Any]:
        """
        澄清用户需求，填充业务上下文
        
        Args:
            user_input: 用户输入的分析需求
            
        Returns:
            dict: 结构化的业务上下文
        """
        # 1. 分析用户输入
        analysis = self._analyze_user_input(user_input)
        
        # 2. 提取业务目标
        business_goal = self._extract_business_goal(user_input)
        
        # 3. 确定时间范围
        time_range = self._extract_time_range(user_input)
        
        # 4. 识别产品周期
        product_cycle = self._infer_product_cycle(user_input)
        
        # 5. 生成结构化需求书
        requirement_doc = self._generate_requirement_doc(
            user_input,
            analysis,
            business_goal,
            time_range,
            product_cycle
        )
        
        return requirement_doc
    
    def _analyze_user_input(self, user_input: str) -> Dict[str, Any]:
        """分析用户输入"""
        # 提取关键词
        keywords = self._extract_keywords(user_input)
        
        # 识别分析类型
        analysis_type = self._identify_analysis_type(keywords)
        
        # 识别业务领域
        business_domain = self._identify_business_domain(keywords)
        
        return {
            'keywords': keywords,
            'analysis_type': analysis_type,
            'business_domain': business_domain,
            'input_length': len(user_input)
        }
    
    def _extract_keywords(self, user_input: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        keywords = re.findall(r'\b\w+\b', user_input.lower())
        # 过滤停用词
        stop_words = {'的', '了', '和', '与', '或', '是', '在', '有', '为'}
        keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 1]
        return list(set(keywords))
    
    def _identify_analysis_type(self, keywords: List[str]) -> str:
        """识别分析类型"""
        analysis_types = {
            'conversion': ['转化', '转化路', '漏斗', '转化流'],
            'payment': ['支付', '付款', 'payment', '支付方式'],
            'sales': ['销售', '销量', 'gmv', '营收'],
            'user': ['用户', '留存', '活跃', '注册'],
            'product': ['产品', '商品', '库存', 'SKU'],
            'marketing': ['营销', '推广', '活动', '促销'],
            'pricing': ['价格', '定价', '折扣', '优惠'],
            'rfm': ['RFM', '价值用户', '用户价值', '用户分层']
        }
        
        # 优先检查支付方式相关关键词
        for kw in keywords:
            if '支付' in kw or 'payment' in kw:
                return 'payment'
        
        for analysis_type, indicators in analysis_types.items():
            for indicator in indicators:
                if any(indicator in kw for kw in keywords):
                    return analysis_type
        
        return 'general'
    
    def _identify_business_domain(self, keywords: List[str]) -> str:
        """识别业务领域"""
        domains = {
            'ecommerce': ['电商', '零售', '商城', '店铺'],
            'finance': ['金融', '银行', '保险', '投资'],
            'content': ['内容', '媒体', '新闻', '视频'],
            'social': ['社交', '社区', '论坛', '互动'],
            'gaming': ['游戏', '电竞', '娱乐', '休闲']
        }
        
        for domain, indicators in domains.items():
            for indicator in indicators:
                if any(indicator in kw for kw in keywords):
                    return domain
        
        return 'general'
    
    def _extract_business_goal(self, user_input: str) -> str:
        """提取业务目标"""
        for goal in self.business_goals:
            if goal in user_input:
                return goal
        
        # 默认目标
        return '提升GMV'
    
    def _extract_time_range(self, user_input: str) -> str:
        """提取时间范围"""
        for time_range in self.time_ranges:
            if time_range in user_input:
                return time_range
        
        # 默认时间范围
        return '30天'
    
    def _infer_product_cycle(self, user_input: str) -> str:
        """推断产品周期"""
        for cycle in self.product_cycles:
            if cycle in user_input:
                return cycle
        
        # 根据关键词推断
        growth_indicators = ['增长', '扩张', '新用户', '快速']
        mature_indicators = ['稳定', '优化', '效率', '成本']
        decline_indicators = ['下降', '衰退', '流失', '萎缩']
        
        for indicator in growth_indicators:
            if indicator in user_input:
                return '增长期'
        
        for indicator in mature_indicators:
            if indicator in user_input:
                return '成熟期'
        
        for indicator in decline_indicators:
            if indicator in user_input:
                return '衰退期'
        
        # 默认产品周期
        return '探索期'
    
    def _generate_requirement_doc(self, user_input: str, analysis: Dict[str, Any], 
                               business_goal: str, time_range: str, 
                               product_cycle: str) -> Dict[str, Any]:
        """生成结构化需求书"""
        return {
            'original_input': user_input,
            'analysis': analysis,
            'business_goal': business_goal,
            'time_range': time_range,
            'product_cycle': product_cycle,
            'analysis_type': analysis['analysis_type'],
            'business_domain': analysis['business_domain'],
            'keywords': analysis['keywords'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_requirements': self._generate_data_requirements(analysis['analysis_type']),
            'success_metrics': self._generate_success_metrics(business_goal),
            'risk_factors': self._identify_risk_factors(product_cycle)
        }
    
    def _generate_data_requirements(self, analysis_type: str) -> List[str]:
        """生成数据需求"""
        data_requirements_map = {
            'conversion': ['用户行为数据', '转化漏斗数据', '页面停留时间'],
            'sales': ['销售数据', '订单数据', '产品数据'],
            'user': ['用户数据', '行为数据', '留存数据'],
            'product': ['产品数据', '库存数据', '价格数据'],
            'marketing': ['营销活动数据', '渠道数据', '效果数据'],
            'pricing': ['价格数据', '促销数据', '销量数据'],
            'payment': ['支付方式数据', '订单数据', '交易数据'],
            'rfm': ['用户交易数据', '订单时间数据', '交易金额数据']
        }
        
        return data_requirements_map.get(analysis_type, ['通用业务数据'])
    
    def _generate_success_metrics(self, business_goal: str) -> List[str]:
        """生成成功指标"""
        success_metrics_map = {
            '提升GMV': ['GMV增长率', '客单价', '订单量'],
            '提高转化率': ['转化率', '转化漏斗各环节转化率', '转化成本'],
            '增加用户留存': ['留存率', '复购率', '用户活跃天数'],
            '降低获客成本': ['获客成本', 'CAC', '渠道ROI'],
            '优化库存管理': ['库存周转率', '缺货率', '滞销率'],
            '提升用户体验': ['用户满意度', 'NPS', '页面加载时间'],
            '增加客单价': ['客单价', '关联购买率', '高端产品占比'],
            '提高复购率': ['复购率', '用户生命周期价值', '回购间隔']
        }
        
        return success_metrics_map.get(business_goal, ['业务指标改善'])
    
    def _identify_risk_factors(self, product_cycle: str) -> List[str]:
        """识别风险因素"""
        risk_factors_map = {
            '探索期': ['数据不足', '用户反馈有限', '市场定位不明确'],
            '增长期': ['竞争加剧', '用户增长瓶颈', '运营压力'],
            '成熟期': ['增长放缓', '用户疲劳', '创新不足'],
            '衰退期': ['用户流失', '市场萎缩', '盈利下降']
        }
        
        return risk_factors_map.get(product_cycle, ['业务风险'])

# 全局实例
context_agent = ContextAgent()

def clarify_requirement(user_input: str) -> Dict[str, Any]:
    """澄清用户需求的便捷函数"""
    return context_agent.clarify_requirement(user_input)
