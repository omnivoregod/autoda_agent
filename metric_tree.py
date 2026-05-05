"""
指标体系拆解模块
实现OSM (目标-策略-度量)框架和UJM (用户旅程地图)分析
"""

from typing import Dict, List, Any

class MetricTreeBuilder:
    """指标树构建器"""
    
    def __init__(self):
        """初始化指标树构建器"""
        # OSM模型映射
        self.osm_mappings = {
            '提升GMV': {
                'strategies': [
                    '增加流量',
                    '提高转化率',
                    '提升客单价',
                    '增加复购率'
                ],
                'metrics': {
                    '增加流量': ['UV', 'PV', '新访客数', '渠道转化率'],
                    '提高转化率': ['整体转化率', '漏斗各环节转化率', '购物车放弃率'],
                    '提升客单价': ['客单价', '关联购买率', '高端产品占比'],
                    '增加复购率': ['复购率', '用户生命周期价值', '回购间隔']
                }
            },
            '提高转化率': {
                'strategies': [
                    '优化产品页面',
                    '简化购买流程',
                    '增强信任背书',
                    '个性化推荐'
                ],
                'metrics': {
                    '优化产品页面': ['页面停留时间', '跳出率', '加购率'],
                    '简化购买流程': ['结账步骤完成率', '支付成功率', '平均购买时间'],
                    '增强信任背书': ['评论数量', '评分均值', '信任标识点击率'],
                    '个性化推荐': ['推荐点击率', '推荐转化率', '个性化匹配度']
                }
            },
            '增加用户留存': {
                'strategies': [
                    '提升产品体验',
                    '建立用户激励',
                    '个性化运营',
                    '社区建设'
                ],
                'metrics': {
                    '提升产品体验': ['用户满意度', 'NPS', '功能使用率'],
                    '建立用户激励': ['积分获取率', '会员活跃度', '奖励兑换率'],
                    '个性化运营': ['个性化内容点击率', '邮件打开率', '推送点击率'],
                    '社区建设': ['社区活跃度', '用户生成内容量', '社交分享率']
                }
            },
            '降低获客成本': {
                'strategies': [
                    '优化渠道投放',
                    '提升内容质量',
                    '增强病毒传播',
                    '提高转化效率'
                ],
                'metrics': {
                    '优化渠道投放': ['渠道ROI', '获客成本', '渠道转化率'],
                    '提升内容质量': ['内容阅读率', '内容分享率', '内容转化率'],
                    '增强病毒传播': ['病毒系数', '分享转化率', '邀请成功率'],
                    '提高转化效率': ['落地页转化率', '线索质量', '销售周期']
                }
            }
        }
        
        # UJM用户旅程地图
        self.ujm_stages = [
            {
                'stage': '曝光',
                'description': '用户首次接触品牌或产品',
                'metrics': ['曝光量', '品牌知名度', '渠道覆盖率'],
                'pain_points': ['曝光不足', '目标用户不精准', '渠道效果差']
            },
            {
                'stage': '触达',
                'description': '用户主动或被动接触产品信息',
                'metrics': ['触达率', '点击率', '打开率'],
                'pain_points': ['触达率低', '内容吸引力不足', '时机不当']
            },
            {
                'stage': '互动',
                'description': '用户与产品进行交互',
                'metrics': ['互动率', '停留时间', '页面浏览深度'],
                'pain_points': ['交互体验差', '内容不相关', '操作复杂']
            },
            {
                'stage': '转化',
                'description': '用户完成核心目标行为',
                'metrics': ['转化率', '转化成本', '转化时间'],
                'pain_points': ['转化路径长', '支付障碍', '信任缺失']
            },
            {
                'stage': '留存',
                'description': '用户持续使用产品',
                'metrics': ['留存率', '复购率', '用户生命周期价值'],
                'pain_points': ['用户流失', '活跃度下降', '价值衰减']
            }
        ]
    
    def build_metric_tree(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建指标树
        
        Args:
            business_context: 业务上下文
            
        Returns:
            dict: 指标树结构
        """
        business_goal = business_context.get('business_goal', '提升GMV')
        analysis_type = business_context.get('analysis_type', 'general')
        
        # 1. 构建OSM指标树
        osm_tree = self._build_osm_tree(business_goal)
        
        # 2. 构建UJM指标树
        ujm_tree = self._build_ujm_tree(analysis_type)
        
        # 3. 整合指标树
        metric_tree = {
            'osm': osm_tree,
            'ujm': ujm_tree,
            'business_goal': business_goal,
            'analysis_type': analysis_type,
            'core_metrics': self._identify_core_metrics(osm_tree, ujm_tree),
            'data_sources': self._identify_data_sources(analysis_type),
            'analysis_angles': self._generate_analysis_angles(analysis_type)
        }
        
        return metric_tree
    
    def _build_osm_tree(self, business_goal: str) -> Dict[str, Any]:
        """构建OSM指标树"""
        if business_goal in self.osm_mappings:
            mapping = self.osm_mappings[business_goal]
            return {
                'objective': business_goal,
                'strategies': [
                    {
                        'strategy': strategy,
                        'metrics': mapping['metrics'].get(strategy, [])
                    }
                    for strategy in mapping['strategies']
                ]
            }
        else:
            # 默认OSM树
            return {
                'objective': business_goal,
                'strategies': [
                    {
                        'strategy': '优化运营策略',
                        'metrics': ['核心业务指标', '运营效率指标', '用户体验指标']
                    }
                ]
            }
    
    def _build_ujm_tree(self, analysis_type: str) -> Dict[str, Any]:
        """构建UJM指标树"""
        # 根据分析类型调整UJM阶段
        if analysis_type == 'conversion':
            # 转化分析重点关注转化和留存阶段
            stages = [stage for stage in self.ujm_stages if stage['stage'] in ['互动', '转化', '留存']]
        elif analysis_type == 'sales':
            # 销售分析重点关注曝光、转化和留存
            stages = [stage for stage in self.ujm_stages if stage['stage'] in ['曝光', '转化', '留存']]
        elif analysis_type == 'user':
            # 用户分析关注所有阶段
            stages = self.ujm_stages
        else:
            # 其他分析类型使用完整UJM
            stages = self.ujm_stages
        
        return {
            'stages': stages,
            'critical_path': [stage['stage'] for stage in stages],
            'potential_breakpoints': self._identify_potential_breakpoints(stages)
        }
    
    def _identify_potential_breakpoints(self, stages: List[Dict[str, Any]]) -> List[str]:
        """识别潜在的断点"""
        breakpoints = []
        for stage in stages:
            if stage['stage'] in ['互动', '转化']:
                breakpoints.extend(stage['pain_points'])
        return list(set(breakpoints))
    
    def _identify_core_metrics(self, osm_tree: Dict[str, Any], ujm_tree: Dict[str, Any]) -> List[str]:
        """识别核心指标"""
        core_metrics = []
        
        # 从OSM中提取核心指标
        for strategy in osm_tree.get('strategies', []):
            metrics = strategy.get('metrics', [])
            # 每个策略取前2个指标作为核心指标
            core_metrics.extend(metrics[:2])
        
        # 从UJM中提取核心指标
        for stage in ujm_tree.get('stages', []):
            metrics = stage.get('metrics', [])
            # 每个阶段取第一个指标作为核心指标
            if metrics:
                core_metrics.append(metrics[0])
        
        # 去重并限制数量
        return list(set(core_metrics))[:10]
    
    def _identify_data_sources(self, analysis_type: str) -> List[str]:
        """识别数据来源"""
        data_sources_map = {
            'conversion': ['用户行为数据', '转化漏斗数据', '页面性能数据'],
            'sales': ['销售数据', '订单数据', '产品数据'],
            'user': ['用户数据', '行为数据', '留存数据', '社交数据'],
            'product': ['产品数据', '库存数据', '价格数据', '评价数据'],
            'marketing': ['营销活动数据', '渠道数据', '效果数据'],
            'pricing': ['价格数据', '促销数据', '销量数据', '竞争对手数据']
        }
        
        return data_sources_map.get(analysis_type, ['通用业务数据'])
    
    def _generate_analysis_angles(self, analysis_type: str) -> List[str]:
        """生成分析角度"""
        analysis_angles_map = {
            'conversion': [
                '转化漏斗分析',
                '用户路径分析',
                'A/B测试分析',
                '流失原因分析'
            ],
            'sales': [
                '销售趋势分析',
                '产品表现分析',
                '客户价值分析',
                '渠道效果分析'
            ],
            'user': [
                '用户画像分析',
                '行为特征分析',
                '留存分析',
                '生命周期分析'
            ],
            'product': [
                '产品表现分析',
                '库存优化分析',
                '价格策略分析',
                '竞品对比分析'
            ],
            'marketing': [
                '营销活动效果分析',
                '渠道ROI分析',
                '用户获取成本分析',
                '品牌影响力分析'
            ],
            'pricing': [
                '价格弹性分析',
                '促销效果分析',
                '竞品价格分析',
                '利润优化分析'
            ]
        }
        
        return analysis_angles_map.get(analysis_type, ['通用分析角度'])

# 全局实例
metric_tree_builder = MetricTreeBuilder()

def build_metric_tree(business_context: Dict[str, Any]) -> Dict[str, Any]:
    """构建指标树的便捷函数"""
    return metric_tree_builder.build_metric_tree(business_context)
