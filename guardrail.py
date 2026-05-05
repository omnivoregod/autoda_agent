"""
数据校验模块
对分析结果进行质量校验和异常检测
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from field_semantic import analyze_field_semantics


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ValidationResult:
    """校验结果数据结构"""
    is_valid: bool
    risk_level: RiskLevel
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]


class Guardrail:
    """数据校验器 - 对分析结果进行质量校验和异常检测"""

    def __init__(self):
        self.validation_rules = self._init_validation_rules()

    def _init_validation_rules(self) -> Dict[str, Any]:
        """初始化校验规则"""
        return {
            'min_row_count': 3,
            'max_row_count': 100000,
            'max_null_percentage': 0.5,
            'max_outlier_zscore': 4.0,
            'min_conversion_rate': 0.0,
            'max_conversion_rate': 100.0
        }

    def validate(self, data: pd.DataFrame, analysis_result: Dict[str, Any]) -> ValidationResult:
        """
        对分析结果进行全面校验

        Args:
            data: 数据DataFrame
            analysis_result: 分析结果字典

        Returns:
            ValidationResult: 校验结果对象
        """
        issues = []
        warnings = []
        recommendations = []
        risk_level = RiskLevel.LOW

        # 1. 数据量校验
        row_count_issue = self._check_row_count(data)
        if row_count_issue:
            issues.append(row_count_issue)
            risk_level = RiskLevel.MEDIUM

        # 2. 空值校验
        null_issues = self._check_null_values(data)
        if null_issues:
            warnings.extend(null_issues)

        # 3. 异常值校验
        outlier_issues = self._check_outliers(data)
        if outlier_issues:
            warnings.extend(outlier_issues)

        # 4. 数据一致性校验
        consistency_issues = self._check_consistency(data, analysis_result)
        if consistency_issues:
            warnings.extend(consistency_issues)

        # 5. 分析类型特定校验
        if analysis_result.get('analysis_type'):
            type_specific_issues = self._check_type_specific(data, analysis_result)
            if type_specific_issues:
                issues.extend(type_specific_issues)
                risk_level = RiskLevel.HIGH

        # 6. 生成建议
        recommendations = self._generate_recommendations(issues, warnings, analysis_result)

        # 判断是否有效
        is_valid = len([i for i in issues if '严重' in i or '错误' in i]) == 0

        return ValidationResult(
            is_valid=is_valid,
            risk_level=risk_level,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations
        )

    def _check_row_count(self, data: pd.DataFrame) -> Optional[str]:
        """检查数据行数"""
        row_count = len(data)

        if row_count == 0:
            return "严重错误：数据为空，无法生成有效分析"
        elif row_count < self.validation_rules['min_row_count']:
            return f"警告：数据行数过少（{row_count}行），可能无法反映整体情况"
        elif row_count > self.validation_rules['max_row_count']:
            return f"警告：数据行数过多（{row_count}行），可能影响分析性能"

        return None

    def _check_null_values(self, data: pd.DataFrame) -> List[str]:
        """检查空值"""
        issues = []

        for col in data.columns:
            null_count = data[col].isnull().sum()
            null_percentage = null_count / len(data) if len(data) > 0 else 0

            if null_percentage > self.validation_rules['max_null_percentage']:
                issues.append(
                    f"字段「{col}」空值比例过高（{null_percentage*100:.1f}%），可能影响分析准确性"
                )
            elif null_count > 0:
                issues.append(
                    f"字段「{col}」存在{null_count}个空值"
                )

        return issues

    def _check_outliers(self, data: pd.DataFrame) -> List[str]:
        """检查异常值"""
        issues = []

        numeric_cols = data.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            values = data[col].dropna()
            if len(values) == 0:
                continue

            # 计算Z-score
            mean = values.mean()
            std = values.std()

            if std > 0:
                z_scores = np.abs((values - mean) / std)
                outlier_count = (z_scores > self.validation_rules['max_outlier_zscore']).sum()
                outlier_percentage = outlier_count / len(values)

                if outlier_percentage > 0.1:  # 超过10%的异常值
                    issues.append(
                        f"字段「{col}」存在{outlier_count}个异常值（占比{outlier_percentage*100:.1f}%），建议进行异常值检测"
                    )

        return issues

    def _check_consistency(self, data: pd.DataFrame, analysis_result: Dict[str, Any]) -> List[str]:
        """检查数据一致性"""
        issues = []

        # 检查分析类型与数据是否匹配
        analysis_type = analysis_result.get('analysis_type')

        if analysis_type == 'funnel':
            # 漏斗数据检查
            funnel_stages = analysis_result.get('funnel_stages', [])
            if len(funnel_stages) > 1:
                # 检查转化率是否递减
                for i in range(1, len(funnel_stages)):
                    prev_count = funnel_stages[i-1].get('count', 0)
                    curr_count = funnel_stages[i].get('count', 0)
                    if curr_count > prev_count:
                        issues.append(
                            f"漏斗阶段「{funnel_stages[i].get('name', i)}」用户数异常增长，可能存在数据问题"
                        )

        elif analysis_type == 'comparison':
            # 比较数据检查
            comparison_summary = analysis_result.get('comparison_summary', {})
            groups = comparison_summary.get('groups', [])

            if len(groups) > 0:
                total_count = sum(g.get('count', 0) for g in groups)
                if total_count == 0:
                    issues.append("比较分析中所有组别的数量为0，数据可能存在问题")

        elif analysis_type == 'trend':
            # 趋势数据检查
            trend_summary = analysis_result.get('trend_summary', {})
            start_value = trend_summary.get('start_value', 0)
            end_value = trend_summary.get('end_value', 0)

            if start_value == 0 and end_value == 0:
                issues.append("趋势分析中起始值和结束值都为0，数据可能存在问题")

        return issues

    def _check_type_specific(self, data: pd.DataFrame, analysis_result: Dict[str, Any]) -> List[str]:
        """检查分析类型特定的问题"""
        issues = []
        analysis_type = analysis_result.get('analysis_type')

        if analysis_type == 'funnel':
            funnel_stages = analysis_result.get('funnel_stages', [])

            # 检查是否缺少必要的漏斗阶段
            if len(funnel_stages) < 2:
                issues.append("严重错误：漏斗分析需要至少2个阶段，数据不完整")

            # 检查转化率是否在合理范围
            for stage in funnel_stages:
                rate = stage.get('conversion_rate', 0)
                if rate < self.validation_rules['min_conversion_rate'] or rate > self.validation_rules['max_conversion_rate']:
                    issues.append(
                        f"严重错误：漏斗阶段「{stage.get('name', 'unknown')}」转化率异常（{rate}%）"
                    )

        elif analysis_type == 'rfm':
            # 检查RFM分析结果是否包含segments（实际返回的结构）
            if 'segments' not in analysis_result:
                # 尝试检查原始数据是否包含RFM所需字段
                required_columns = ['recency', 'frequency', 'monetary', 'recency_days', 'r_score', 'f_score', 'm_score']
                data_columns = data.columns.tolist() if data is not None else []
                has_rfm_fields = any(col in data_columns for col in required_columns)
                
                if not has_rfm_fields:
                    issues.append("严重错误：RFM分析缺少必要维度数据")
            # 对于RFM分析，只要有segments或相关字段就认为有效
            # 不再严格要求rfm_summary结构

        elif analysis_type == 'ab_test':
            # 检查A/B测试特定问题
            issues.extend(self._check_ab_test_issues(data, analysis_result))

        return issues

    def _check_ab_test_issues(self, data: pd.DataFrame, analysis_result: Dict[str, Any]) -> List[str]:
        """检查A/B测试特定问题"""
        issues = []

        # 检查是否至少有两组进行比较
        if 'group' in data.columns:
            groups = data['group'].unique()
            if len(groups) < 2:
                issues.append("严重错误：A/B测试需要至少两组数据进行比较")

            # 检查样本量是否足够
            group_counts = data['group'].value_counts()
            for group, count in group_counts.items():
                if count < 30:
                    issues.append(
                        f"警告：组别「{group}」样本量过少（{count}），统计结果可能不可靠"
                    )

            # 检查SRM（比例异常）
            srm_issue = self._check_srm(group_counts)
            if srm_issue:
                issues.append(srm_issue)

        else:
            issues.append("严重错误：A/B测试数据缺少'group'字段")

        return issues

    def _check_srm(self, group_counts: pd.Series) -> Optional[str]:
        """检查A/B测试的SRM（比例异常）"""
        if len(group_counts) < 2:
            return None

        # 计算各组比例
        total = group_counts.sum()
        expected = total / len(group_counts)
        max_deviation = max(abs(count - expected) for count in group_counts)
        deviation_percentage = (max_deviation / expected) * 100

        # SRM阈值：通常认为超过5%的偏差需要关注
        if deviation_percentage > 5:
            return f"警告：A/B测试存在SRM比例异常，最大偏差为{deviation_percentage:.1f}%"

        return None

    def validate_with_dsl_sql(self, dsl: Dict[str, Any], sql: str, analysis_result: Dict[str, Any], data: pd.DataFrame, user_input: Optional[str] = None) -> Dict[str, Any]:
        """
        企业级关键检查 - 检查分析过程

        Args:
            dsl: DSL语句
            sql: SQL查询
            analysis_result: 分析结果
            data: 分析数据
            user_input: 用户输入（可选）

        Returns:
            Dict: 检查结果
        """
        issues = []

        # 1. 检查数据与用户问题的匹配性
        if user_input and data is not None:
            match_issues = self._check_data_match(user_input, data)
            issues.extend(match_issues)

        # 2. 检查字段错误
        field_issues = self._check_field_errors(dsl, sql, data)
        issues.extend(field_issues)

        # 3. 检查样本量是否过小
        sample_issue = self._check_sample_size(data, analysis_result)
        if sample_issue:
            issues.append(sample_issue)

        # 4. 检查A/B测试是否存在SRM
        if analysis_result.get('analysis_type') == 'ab_test':
            srm_issue = self._check_ab_srm(data)
            if srm_issue:
                issues.append(srm_issue)

        # 5. 检查是否存在明显逻辑错误
        logic_issues = self._check_logic_errors(analysis_result, data)
        issues.extend(logic_issues)

        # 6. 检查数据质量
        quality_issues = self._check_data_quality_issues(data)
        issues.extend(quality_issues)

        # 7. 检查分析结果的合理性
        result_issues = self._check_result_reasonability(analysis_result)
        issues.extend(result_issues)

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def _check_field_errors(self, dsl: Dict[str, Any], sql: str, data: pd.DataFrame) -> List[str]:
        """检查字段错误"""
        issues = []

        # 检查DSL中定义的字段是否存在于数据中
        if 'dimensions' in dsl:
            for dimension in dsl['dimensions']:
                if dimension not in data.columns:
                    issues.append(f"字段错误：DSL中定义的维度字段「{dimension}」不存在于数据中")

        # 检查SQL中使用的字段是否存在于数据中
        # 更准确的字段提取逻辑
        import re
        
        # 提取SELECT子句中的字段
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if select_match:
            select_clause = select_match.group(1)
            
            # 分割SELECT子句中的字段
            fields = [field.strip() for field in select_clause.split(',')]
            
            # 过滤掉SQL关键字和常见函数名
            sql_keywords = {
                'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'LIMIT', 
                'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'AS', 'AND', 'OR', 'NOT',
                'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
                'DATE', 'NOW', 'DATEDIFF', 'TIMESTAMP', 'STRFTIME'
            }
            data_fields = set(data.columns)

            for field in fields:
                # 提取字段名，排除别名和函数
                field_parts = field.split(' ')
                # 找到实际的字段名
                actual_field = None
                for part in field_parts:
                    part = part.strip()
                    if part.lower() not in sql_keywords and not part.startswith('(') and not part.endswith(')'):
                        # 检查是否是函数调用
                        if '(' in part or ')' in part:
                            continue
                        # 检查是否是别名
                        if part.lower() == 'as':
                            break
                        actual_field = part
                        break
                
                if actual_field:
                    # 处理表名.字段名格式
                    if '.' in actual_field:
                        actual_field = actual_field.split('.')[-1]
                    
                    # 检查字段是否存在
                    if actual_field not in data_fields:
                        # 忽略聚合函数的结果字段（如count、avg等）
                        if actual_field not in ['count', 'avg', 'sum', 'max', 'min']:
                            issues.append(f"字段错误：SQL中使用的字段「{actual_field}」不存在于数据中")

        return issues

    def _check_data_match(self, user_input: str, data: pd.DataFrame) -> List[str]:
        """检查数据与用户问题的匹配性"""
        issues = []

        if data is None or data.empty:
            issues.append("严重错误：数据为空，无法生成有效分析")
            return issues

        # 分析数据字段语义
        data_fields = data.columns.tolist()
        field_semantics = analyze_field_semantics(data_fields)

        # 分析用户问题中可能需要的字段类型
        required_field_types = self._extract_required_fields(user_input)

        # 字段类型映射
        field_type_mappings = {
            '用户标识': ['用户标识', '用户维度', 'customer', 'user', 'customer_id', 'user_id'],
            '订单标识': ['订单标识', '交易维度', 'order', 'id', 'order_id'],
            '交易时间': ['时间维度', '交易维度', 'time', 'date', 'order_time', 'created_at', 'order_date', 'timestamp'],
            '交易金额': ['交易金额', '交易维度', 'amount', 'total', 'usd', 'total_usd', 'subtotal_usd', 'transaction_amount', 'amount_usd'],
            '订单状态': ['状态维度', 'status', 'order_status', 'refund_status'],
            '商品数量': ['数量', '交易维度', 'quantity', 'qty', 'item_count', 'item_quantity'],
            '时间维度': ['时间维度', 'time', 'date', 'order_time', 'created_at', 'timestamp'],
            '用户维度': ['用户维度', 'customer', 'user', 'customer_id'],
            '交易维度': ['交易维度', 'order', 'amount', 'total', 'order_id', 'total_usd'],
            '商品维度': ['商品维度', 'product', 'item', 'product_id'],
            '状态维度': ['状态维度', 'status', 'order_status'],
            '事件类型': ['事件类型', 'event_type', 'action', 'event'],
            '会话标识': ['会话标识', 'session_id', 'session']
        }

        # 检查是否缺少必要的字段类型
        missing_field_types = []
        for field_type, required in required_field_types.items():
            if required:
                # 检查是否有匹配的字段
                has_field = False
                
                # 检查字段语义
                for sem in field_semantics.values():
                    if (
                        sem['category'] == field_type or 
                        sem['main_dimension'] == field_type or
                        field_type in sem['description'] or
                        field_type in sem['analysis_angle'] or
                        # 检查映射关系
                        any(mapped_type in [sem['category'], sem['main_dimension']] 
                            for mapped_type in field_type_mappings.get(field_type, []))
                    ):
                        has_field = True
                        break
                
                # 如果语义检查失败，检查实际字段名
                if not has_field:
                    for field in data_fields:
                        field_lower = field.lower()
                        # 检查字段名是否包含映射的关键词
                        if any(keyword in field_lower for keyword in field_type_mappings.get(field_type, [])):
                            has_field = True
                            break
                
                if not has_field:
                    missing_field_types.append(field_type)

        # 只有在确实缺少必要字段时才返回错误
        # 但要注意：即使缺少某些字段，只要数据中包含足够的信息来回答用户的核心问题，就不应该返回错误
        # 例如：如果用户要求分析销售趋势，只要有交易时间和交易金额，就可以进行分析
        if missing_field_types:
            # 检查是否有足够的字段来回答用户的核心问题
            user_input_lower = user_input.lower()
            
            # 销售概览相关：需要交易金额和时间维度
            if any(keyword in user_input_lower for keyword in ['销售概览', '销售额', '销售分析', '总订单量', '总销售额', '总销量', '平均客单价', '平均订单商品数']):
                has_sales_fields = False
                # 检查是否有交易金额和时间维度
                for field_type in ['交易金额', '时间维度']:
                    for field in data_fields:
                        field_lower = field.lower()
                        if any(keyword in field_lower for keyword in field_type_mappings.get(field_type, [])):
                            has_sales_fields = True
                            break
                    if not has_sales_fields:
                        break
                if has_sales_fields:
                    # 有足够的字段进行销售概览分析
                    pass
                else:
                    # 生成详细的错误信息，包括实际可用的字段
                    available_fields = []
                    for field, sem in field_semantics.items():
                        available_fields.append(f"{field} ({sem['category']})")
                    
                    issues.append(f"严重错误：缺少必要的字段类型：{', '.join(missing_field_types)}。可用字段：{', '.join(available_fields)}")
            # 时段分析相关：需要交易时间
            elif any(keyword in user_input_lower for keyword in ['时段分析', '时间分析', '趋势分析', '高峰时段', '最佳时间段', '最差时间段', '月度趋势']):
                has_time_field = False
                for field in data_fields:
                    field_lower = field.lower()
                    if any(keyword in field_lower for keyword in field_type_mappings.get('交易时间', [])):
                        has_time_field = True
                        break
                if has_time_field:
                    # 有足够的字段进行时段分析
                    pass
                else:
                    # 生成详细的错误信息，包括实际可用的字段
                    available_fields = []
                    for field, sem in field_semantics.items():
                        available_fields.append(f"{field} ({sem['category']})")
                    
                    issues.append(f"严重错误：缺少必要的字段类型：{', '.join(missing_field_types)}。可用字段：{', '.join(available_fields)}")
            # 退款分析相关：需要订单状态和交易金额
            elif any(keyword in user_input_lower for keyword in ['退款分析', '退货分析', '退款率', '取消订单', '退款金额', '退款占比', '退款高发原因']):
                has_refund_fields = False
                # 检查是否有订单状态和交易金额
                for field_type in ['订单状态', '交易金额']:
                    for field in data_fields:
                        field_lower = field.lower()
                        if any(keyword in field_lower for keyword in field_type_mappings.get(field_type, [])):
                            has_refund_fields = True
                            break
                    if not has_refund_fields:
                        break
                if has_refund_fields:
                    # 有足够的字段进行退款分析
                    pass
                else:
                    # 生成详细的错误信息，包括实际可用的字段
                    available_fields = []
                    for field, sem in field_semantics.items():
                        available_fields.append(f"{field} ({sem['category']})")
                    
                    issues.append(f"严重错误：缺少必要的字段类型：{', '.join(missing_field_types)}。可用字段：{', '.join(available_fields)}")
            # 新老客对比相关：需要用户标识和交易时间
            elif any(keyword in user_input_lower for keyword in ['新老客对比', '新客', '老客', '用户分层']):
                has_user_fields = False
                # 检查是否有用户标识和交易时间
                for field_type in ['用户标识', '交易时间']:
                    for field in data_fields:
                        field_lower = field.lower()
                        if any(keyword in field_lower for keyword in field_type_mappings.get(field_type, [])):
                            has_user_fields = True
                            break
                    if not has_user_fields:
                        break
                if has_user_fields:
                    # 有足够的字段进行新老客对比分析
                    pass
                else:
                    # 生成详细的错误信息，包括实际可用的字段
                    available_fields = []
                    for field, sem in field_semantics.items():
                        available_fields.append(f"{field} ({sem['category']})")
                    
                    issues.append(f"严重错误：缺少必要的字段类型：{', '.join(missing_field_types)}。可用字段：{', '.join(available_fields)}")
            # 流量与用户行为转化相关：需要事件类型和会话标识
            elif any(keyword in user_input_lower for keyword in ['流量', '用户行为', '转化', '漏斗', '会话', '加购率', '转化率', '转化漏斗']):
                # 特殊处理：检查数据库中是否存在events表，并且包含必要的字段
                import sqlite3
                has_event_fields = False
                try:
                    conn = sqlite3.connect('ecommerce.db')
                    cursor = conn.cursor()
                    
                    # 检查events表是否存在
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
                    if cursor.fetchone():
                        # 检查events表是否包含必要的字段
                        cursor.execute("PRAGMA table_info(events)")
                        columns = cursor.fetchall()
                        event_columns = [col[1].lower() for col in columns]
                        
                        # 检查是否包含event_type和session_id字段
                        if 'event_type' in event_columns and 'session_id' in event_columns:
                            has_event_fields = True
                    conn.close()
                except Exception:
                    # 数据库操作失败，使用默认检查
                    pass
                
                # 如果数据库检查失败，使用传统的字段检查
                if not has_event_fields:
                    has_event_fields = False
                    # 检查是否有事件类型和会话标识
                    for field_type in ['事件类型', '会话标识']:
                        for field in data_fields:
                            field_lower = field.lower()
                            if any(keyword in field_lower for keyword in field_type_mappings.get(field_type, [])):
                                has_event_fields = True
                                break
                        if not has_event_fields:
                            break
                
                if has_event_fields:
                    # 有足够的字段进行流量与用户行为转化分析
                    # 清空missing_field_types，因为我们已经确认数据库中有必要的字段
                    missing_field_types = []
                else:
                    # 生成详细的错误信息，包括实际可用的字段
                    available_fields = []
                    for field, sem in field_semantics.items():
                        available_fields.append(f"{field} ({sem['category']})")
                    
                    issues.append(f"严重错误：缺少必要的字段类型：{', '.join(missing_field_types)}。可用字段：{', '.join(available_fields)}")
            # 其他情况
            else:
                # 生成详细的错误信息，包括实际可用的字段
                available_fields = []
                for field, sem in field_semantics.items():
                    available_fields.append(f"{field} ({sem['category']})")
                
                issues.append(f"严重错误：缺少必要的字段类型：{', '.join(missing_field_types)}。可用字段：{', '.join(available_fields)}")

        return issues

    def _extract_required_fields(self, user_input: str) -> Dict[str, bool]:
        """从用户问题中提取所需的字段类型"""
        required_fields = {
            '用户标识': False,
            '订单标识': False,
            '交易时间': False,
            '交易金额': False,
            '订单状态': False,
            '商品数量': False,
            '用户维度': False,
            '交易维度': False,
            '时间维度': False,
            '商品维度': False,
            '状态维度': False,
            '事件类型': False,
            '会话标识': False
        }

        # 分析用户问题
        user_input_lower = user_input.lower()

        # 销售概览相关
        if any(keyword in user_input_lower for keyword in ['销售概览', '销售额', '销售分析', '总订单量', '总销售额', '总销量', '平均客单价', '平均订单商品数']):
            required_fields['交易金额'] = True
            required_fields['时间维度'] = True
            required_fields['订单标识'] = True
            required_fields['商品数量'] = True

        # 时段分析相关
        if any(keyword in user_input_lower for keyword in ['时段分析', '时间分析', '趋势分析', '高峰时段', '最佳时间段', '最差时间段', '月度趋势']):
            required_fields['交易时间'] = True

        # 退款分析相关
        if any(keyword in user_input_lower for keyword in ['退款分析', '退货分析', '退款率', '取消订单', '退款金额', '退款占比', '退款高发原因']):
            required_fields['订单状态'] = True
            required_fields['交易金额'] = True

        # 新老客对比相关
        if any(keyword in user_input_lower for keyword in ['新老客对比', '新客', '老客', '用户分层']):
            required_fields['用户标识'] = True
            required_fields['交易时间'] = True

        # RFM分析相关
        if any(keyword in user_input_lower for keyword in ['rfm', '用户价值', '用户分层']):
            required_fields['用户标识'] = True
            required_fields['交易时间'] = True
            required_fields['交易金额'] = True

        # 订单相关
        if any(keyword in user_input_lower for keyword in ['订单', '交易', '购买']):
            required_fields['订单标识'] = True
            required_fields['交易金额'] = True

        # 流量与用户行为转化相关
        if any(keyword in user_input_lower for keyword in ['流量', '用户行为', '转化', '漏斗', '会话', '加购率', '转化率', '转化漏斗']):
            required_fields['事件类型'] = True
            required_fields['会话标识'] = True
            required_fields['交易时间'] = True

        return required_fields

    def _check_sample_size(self, data: pd.DataFrame, analysis_result: Dict[str, Any]) -> Optional[str]:
        """检查样本量是否过小"""
        row_count = len(data)

        if row_count == 0:
            return "样本量错误：数据为空，无法进行分析"
        elif row_count < 10:
            return "样本量错误：数据样本量过小（小于10条），分析结果可能不可靠"
        elif row_count < 30:
            return "样本量警告：数据样本量较小（小于30条），建议增加样本量以提高统计显著性"

        return None

    def _check_ab_srm(self, data: pd.DataFrame) -> Optional[str]:
        """检查A/B测试是否存在SRM"""
        if 'group' in data.columns:
            group_counts = data['group'].value_counts()
            return self._check_srm(group_counts)
        return None

    def _check_logic_errors(self, analysis_result: Dict[str, Any], data: pd.DataFrame) -> List[str]:
        """检查是否存在明显逻辑错误"""
        issues = []

        # 检查分析类型与数据是否匹配
        analysis_type = analysis_result.get('analysis_type')

        if analysis_type == 'funnel':
            # 检查漏斗阶段是否递减
            funnel_stages = analysis_result.get('funnel_stages', [])
            for i in range(1, len(funnel_stages)):
                prev_count = funnel_stages[i-1].get('count', 0)
                curr_count = funnel_stages[i].get('count', 0)
                if curr_count > prev_count:
                    issues.append("逻辑错误：漏斗阶段用户数不应递增")

        elif analysis_type == 'ab_test':
            # 检查转化率是否在合理范围
            conversion_a = analysis_result.get('conversion_A', 0)
            conversion_b = analysis_result.get('conversion_B', 0)
            if conversion_a < 0 or conversion_a > 1 or conversion_b < 0 or conversion_b > 1:
                issues.append("逻辑错误：转化率应在0-1之间")

        # 检查数据一致性
        if data is not None and not data.empty:
            # 检查数值字段是否有负值（根据业务逻辑）
            numeric_cols = data.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if col.lower() in ['revenue', 'sales', 'amount', 'count']:
                    if (data[col] < 0).any():
                        issues.append(f"逻辑错误：字段「{col}」不应包含负值")

        return issues

    def _check_data_quality_issues(self, data: pd.DataFrame) -> List[str]:
        """检查数据质量问题"""
        issues = []

        # 检查空值比例
        if len(data) > 0:
            total_cells = data.size
            null_cells = data.isnull().sum().sum()
            null_percentage = (null_cells / total_cells) * 100
            if null_percentage > 50:
                issues.append(f"数据质量问题：数据空值比例过高（{null_percentage:.1f}%）")

        # 检查重复行
        duplicate_rows = data.duplicated().sum()
        if duplicate_rows > 0:
            issues.append(f"数据质量问题：存在{duplicate_rows}条重复记录")

        return issues

    def _check_result_reasonability(self, analysis_result: Dict[str, Any]) -> List[str]:
        """检查分析结果的合理性"""
        issues = []

        # 检查分析结果是否为空
        if not analysis_result:
            issues.append("分析结果问题：分析结果为空")

        # 检查关键指标是否合理
        analysis_type = analysis_result.get('analysis_type')

        if analysis_type == 'ltv_roi':
            metrics = analysis_result.get('metrics', {})
            roi = metrics.get('roi', 0)
            if roi > 10:  # ROI超过1000%可能不合理
                issues.append("分析结果问题：ROI值过高，可能存在数据异常")

        elif analysis_type == 'trend':
            trend_summary = analysis_result.get('trend_summary', {})
            change_rate = trend_summary.get('change_rate', 0)
            if abs(change_rate) > 100:
                issues.append("分析结果问题：趋势变化率过大，可能存在数据异常")

        return issues

    def _generate_recommendations(self, issues: List[str], warnings: List[str], analysis_result: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于问题生成建议
        for issue in issues:
            if '数据为空' in issue:
                recommendations.append("建议：检查数据上传是否成功，或数据文件是否包含有效记录")
            elif '数据行数过少' in issue:
                recommendations.append("建议：扩大数据时间范围或筛选条件，以获取更多样本")
            elif '空值比例过高' in issue:
                recommendations.append("建议：清理或填补缺失数据，或调整分析维度")
            elif '严重错误' in issue:
                recommendations.append("建议：修复数据问题后重新进行分析")

        # 基于分析类型生成建议
        analysis_type = analysis_result.get('analysis_type')

        if analysis_type == 'funnel':
            recommendations.append("建议：结合用户行为路径，优化转化率较低的漏斗阶段")
            recommendations.append("建议：关注各阶段的流失原因，进行针对性改进")

        elif analysis_type == 'rfm':
            recommendations.append("建议：根据用户分层结果，制定差异化的营销策略")
            recommendations.append("建议：重点关注低价值用户群体，制定激活计划")

        elif analysis_type == 'ab_test':
            recommendations.append("建议：确保实验组和对照组样本量足够，以保证统计显著性")
            recommendations.append("建议：持续跟踪实验结果，避免短期波动影响判断")

        elif analysis_type == 'trend':
            recommendations.append("建议：分析趋势变化的原因，制定相应的业务策略")
            recommendations.append("建议：关注季节性因素，设置合理的对比基准")

        elif analysis_type == 'comparison':
            recommendations.append("建议：深入分析不同组别差异的根本原因")
            recommendations.append("建议：针对表现较差的组别，制定改进计划")

        return recommendations if recommendations else ["当前数据质量良好，未发现明显问题"]

    def check_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        快速检查数据质量

        Args:
            data: 数据DataFrame

        Returns:
            Dict: 数据质量报告
        """
        quality_report = {
            'total_rows': len(data),
            'total_columns': len(data.columns),
            'columns': list(data.columns),
            'column_types': {},
            'null_counts': {},
            'null_percentages': {},
            'numeric_summary': {},
            'quality_score': 0
        }

        # 统计各列类型和空值
        for col in data.columns:
            quality_report['column_types'][col] = str(data[col].dtype)
            null_count = data[col].isnull().sum()
            quality_report['null_counts'][col] = int(null_count)
            quality_report['null_percentages'][col] = round(null_count / len(data) * 100, 2) if len(data) > 0 else 0

            # 数值列统计
            if pd.api.types.is_numeric_dtype(data[col]):
                numeric_values = data[col].dropna()
                if len(numeric_values) > 0:
                    quality_report['numeric_summary'][col] = {
                        'mean': round(numeric_values.mean(), 2),
                        'median': round(numeric_values.median(), 2),
                        'min': round(numeric_values.min(), 2),
                        'max': round(numeric_values.max(), 2),
                        'std': round(numeric_values.std(), 2) if len(numeric_values) > 1 else 0
                    }

        # 计算质量分数
        quality_score = 100

        # 扣分项
        if quality_report['total_rows'] < 10:
            quality_score -= 20

        avg_null_pct = sum(quality_report['null_percentages'].values()) / len(quality_report['null_percentages']) if quality_report['null_percentages'] else 0
        if avg_null_pct > 10:
            quality_score -= int(avg_null_pct / 2)

        quality_report['quality_score'] = max(0, quality_score)

        return quality_report


def validate_analysis_result(data: pd.DataFrame, analysis_result: Dict[str, Any]) -> ValidationResult:
    """
    快速校验分析结果

    Args:
        data: 数据DataFrame
        analysis_result: 分析结果字典

    Returns:
        ValidationResult: 校验结果对象
    """
    guardrail = Guardrail()
    return guardrail.validate(data, analysis_result)