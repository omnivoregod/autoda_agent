"""
数据质量检验模块
实现数据质量检验功能，包括辛普森悖论检测、幸存者偏差检测和异常值检测
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Any, Tuple

class DataQAChecker:
    """数据质量检验器"""
    
    def __init__(self):
        """初始化数据质量检验器"""
        pass
    
    def detect_simpson_paradox(self, df: pd.DataFrame, group_col: str, metric_col: str, 
                              subgroup_col: str) -> Dict[str, Any]:
        """
        检测辛普森悖论
        
        Args:
            df: 数据框
            group_col: 分组列
            metric_col: 度量列
            subgroup_col: 子分组列
            
        Returns:
            dict: 检测结果
        """
        try:
            # 1. 计算整体层面的分组差异
            overall_stats = df.groupby(group_col)[metric_col].mean().reset_index()
            overall_trend = self._calculate_trend(overall_stats[group_col], overall_stats[metric_col])
            
            # 2. 计算子组层面的分组差异
            subgroup_stats = df.groupby([subgroup_col, group_col])[metric_col].mean().reset_index()
            
            # 3. 检查每个子组的趋势是否与整体趋势相反
            paradox_detected = False
            paradox_details = []
            
            for subgroup in df[subgroup_col].unique():
                subgroup_data = subgroup_stats[subgroup_stats[subgroup_col] == subgroup]
                if len(subgroup_data) < 2:
                    continue
                
                subgroup_trend = self._calculate_trend(subgroup_data[group_col], subgroup_data[metric_col])
                
                if overall_trend * subgroup_trend < 0:  # 趋势相反
                    paradox_detected = True
                    paradox_details.append({
                        'subgroup': subgroup,
                        'overall_trend': '上升' if overall_trend > 0 else '下降',
                        'subgroup_trend': '上升' if subgroup_trend > 0 else '下降'
                    })
            
            return {
                'detected': paradox_detected,
                'details': paradox_details,
                'overall_stats': overall_stats.to_dict('records'),
                'message': '检测到辛普森悖论' if paradox_detected else '未检测到辛普森悖论'
            }
        except Exception as e:
            return {
                'detected': False,
                'details': [],
                'error': str(e),
                'message': f'检测失败: {str(e)}'
            }
    
    def _calculate_trend(self, x: pd.Series, y: pd.Series) -> int:
        """计算趋势方向"""
        if len(x) < 2:
            return 0
        
        # 简单线性回归计算斜率
        slope, _, _, _, _ = stats.linregress(range(len(x)), y)
        
        if abs(slope) < 1e-6:
            return 0  # 无明显趋势
        elif slope > 0:
            return 1  # 上升趋势
        else:
            return -1  # 下降趋势
    
    def detect_survivor_bias(self, df: pd.DataFrame, survival_col: str, 
                            metric_col: str) -> Dict[str, Any]:
        """
        检测幸存者偏差
        
        Args:
            df: 数据框
            survival_col: 生存状态列（0=流失，1=留存）
            metric_col: 度量列
            
        Returns:
            dict: 检测结果
        """
        try:
            # 计算留存用户和流失用户的度量差异
            survival_stats = df.groupby(survival_col)[metric_col].agg(['mean', 'std', 'count']).reset_index()
            
            # 检查是否存在显著差异
            if len(survival_stats) == 2:
                retained = survival_stats[survival_stats[survival_col] == 1]
                churned = survival_stats[survival_stats[survival_col] == 0]
                
                if len(retained) > 0 and len(churned) > 0:
                    # 执行t检验
                    retained_data = df[df[survival_col] == 1][metric_col]
                    churned_data = df[df[survival_col] == 0][metric_col]
                    
                    t_stat, p_value = stats.ttest_ind(retained_data, churned_data, equal_var=False)
                    
                    significant_diff = p_value < 0.05
                    
                    return {
                        'detected': significant_diff,
                        'details': {
                            'retained_mean': float(retained[metric_col]['mean'].values[0]),
                            'churned_mean': float(churned[metric_col]['mean'].values[0]),
                            'retained_count': int(retained[metric_col]['count'].values[0]),
                            'churned_count': int(churned[metric_col]['count'].values[0]),
                            't_statistic': t_stat,
                            'p_value': p_value
                        },
                        'message': '检测到幸存者偏差' if significant_diff else '未检测到幸存者偏差'
                    }
            
            return {
                'detected': False,
                'details': {},
                'message': '数据不足，无法检测幸存者偏差'
            }
        except Exception as e:
            return {
                'detected': False,
                'details': {},
                'error': str(e),
                'message': f'检测失败: {str(e)}'
            }
    
    def detect_anomalies(self, df: pd.DataFrame, numeric_cols: List[str] = None) -> Dict[str, Any]:
        """
        检测异常值
        
        Args:
            df: 数据框
            numeric_cols: 要检测的数值列列表，如果为None则自动检测
            
        Returns:
            dict: 检测结果
        """
        try:
            if numeric_cols is None:
                # 自动检测数值列
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            anomalies = {}
            total_anomalies = 0
            
            for col in numeric_cols:
                if col in df.columns:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        # 使用IQR方法检测异常值
                        q1 = col_data.quantile(0.25)
                        q3 = col_data.quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        
                        # 识别异常值
                        outlier_mask = (col_data < lower_bound) | (col_data > upper_bound)
                        outlier_count = outlier_mask.sum()
                        outlier_percentage = (outlier_count / len(col_data)) * 100
                        
                        if outlier_count > 0:
                            anomalies[col] = {
                                'count': int(outlier_count),
                                'percentage': outlier_percentage,
                                'lower_bound': lower_bound,
                                'upper_bound': upper_bound,
                                'outliers': col_data[outlier_mask].tolist()[:10]  # 只返回前10个异常值
                            }
                            total_anomalies += outlier_count
            
            return {
                'detected': len(anomalies) > 0,
                'anomalies': anomalies,
                'total_anomalies': total_anomalies,
                'message': f'检测到 {len(anomalies)} 列存在异常值' if len(anomalies) > 0 else '未检测到异常值'
            }
        except Exception as e:
            return {
                'detected': False,
                'anomalies': {},
                'error': str(e),
                'message': f'检测失败: {str(e)}'
            }
    
    def detect_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检测缺失值
        
        Args:
            df: 数据框
            
        Returns:
            dict: 检测结果
        """
        try:
            missing_info = {}
            total_missing = 0
            
            for col in df.columns:
                missing_count = df[col].isna().sum()
                missing_percentage = (missing_count / len(df)) * 100
                
                if missing_count > 0:
                    missing_info[col] = {
                        'count': int(missing_count),
                        'percentage': missing_percentage
                    }
                    total_missing += missing_count
            
            return {
                'detected': len(missing_info) > 0,
                'missing_info': missing_info,
                'total_missing': total_missing,
                'message': f'检测到 {len(missing_info)} 列存在缺失值' if len(missing_info) > 0 else '未检测到缺失值'
            }
        except Exception as e:
            return {
                'detected': False,
                'missing_info': {},
                'error': str(e),
                'message': f'检测失败: {str(e)}'
            }
    
    def run_comprehensive_qa(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        运行综合数据质量检验
        
        Args:
            df: 数据框
            
        Returns:
            dict: 综合检验结果
        """
        try:
            # 1. 基本信息
            basic_info = {
                'rows': len(df),
                'columns': len(df.columns),
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object', 'category']).columns.tolist()
            }
            
            # 2. 缺失值检测
            missing_result = self.detect_missing_values(df)
            
            # 3. 异常值检测
            numeric_cols = basic_info['numeric_columns']
            anomaly_result = self.detect_anomalies(df, numeric_cols)
            
            # 4. 数据质量评分
            data_quality_score = self._calculate_data_quality_score(
                basic_info['rows'],
                missing_result['total_missing'],
                anomaly_result['total_anomalies']
            )
            
            return {
                'success': True,
                'basic_info': basic_info,
                'missing_values': missing_result,
                'anomalies': anomaly_result,
                'data_quality_score': data_quality_score,
                'message': f'数据质量检验完成，评分: {data_quality_score}/100'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'综合检验失败: {str(e)}'
            }
    
    def _calculate_data_quality_score(self, total_rows: int, total_missing: int, 
                                     total_anomalies: int) -> int:
        """
        计算数据质量评分
        
        Args:
            total_rows: 总行数
            total_missing: 总缺失值数
            total_anomalies: 总异常值数
            
        Returns:
            int: 数据质量评分 (0-100)
        """
        if total_rows == 0:
            return 0
        
        # 缺失值影响（权重40%）
        missing_ratio = total_missing / (total_rows * 10)  # 假设平均每列10个字段
        missing_penalty = min(40, missing_ratio * 100)
        
        # 异常值影响（权重30%）
        anomaly_ratio = total_anomalies / total_rows
        anomaly_penalty = min(30, anomaly_ratio * 100)
        
        # 基础分（30%）
        base_score = 30
        
        # 计算最终得分
        score = base_score + (40 - missing_penalty) + (30 - anomaly_penalty)
        return max(0, min(100, int(score)))

# 全局实例
data_qa_checker = DataQAChecker()

def detect_simpson_paradox(df: pd.DataFrame, group_col: str, metric_col: str, 
                          subgroup_col: str) -> Dict[str, Any]:
    """检测辛普森悖论的便捷函数"""
    return data_qa_checker.detect_simpson_paradox(df, group_col, metric_col, subgroup_col)

def detect_survivor_bias(df: pd.DataFrame, survival_col: str, 
                        metric_col: str) -> Dict[str, Any]:
    """检测幸存者偏差的便捷函数"""
    return data_qa_checker.detect_survivor_bias(df, survival_col, metric_col)

def detect_anomalies(df: pd.DataFrame, numeric_cols: List[str] = None) -> Dict[str, Any]:
    """检测异常值的便捷函数"""
    return data_qa_checker.detect_anomalies(df, numeric_cols)

def run_comprehensive_qa(df: pd.DataFrame) -> Dict[str, Any]:
    """运行综合数据质量检验的便捷函数"""
    return data_qa_checker.run_comprehensive_qa(df)
