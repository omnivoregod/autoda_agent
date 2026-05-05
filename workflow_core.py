"""
工作流核心模块
实现Planner、Clarifier、DSL Generator三个核心组件
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AnalysisType(Enum):
    """分析类型枚举"""
    TREND = "趋势分析"
    DISTRIBUTION = "分布分析"
    COMPARISON = "比较分析"
    CORRELATION = "关联分析"
    FUNNEL = "漏斗分析"
    RFM = "RFM分析"
    AB_TEST = "A/B测试"
    SEGMENTATION = "分层分析"
    CUSTOM = "自定义分析"


@dataclass
class AnalysisTask:
    """分析任务数据结构"""
    task_id: str
    original_input: str
    analysis_type: AnalysisType
    target_fields: List[str]
    filters: Dict[str, Any]
    group_by: Optional[List[str]]
    metrics: List[str]
    time_range: Optional[Dict[str, str]]
    business_context: str
    requires_clarification: bool
    clarification_questions: List[str]
    data_source: Optional[str] = None


@dataclass
class ClarifiedInfo:
    """补全后的信息"""
    confirmed_fields: List[str]
    additional_context: Dict[str, Any]
    confirmed_filters: Dict[str, Any]
    confirmed_metrics: List[str]


@dataclass
class DSLStatement:
    """标准分析语言数据结构"""
    dsl_type: str
    operation: str
    source: str
    dimensions: List[str]
    measures: List[str]
    filters: List[str]
    order_by: Optional[List[str]]
    limit: Optional[int]


class Planner:
    """任务拆解器 - 将用户输入拆解为结构化任务"""

    def __init__(self):
        self.task_counter = 0

    def parse(self, user_input: str, db_schema: Dict[str, Any]) -> AnalysisTask:
        """
        解析用户输入，生成分析任务

        Args:
            user_input: 用户输入的自然语言
            db_schema: 数据库schema信息

        Returns:
            AnalysisTask: 结构化的分析任务
        """
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"

        # 识别分析类型
        analysis_type = self._identify_analysis_type(user_input)

        # 提取目标字段
        target_fields = self._extract_fields(user_input, db_schema)

        # 提取过滤条件
        filters = self._extract_filters(user_input)

        # 提取分组字段
        group_by = self._extract_group_by(user_input)

        # 提取指标
        metrics = self._extract_metrics(user_input)

        # 提取时间范围
        time_range = self._extract_time_range(user_input)

        # 判断是否需要信息补全
        requires_clarification, clarification_questions = self._check_clarification_needed(
            user_input, target_fields, metrics
        )

        # 提取业务上下文
        business_context = self._extract_business_context(user_input)

        # 提取数据源
        data_source = self._extract_data_source(user_input, db_schema)

        return AnalysisTask(
            task_id=task_id,
            original_input=user_input,
            analysis_type=analysis_type,
            target_fields=target_fields,
            filters=filters,
            group_by=group_by,
            metrics=metrics,
            time_range=time_range,
            business_context=business_context,
            requires_clarification=requires_clarification,
            clarification_questions=clarification_questions,
            data_source=data_source
        )

    def _identify_analysis_type(self, user_input: str) -> AnalysisType:
        """识别分析类型"""
        input_lower = user_input.lower()

        if any(keyword in input_lower for keyword in ['漏斗', '转化', 'funnel', 'conversion']):
            return AnalysisType.FUNNEL
        elif any(keyword in input_lower for keyword in ['rfm', '用户分层', '用户价值', '用户分群']):
            return AnalysisType.RFM
        elif any(keyword in input_lower for keyword in ['ab', 'a/b', '测试', '实验']):
            return AnalysisType.AB_TEST
        elif any(keyword in input_lower for keyword in ['趋势', '变化', '增长', 'trend', 'time']):
            return AnalysisType.TREND
        elif any(keyword in input_lower for keyword in ['分布', '占比', '构成', 'distribution', '占比']):
            return AnalysisType.DISTRIBUTION
        elif any(keyword in input_lower for keyword in ['比较', '对比', '差异', 'compare', '对比']):
            return AnalysisType.COMPARISON
        elif any(keyword in input_lower for keyword in ['关联', '相关', 'correlation', 'relationship']):
            return AnalysisType.CORRELATION
        else:
            return AnalysisType.CUSTOM

    def _extract_fields(self, user_input: str, db_schema: Dict[str, Any]) -> List[str]:
        """提取目标字段"""
        fields = []
        input_lower = user_input.lower()

        # 字段映射表
        field_mapping = {
            '年龄': ['age', 'customer_age'],
            '折扣': ['discount_pct', 'discount_amount'],
            '金额': ['total_usd', 'amount', 'monetary'],
            '订单': ['order_id', 'order_time', 'order_count'],
            '时间': ['order_time', 'timestamp', 'create_time'],
            '品类': ['category', 'product_category'],
            '产品': ['product_id', 'product_name'],
            '客户': ['customer_id', 'user_id'],
            '地区': ['country', 'region', 'city'],
            '设备': ['device', 'platform'],
            '来源': ['source', 'traffic_source']
        }

        # 根据用户输入的关键词提取字段
        for ch_keyword, en_keywords in field_mapping.items():
            if ch_keyword in user_input or any(kw in input_lower for kw in en_keywords):
                for db_field in db_schema.get('all_fields', []):
                    field_lower = db_field.lower()
                    if any(kw in field_lower for kw in en_keywords):
                        if db_field not in fields:
                            fields.append(db_field)

        return fields

    def _extract_filters(self, user_input: str) -> Dict[str, Any]:
        """提取过滤条件"""
        filters = {}
        input_lower = user_input.lower()

        # 提取时间过滤
        if '最近' in user_input:
            time_match = re.search(r'最近(\d+)(天|周|月|年)', user_input)
            if time_match:
                filters['time_range'] = f"last_{time_match.group(1)}_{time_match.group(2)}"

        # 提取数值过滤
        if '大于' in user_input or '>' in user_input:
            gt_match = re.search(r'大于(\d+\.?\d*)', user_input)
            if gt_match:
                filters['min_value'] = float(gt_match.group(1))

        if '小于' in user_input or '<' in user_input:
            lt_match = re.search(r'小于(\d+\.?\d*)', user_input)
            if lt_match:
                filters['max_value'] = float(lt_match.group(1))

        # 提取类别过滤
        if '年龄段' in user_input:
            age_group_match = re.search(r'(\d+)-(\d+)岁', user_input)
            if age_group_match:
                filters['age_group'] = {
                    'min': int(age_group_match.group(1)),
                    'max': int(age_group_match.group(2))
                }

        return filters

    def _extract_group_by(self, user_input: str) -> Optional[List[str]]:
        """提取分组字段"""
        group_by = None
        input_lower = user_input.lower()

        if '按' in user_input or '按照' in user_input:
            # 提取"按X分组"中的X
            match = re.search(r'按(\w+)分组', user_input)
            if match:
                group_by_field = match.group(1)
                # 映射到实际字段
                field_mapping = {
                    '年龄': 'age',
                    '品类': 'category',
                    '地区': 'country',
                    '设备': 'device',
                    '来源': 'source',
                    '时间': 'order_time'
                }
                if group_by_field in field_mapping:
                    group_by = [field_mapping[group_by_field]]

        return group_by

    def _extract_metrics(self, user_input: str) -> List[str]:
        """提取指标"""
        metrics = []
        input_lower = user_input.lower()

        if any(keyword in input_lower for keyword in ['数量', 'count', '次数']):
            metrics.append('count')
        if any(keyword in input_lower for keyword in ['金额', '销售额', '收入', 'amount', 'revenue', 'sales']):
            metrics.append('sum')
        if any(keyword in input_lower for keyword in ['平均', 'avg', '客单价']):
            metrics.append('avg')
        if any(keyword in input_lower for keyword in ['转化率', 'conversion rate']):
            metrics.append('conversion_rate')
        if any(keyword in input_lower for keyword in ['占比', 'percentage', '比率']):
            metrics.append('percentage')

        # 如果没有识别到指标，提供默认指标
        if not metrics:
            metrics = ['count', 'avg']

        return metrics

    def _extract_time_range(self, user_input: str) -> Optional[Dict[str, str]]:
        """提取时间范围"""
        time_range = None

        if '最近' in user_input:
            time_match = re.search(r'最近(\d+)(天|周|月|年)', user_input)
            if time_match:
                time_range = {
                    'type': 'recent',
                    'value': time_match.group(1),
                    'unit': time_match.group(2)
                }

        return time_range

    def _check_clarification_needed(self, user_input: str, fields: List[str], metrics: List[str]) -> tuple:
        """检查是否需要信息补全"""
        questions = []

        # 字段不足
        if len(fields) < 2 and '分析' in user_input:
            questions.append("您想分析哪些维度和指标？")

        # 指标不足
        if not metrics:
            questions.append("您想了解哪些具体的指标？")

        return len(questions) > 0, questions

    def _extract_business_context(self, user_input: str) -> str:
        """提取业务上下文"""
        # 移除疑问词和分析动词，保留业务含义
        context = user_input
        remove_patterns = [
            r'怎么', r'如何', r'为什么', r'是什么', r'分析',
            r'看一下', r'查看', r'查看', r'了解', r'看看'
        ]
        for pattern in remove_patterns:
            context = re.sub(pattern, '', context)

        return context.strip()

    def _extract_data_source(self, user_input: str, db_schema: Dict[str, Any]) -> Optional[str]:
        """提取数据源"""
        input_lower = user_input.lower()
        tables = db_schema.get('tables', {}).keys()
        
        # 检查用户输入中是否包含表名
        for table in tables:
            if table.lower() in input_lower:
                return table
        
        # 根据分析类型推断默认数据源
        if 'funnel' in input_lower or '转化' in user_input:
            return 'events'
        elif 'rfm' in input_lower or '用户' in user_input:
            return 'customers'
        elif 'ab' in input_lower or '测试' in user_input:
            return 'events'
        else:
            return 'orders'


    def plan_analysis(self, user_input: str, db_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        制定分析计划，生成符合要求的JSON输出

        Args:
            user_input: 用户输入
            db_schema: 数据库schema信息

        Returns:
            Dict: 包含分析类型和步骤的JSON结构
        """
        # 识别分析类型（支持多选）
        analysis_types = self._identify_analysis_types(user_input)
        
        # 拆解分析步骤
        steps = self._generate_analysis_steps(analysis_types)
        
        return {
            "analysis_types": analysis_types,
            "steps": steps
        }

    def _identify_analysis_types(self, user_input: str) -> List[str]:
        """识别分析类型（支持多选）"""
        analysis_types = []
        input_lower = user_input.lower()

        # 检查各种分析类型
        if any(keyword in input_lower for keyword in ['ab', 'a/b', '测试', '实验']):
            analysis_types.append('ab_test')
        if any(keyword in input_lower for keyword in ['漏斗', '转化', 'funnel', 'conversion']):
            analysis_types.append('funnel')
        if any(keyword in input_lower for keyword in ['rfm', '用户分层', '用户价值', '用户分群']):
            analysis_types.append('rfm')
        if any(keyword in input_lower for keyword in ['分析', '统计', '描述', 'descriptive']):
            analysis_types.append('descriptive_analysis')

        # 如果没有识别到任何分析类型，默认为描述性分析
        if not analysis_types:
            analysis_types.append('descriptive_analysis')

        return analysis_types

    def _generate_analysis_steps(self, analysis_types: List[str]) -> List[Dict[str, Any]]:
        """
        生成分析步骤

        Args:
            analysis_types: 分析类型列表

        Returns:
            List[Dict]: 分析步骤列表
        """
        steps = []
        step_id = 1

        # 基础步骤：数据获取和DSL生成
        steps.append({
            "step_id": step_id,
            "name": "数据获取与DSL生成",
            "tool": "dsl_generator",
            "description": "分析用户需求，生成标准分析语言（DSL）"
        })
        step_id += 1

        steps.append({
            "step_id": step_id,
            "name": "SQL查询生成",
            "tool": "sql_generator",
            "description": "将DSL转换为可执行的SQL查询"
        })
        step_id += 1

        # 根据分析类型添加特定步骤
        if 'funnel' in analysis_types:
            steps.append({
                "step_id": step_id,
                "name": "漏斗分析",
                "tool": "funnel_analysis",
                "description": "执行转化漏斗分析，计算各阶段转化率"
            })
            step_id += 1

        if 'rfm' in analysis_types:
            steps.append({
                "step_id": step_id,
                "name": "RFM分析",
                "tool": "rfm_analysis",
                "description": "执行用户价值分层分析"
            })
            step_id += 1

        if 'ab_test' in analysis_types:
            steps.append({
                "step_id": step_id,
                "name": "A/B测试分析",
                "tool": "stat_analysis",
                "description": "执行A/B测试统计分析，验证实验效果"
            })
            step_id += 1

        if 'descriptive_analysis' in analysis_types:
            steps.append({
                "step_id": step_id,
                "name": "描述性分析",
                "tool": "stat_analysis",
                "description": "执行描述性统计分析，生成关键指标"
            })
            step_id += 1

        # 通用步骤：可视化和报告生成
        steps.append({
            "step_id": step_id,
            "name": "数据可视化",
            "tool": "visualization",
            "description": "生成数据可视化图表"
        })
        step_id += 1

        steps.append({
            "step_id": step_id,
            "name": "报告生成",
            "tool": "report",
            "description": "生成完整的分析报告，包含洞察和建议"
        })

        return steps


