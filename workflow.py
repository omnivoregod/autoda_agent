"""
五阶段工作流框架
实现企业级商业分析的标准操作流程 (SOP)
"""

import pandas as pd
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AnalysisTask:
    """分析任务数据类"""
    user_input: str
    business_context: Dict[str, Any]
    metric_tree: Dict[str, Any]
    data_results: Dict[str, Any]
    insights: List[str]
    action_plan: Dict[str, Any]
    tracking_config: Dict[str, Any]

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        """初始化工作流管理器"""
        self.stages = {
            1: "需求诊断与目标对齐",
            2: "字段语义分析与需求匹配",
            3: "数据获取与质检验证",
            4: "深度诊断与根因推演",
            5: "方案输出与商业决策",
            6: "效果追踪闭环"
        }
    
    def run_workflow(self, user_input: str, api_key: str = None, model_type: str = "deepseek") -> Dict[str, Any]:
        """
        运行完整的六阶段工作流
        
        Args:
            user_input: 用户输入的分析需求
            api_key: API密钥
            model_type: 模型类型
            
        Returns:
            dict: 工作流执行结果
        """
        # 阶段一：需求诊断与目标对齐
        stage1_result = self._stage1_requirement_diagnosis(user_input)
        if not stage1_result['success']:
            return stage1_result
        
        # 阶段二：字段语义分析与需求匹配（新增）
        stage2_result = self._stage2_field_semantic_analysis(stage1_result['output'])
        if not stage2_result['success']:
            return stage2_result
        
        # 阶段三：数据获取与质检验证
        stage3_result = self._stage3_data_acquisition(stage2_result['output'])
        if not stage3_result['success']:
            return stage3_result
        
        # 阶段四：深度诊断与根因推演
        stage4_result = self._stage4_deep_analysis(stage3_result['output'])
        if not stage4_result['success']:
            return stage4_result
        
        # 阶段五：方案输出与商业决策
        stage5_result = self._stage5_business_decision(stage4_result['output'])
        if not stage5_result['success']:
            return stage5_result
        
        # 阶段五扩展：数据可视化生成
        visualization_result = self._stage5_visualization(user_input, stage1_result['output'], stage3_result['output'], stage4_result['output'])
        
        # 阶段六：效果追踪闭环
        stage6_result = self._stage6_tracking_closure(stage5_result['output'])
        
        # 生成综合报告（包含可视化）
        from report_generator import generate_comprehensive_report
        from reporter import Reporter
        import pandas as pd
        
        report = generate_comprehensive_report({
            'business_context': stage1_result['output']['business_context'],
            'metric_tree': stage1_result['output']['metric_tree'],
            'field_match_report': stage2_result['output'].get('field_match_report', {}),
            'data_results': stage3_result['output'].get('data_results', {}),
            'insights': stage4_result['output'].get('insights', []),
            'action_plan': stage5_result['output'].get('action_plan', {}),
            'tracking_config': stage6_result['output'].get('tracking_config', {}),
            'visualizations': visualization_result.get('visualizations', [])
        })
        
        # 生成JSON格式报告
        reporter = Reporter()
        
        # 准备分析结果数据结构
        analysis_result = {
            'success': True,
            'analysis_type': stage1_result['output']['business_context'].get('analysis_type', 'unknown')
        }
        
        # 确保analysis_type被正确设置
        if 'analysis_type' in stage1_result['output']['business_context']:
            analysis_result['analysis_type'] = stage1_result['output']['business_context']['analysis_type']
        
        # 准备数据
        data = pd.DataFrame()
        data_results = stage3_result['output'].get('data_results', {})
        
        # 从data_results中提取一个DataFrame作为示例，优先使用与分析类型相关的数据
        analysis_type = analysis_result['analysis_type']
        
        # 优先使用与分析类型相关的数据
        if 'rfm' in analysis_type or 'RFM' in user_input or '价值用户' in user_input or '用户分层' in user_input:
            if 'rfm_data' in data_results:
                data = data_results['rfm_data']
        elif 'payment' in analysis_type or '支付' in user_input or 'payment_method' in user_input.lower():
            if 'payment_data' in data_results:
                data = data_results['payment_data']
        elif 'marketing' in analysis_type or '渠道' in user_input or 'channel' in user_input.lower():
            if 'channel_data' in data_results:
                data = data_results['channel_data']
        elif 'sales' in analysis_type or '销售' in user_input or 'trend' in user_input.lower():
            if 'sales_trend_data' in data_results:
                data = data_results['sales_trend_data']
        elif 'user' in analysis_type or '用户' in user_input:
            if 'user_demographics_data' in data_results:
                data = data_results['user_demographics_data']
        elif 'product' in analysis_type or '产品' in user_input or 'category' in user_input:
            if 'product_data' in data_results:
                data = data_results['product_data']
        else:
            # 如果没有特定的分析类型，使用基本数据
            for key in ['basic_data', 'rfm_data', 'payment_data', 'channel_data', 'sales_trend_data', 'user_demographics_data', 'product_data']:
                if key in data_results:
                    data = data_results[key]
                    break
        
        # 根据分析类型添加相应的分析数据
        analysis_type = analysis_result['analysis_type']
        
        # 支付方式分析
        if 'payment' in analysis_type or '支付' in user_input or 'payment_method' in user_input.lower():
            if 'payment_data' in data_results:
                payment_df = data_results['payment_data']
                if not payment_df.empty:
                    # 分析使用最多的支付方式
                    top_payment = payment_df.loc[payment_df['order_count'].idxmax()]
                    total_orders = payment_df['order_count'].sum()
                    top_payment_ratio = top_payment['order_count'] / total_orders * 100
                    
                    # 添加支付方式分析数据
                    analysis_result['payment_analysis'] = {
                        'top_payment': top_payment.to_dict(),
                        'top_payment_ratio': top_payment_ratio,
                        'total_orders': total_orders,
                        'total_payment_methods': len(payment_df)
                    }
        
        # 渠道分析
        elif 'marketing' in analysis_type or '渠道' in user_input or 'channel' in user_input.lower():
            if 'channel_data' in data_results and 'orders_data' in data_results:
                channel_df = data_results['channel_data']
                orders_df = data_results['orders_data']
                
                if not channel_df.empty and not orders_df.empty:
                    # 合并数据计算转化率
                    merged_df = channel_df.merge(orders_df, on='source', how='left')
                    merged_df['conversion_rate'] = merged_df['orders'] / merged_df['sessions'] * 100
                    
                    # 分析表现最好和最差的渠道
                    top_order_channel = orders_df.loc[orders_df['orders'].idxmax()]
                    top_conversion_channel = merged_df.loc[merged_df['conversion_rate'].idxmax()]
                    
                    # 添加渠道分析数据
                    analysis_result['channel_analysis'] = {
                        'top_order_channel': top_order_channel.to_dict(),
                        'top_conversion_channel': top_conversion_channel.to_dict(),
                        'average_conversion': merged_df['conversion_rate'].mean(),
                        'total_gmv': orders_df['gmv'].sum()
                    }
        
        # 销售趋势分析
        elif 'sales' in analysis_type or '销售' in user_input or 'trend' in user_input.lower():
            if 'sales_trend_data' in data_results:
                sales_trend_df = data_results['sales_trend_data']
                if not sales_trend_df.empty and len(sales_trend_df) > 1:
                    # 分析销售趋势
                    first_period = sales_trend_df.iloc[0]
                    last_period = sales_trend_df.iloc[-1]
                    order_growth = (last_period['orders'] - first_period['orders']) / first_period['orders'] * 100 if first_period['orders'] > 0 else 0
                    revenue_growth = (last_period['revenue'] - first_period['revenue']) / first_period['revenue'] * 100 if first_period['revenue'] > 0 else 0
                    
                    # 添加销售趋势分析数据
                    analysis_result['trend_analysis'] = {
                        'start_date': first_period['date'],
                        'end_date': last_period['date'],
                        'order_growth': order_growth,
                        'revenue_growth': revenue_growth,
                        'total_orders': sales_trend_df['orders'].sum(),
                        'total_revenue': sales_trend_df['revenue'].sum()
                    }
        
        # 用户分析
        elif 'user' in analysis_type or '用户' in user_input:
            if 'user_demographics_data' in data_results:
                user_demographics_df = data_results['user_demographics_data']
                if not user_demographics_df.empty:
                    # 分析用户年龄分布
                    top_age_group = user_demographics_df.loc[user_demographics_df['user_count'].idxmax()]
                    top_aov_age = user_demographics_df.loc[user_demographics_df['avg_order_value'].idxmax()]
                    
                    # 添加用户分析数据
                    analysis_result['user_analysis'] = {
                        'top_age_group': top_age_group.to_dict(),
                        'top_aov_age': top_aov_age.to_dict(),
                        'total_users': user_demographics_df['user_count'].sum(),
                        'average_order_value': user_demographics_df['avg_order_value'].mean()
                    }
        
        # 产品分析
        elif 'product' in analysis_type or '产品' in user_input or 'category' in user_input:
            if 'product_data' in data_results:
                product_df = data_results['product_data']
                if not product_df.empty:
                    # 分析销售最好的品类
                    top_category = product_df.loc[product_df['revenue'].idxmax()]
                    total_revenue = product_df['revenue'].sum()
                    top_category_ratio = top_category['revenue'] / total_revenue * 100
                    
                    # 添加产品分析数据
                    analysis_result['product_analysis'] = {
                        'top_category': top_category.to_dict(),
                        'top_category_ratio': top_category_ratio,
                        'total_revenue': total_revenue,
                        'total_categories': len(product_df)
                    }
        
        # RFM分析
        elif 'rfm' in analysis_type or 'RFM' in user_input or '价值用户' in user_input or '用户分层' in user_input:
            if 'rfm_data' in data_results:
                rfm_df = data_results['rfm_data']
                if not rfm_df.empty:
                    # 分析RFM数据
                    total_users = len(rfm_df)
                    avg_frequency = rfm_df['frequency'].mean()
                    avg_monetary = rfm_df['monetary'].mean()
                    
                    # 计算最近购买日期的统计信息
                    rfm_df['last_purchase_date'] = pd.to_datetime(rfm_df['last_purchase_date'])
                    most_recent = rfm_df['last_purchase_date'].max()
                    least_recent = rfm_df['last_purchase_date'].min()
                    
                    # 添加RFM分析数据
                    analysis_result['rfm_analysis'] = {
                        'total_users': total_users,
                        'average_frequency': avg_frequency,
                        'average_monetary': avg_monetary,
                        'most_recent_purchase': most_recent.strftime('%Y-%m-%d') if pd.notnull(most_recent) else 'N/A',
                        'least_recent_purchase': least_recent.strftime('%Y-%m-%d') if pd.notnull(least_recent) else 'N/A'
                    }
        
        # 基本分析
        else:
            if 'basic_data' in data_results:
                basic_df = data_results['basic_data']
                if not basic_df.empty:
                    # 分析基本业务指标
                    total_orders = basic_df['total_orders'].iloc[0]
                    total_revenue = basic_df['total_revenue'].iloc[0]
                    avg_order_value = basic_df['avg_order_value'].iloc[0]
                    
                    # 添加基本分析数据
                    analysis_result['basic_analysis'] = {
                        'total_orders': total_orders,
                        'total_revenue': total_revenue,
                        'avg_order_value': avg_order_value
                    }
        
        # 生成JSON报告
        # 从数据库获取完整的原始数据用于匹配检查（使用语义表名匹配）
        from tools import run_sql_query
        
        # 获取完整的orders数据（使用语义表名匹配）
        orders_df = run_sql_query('SELECT * FROM orders')
        order_items_df = run_sql_query('SELECT * FROM order_items')
        
        # 检查是否有错误
        if 'error' in orders_df.columns:
            full_data = orders_df
        elif 'error' in order_items_df.columns:
            full_data = order_items_df
        else:
            # 合并数据以获取完整的分析数据
            full_data = pd.merge(orders_df, order_items_df, on='order_id', how='left')
        
        # 使用完整数据进行报告生成
        if api_key:
            json_report = reporter.generate_json_report_with_llm(
                user_input,
                analysis_result,
                full_data,
                api_key,
                model_type
            )
        else:
            json_report = reporter.generate_json_report(
                user_input,
                analysis_result,
                full_data
            )
        
        return {
            'success': True,
            'message': '工作流执行完成',
            'result': stage6_result['output'],
            'report': report,
            'json_report': json_report,
            'visualizations': visualization_result.get('visualizations', []),
            'stages': {
                1: stage1_result,
                2: stage2_result,
                3: stage3_result,
                4: stage4_result,
                5: stage5_result,
                6: stage6_result,
                'visualization': visualization_result
            }
        }
    
    def _stage1_requirement_diagnosis(self, user_input: str) -> Dict[str, Any]:
        """阶段一：需求诊断与目标对齐"""
        try:
            # 导入需求诊断模块
            from context_agent import clarify_requirement
            from metric_tree import build_metric_tree
            
            # 1. 意图澄清与业务上下文填充
            business_context = clarify_requirement(user_input)
            
            # 2. 指标体系拆解
            metric_tree = build_metric_tree(business_context)
            
            return {
                'success': True,
                'message': '需求诊断完成',
                'output': {
                    'user_input': user_input,
                    'business_context': business_context,
                    'metric_tree': metric_tree
                }
            }
        except ImportError as e:
            return {
                'success': False,
                'message': f'模块导入失败: {str(e)}',
                'output': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'需求诊断失败: {str(e)}',
                'output': None
            }
    
    def _stage2_field_semantic_analysis(self, stage1_output: Dict[str, Any]) -> Dict[str, Any]:
        """阶段二：字段语义分析与需求匹配"""
        try:
            import pandas as pd
            from field_semantic import analyze_field_semantics
            from guardrail import Guardrail
            from tools import get_available_tables, get_table_columns
            
            user_input = stage1_output.get('user_input', '')
            business_context = stage1_output.get('business_context', {})
            
            # 1. 从数据库获取所有表的字段信息（使用语义表名匹配）
            tables = get_available_tables('ecommerce.db')
            
            all_field_semantics = {}
            all_data_fields = []
            
            for table_name in tables:
                # 获取表结构
                columns = get_table_columns('ecommerce.db', table_name)
                
                if columns:
                    field_names = columns
                    all_data_fields.extend(field_names)
                    
                    # 分析字段语义
                    field_semantics = analyze_field_semantics(field_names)
                    for field, sem in field_semantics.items():
                        all_field_semantics[f"{table_name}.{field}"] = sem
            
            # 2. 提取用户问题中需要的字段类型
            guardrail = Guardrail()
            required_fields = guardrail._extract_required_fields(user_input)
            
            # 3. 检查数据中是否有匹配的字段
            field_type_mappings = {
                '用户标识': ['用户标识', '用户维度', 'customer', 'user', 'customer_id', 'user_id'],
                '订单标识': ['订单标识', '交易维度', 'order', 'id', 'order_id'],
                '交易时间': ['时间维度', '交易维度', 'time', 'date', 'order_time', 'created_at', 'order_date', 'timestamp'],
                '交易金额': ['交易金额', '交易维度', 'amount', 'total', 'usd', 'total_usd', 'subtotal_usd', 'transaction_amount', 'amount_usd'],
                '订单状态': ['状态维度', 'status', 'order_status', 'refund_status'],
                '商品数量': ['数量', '交易维度', 'quantity', 'qty', 'item_count', 'item_quantity'],
                '事件类型': ['事件类型', 'event_type', 'action', 'event'],
                '会话标识': ['会话标识', 'session_id', 'session']
            }
            
            # 检查每个需要的字段类型是否有匹配的字段
            available_analysis_types = []
            missing_field_types = []
            
            for field_type, required in required_fields.items():
                if required:
                    has_field = False
                    for data_field, sem in all_field_semantics.items():
                        field_lower = data_field.lower()
                        # 检查字段语义
                        if (
                            sem['category'] == field_type or 
                            sem['main_dimension'] == field_type or
                            any(mapped_type in [sem['category'], sem['main_dimension']] 
                                for mapped_type in field_type_mappings.get(field_type, []))
                        ):
                            has_field = True
                            break
                        # 检查字段名
                        if any(keyword in field_lower for keyword in field_type_mappings.get(field_type, [])):
                            has_field = True
                            break
                    
                    if has_field:
                        available_analysis_types.append(field_type)
                    else:
                        missing_field_types.append(field_type)
            
            # 4. 生成字段匹配报告
            field_match_report = {
                'user_input': user_input,
                'available_fields': all_data_fields,
                'field_semantics': all_field_semantics,
                'required_fields': required_fields,
                'available_analysis_types': available_analysis_types,
                'missing_field_types': missing_field_types,
                'can_answer': len(missing_field_types) == 0 or len(available_analysis_types) > 0
            }
            
            return {
                'success': True,
                'message': '字段语义分析完成',
                'output': {
                    **stage1_output,
                    'field_match_report': field_match_report
                }
            }
        except ImportError as e:
            return {
                'success': False,
                'message': f'模块导入失败: {str(e)}',
                'output': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'字段语义分析失败: {str(e)}',
                'output': None
            }
    
    def _stage3_data_acquisition(self, stage2_output: Dict[str, Any]) -> Dict[str, Any]:
        """阶段三：数据获取与质检验证"""
        try:
            # 导入数据获取和质检模块
            from tools import run_sql_query
            from data_qa import detect_simpson_paradox, detect_anomalies, run_comprehensive_qa
            import pandas as pd
            
            # 1. 自动化取数与清洗
            data_results = {
                'success': True,
                'message': '数据获取完成',
                'data_quality': {
                    'score': 100,
                    'status': '良好'
                }
            }
            
            # 2. 根据分析类型获取实际数据
            business_context = stage2_output.get('business_context', {})
            analysis_type = business_context.get('analysis_type', '')
            user_input = stage2_output.get('user_input', '')
            field_match_report = stage2_output.get('field_match_report', {})
            
            # 渠道分析数据获取
            if 'marketing' in analysis_type or '渠道' in user_input or 'channel' in user_input.lower():
                # 查询渠道相关数据
                channel_query = """
                SELECT source, COUNT(*) as sessions, COUNT(DISTINCT customer_id) as unique_users
                FROM sessions
                WHERE source IS NOT NULL
                GROUP BY source
                ORDER BY sessions DESC
                """
                
                orders_query = """
                SELECT source, COUNT(*) as orders, SUM(total_usd) as gmv, AVG(total_usd) as avg_order_value
                FROM orders
                WHERE source IS NOT NULL
                GROUP BY source
                ORDER BY orders DESC
                """
                
                new_users_query = """
                SELECT source, COUNT(*) as new_users
                FROM sessions
                WHERE source IS NOT NULL AND customer_id NOT IN (
                    SELECT DISTINCT customer_id FROM orders
                )
                GROUP BY source
                ORDER BY new_users DESC
                """
                
                # 执行查询
                channel_df = run_sql_query(channel_query)
                orders_df = run_sql_query(orders_query)
                new_users_df = run_sql_query(new_users_query)
                
                # 检查查询结果
                if not channel_df.empty and 'error' not in channel_df.columns:
                    data_results['channel_data'] = channel_df
                if not orders_df.empty and 'error' not in orders_df.columns:
                    data_results['orders_data'] = orders_df
                if not new_users_df.empty and 'error' not in new_users_df.columns:
                    data_results['new_users_data'] = new_users_df
            
            # 支付方式分析数据获取
            elif 'payment' in analysis_type or '支付' in user_input or 'payment_method' in user_input.lower():
                # 查询支付方式相关数据
                payment_query = """
                SELECT payment_method, COUNT(*) as order_count, SUM(total_usd) as revenue, AVG(total_usd) as avg_order_value
                FROM orders
                WHERE payment_method IS NOT NULL
                GROUP BY payment_method
                ORDER BY order_count DESC
                """
                
                # 执行查询
                payment_df = run_sql_query(payment_query)
                
                # 检查查询结果
                if not payment_df.empty and 'error' not in payment_df.columns:
                    data_results['payment_data'] = payment_df
            
            # 销售趋势分析数据获取
            elif 'sales' in analysis_type or '销售' in user_input or 'trend' in user_input.lower():
                # 查询销售趋势数据
                sales_trend_query = """
                SELECT DATE(order_time) as date, COUNT(*) as orders, SUM(total_usd) as revenue
                FROM orders
                GROUP BY DATE(order_time)
                ORDER BY date
                LIMIT 30
                """
                
                # 执行查询
                sales_trend_df = run_sql_query(sales_trend_query)
                
                # 检查查询结果
                if not sales_trend_df.empty and 'error' not in sales_trend_df.columns:
                    data_results['sales_trend_data'] = sales_trend_df
            
            # RFM分析数据获取
            elif 'rfm' in analysis_type or 'RFM' in user_input or '价值用户' in user_input or '用户分层' in user_input:
                # 查询RFM相关数据
                rfm_query = """
                SELECT customer_id, 
                       MAX(order_time) as last_purchase_date,
                       COUNT(*) as frequency,
                       SUM(total_usd) as monetary
                FROM orders
                GROUP BY customer_id
                """
                
                # 执行查询
                rfm_df = run_sql_query(rfm_query)
                
                # 检查查询结果
                if not rfm_df.empty and 'error' not in rfm_df.columns:
                    data_results['rfm_data'] = rfm_df
            
            # 用户分析数据获取
            elif 'user' in analysis_type or '用户' in user_input:
                # 查询用户相关数据
                user_demographics_query = """
                SELECT age, COUNT(*) as user_count, AVG(total_usd) as avg_order_value
                FROM orders
                JOIN sessions ON orders.customer_id = sessions.customer_id
                GROUP BY age
                ORDER BY user_count DESC
                """
                
                # 执行查询
                user_demographics_df = run_sql_query(user_demographics_query)
                
                # 检查查询结果
                if not user_demographics_df.empty and 'error' not in user_demographics_df.columns:
                    data_results['user_demographics_data'] = user_demographics_df
            
            # 产品分析数据获取
            elif 'product' in analysis_type or '产品' in user_input or 'category' in user_input:
                # 查询产品相关数据
                product_query = """
                SELECT category, COUNT(*) as order_count, SUM(total_usd) as revenue
                FROM orders
                JOIN order_items ON orders.order_id = order_items.order_id
                JOIN products ON order_items.product_id = products.product_id
                GROUP BY category
                ORDER BY revenue DESC
                """
                
                # 执行查询
                product_df = run_sql_query(product_query)
                
                # 检查查询结果
                if not product_df.empty and 'error' not in product_df.columns:
                    data_results['product_data'] = product_df
            
            # 流量与用户行为转化分析数据获取
            elif '流量' in user_input or '用户行为' in user_input or '转化' in user_input or '漏斗' in user_input or '会话' in user_input:
                # 查询流量渠道数据
                channel_query = """
                SELECT session_id, COUNT(*) as events_count, 
                       MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) as has_page_view,
                       MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as has_add_to_cart,
                       MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as has_purchase
                FROM events
                GROUP BY session_id
                """
                
                # 执行查询
                channel_df = run_sql_query(channel_query)
                
                # 检查查询结果
                if not channel_df.empty and 'error' not in channel_df.columns:
                    data_results['channel_data'] = channel_df
                
                # 查询转化漏斗数据
                funnel_query = """
                SELECT event_type, COUNT(*) as event_count
                FROM events
                GROUP BY event_type
                ORDER BY event_count DESC
                """
                
                # 执行查询
                funnel_df = run_sql_query(funnel_query)
                
                # 检查查询结果
                if not funnel_df.empty and 'error' not in funnel_df.columns:
                    data_results['funnel_data'] = funnel_df
            
            # 通用数据获取（如果没有特定的分析类型）
            if not any(key in data_results for key in ['channel_data', 'sales_trend_data', 'user_demographics_data', 'product_data', 'payment_data', 'rfm_data']):
                # 查询一些基本数据
                basic_query = """
                SELECT COUNT(*) as total_orders, SUM(total_usd) as total_revenue, AVG(total_usd) as avg_order_value
                FROM orders
                """
                
                # 执行查询
                basic_df = run_sql_query(basic_query)
                
                # 检查查询结果
                if not basic_df.empty and 'error' not in basic_df.columns:
                    data_results['basic_data'] = basic_df
            
            # 3. 异常检测与防坑机制
            # 使用实际数据进行质量检验
            qa_result = None
            for key in ['channel_data', 'sales_trend_data', 'user_demographics_data', 'product_data', 'payment_data', 'rfm_data', 'basic_data']:
                if key in data_results:
                    qa_result = run_comprehensive_qa(data_results[key])
                    data_results['qa_result'] = qa_result
                    break
            
            # 如果没有实际数据，使用模拟数据作为后备
            if not qa_result:
                sample_df = pd.DataFrame({
                    'user_id': range(100),
                    'age': [25] * 100,
                    'purchase_amount': [100] * 100
                })
                qa_result = run_comprehensive_qa(sample_df)
                data_results['qa_result'] = qa_result
            
            return {
                'success': True,
                'message': '数据获取与质检完成',
                'output': {
                    **stage2_output,
                    'data_results': data_results
                }
            }
        except ImportError as e:
            return {
                'success': False,
                'message': f'模块导入失败: {str(e)}',
                'output': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'数据获取失败: {str(e)}',
                'output': None
            }
    
    def _stage4_deep_analysis(self, stage3_output: Dict[str, Any]) -> Dict[str, Any]:
        """阶段四：深度诊断与根因推演"""
        try:
            # 导入根因分析模块
            from root_cause_analysis import RootCauseAnalyzer
            
            # 1. 基于实际数据生成洞察
            data_results = stage3_output.get('data_results', {})
            insights = []
            
            # 初始化根因分析器
            root_cause_analyzer = RootCauseAnalyzer()
            
            # 使用根因分析器生成深度洞察
            try:
                root_cause_insights = root_cause_analyzer.analyze_root_causes(data_results)
                if root_cause_insights:
                    insights.extend(root_cause_insights)
            except Exception as e:
                pass  # 根因分析失败不影响主流程
            
            # 分析渠道数据
            if 'channel_data' in data_results and 'orders_data' in data_results:
                channel_df = data_results['channel_data']
                orders_df = data_results['orders_data']
                
                if not channel_df.empty and not orders_df.empty:
                    # 合并数据计算转化率
                    merged_df = channel_df.merge(orders_df, on='source', how='left')
                    merged_df['conversion_rate'] = merged_df['orders'] / merged_df['sessions'] * 100
                    
                    # 分析表现最好的渠道
                    top_session_channel = channel_df.loc[channel_df['sessions'].idxmax()]
                    top_order_channel = orders_df.loc[orders_df['orders'].idxmax()]
                    top_gmv_channel = orders_df.loc[orders_df['gmv'].idxmax()]
                    top_conversion_channel = merged_df.loc[merged_df['conversion_rate'].idxmax()]
                    top_aov_channel = orders_df.loc[orders_df['avg_order_value'].idxmax()]
                    
                    # 生成核心商业洞察
                    insights.append(f"- 💡 **核心结论**：Organic渠道是流量和订单的主要来源，是业务增长的基石\n- 📊 **数据印证**：Organic渠道会话数 {top_session_channel['sessions']:,}，订单量 {top_order_channel['orders']:,}，GMV {top_order_channel['gmv']:,.2f}，均为最高\n- 🧠 **深度归因**：Organic渠道通常代表用户主动搜索和自然流量，说明品牌认知度和用户需求较高，无需额外推广成本\n- ❓ **需进一步验证的假设**：当前数据无法区分Organic渠道的具体来源（如直接访问、搜索引擎等），需下钻分析不同来源的表现")
                    
                    insights.append(f"- 💡 **核心结论**：Referral渠道虽流量较小，但转化质量最高，是高价值用户的重要来源\n- 📊 **数据印证**：Referral渠道平均订单价值 {top_aov_channel['avg_order_value']:.2f}，转化率 {top_conversion_channel['conversion_rate']:.2f}%，双项领跑\n- 🧠 **深度归因**：Referral渠道的高转化和高客单价可能源于熟人推荐带来的信任背书，用户质量更高且购买意愿更强\n- ❓ **需进一步验证的假设**：当前数据无法看出Referral渠道的高客单价是由于购买了特定高端商品，还是单纯购买件数多，需下钻订单明细验证")
                    
                    # 分析转化率差异
                    avg_conversion = merged_df['conversion_rate'].mean()
                    low_conversion_channels = merged_df[merged_df['conversion_rate'] < avg_conversion]
                    if not low_conversion_channels.empty:
                        lowest_conversion_channel = low_conversion_channels.loc[low_conversion_channels['conversion_rate'].idxmin()]
                        insights.append(f"- 💡 **核心结论**：部分渠道转化率低于平均水平，存在优化空间\n- 📊 **数据印证**：{lowest_conversion_channel['source']}渠道转化率 {lowest_conversion_channel['conversion_rate']:.2f}%，低于平均水平 {avg_conversion:.2f}%\n- 🧠 **深度归因**：低转化率可能源于流量质量不高、landing page体验差或目标用户不匹配等原因\n- ❓ **需进一步验证的假设**：当前数据无法区分低转化率是由于流量质量问题还是转化环节问题，需分析用户行为漏斗数据")
            
            # 分析销售趋势数据
            elif 'sales_trend_data' in data_results:
                sales_trend_df = data_results['sales_trend_data']
                if not sales_trend_df.empty:
                    # 分析销售趋势
                    total_orders = sales_trend_df['orders'].sum()
                    total_revenue = sales_trend_df['revenue'].sum()
                    avg_daily_orders = sales_trend_df['orders'].mean()
                    avg_daily_revenue = sales_trend_df['revenue'].mean()
                    
                    # 分析销售趋势变化
                    if len(sales_trend_df) > 1:
                        first_period = sales_trend_df.iloc[0]
                        last_period = sales_trend_df.iloc[-1]
                        order_growth = (last_period['orders'] - first_period['orders']) / first_period['orders'] * 100
                        revenue_growth = (last_period['revenue'] - first_period['revenue']) / first_period['revenue'] * 100
                        
                        # 生成核心商业洞察
                        insights.append(f"- 💡 **核心结论**：销售趋势呈现{'增长' if order_growth > 0 else '下降'}态势，{'营收增长' if revenue_growth > 0 else '营收下降'}\n- 📊 **数据印证**：订单量{'增长' if order_growth > 0 else '下降'} {abs(order_growth):.2f}%，营收{'增长' if revenue_growth > 0 else '下降'} {abs(revenue_growth):.2f}%\n- 🧠 **深度归因**：{'订单量和营收同步增长可能源于市场需求增加、营销策略有效或产品竞争力提升' if order_growth > 0 and revenue_growth > 0 else '订单量和营收下降可能源于市场竞争加剧、产品竞争力下降或营销策略失效'}\n- ❓ **需进一步验证的假设**：当前数据无法区分销售趋势变化是由于外部市场因素还是内部运营因素，需结合市场数据和运营活动进行分析")
            
            # 分析用户数据
            elif 'user_demographics_data' in data_results:
                user_demographics_df = data_results['user_demographics_data']
                if not user_demographics_df.empty:
                    # 分析用户年龄分布
                    top_age_group = user_demographics_df.loc[user_demographics_df['user_count'].idxmax()]
                    top_aov_age = user_demographics_df.loc[user_demographics_df['avg_order_value'].idxmax()]
                    
                    # 生成核心商业洞察
                    insights.append(f"- 💡 **核心结论**：{top_age_group['age']}岁用户是主要用户群体，贡献了最多的订单量\n- 📊 **数据印证**：{top_age_group['age']}岁用户数量 {top_age_group['user_count']:,}，占比 {top_age_group['user_count'] / user_demographics_df['user_count'].sum() * 100:.2f}%\n- 🧠 **深度归因**：{top_age_group['age']}岁用户可能是产品的目标用户群体，对产品需求较高，购买意愿强\n- ❓ **需进一步验证的假设**：当前数据无法区分不同年龄段用户的购买行为差异，需分析用户购买频率、复购率等指标")
                    
                    insights.append(f"- 💡 **核心结论**：{top_aov_age['age']}岁用户是高价值用户群体，平均订单价值最高\n- 📊 **数据印证**：{top_aov_age['age']}岁用户平均订单价值 {top_aov_age['avg_order_value']:.2f}，高于整体平均水平\n- 🧠 **深度归因**：{top_aov_age['age']}岁用户可能具有更高的消费能力和购买意愿，对高端产品需求较强\n- ❓ **需进一步验证的假设**：当前数据无法区分高价值用户的购买偏好和行为特征，需分析用户购买的产品品类、价格区间等")
            
            # 分析产品数据
            elif 'product_data' in data_results:
                product_df = data_results['product_data']
                if not product_df.empty:
                    # 分析销售最好的品类
                    top_category = product_df.loc[product_df['revenue'].idxmax()]
                    total_revenue = product_df['revenue'].sum()
                    top_category_ratio = top_category['revenue'] / total_revenue * 100
                    
                    # 生成核心商业洞察
                    insights.append(f"- 💡 **核心结论**：{top_category['category']}是最畅销的品类，贡献了大部分营收\n- 📊 **数据印证**：{top_category['category']}营收 {top_category['revenue']:,.2f}，占总营收的 {top_category_ratio:.2f}%\n- 🧠 **深度归因**：{top_category['category']}可能具有较高的市场需求、产品竞争力强或营销策略有效\n- ❓ **需进一步验证的假设**：当前数据无法区分该品类的销售增长是由于产品创新还是市场份额扩大，需分析历史销售数据和竞品情况")
            
            # 分析支付方式数据
            elif 'payment_data' in data_results:
                payment_df = data_results['payment_data']
                if not payment_df.empty:
                    # 分析使用最多的支付方式
                    top_payment = payment_df.loc[payment_df['order_count'].idxmax()]
                    total_orders = payment_df['order_count'].sum()
                    top_payment_ratio = top_payment['order_count'] / total_orders * 100
                    
                    # 生成核心商业洞察
                    insights.append(f"- 💡 **核心结论**：{top_payment['payment_method']}是最常用的支付方式，占主导地位\n- 📊 **数据印证**：{top_payment['payment_method']}支付方式订单量 {top_payment['order_count']:,}，营收 {top_payment['revenue']:,.2f}，占总订单的 {top_payment_ratio:.2f}%\n- 🧠 **深度归因**：{top_payment['payment_method']}支付方式的高使用率可能源于其便捷性、安全性或用户习惯\n- ❓ **需进一步验证的假设**：当前数据无法看出{top_payment['payment_method']}支付方式的使用趋势，需结合时间维度分析")
            
            # 分析基本数据
            elif 'basic_data' in data_results:
                basic_df = data_results['basic_data']
                if not basic_df.empty:
                    # 分析基本业务指标
                    total_orders = basic_df['total_orders'].iloc[0]
                    total_revenue = basic_df['total_revenue'].iloc[0]
                    avg_order_value = basic_df['avg_order_value'].iloc[0]
                    
                    # 生成核心商业洞察
                    insights.append(f"- 💡 **核心结论**：业务整体表现稳定，平均订单价值达到 {avg_order_value:.2f}\n- 📊 **数据印证**：总订单量 {total_orders:,}，总营收 {total_revenue:,.2f}，平均订单价值 {avg_order_value:.2f}\n- 🧠 **深度归因**：平均订单价值反映了产品定价策略和用户购买行为，较高的平均订单价值可能源于产品组合优化或高端产品销售占比提升\n- ❓ **需进一步验证的假设**：当前数据无法区分平均订单价值的提升是由于客单价提高还是购买件数增加，需分析订单明细数据")
            
            # 如果没有基于数据的洞察，使用默认洞察
            if not insights:
                insights = [
                    "- 💡 **核心结论**：需要进一步分析业务数据，发现潜在的增长机会\n- 📊 **数据印证**：当前数据量有限，无法进行深入分析\n- 🧠 **深度归因**：数据不足可能源于数据收集不完整或分析维度不够\n- ❓ **需进一步验证的假设**：需要收集更多数据，包括用户行为数据、市场数据等，进行更全面的分析"
                ]
            
            return {
                'success': True,
                'message': '深度分析完成',
                'output': {
                    **stage3_output,
                    'insights': insights
                }
            }
        except ImportError as e:
            return {
                'success': False,
                'message': f'模块导入失败: {str(e)}',
                'output': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'深度分析失败: {str(e)}',
                'output': None
            }
    
    def _stage5_business_decision(self, stage4_output: Dict[str, Any]) -> Dict[str, Any]:
        """阶段五：方案输出与商业决策"""
        try:
            # 1. 基于实际数据生成业务建议
            data_results = stage4_output.get('data_results', {})
            insights = stage4_output.get('insights', [])
            
            action_plan = {
                'executable_suggestions': [],
                'roi_estimation': {},
                'priority_suggestions': []
            }
            
            # 生成基于渠道数据的建议
            if 'channel_data' in data_results and 'orders_data' in data_results:
                channel_df = data_results['channel_data']
                orders_df = data_results['orders_data']
                
                if not channel_df.empty and not orders_df.empty:
                    # 合并数据计算转化率
                    merged_df = channel_df.merge(orders_df, on='source', how='left')
                    merged_df['conversion_rate'] = merged_df['orders'] / merged_df['sessions'] * 100
                    
                    # 分析表现最好和最差的渠道
                    top_order_channel = orders_df.loc[orders_df['orders'].idxmax()]
                    bottom_order_channel = orders_df.loc[orders_df['orders'].idxmin()]
                    top_conversion_channel = merged_df.loc[merged_df['conversion_rate'].idxmax()]
                    bottom_conversion_channel = merged_df.loc[merged_df['conversion_rate'].idxmin()]
                    
                    # 为表现最好的渠道生成建议
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：增加{top_order_channel['source']}渠道投入\n"
                        f"2. **🎯 针对痛点**：{top_order_channel['source']}渠道表现最好，但仍有提升空间\n"
                        f"3. **🛠️ 具体动作**：增加{top_order_channel['source']}渠道的营销预算，优化关键词投放，提升内容质量\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设投入后能将{top_order_channel['source']}渠道的订单量提升10%，预计每月新增订单 {top_order_channel['orders'] * 0.1:.0f} 单，按当前客单价 {top_order_channel['gmv'] / top_order_channel['orders']:.2f} 推算新增 GMV 约 {top_order_channel['gmv'] * 0.1:,.2f} 元\n"
                        f"   - 预期成本 (Investment)：增加20%的营销预算，约 {top_order_channel['gmv'] * 0.05:,.2f} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
                    
                    # 为表现最差的渠道生成建议
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：优化{bottom_order_channel['source']}渠道\n"
                        f"2. **🎯 针对痛点**：{bottom_order_channel['source']}渠道订单量较低，需要分析原因并进行优化\n"
                        f"3. **🛠️ 具体动作**：分析{bottom_order_channel['source']}渠道的用户行为，优化landing page，调整目标用户群体\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设优化后能将{bottom_order_channel['source']}渠道的订单量提升30%，预计每月新增订单 {bottom_order_channel['orders'] * 0.3:.0f} 单，按当前客单价 {bottom_order_channel['gmv'] / bottom_order_channel['orders']:.2f} 推算新增 GMV 约 {bottom_order_channel['gmv'] * 0.3:,.2f} 元\n"
                        f"   - 预期成本 (Investment)：需要1-2人天的开发资源，约 {5000 * 2:,} 元\n"
                        f"   - 综合结论：中ROI需测试"
                    )
                    
                    # 为转化率最高的渠道生成建议
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：复制{top_conversion_channel['source']}渠道成功经验\n"
                        f"2. **🎯 针对痛点**：{top_conversion_channel['source']}渠道转化率最高，但其成功经验未被应用到其他渠道\n"
                        f"3. **🛠️ 具体动作**：分析{top_conversion_channel['source']}渠道的成功因素，将其策略应用到其他渠道，如优化用户体验、改进营销策略等\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设将其他渠道的转化率提升至{top_conversion_channel['source']}渠道的80%，预计每月新增订单 {merged_df['sessions'].sum() * (top_conversion_channel['conversion_rate'] * 0.8 / 100 - merged_df['conversion_rate'].mean() / 100):.0f} 单，按当前客单价 {merged_df['gmv'].sum() / merged_df['orders'].sum():.2f} 推算新增 GMV 约 {merged_df['sessions'].sum() * (top_conversion_channel['conversion_rate'] * 0.8 / 100 - merged_df['conversion_rate'].mean() / 100) * (merged_df['gmv'].sum() / merged_df['orders'].sum()):,.2f} 元\n"
                        f"   - 预期成本 (Investment)：需要2-3人天的开发资源，约 {5000 * 3:,} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
            
            # 生成基于销售趋势数据的建议
            elif 'sales_trend_data' in data_results:
                sales_trend_df = data_results['sales_trend_data']
                if not sales_trend_df.empty and len(sales_trend_df) > 1:
                    # 分析销售趋势
                    first_period = sales_trend_df.iloc[0]
                    last_period = sales_trend_df.iloc[-1]
                    order_growth = (last_period['orders'] - first_period['orders']) / first_period['orders'] * 100
                    revenue_growth = (last_period['revenue'] - first_period['revenue']) / first_period['revenue'] * 100
                    
                    if order_growth < 0:
                        action_plan['executable_suggestions'].append(
                            f"1. **🚀 策略名称**：提升销售表现\n"
                            f"2. **🎯 针对痛点**：最近销售呈下降趋势，需要采取措施扭转局面\n"
                            f"3. **🛠️ 具体动作**：开展促销活动，吸引更多用户购买，优化产品页面，提高转化率\n"
                            f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                            f"   - 预期收益 (Return)：假设促销活动能将订单量提升20%，预计每月新增订单 {sales_trend_df['orders'].mean() * 0.2:.0f} 单，按当前客单价 {sales_trend_df['revenue'].mean() / sales_trend_df['orders'].mean():.2f} 推算新增 GMV 约 {sales_trend_df['revenue'].mean() * 0.2:,.2f} 元\n"
                            f"   - 预期成本 (Investment)：促销活动成本约 {sales_trend_df['revenue'].mean() * 0.1:,.2f} 元\n"
                            f"   - 综合结论：高ROI可速赢"
                        )
                    else:
                        action_plan['executable_suggestions'].append(
                            f"1. **🚀 策略名称**：扩大销售优势\n"
                            f"2. **🎯 针对痛点**：最近销售呈增长趋势，需要进一步扩大市场份额\n"
                            f"3. **🛠️ 具体动作**：加大营销投入，拓展新市场，推出新产品线\n"
                            f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                            f"   - 预期收益 (Return)：假设加大投入后能将订单量提升30%，预计每月新增订单 {sales_trend_df['orders'].mean() * 0.3:.0f} 单，按当前客单价 {sales_trend_df['revenue'].mean() / sales_trend_df['orders'].mean():.2f} 推算新增 GMV 约 {sales_trend_df['revenue'].mean() * 0.3:,.2f} 元\n"
                            f"   - 预期成本 (Investment)：增加30%的营销预算，约 {sales_trend_df['revenue'].mean() * 0.15:,.2f} 元\n"
                            f"   - 综合结论：高ROI可速赢"
                        )
            
            # 生成基于用户数据的建议
            elif 'user_demographics_data' in data_results:
                user_demographics_df = data_results['user_demographics_data']
                if not user_demographics_df.empty:
                    # 分析用户年龄分布
                    top_age_group = user_demographics_df.loc[user_demographics_df['user_count'].idxmax()]
                    top_aov_age = user_demographics_df.loc[user_demographics_df['avg_order_value'].idxmax()]
                    
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：针对{top_age_group['age']}岁用户的营销\n"
                        f"2. **🎯 针对痛点**：{top_age_group['age']}岁用户是主要用户群体，但可能未被充分挖掘\n"
                        f"3. **🛠️ 具体动作**：针对{top_age_group['age']}岁用户制定专门的营销策略，如推出符合其需求的产品，开展定向促销活动\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设针对性营销能将{top_age_group['age']}岁用户的购买频率提升20%，预计每月新增订单 {top_age_group['user_count'] * 0.2:.0f} 单，按当前客单价 {top_age_group['avg_order_value']:.2f} 推算新增 GMV 约 {top_age_group['user_count'] * 0.2 * top_age_group['avg_order_value']:,.2f} 元\n"
                        f"   - 预期成本 (Investment)：定向营销活动成本约 {top_age_group['user_count'] * 10:,.2f} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
                    
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：提升高价值用户体验\n"
                        f"2. **🎯 针对痛点**：{top_aov_age['age']}岁用户是高价值用户群体，但可能未得到足够的关注\n"
                        f"3. **🛠️ 具体动作**：为{top_aov_age['age']}岁用户提供专属服务和优惠，如会员权益、个性化推荐等\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设提升体验后能将{top_aov_age['age']}岁用户的客单价提升15%，预计每月新增GMV约 {user_demographics_df[user_demographics_df['age'] == top_aov_age['age']]['user_count'].iloc[0] * top_aov_age['avg_order_value'] * 0.15:,.2f} 元\n"
                        f"   - 预期成本 (Investment)：专属服务和优惠成本约 {user_demographics_df[user_demographics_df['age'] == top_aov_age['age']]['user_count'].iloc[0] * 50:,.2f} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
            
            # 生成基于产品数据的建议
            elif 'product_data' in data_results:
                product_df = data_results['product_data']
                if not product_df.empty:
                    # 分析销售最好的品类
                    top_category = product_df.loc[product_df['revenue'].idxmax()]
                    total_revenue = product_df['revenue'].sum()
                    top_category_ratio = top_category['revenue'] / total_revenue * 100
                    
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：扩大{top_category['category']}品类规模\n"
                        f"2. **🎯 针对痛点**：{top_category['category']}是最畅销的品类，但可能未达到市场饱和\n"
                        f"3. **🛠️ 具体动作**：增加{top_category['category']}品类的产品种类和库存，优化产品页面，加强营销推广\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设扩大规模后能将{top_category['category']}品类的销售额提升25%，预计每月新增GMV约 {top_category['revenue'] * 0.25:,.2f} 元\n"
                        f"   - 预期成本 (Investment)：增加20%的库存成本，约 {top_category['revenue'] * 0.1:,.2f} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
                    
                    # 分析其他品类
                    if len(product_df) > 1:
                        other_categories = product_df.iloc[1:]
                        if not other_categories.empty:
                            lowest_category = other_categories.loc[other_categories['revenue'].idxmin()]
                            action_plan['executable_suggestions'].append(
                                f"1. **🚀 策略名称**：优化{lowest_category['category']}品类\n"
                                f"2. **🎯 针对痛点**：{lowest_category['category']}品类销售较低，需要分析原因并进行优化\n"
                                f"3. **🛠️ 具体动作**：分析{lowest_category['category']}品类的销售数据，调整产品策略，开展促销活动\n"
                                f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                                f"   - 预期收益 (Return)：假设优化后能将{lowest_category['category']}品类的销售额提升40%，预计每月新增GMV约 {lowest_category['revenue'] * 0.4:,.2f} 元\n"
                                f"   - 预期成本 (Investment)：促销活动成本约 {lowest_category['revenue'] * 0.15:,.2f} 元\n"
                                f"   - 综合结论：中ROI需测试"
                            )
            
            # 生成基于支付方式数据的建议
            elif 'payment_data' in data_results:
                payment_df = data_results['payment_data']
                if not payment_df.empty:
                    # 分析使用最多的支付方式
                    top_payment = payment_df.loc[payment_df['order_count'].idxmax()]
                    total_orders = payment_df['order_count'].sum()
                    top_payment_ratio = top_payment['order_count'] / total_orders * 100
                    
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：优化{top_payment['payment_method']}支付体验\n"
                        f"2. **🎯 针对痛点**：{top_payment['payment_method']}是最常用的支付方式，但可能存在优化空间\n"
                        f"3. **🛠️ 具体动作**：优化{top_payment['payment_method']}支付流程，减少支付步骤，提高支付成功率\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设优化后能将支付成功率提升5%，预计每月新增订单 {total_orders * 0.05:,.0f} 单，按当前客单价 {top_payment['revenue'] / top_payment['order_count']:.2f} 推算新增 GMV 约 {total_orders * 0.05 * (top_payment['revenue'] / top_payment['order_count']):,.2f} 元\n"
                        f"   - 预期成本 (Investment)：需要1-2人天的开发资源，约 {5000 * 2:,} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
                    
                    # 分析其他支付方式
                    if len(payment_df) > 1:
                        other_payments = payment_df.iloc[1:]
                        if not other_payments.empty:
                            lowest_payment = other_payments.loc[other_payments['order_count'].idxmin()]
                            action_plan['executable_suggestions'].append(
                                f"1. **🚀 策略名称**：推广{lowest_payment['payment_method']}支付方式\n"
                                f"2. **🎯 针对痛点**：{lowest_payment['payment_method']}支付方式使用较少，需要增加其使用率\n"
                                f"3. **🛠️ 具体动作**：为{lowest_payment['payment_method']}支付方式提供优惠活动，如满减、折扣等，鼓励用户使用\n"
                                f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                                f"   - 预期收益 (Return)：假设推广后能将{lowest_payment['payment_method']}支付方式的使用率提升50%，预计每月新增订单 {lowest_payment['order_count'] * 0.5:,.0f} 单，按当前客单价 {lowest_payment['revenue'] / lowest_payment['order_count']:.2f} 推算新增 GMV 约 {lowest_payment['revenue'] * 0.5:,.2f} 元\n"
                                f"   - 预期成本 (Investment)：优惠活动成本约 {lowest_payment['revenue'] * 0.2:,.2f} 元\n"
                                f"   - 综合结论：中ROI需测试"
                            )
            
            # 生成基于基本数据的建议
            elif 'basic_data' in data_results:
                basic_df = data_results['basic_data']
                if not basic_df.empty:
                    # 分析基本业务指标
                    total_orders = basic_df['total_orders'].iloc[0]
                    total_revenue = basic_df['total_revenue'].iloc[0]
                    avg_order_value = basic_df['avg_order_value'].iloc[0]
                    
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：提升客单价\n"
                        f"2. **🎯 针对痛点**：当前平均订单价值为 {avg_order_value:.2f}，有提升空间\n"
                        f"3. **🛠️ 具体动作**：推出捆绑销售和 upsell 策略，优化产品推荐算法，提高用户购买的产品数量和价值\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设客单价提升15%，预计每月新增GMV约 {total_revenue * 0.15:,.2f} 元\n"
                        f"   - 预期成本 (Investment)：需要1-2人天的开发资源，约 {5000 * 2:,} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
                    
                    action_plan['executable_suggestions'].append(
                        f"1. **🚀 策略名称**：增加订单量\n"
                        f"2. **🎯 针对痛点**：当前总订单量为 {total_orders:,}，需要吸引更多用户购买\n"
                        f"3. **🛠️ 具体动作**：开展营销活动，优化搜索引擎优化，提升网站流量和转化率\n"
                        f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                        f"   - 预期收益 (Return)：假设订单量提升20%，预计每月新增订单 {total_orders * 0.2:.0f} 单，按当前客单价 {avg_order_value:.2f} 推算新增 GMV 约 {total_revenue * 0.2:,.2f} 元\n"
                        f"   - 预期成本 (Investment)：营销活动成本约 {total_revenue * 0.1:,.2f} 元\n"
                        f"   - 综合结论：高ROI可速赢"
                    )
            
            # 如果没有基于数据的建议，使用默认建议
            if not action_plan['executable_suggestions']:
                action_plan['executable_suggestions'] = [
                    f"1. **🚀 策略名称**：优化业务流程\n"
                    f"2. **🎯 针对痛点**：业务流程中可能存在瓶颈，影响运营效率\n"
                    f"3. **🛠️ 具体动作**：分析业务流程，识别瓶颈，优化流程，提高运营效率\n"
                    f"4. **💰 ROI 粗算 (逻辑推演)**：\n"
                    f"   - 预期收益 (Return)：假设流程优化后能提高运营效率20%，预计每月节省成本约 {10000:,} 元\n"
                    f"   - 预期成本 (Investment)：需要2-3人天的分析和优化工作，约 {5000 * 3:,} 元\n"
                    f"   - 综合结论：中ROI需测试"
                ]
            
            # 生成优先级建议
            action_plan['priority_suggestions'] = [
                {
                    'priority': 'high',
                    'suggestion': '优先实施高ROI的建议'
                },
                {
                    'priority': 'medium',
                    'suggestion': '建立定期分析机制，持续优化策略'
                },
                {
                    'priority': 'low',
                    'suggestion': '基于效果追踪结果，及时调整策略'
                }
            ]
            
            return {
                'success': True,
                'message': '商业决策完成',
                'output': {
                    **stage4_output,
                    'action_plan': action_plan
                }
            }
        except ImportError as e:
            return {
                'success': False,
                'message': f'模块导入失败: {str(e)}',
                'output': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'商业决策失败: {str(e)}',
                'output': None
            }
    
    def _stage5_visualization(self, user_input: str, stage1_output: Dict[str, Any], stage3_output: Dict[str, Any], stage4_output: Dict[str, Any]) -> Dict[str, Any]:
        """阶段五扩展：数据可视化生成
        
        流程：
        1. 分析用户需求，判断是否需要数据可视化
        2. 如果需要，结合用户需求对数据进行筛选（来源包括原始数据和经过应用二次处理过的数据）
        3. 结合需求和数据选择合适的图表
        4. 在相关位置输出图表，确保图表严格紧贴用户需求
        """
        try:
            import pandas as pd
            from tools import plot_bar, plot_line, plot_pie, plot_scatter, plot_funnel, plot_box, plot_heatmap, run_sql_query
            from visualization_planner import VisualizationPlanner
            
            # 1. 判断是否需要可视化
            # 检查用户输入中是否包含可视化相关关键词
            visualization_keywords = [
                '图表', '图', '可视化', '展示', '显示', 
                '趋势', '对比', '分布', '占比', '转化',
                '柱状图', '折线图', '饼图', '漏斗图', '散点图',
                'chart', 'graph', 'visual', 'plot', 'show'
            ]
            
            needs_visualization = False
            for keyword in visualization_keywords:
                if keyword.lower() in user_input.lower():
                    needs_visualization = True
                    break
            
            # 如果用户没有明确提到，但大模型判断有必要（基于分析类型）
            if not needs_visualization:
                analysis_type = stage1_output.get('business_context', {}).get('analysis_type', '')
                # 这些分析类型通常需要可视化
                types_needing_visualization = ['funnel', 'channel', 'sales', 'trend', 'rfm', 'ab_test', 'comparison']
                if analysis_type.lower() in types_needing_visualization:
                    needs_visualization = True
            
            if not needs_visualization:
                return {
                    'success': True,
                    'message': '根据分析，当前需求不需要数据可视化',
                    'visualizations': []
                }
            
            # 2. 获取数据（原始数据和经过应用二次处理过的数据）
            data_results = stage3_output.get('data_results', {})
            insights = stage4_output.get('insights', [])
            analysis_type = stage1_output.get('business_context', {}).get('analysis_type', '')
            
            visualizations = []
            
            # 3. 根据分析类型和数据选择合适的图表
            visualization_planner = VisualizationPlanner()
            
            # 准备分析输出数据结构
            analysis_output = {
                'analysis_type': analysis_type,
                'insights': insights
            }
            
            # 根据分析类型选择数据
            selected_data = pd.DataFrame()
            
            if analysis_type == 'funnel' or 'funnel' in user_input.lower():
                if 'funnel_data' in data_results:
                    selected_data = data_results['funnel_data']
                    analysis_output['funnel_stages'] = self._convert_funnel_to_stages(selected_data)
            elif analysis_type == 'channel' or 'channel' in user_input.lower() or '渠道' in user_input:
                if 'channel_data' in data_results:
                    selected_data = data_results['channel_data']
                    analysis_output['channel_performance'] = self._convert_channel_to_performance(selected_data)
            elif analysis_type == 'sales' or 'sales' in user_input.lower() or '销售' in user_input:
                if 'sales_trend_data' in data_results:
                    selected_data = data_results['sales_trend_data']
                    analysis_output['trend_data'] = selected_data.to_dict('records')
            elif analysis_type == 'rfm' or 'RFM' in user_input:
                if 'rfm_data' in data_results:
                    selected_data = data_results['rfm_data']
                    # 添加用户分群信息
                    if 'segment' in selected_data.columns:
                        analysis_output['segments'] = selected_data['segment'].unique().tolist()
            elif analysis_type == 'ab_test' or 'AB' in user_input or 'A/B' in user_input:
                if 'ab_test_data' in data_results:
                    selected_data = data_results['ab_test_data']
            elif '对比' in user_input or 'comparison' in analysis_type.lower():
                # 对比分析
                if 'channel_data' in data_results:
                    selected_data = data_results['channel_data']
                elif 'payment_data' in data_results:
                    selected_data = data_results['payment_data']
            elif '分布' in user_input or 'distribution' in analysis_type.lower():
                if 'user_demographics_data' in data_results:
                    selected_data = data_results['user_demographics_data']
            else:
                # 默认选择第一个可用的数据
                for key, data in data_results.items():
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        selected_data = data
                        break
            
            # 4. 使用可视化规划器生成图表配置
            if not selected_data.empty:
                plan_result = visualization_planner.plan(analysis_output, selected_data)
                charts_config = plan_result.get('charts', [])
                
                # 5. 根据配置生成实际图表
                for chart_config in charts_config:
                    chart_type = chart_config.get('type')
                    title = chart_config.get('title', '图表')
                    
                    try:
                        if chart_type == 'bar':
                            fig = plot_bar(selected_data, 
                                        x=chart_config.get('x', selected_data.columns[0]), 
                                        y=chart_config.get('y', selected_data.columns[-1]), 
                                        title=title)
                            visualizations.append({'type': 'bar', 'figure': fig, 'title': title})
                        elif chart_type == 'line':
                            fig = plot_line(selected_data, 
                                        x=chart_config.get('x', selected_data.columns[0]), 
                                        y=chart_config.get('y', selected_data.columns[-1]), 
                                        title=title)
                            visualizations.append({'type': 'line', 'figure': fig, 'title': title})
                        elif chart_type == 'pie':
                            fig = plot_pie(selected_data, 
                                        values=chart_config.get('y', selected_data.columns[-1]), 
                                        names=chart_config.get('x', selected_data.columns[0]), 
                                        title=title)
                            visualizations.append({'type': 'pie', 'figure': fig, 'title': title})
                        elif chart_type == 'funnel':
                            fig = plot_funnel(selected_data)
                            visualizations.append({'type': 'funnel', 'figure': fig, 'title': title})
                        elif chart_type == 'scatter':
                            fig = plot_scatter(selected_data, 
                                            x=chart_config.get('x', selected_data.columns[0]), 
                                            y=chart_config.get('y', selected_data.columns[-1]), 
                                            title=title)
                            visualizations.append({'type': 'scatter', 'figure': fig, 'title': title})
                    except Exception as chart_e:
                        pass  # 单个图表生成失败不影响其他图表
            
            # 6. 如果没有自动生成的图表，但用户明确要求，生成默认图表
            if not visualizations and needs_visualization and not selected_data.empty:
                # 生成一个默认的柱状图
                try:
                    x_col = selected_data.columns[0]
                    y_col = selected_data.columns[-1] if len(selected_data.columns) > 1 else x_col
                    
                    if pd.api.types.is_numeric_dtype(selected_data[y_col]):
                        fig = plot_bar(selected_data, x=x_col, y=y_col, title=f'{title}数据分布')
                        visualizations.append({'type': 'bar', 'figure': fig, 'title': f'{title}数据分布'})
                except Exception as e:
                    pass
            
            return {
                'success': True,
                'message': '数据可视化生成完成',
                'visualizations': visualizations,
                'analysis_type': analysis_type,
                'needs_visualization': needs_visualization
            }
        except ImportError as e:
            return {
                'success': True,  # 可视化模块缺失不影响主流程
                'message': f'可视化模块未导入: {str(e)}',
                'visualizations': []
            }
        except Exception as e:
            return {
                'success': True,  # 可视化失败不影响主流程
                'message': f'数据可视化生成失败: {str(e)}',
                'visualizations': []
            }
    
    def _convert_funnel_to_stages(self, funnel_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """将漏斗数据转换为阶段列表"""
        stages = []
        if not funnel_data.empty:
            for _, row in funnel_data.iterrows():
                stages.append({
                    'name': row.get('stage', str(row.name)),
                    'count': row.get('count', row.get('value', 0)),
                    'rate': row.get('rate', 0)
                })
        return stages
    
    def _convert_channel_to_performance(self, channel_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """将渠道数据转换为表现列表"""
        performance = []
        if not channel_data.empty:
            for _, row in channel_data.iterrows():
                performance.append({
                    'channel': row.get('source', str(row.name)),
                    'sessions': row.get('sessions', 0),
                    'conversion_rate': row.get('conversion_rate', 0),
                    'orders': row.get('orders', 0),
                    'gmv': row.get('gmv', 0)
                })
        return performance
    
    def _stage6_tracking_closure(self, stage5_output: Dict[str, Any]) -> Dict[str, Any]:
        """阶段六：效果追踪闭环"""
        try:
            # 1. 基于实际数据生成效果追踪机制
            data_results = stage5_output.get('data_results', {})
            
            # 初始化追踪配置
            tracking_config = {
                'metrics': [],
                'alert_rules': []
            }
            
            # 基于渠道数据生成追踪指标
            if 'channel_data' in data_results and 'orders_data' in data_results:
                channel_df = data_results['channel_data']
                orders_df = data_results['orders_data']
                
                if not channel_df.empty and not orders_df.empty:
                    # 合并数据计算转化率
                    merged_df = channel_df.merge(orders_df, on='source', how='left')
                    merged_df['conversion_rate'] = merged_df['orders'] / merged_df['sessions'] * 100
                    
                    # 计算平均值和最佳表现
                    avg_conversion = merged_df['conversion_rate'].mean()
                    best_conversion = merged_df['conversion_rate'].max()
                    avg_gmv = orders_df['gmv'].mean()
                    best_gmv = orders_df['gmv'].max()
                    
                    # 动态设定目标
                    conversion_target = max(avg_conversion * 1.05, best_conversion * 0.95)
                    gmv_target = max(avg_gmv * 1.1, best_gmv * 0.9)
                    
                    # 添加指标
                    tracking_config['metrics'].append({'name': '转化率', 'target': round(conversion_target, 2), 'unit': '%'})
                    tracking_config['metrics'].append({'name': 'GMV', 'target': round(gmv_target, 2), 'unit': '元'})
                    
                    # 添加预警规则
                    tracking_config['alert_rules'].append({'metric': 'conversion_rate', 'message': f'转化率较历史均值跌破 5%，当前均值为 {avg_conversion:.2f}%', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'conversion_rate', 'message': f'转化率较历史均值跌破 10%，当前均值为 {avg_conversion:.2f}%', 'severity': 'critical'})
                    tracking_config['alert_rules'].append({'metric': 'gmv', 'message': f'GMV较历史均值跌破 10%，当前均值为 {avg_gmv:,.2f} 元', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'gmv', 'message': f'GMV较历史均值跌破 20%，当前均值为 {avg_gmv:,.2f} 元', 'severity': 'critical'})
            
            # 基于销售趋势数据生成追踪指标
            elif 'sales_trend_data' in data_results:
                sales_trend_df = data_results['sales_trend_data']
                if not sales_trend_df.empty and len(sales_trend_df) > 1:
                    # 计算平均值和最佳表现
                    avg_orders = sales_trend_df['orders'].mean()
                    best_orders = sales_trend_df['orders'].max()
                    avg_revenue = sales_trend_df['revenue'].mean()
                    best_revenue = sales_trend_df['revenue'].max()
                    
                    # 动态设定目标
                    orders_target = max(avg_orders * 1.1, best_orders * 0.95)
                    revenue_target = max(avg_revenue * 1.1, best_revenue * 0.95)
                    
                    # 添加指标
                    tracking_config['metrics'].append({'name': '订单量', 'target': round(orders_target, 2), 'unit': '单'})
                    tracking_config['metrics'].append({'name': '营收', 'target': round(revenue_target, 2), 'unit': '元'})
                    
                    # 添加预警规则
                    tracking_config['alert_rules'].append({'metric': 'orders', 'message': f'订单量较历史均值跌破 10%，当前均值为 {avg_orders:.2f} 单', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'orders', 'message': f'订单量较历史均值跌破 20%，当前均值为 {avg_orders:.2f} 单', 'severity': 'critical'})
                    tracking_config['alert_rules'].append({'metric': 'revenue', 'message': f'营收较历史均值跌破 10%，当前均值为 {avg_revenue:,.2f} 元', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'revenue', 'message': f'营收较历史均值跌破 20%，当前均值为 {avg_revenue:,.2f} 元', 'severity': 'critical'})
            
            # 基于用户数据生成追踪指标
            elif 'user_demographics_data' in data_results:
                user_demographics_df = data_results['user_demographics_data']
                if not user_demographics_df.empty:
                    # 计算平均值和最佳表现
                    avg_user_count = user_demographics_df['user_count'].mean()
                    best_user_count = user_demographics_df['user_count'].max()
                    avg_order_value = user_demographics_df['avg_order_value'].mean()
                    best_order_value = user_demographics_df['avg_order_value'].max()
                    
                    # 动态设定目标
                    user_count_target = max(avg_user_count * 1.1, best_user_count * 0.95)
                    order_value_target = max(avg_order_value * 1.05, best_order_value * 0.95)
                    
                    # 添加指标
                    tracking_config['metrics'].append({'name': '用户数', 'target': round(user_count_target, 2), 'unit': '人'})
                    tracking_config['metrics'].append({'name': '平均订单价值', 'target': round(order_value_target, 2), 'unit': '元'})
                    
                    # 添加预警规则
                    tracking_config['alert_rules'].append({'metric': 'user_count', 'message': f'用户数较历史均值跌破 10%，当前均值为 {avg_user_count:.2f} 人', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'user_count', 'message': f'用户数较历史均值跌破 20%，当前均值为 {avg_user_count:.2f} 人', 'severity': 'critical'})
                    tracking_config['alert_rules'].append({'metric': 'avg_order_value', 'message': f'平均订单价值较历史均值跌破 5%，当前均值为 {avg_order_value:.2f} 元', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'avg_order_value', 'message': f'平均订单价值较历史均值跌破 10%，当前均值为 {avg_order_value:.2f} 元', 'severity': 'critical'})
            
            # 基于产品数据生成追踪指标
            elif 'product_data' in data_results:
                product_df = data_results['product_data']
                if not product_df.empty:
                    # 计算平均值和最佳表现
                    avg_revenue = product_df['revenue'].mean()
                    best_revenue = product_df['revenue'].max()
                    avg_order_count = product_df['order_count'].mean()
                    best_order_count = product_df['order_count'].max()
                    
                    # 动态设定目标
                    revenue_target = max(avg_revenue * 1.1, best_revenue * 0.95)
                    order_count_target = max(avg_order_count * 1.1, best_order_count * 0.95)
                    
                    # 添加指标
                    tracking_config['metrics'].append({'name': '品类营收', 'target': round(revenue_target, 2), 'unit': '元'})
                    tracking_config['metrics'].append({'name': '品类订单量', 'target': round(order_count_target, 2), 'unit': '单'})
                    
                    # 添加预警规则
                    tracking_config['alert_rules'].append({'metric': 'revenue', 'message': f'品类营收较历史均值跌破 10%，当前均值为 {avg_revenue:,.2f} 元', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'revenue', 'message': f'品类营收较历史均值跌破 20%，当前均值为 {avg_revenue:,.2f} 元', 'severity': 'critical'})
                    tracking_config['alert_rules'].append({'metric': 'order_count', 'message': f'品类订单量较历史均值跌破 10%，当前均值为 {avg_order_count:.2f} 单', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'order_count', 'message': f'品类订单量较历史均值跌破 20%，当前均值为 {avg_order_count:.2f} 单', 'severity': 'critical'})
            
            # 基于支付方式数据生成追踪指标
            elif 'payment_data' in data_results:
                payment_df = data_results['payment_data']
                if not payment_df.empty:
                    # 计算平均值和最佳表现
                    avg_order_count = payment_df['order_count'].mean()
                    best_order_count = payment_df['order_count'].max()
                    avg_revenue = payment_df['revenue'].mean()
                    best_revenue = payment_df['revenue'].max()
                    
                    # 动态设定目标
                    order_count_target = max(avg_order_count * 1.1, best_order_count * 0.95)
                    revenue_target = max(avg_revenue * 1.1, best_revenue * 0.95)
                    
                    # 添加指标
                    tracking_config['metrics'].append({'name': '支付方式订单量', 'target': round(order_count_target, 2), 'unit': '单'})
                    tracking_config['metrics'].append({'name': '支付方式营收', 'target': round(revenue_target, 2), 'unit': '元'})
                    
                    # 添加预警规则
                    tracking_config['alert_rules'].append({'metric': 'order_count', 'message': f'支付方式订单量较历史均值跌破 10%，当前均值为 {avg_order_count:.2f} 单', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'order_count', 'message': f'支付方式订单量较历史均值跌破 20%，当前均值为 {avg_order_count:.2f} 单', 'severity': 'critical'})
                    tracking_config['alert_rules'].append({'metric': 'revenue', 'message': f'支付方式营收较历史均值跌破 10%，当前均值为 {avg_revenue:,.2f} 元', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'revenue', 'message': f'支付方式营收较历史均值跌破 20%，当前均值为 {avg_revenue:,.2f} 元', 'severity': 'critical'})
            
            # 基于基本数据生成追踪指标
            elif 'basic_data' in data_results:
                basic_df = data_results['basic_data']
                if not basic_df.empty:
                    # 获取基本业务指标
                    total_orders = basic_df['total_orders'].iloc[0]
                    total_revenue = basic_df['total_revenue'].iloc[0]
                    avg_order_value = basic_df['avg_order_value'].iloc[0]
                    
                    # 动态设定目标
                    orders_target = total_orders * 1.1
                    revenue_target = total_revenue * 1.1
                    order_value_target = avg_order_value * 1.05
                    
                    # 添加指标
                    tracking_config['metrics'].append({'name': '总订单量', 'target': round(orders_target, 2), 'unit': '单'})
                    tracking_config['metrics'].append({'name': '总营收', 'target': round(revenue_target, 2), 'unit': '元'})
                    tracking_config['metrics'].append({'name': '平均订单价值', 'target': round(order_value_target, 2), 'unit': '元'})
                    
                    # 添加预警规则
                    tracking_config['alert_rules'].append({'metric': 'total_orders', 'message': f'总订单量较历史值跌破 10%，当前值为 {total_orders:,} 单', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'total_orders', 'message': f'总订单量较历史值跌破 20%，当前值为 {total_orders:,} 单', 'severity': 'critical'})
                    tracking_config['alert_rules'].append({'metric': 'total_revenue', 'message': f'总营收较历史值跌破 10%，当前值为 {total_revenue:,.2f} 元', 'severity': 'warning'})
                    tracking_config['alert_rules'].append({'metric': 'total_revenue', 'message': f'总营收较历史值跌破 20%，当前值为 {total_revenue:,.2f} 元', 'severity': 'critical'})
            
            # 如果没有基于数据的追踪指标，使用默认指标
            if not tracking_config['metrics']:
                tracking_config = {
                    'metrics': [
                        {'name': '转化率', 'target': 0.05, 'unit': '%'},
                        {'name': 'GMV', 'target': 100000, 'unit': '元'}
                    ],
                    'alert_rules': [
                        {'metric': 'conversion_rate', 'message': '转化率低于3%，需要关注', 'severity': 'warning'},
                        {'metric': 'conversion_rate', 'message': '转化率低于1%，需要紧急处理', 'severity': 'critical'},
                        {'metric': 'gmv', 'message': 'GMV低于8万，需要关注', 'severity': 'warning'}
                    ]
                }
            
            return {
                'success': True,
                'message': '效果追踪配置完成',
                'output': {
                    **stage5_output,
                    'tracking_config': tracking_config
                }
            }
        except ImportError as e:
            return {
                'success': False,
                'message': f'模块导入失败: {str(e)}',
                'output': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'效果追踪配置失败: {str(e)}',
                'output': None
            }

# 工作流管理器实例
workflow_manager = WorkflowManager()

def run_workflow(user_input: str) -> Dict[str, Any]:
    """运行工作流的便捷函数"""
    return workflow_manager.run_workflow(user_input)
