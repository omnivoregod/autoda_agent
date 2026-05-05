"""
集成工作流运行器
整合所有工作流模块，执行完整的分析流程
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from workflow_core import Planner, Clarifier, DSLGenerator, AnalysisType, AnalysisTask
from sql_generator import SQLGenerator
from analysis_executor import AnalysisExecutor
from guardrail import Guardrail
from reporter import Reporter
from visualization_planner import VisualizationPlanner


class AnalysisWorkflow:
    """分析工作流 - 整合所有模块的执行器"""

    def __init__(self, db_schema: Optional[Dict[str, Any]] = None, db_path: str = "autoda_agent.db"):
        """
        初始化分析工作流

        Args:
            db_schema: 数据库schema信息
            db_path: 数据库路径
        """
        self.db_schema = db_schema or self._get_default_schema()
        self.db_path = db_path
        
        # 初始化各个组件
        self.planner = Planner()
        self.clarifier = Clarifier()
        self.dsl_generator = DSLGenerator()
        self.sql_generator = SQLGenerator()
        self.analysis_executor = AnalysisExecutor()
        self.visualization_planner = VisualizationPlanner()
        self.guardrail = Guardrail()
        self.reporter = Reporter()

    def _get_default_schema(self) -> Dict[str, Any]:
        """获取默认的数据库schema"""
        return {
            'tables': {
                'customers': {
                    'columns': ['customer_id', 'name', 'email', 'country', 'age', 'signup_date', 'marketing_opt_in']
                },
                'orders': {
                    'columns': ['order_id', 'customer_id', 'order_time', 'payment_method', 'discount_pct', 'subtotal_usd', 'total_usd', 'country', 'device', 'source']
                },
                'products': {
                    'columns': ['product_id', 'category', 'name', 'price_usd', 'cost_usd', 'margin_usd']
                },
                'order_items': {
                    'columns': ['order_id', 'product_id', 'unit_price_usd', 'quantity', 'line_total_usd']
                },
                'events': {
                    'columns': ['event_id', 'session_id', 'timestamp', 'event_type', 'product_id', 'qty', 'cart_size', 'payment', 'discount_pct', 'amount_usd']
                },
                'reviews': {
                    'columns': ['review_id', 'order_id', 'product_id', 'rating', 'review_text', 'review_time']
                },
                'sessions': {
                    'columns': ['session_id', 'customer_id', 'start_time', 'device', 'source', 'country']
                }
            },
            'all_fields': [
                'age', 'discount_pct', 'total_usd', 'order_time', 'category',
                'customer_id', 'order_id', 'product_id', 'session_id', 'source',
                'device', 'country', 'amount_usd', 'price_usd', 'quantity'
            ]
        }

    def execute(self, user_input: str, user_answers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行完整的分析工作流

        Args:
            user_input: 用户输入
            user_answers: 用户的补充回答（可选）

        Returns:
            Dict: 工作流执行结果
        """
        result = {
            'success': False,
            'stages': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'total_time': 0
        }

        start_time = datetime.now()

        try:
            # ① Planner - 任务拆解
            stage_result = self._execute_planner(user_input)
            result['stages']['planner'] = stage_result
            if not stage_result.get('success'):
                result['message'] = '任务拆解失败'
                return result

            task = stage_result.get('task')
            analysis_plan = stage_result.get('analysis_plan')
            result['analysis_plan'] = analysis_plan

            # ② Clarifier - 信息补全（如果需要）
            # 检查是否缺少关键字段
            clarification_result = self.clarifier.check_missing_fields(task, self.db_schema)
            
            if clarification_result['need_clarification']:
                if user_answers:
                    task = self.clarifier.apply_clarification(task, user_answers)
                    result['stages']['clarifier'] = {
                        'success': True,
                        'message': '信息补全完成',
                        'task': task
                    }
                else:
                    questions = clarification_result['questions']
                    result['requires_input'] = True
                    result['questions'] = questions
                    result['message'] = '需要补充信息'
                    return result
            else:
                result['stages']['clarifier'] = {
                    'success': True,
                    'message': '无需信息补全',
                    'task': task
                }

            # ③ DSL Generator - 生成标准分析语言
            dsl = self.dsl_generator.generate(task)
            
            # 生成标准DSL格式
            standard_dsl = self.dsl_generator.generate_standard_dsl(task, analysis_plan)
            
            result['stages']['dsl_generator'] = {
                'success': True,
                'dsl_type': dsl.dsl_type,
                'dsl_string': self.dsl_generator.to_string(dsl),
                'standard_dsl': standard_dsl
            }
            
            result['standard_dsl'] = standard_dsl

            # ④ SQL Generator - 生成SQL查询
            # 使用标准DSL生成SQL
            sql_result = None
            try:
                sql_result = self.sql_generator.generate_from_standard_dsl(result['standard_dsl'], self.db_schema)
                sql = sql_result['sql']
            except Exception as e:
                # 如果标准DSL生成失败，使用原始DSL作为备用
                sql_query = self.sql_generator.generate(dsl, self.db_schema)
                sql = sql_query.sql
            
            # 验证SQL
            is_valid, error_msg = self.sql_generator.validate_sql(sql)
            if not is_valid:
                result['stages']['sql_generator'] = {
                    'success': False,
                    'error': error_msg
                }
                result['message'] = f'SQL验证失败: {error_msg}'
                return result

            result['stages']['sql_generator'] = {
                'success': True,
                'sql': sql,
                'description': '从标准DSL生成的SQL查询'
            }

            # ⑤ Analysis Executor - 执行分析
            executor_result = self.analysis_executor.execute(sql, self.db_path)
            
            if not executor_result.success:
                result['stages']['executor'] = {
                    'success': False,
                    'error': executor_result.error_message
                }
                result['message'] = f'查询执行失败: {executor_result.error_message}'
                return result

            result['stages']['executor'] = {
                'success': True,
                'row_count': executor_result.row_count,
                'column_count': executor_result.column_count,
                'execution_time': executor_result.execution_time,
                'data': executor_result.data
            }

            # ⑥ Visualization Planner - 图表规划
            # 先进行数据分析
            # 从标准DSL中获取分析类型
            analysis_type = result['standard_dsl'].get('analysis_type', 'auto')
            analysis_result = self.analysis_executor.analyze_generic(executor_result.data, analysis_type)
            
            # 生成图表规划
            visualization_plan = self.visualization_planner.plan(analysis_result, executor_result.data)
            result['stages']['visualization'] = {
                'success': True,
                'message': '图表规划已完成',
                'charts': visualization_plan['charts']
            }
            
            result['visualization_plan'] = visualization_plan

            # ⑦ Guardrail - 数据校验
            
            # 执行企业级关键检查
            guardrail_result = self.guardrail.validate_with_dsl_sql(
                result['standard_dsl'],
                result['stages']['sql_generator']['sql'],
                analysis_result,
                executor_result.data,
                user_input
            )
            
            # 同时执行传统校验
            validation_result = self.guardrail.validate(executor_result.data, analysis_result)
            
            result['stages']['guardrail'] = {
                'success': True,
                'is_valid': guardrail_result['valid'] and validation_result.is_valid,
                'risk_level': validation_result.risk_level.value if hasattr(validation_result.risk_level, 'value') else str(validation_result.risk_level),
                'issues': guardrail_result['issues'] + validation_result.issues,
                'warnings': validation_result.warnings
            }
            
            result['guardrail_result'] = guardrail_result

            # ⑧ Reporter - 生成报告
            report = self.reporter.generate(
                user_input=user_input,
                analysis_result=analysis_result,
                validation_result=validation_result,
                data=executor_result.data,
                dsl_info=dsl,
                visualization_plan=result.get('visualization_plan'),
                guardrail_result=result.get('guardrail_result')
            )

            result['stages']['reporter'] = {
                'success': True,
                'report': report
            }

            # ⑨ Self-Check - 报告自检
            self_check_result = self.reporter.self_check(
                report=report,
                analysis_result=analysis_result,
                data=executor_result.data
            )
            
            result['stages']['self_check'] = {
                'success': True,
                'quality_score': self_check_result['quality_score'],
                'issues': self_check_result['issues'],
                'improved_version': self_check_result['improved_version']
            }

            # 汇总结果
            result['success'] = True
            result['message'] = '分析完成'
            result['data'] = executor_result.data
            result['analysis_result'] = analysis_result
            result['report'] = report
            result['self_check_result'] = self_check_result
            result['sql_query'] = sql
            result['dsl_type'] = dsl.dsl_type

        except Exception as e:
            result['error'] = str(e)
            result['message'] = f'工作流执行出错: {str(e)}'

        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.isoformat()
            result['total_time'] = (end_time - start_time).total_seconds()

        return result

    def _execute_planner(self, user_input: str) -> Dict[str, Any]:
        """执行Planner阶段"""
        try:
            # 解析任务
            task = self.planner.parse(user_input, self.db_schema)
            
            # 生成分析计划
            analysis_plan = self.planner.plan_analysis(user_input, self.db_schema)
            
            return {
                'success': True,
                'task': task,
                'task_id': task.task_id,
                'analysis_type': task.analysis_type.value if hasattr(task.analysis_type, 'value') else str(task.analysis_type),
                'target_fields': task.target_fields,
                'metrics': task.metrics,
                'requires_clarification': task.requires_clarification,
                'analysis_plan': analysis_plan
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_supported_analysis_types(self) -> List[str]:
        """获取支持的分析类型"""
        return [at.value for at in AnalysisType]


def run_analysis_workflow(user_input: str, 
                         db_schema: Optional[Dict[str, Any]] = None,
                         db_path: str = "autoda_agent.db",
                         user_answers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    快速运行分析工作流

    Args:
        user_input: 用户输入
        db_schema: 数据库schema信息（可选）
        db_path: 数据库路径
        user_answers: 用户的补充回答（可选）

    Returns:
        Dict: 工作流执行结果
    """
    workflow = AnalysisWorkflow(db_schema, db_path)
    return workflow.execute(user_input, user_answers)


def get_workflow_info() -> Dict[str, Any]:
    """获取工作流信息"""
    return {
        'name': '电商数据分析工作流',
        'version': '2.0',
        'stages': [
            {'name': 'Planner', 'description': '任务拆解', 'order': 1},
            {'name': 'Clarifier', 'description': '信息补全', 'order': 2},
            {'name': 'DSL Generator', 'description': '标准分析语言生成', 'order': 3},
            {'name': 'SQL Generator', 'description': 'SQL查询生成', 'order': 4},
            {'name': 'Analysis Executor', 'description': '分析执行', 'order': 5},
            {'name': 'Visualization Planner', 'description': '图表规划', 'order': 6},
            {'name': 'Guardrail', 'description': '数据校验', 'order': 7},
            {'name': 'Reporter', 'description': '报告生成', 'order': 8}
        ],
        'supported_analysis_types': [
            {'type': 'funnel', 'name': '转化漏斗分析', 'description': '分析用户转化路径'},
            {'type': 'rfm', 'name': 'RFM分析', 'description': '用户价值分层分析'},
            {'type': 'comparison', 'name': '对比分析', 'description': '比较不同组别的指标差异'},
            {'type': 'trend', 'name': '趋势分析', 'description': '分析指标随时间的变化趋势'},
            {'type': 'distribution', 'name': '分布分析', 'description': '分析数据的分布情况'},
            {'type': 'ab_test', 'name': 'A/B测试', 'description': '分析A/B测试结果'}
        ]
    }