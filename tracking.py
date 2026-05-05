"""
效果追踪模块
实现策略效果监控和预警功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

class TrackingManager:
    """效果追踪管理器"""
    
    def __init__(self):
        """初始化效果追踪管理器"""
        pass
    
    def create_tracking_config(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建效果追踪配置
        
        Args:
            action_plan: 行动方案
            
        Returns:
            dict: 追踪配置
        """
        tracking_config = {
            'metrics': self._identify_tracking_metrics(action_plan),
            'frequency': 'daily',  # 追踪频率
            'thresholds': self._set_thresholds(action_plan),
            'alert_rules': self._create_alert_rules(action_plan),
            'dashboard_config': self._create_dashboard_config(action_plan),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return tracking_config
    
    def _identify_tracking_metrics(self, action_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别需要追踪的指标"""
        metrics = []
        
        # 根据行动方案识别指标
        if 'suggestions' in action_plan:
            for suggestion in action_plan['suggestions']:
                if '转化' in suggestion:
                    metrics.append({
                        'name': 'conversion_rate',
                        'display_name': '转化率',
                        'description': '用户转化百分比',
                        'target': 0.05,  # 5%
                        'unit': '%'
                    })
                elif 'GMV' in suggestion or '销售额' in suggestion:
                    metrics.append({
                        'name': 'gmv',
                        'display_name': 'GMV',
                        'description': '商品交易总额',
                        'target': 100000,  # 10万
                        'unit': '元'
                    })
                elif '留存' in suggestion:
                    metrics.append({
                        'name': 'retention_rate',
                        'display_name': '留存率',
                        'description': '用户留存百分比',
                        'target': 0.4,  # 40%
                        'unit': '%'
                    })
                elif '获客' in suggestion or '流量' in suggestion:
                    metrics.append({
                        'name': 'new_users',
                        'display_name': '新用户数',
                        'description': '新增用户数量',
                        'target': 1000,  # 1000
                        'unit': '人'
                    })
        
        # 默认指标
        if not metrics:
            metrics = [
                {
                    'name': 'conversion_rate',
                    'display_name': '转化率',
                    'description': '用户转化百分比',
                    'target': 0.05,
                    'unit': '%'
                },
                {
                    'name': 'gmv',
                    'display_name': 'GMV',
                    'description': '商品交易总额',
                    'target': 100000,
                    'unit': '元'
                }
            ]
        
        return metrics
    
    def _set_thresholds(self, action_plan: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """设置阈值"""
        thresholds = {
            'conversion_rate': {
                'warning': 0.03,  # 警告阈值
                'critical': 0.01   # 严重阈值
            },
            'gmv': {
                'warning': 80000,   # 警告阈值
                'critical': 50000   # 严重阈值
            },
            'retention_rate': {
                'warning': 0.3,     # 警告阈值
                'critical': 0.2     # 严重阈值
            },
            'new_users': {
                'warning': 800,     # 警告阈值
                'critical': 500     # 严重阈值
            }
        }
        
        return thresholds
    
    def _create_alert_rules(self, action_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建预警规则"""
        alert_rules = [
            {
                'metric': 'conversion_rate',
                'condition': 'below',
                'threshold': 0.03,
                'severity': 'warning',
                'message': '转化率低于3%，需要关注'
            },
            {
                'metric': 'conversion_rate',
                'condition': 'below',
                'threshold': 0.01,
                'severity': 'critical',
                'message': '转化率低于1%，需要紧急处理'
            },
            {
                'metric': 'gmv',
                'condition': 'below',
                'threshold': 80000,
                'severity': 'warning',
                'message': 'GMV低于8万，需要关注'
            },
            {
                'metric': 'gmv',
                'condition': 'below',
                'threshold': 50000,
                'severity': 'critical',
                'message': 'GMV低于5万，需要紧急处理'
            },
            {
                'metric': 'retention_rate',
                'condition': 'below',
                'threshold': 0.3,
                'severity': 'warning',
                'message': '留存率低于30%，需要关注'
            },
            {
                'metric': 'new_users',
                'condition': 'below',
                'threshold': 800,
                'severity': 'warning',
                'message': '新用户数低于800，需要关注'
            }
        ]
        
        return alert_rules
    
    def _create_dashboard_config(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """创建仪表盘配置"""
        dashboard_config = {
            'widgets': [
                {
                    'type': 'line_chart',
                    'title': '转化率趋势',
                    'metric': 'conversion_rate',
                    'time_range': '7d'
                },
                {
                    'type': 'line_chart',
                    'title': 'GMV趋势',
                    'metric': 'gmv',
                    'time_range': '7d'
                },
                {
                    'type': 'line_chart',
                    'title': '新用户趋势',
                    'metric': 'new_users',
                    'time_range': '7d'
                },
                {
                    'type': 'gauge',
                    'title': '当前转化率',
                    'metric': 'conversion_rate',
                    'target': 0.05
                },
                {
                    'type': 'gauge',
                    'title': '当前GMV',
                    'metric': 'gmv',
                    'target': 100000
                },
                {
                    'type': 'alert_list',
                    'title': '预警信息',
                    'max_alerts': 10
                }
            ],
            'refresh_interval': 3600  # 1小时刷新一次
        }
        
        return dashboard_config
    
    def monitor_performance(self, tracking_config: Dict[str, Any], 
                          current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        监控性能
        
        Args:
            tracking_config: 追踪配置
            current_metrics: 当前指标值
            
        Returns:
            dict: 监控结果
        """
        alerts = []
        status = 'normal'
        
        # 检查每个指标
        for metric_config in tracking_config.get('metrics', []):
            metric_name = metric_config['name']
            if metric_name in current_metrics:
                current_value = current_metrics[metric_name]
                target = metric_config.get('target', 0)
                
                # 检查预警规则
                for rule in tracking_config.get('alert_rules', []):
                    if rule['metric'] == metric_name:
                        if rule['condition'] == 'below' and current_value < rule['threshold']:
                            alerts.append({
                                'metric': metric_name,
                                'value': current_value,
                                'threshold': rule['threshold'],
                                'severity': rule['severity'],
                                'message': rule['message'],
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            if rule['severity'] == 'critical':
                                status = 'critical'
                            elif rule['severity'] == 'warning' and status != 'critical':
                                status = 'warning'
        
        return {
            'status': status,
            'alerts': alerts,
            'current_metrics': current_metrics,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'监控完成，状态: {status}'
        }
    
    def generate_performance_report(self, historical_data: pd.DataFrame, 
                                  tracking_config: Dict[str, Any]) -> str:
        """
        生成性能报告
        
        Args:
            historical_data: 历史数据
            tracking_config: 追踪配置
            
        Returns:
            str: 性能报告
        """
        report = f"# 性能追踪报告\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 分析趋势
        if not historical_data.empty:
            report += "## 趋势分析\n"
            
            for metric_config in tracking_config.get('metrics', []):
                metric_name = metric_config['name']
                if metric_name in historical_data.columns:
                    # 计算趋势
                    data = historical_data[metric_name].dropna()
                    if len(data) > 1:
                        # 计算变化率
                        first_value = data.iloc[0]
                        last_value = data.iloc[-1]
                        if first_value > 0:
                            change_rate = ((last_value - first_value) / first_value) * 100
                            trend = '上升' if change_rate > 0 else '下降'
                            
                            report += f"- **{metric_config['display_name']}**: {trend}{abs(change_rate):.1f}%\n"
                            
                            # 与目标比较
                            target = metric_config.get('target', 0)
                            if last_value >= target:
                                report += f"  状态: 达到目标 (当前: {last_value:.2f}{metric_config['unit']}, 目标: {target:.2f}{metric_config['unit']})\n"
                            else:
                                gap = ((target - last_value) / target) * 100
                                report += f"  状态: 未达到目标 (当前: {last_value:.2f}{metric_config['unit']}, 目标: {target:.2f}{metric_config['unit']}, 差距: {gap:.1f}%)\n"
        
        # 预警信息
        report += "\n## 预警信息\n"
        # 这里可以添加最近的预警信息
        report += "- 暂无预警信息\n"
        
        # 建议
        report += "\n## 建议\n"
        report += "- 持续监控关键指标变化\n"
        report += "- 定期分析趋势，及时调整策略\n"
        report += "- 关注预警信息，快速响应异常情况\n"
        
        return report
    
    def predict_performance(self, historical_data: pd.DataFrame, 
                          forecast_days: int = 7) -> Dict[str, Any]:
        """
        预测性能
        
        Args:
            historical_data: 历史数据
            forecast_days: 预测天数
            
        Returns:
            dict: 预测结果
        """
        predictions = {}
        
        if not historical_data.empty:
            # 简单线性预测
            for col in historical_data.columns:
                if pd.api.types.is_numeric_dtype(historical_data[col]):
                    data = historical_data[col].dropna()
                    if len(data) > 1:
                        # 计算趋势
                        x = np.arange(len(data))
                        y = data.values
                        
                        # 线性回归
                        slope, intercept = np.polyfit(x, y, 1)
                        
                        # 预测未来值
                        future_x = np.arange(len(data), len(data) + forecast_days)
                        future_y = slope * future_x + intercept
                        
                        predictions[col] = {
                            'forecast': future_y.tolist(),
                            'trend': '上升' if slope > 0 else '下降' if slope < 0 else '稳定',
                            'slope': float(slope)
                        }
        
        return {
            'predictions': predictions,
            'forecast_days': forecast_days,
            'message': f'预测完成，预测未来{forecast_days}天的性能'
        }

# 全局实例
tracking_manager = TrackingManager()

def create_tracking_config(action_plan: Dict[str, Any]) -> Dict[str, Any]:
    """创建效果追踪配置的便捷函数"""
    return tracking_manager.create_tracking_config(action_plan)

def monitor_performance(tracking_config: Dict[str, Any], 
                      current_metrics: Dict[str, float]) -> Dict[str, Any]:
    """监控性能的便捷函数"""
    return tracking_manager.monitor_performance(tracking_config, current_metrics)

def generate_performance_report(historical_data: pd.DataFrame, 
                              tracking_config: Dict[str, Any]) -> str:
    """生成性能报告的便捷函数"""
    return tracking_manager.generate_performance_report(historical_data, tracking_config)

def predict_performance(historical_data: pd.DataFrame, 
                      forecast_days: int = 7) -> Dict[str, Any]:
    """预测性能的便捷函数"""
    return tracking_manager.predict_performance(historical_data, forecast_days)