class Clarifier:
    """信息补全器 - 补全任务中缺失的信息"""

    def __init__(self):
        self.clarified_tasks = {}

    def need_clarification(self, task: AnalysisTask) -> bool:
        """判断是否需要信息补全"""
        return task.requires_clarification

    def generate_questions(self, task: AnalysisTask) -> List[str]:
        """生成补全问题"""
        questions = []

        # 根据分析类型生成不同的问题
        if task.analysis_type == AnalysisType.FUNNEL:
            questions.append("您想分析的转化漏斗包含哪些阶段？（如：浏览→加购→购买）")
        elif task.analysis_type == AnalysisType.RFM:
            questions.append("您想按照什么维度进行用户分层？")
        elif task.analysis_type == AnalysisType.AB_TEST:
            questions.append("您想对比哪些组别的转化率？")

        # 添加通用问题
        questions.extend(task.clarification_questions)

        return questions

    def apply_clarification(self, task: AnalysisTask, answers: Dict[str, Any]) -> AnalysisTask:
        """
        应用补全的答案，更新任务

        Args:
            task: 原始任务
            answers: 用户的回答

        Returns:
            AnalysisTask: 更新后的任务
        """
        # 更新字段
        if 'fields' in answers:
            task.target_fields = answers['fields']

        # 更新过滤条件
        if 'filters' in answers:
            task.filters.update(answers['filters'])

        # 更新指标
        if 'metrics' in answers:
            task.metrics = answers['metrics']

        # 更新分组
        if 'group_by' in answers:
            task.group_by = answers['group_by']

        # 更新时间范围
        if 'time_range' in answers:
            task.time_range = answers['time_range']

        # 更新数据源
        if 'data_source' in answers:
            task.data_source = answers.get('data_source')

        # 标记为已补全
        task.requires_clarification = False
        task.clarification_questions = []

        return task

    def check_missing_fields(self, task: AnalysisTask, db_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查是否缺少关键字段，生成补全问题

        Args:
            task: 分析任务
            db_schema: 数据库schema信息

        Returns:
            Dict: 包含是否需要补全和问题列表的JSON结构
        """
        questions = []

        # 检查指标定义
        if not task.metrics or len(task.metrics) == 0:
            questions.append("请定义您需要分析的具体指标（如：转化率、销售额、订单量等）")

        # 检查分组字段
        if not task.group_by:
            questions.append("请指定分析的分组字段（如：年龄组、产品类别、实验组等）")

        # 检查时间范围
        if not task.time_range:
            questions.append("请指定分析的时间范围（如：最近30天、2024年Q1等）")

        # 检查数据源/表名
        if not hasattr(task, 'data_source') or not task.data_source:
            questions.append("请指定分析的数据源或表名")

        # 根据分析类型生成特定问题
        if task.analysis_type == AnalysisType.FUNNEL:
            questions.append("请定义转化漏斗的具体阶段（如：浏览→加购→购买）")
        elif task.analysis_type == AnalysisType.AB_TEST:
            questions.append("请指定A/B测试的分组字段和比较的指标")
        elif task.analysis_type == AnalysisType.RFM:
            questions.append("请指定RFM分析的具体字段（最近购买时间、购买频次、购买金额）")

        # 限制问题数量不超过5个
        questions = questions[:5]

        return {
            "need_clarification": len(questions) > 0,
            "questions": questions
        }


class DSLGenerator:
    """DSL生成器 - 将结构化任务转换为标准分析语言"""

    def __init__(self):
        self.dsl_templates = self._init_templates()

    def _init_templates(self) -> Dict[str, str]:
        """初始化DSL模板"""
        return {
            'funnel': """
ANALYZE FUNNEL
  SOURCE = events
  STEPS = [{steps}]
  MEASURE = {measure}
  GROUP BY = {group_by}
  TIME_RANGE = {time_range}
  FILTER = {filter}
""",
            'rfm': """
ANALYZE RFM
  USER_ID = {user_id}
  RECENCY_FIELD = {recency_field}
  FREQUENCY_FIELD = {frequency_field}
  MONETARY_FIELD = {monetary_field}
  SEGMENT_METHOD = {segment_method}
  TOP_N = {top_n}
""",
            'comparison': """
ANALYZE COMPARISON
  METRICS = [{metrics}]
  GROUP BY = {group_by}
  SOURCE = {source}
  FILTER = {filter}
  ORDER BY = {order_by}
  LIMIT = {limit}
""",
            'trend': """
ANALYZE TREND
  METRICS = [{metrics}]
  TIME_FIELD = {time_field}
  TIME_GRANULARITY = {granularity}
  SOURCE = {source}
  FILTER = {filter}
""",
            'distribution': """
ANALYZE DISTRIBUTION
  FIELD = {field}
  SOURCE = {source}
  FILTER = {filter}
  BIN_COUNT = {bin_count}
""",
            'ab_test': """
ANALYZE AB_TEST
  METRIC = {metric}
  GROUP_A = {group_a}
  GROUP_B = {group_b}
  SOURCE = {source}
  FILTER = {filter}
"""
        }

    def generate(self, task: AnalysisTask) -> DSLStatement:
        """
        生成DSL语句

        Args:
            task: 结构化的分析任务

        Returns:
            DSLStatement: DSL语句对象
        """
        if task.analysis_type == AnalysisType.FUNNEL:
            return self._generate_funnel_dsl(task)
        elif task.analysis_type == AnalysisType.RFM:
            return self._generate_rfm_dsl(task)
        elif task.analysis_type == AnalysisType.AB_TEST:
            return self._generate_ab_test_dsl(task)
        elif task.analysis_type == AnalysisType.TREND:
            return self._generate_trend_dsl(task)
        elif task.analysis_type == AnalysisType.DISTRIBUTION:
            return self._generate_distribution_dsl(task)
        else:
            return self._generate_custom_dsl(task)

    def _generate_funnel_dsl(self, task: AnalysisTask) -> DSLStatement:
        """生成漏斗分析DSL"""
        return DSLStatement(
            dsl_type='funnel',
            operation='analyze',
            source='events',
            dimensions=['event_type'],
            measures=['count(distinct session_id)'],
            filters=[f"{k}={v}" for k, v in task.filters.items()],
            order_by=['event_type'],
            limit=None
        )

    def _generate_rfm_dsl(self, task: AnalysisTask) -> DSLStatement:
        """生成RFM分析DSL"""
        return DSLStatement(
            dsl_type='rfm',
            operation='analyze',
            source='events',
            dimensions=['session_id'],
            measures=['count(*)', 'sum(amount_usd)'],
            filters=[],
            order_by=None,
            limit=None
        )

    def _generate_ab_test_dsl(self, task: AnalysisTask) -> DSLStatement:
        """生成A/B测试DSL"""
        return DSLStatement(
            dsl_type='ab_test',
            operation='analyze',
            source='events',
            dimensions=['source'],
            measures=['count(distinct session_id)', 'sum(case when event_type="Purchase" then 1 else 0 end)'],
            filters=[f"session_id is not null"],
            order_by=None,
            limit=None
        )

    def _generate_trend_dsl(self, task: AnalysisTask) -> DSLStatement:
        """生成趋势分析DSL"""
        return DSLStatement(
            dsl_type='trend',
            operation='analyze',
            source=task.target_fields[0].split('.')[0] if task.target_fields else 'orders',
            dimensions=task.group_by or ['order_time'],
            measures=task.metrics,
            filters=[f"{k}={v}" for k, v in task.filters.items()],
            order_by=task.group_by,
            limit=None
        )

    def _generate_distribution_dsl(self, task: AnalysisTask) -> DSLStatement:
        """生成分布分析DSL"""
        return DSLStatement(
            dsl_type='distribution',
            operation='analyze',
            source=task.target_fields[0].split('.')[0] if task.target_fields else 'orders',
            dimensions=task.target_fields,
            measures=task.metrics,
            filters=[f"{k}={v}" for k, v in task.filters.items()],
            order_by=None,
            limit=100
        )

    def _generate_custom_dsl(self, task: AnalysisTask) -> DSLStatement:
        """生成自定义分析DSL"""
        return DSLStatement(
            dsl_type='custom',
            operation='analyze',
            source=task.target_fields[0].split('.')[0] if task.target_fields else 'orders',
            dimensions=task.group_by or [],
            measures=task.metrics,
            filters=[f"{k}={v}" for k, v in task.filters.items()],
            order_by=None,
            limit=1000
        )

    def to_string(self, dsl: DSLStatement) -> str:
        """将DSL对象转换为字符串"""
        return f"""
=== DSL Statement ===
Type: {dsl.dsl_type}
Operation: {dsl.operation}
Source: {dsl.source}
Dimensions: {', '.join(dsl.dimensions)}
Measures: {', '.join(dsl.measures)}
Filters: {', '.join(dsl.filters) if dsl.filters else 'None'}
Order By: {', '.join(dsl.order_by) if dsl.order_by else 'None'}
Limit: {dsl.limit if dsl.limit else 'None'}
===
"""

    def generate_standard_dsl(self, task: AnalysisTask, analysis_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成标准DSL格式

        Args:
            task: 分析任务
            analysis_plan: 分析计划

        Returns:
            Dict: 标准DSL格式
        """
        # 构建指标列表
        metrics = []
        for metric in task.metrics:
            metrics.append({
                "name": metric,
                "formula": self._get_metric_formula(metric)
            })

        # 构建维度列表
        dimensions = task.target_fields

        # 构建过滤条件列表
        filters = []
        for key, value in task.filters.items():
            if isinstance(value, dict):
                if key == 'age_group':
                    filters.append(f"age >= {value['min']} AND age <= {value['max']}")
            else:
                filters.append(f"{key} = '{value}'")

        # 构建时间范围
        time_range = ""
        if task.time_range:
            if task.time_range.get('type') == 'recent':
                time_range = f"last_{task.time_range['value']}_{task.time_range['unit']}"

        # 构建分组字段
        group_by = ", ".join(task.group_by) if task.group_by else ""

        # 构建步骤列表（针对漏斗分析）
        steps = []
        if task.analysis_type == AnalysisType.FUNNEL:
            # 默认漏斗步骤
            steps = ["浏览", "加购", "购买"]

        # 构建标准DSL
        standard_dsl = {
            "analysis_type": task.analysis_type.value,
            "metrics": metrics,
            "dimensions": dimensions,
            "filters": filters,
            "time_range": time_range,
            "group_by": group_by,
            "steps": steps
        }

        # 针对A/B测试的特殊处理
        if task.analysis_type == AnalysisType.AB_TEST:
            if not group_by:
                standard_dsl["group_by"] = "source"  # 默认使用source字段作为分组

        return standard_dsl

    def _get_metric_formula(self, metric: str) -> str:
        """
        获取指标的计算逻辑

        Args:
            metric: 指标名称

        Returns:
            str: 指标计算公式
        """
        metric_formulas = {
            "count": "COUNT(*)",
            "sum": "SUM(total_usd)",
            "avg": "AVG(total_usd)",
            "conversion_rate": "COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) / COUNT(CASE WHEN event_type = 'view' THEN 1 END)",
            "percentage": "COUNT(*) / (SELECT COUNT(*) FROM events)",
            "revenue": "SUM(total_usd)",
            "order_count": "COUNT(DISTINCT order_id)",
            "avg_order_value": "SUM(total_usd) / COUNT(DISTINCT order_id)"
        }

        return metric_formulas.get(metric, f"{metric}()")


def create_analysis_workflow(db_schema: Dict[str, Any]) -> tuple:
    """
    创建分析工作流

    Args:
        db_schema: 数据库schema信息

    Returns:
        tuple: (planner, clarifier, dsl_generator)
    """
    planner = Planner()
    clarifier = Clarifier()
    dsl_generator = DSLGenerator()

    return planner, clarifier, dsl_generator


def execute_workflow(user_input: str, db_schema: Dict[str, Any], user_answers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    执行完整的工作流

    Args:
        user_input: 用户输入
        db_schema: 数据库schema信息
        user_answers: 用户的补充回答（可选）

    Returns:
        Dict: 工作流执行结果
    """
    # 1. Planner - 任务拆解
    planner, clarifier, dsl_generator = create_analysis_workflow(db_schema)
    task = planner.parse(user_input, db_schema)

    result = {
        'stage': 'planner',
        'task': task,
        'success': True,
        'message': '任务拆解完成'
    }

    # 2. Clarifier - 信息补全（如果需要）
    if clarifier.need_clarification(task):
        if user_answers:
            # 应用用户的回答
            task = clarifier.apply_clarification(task, user_answers)
            result['stage'] = 'clarifier'
            result['message'] = '信息补全完成'
            result['task'] = task
        else:
            # 返回需要补全的问题
            questions = clarifier.generate_questions(task)
            return {
                'stage': 'clarifier',
                'requires_input': True,
                'questions': questions,
                'success': False,
                'message': '需要补充信息'
            }

    # 3. DSL Generator - 生成标准分析语言
    dsl = dsl_generator.generate(task)
    result['stage'] = 'dsl_generator'
    result['dsl'] = dsl
    result['dsl_string'] = dsl_generator.to_string(dsl)
    result['message'] = 'DSL生成完成'

    return result