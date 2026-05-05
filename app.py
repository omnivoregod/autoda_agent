import streamlit as st
import asyncio
import os
import glob
import pandas as pd
import plotly.express as px
import json
from agent import run_agent
from tools import calculate_funnel, plot_funnel, get_ab_conversion, plot_bar, plot_line, plot_pie, plot_scatter, plot_box, plot_heatmap, run_sql_query
from data_processor import process_files, get_database_summary
from report_generator import generate_comprehensive_report, generate_funnel_report, generate_ab_test_report, generate_rfm_report
from analysis_workflow import run_analysis_workflow, get_workflow_info
from reporter import Reporter

# 设置页面配置
st.set_page_config(
    page_title="AutoDA-Agent 企业级商业分析助手",
    page_icon="📊",
    layout="wide"
)

# 初始化session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'db_summary' not in st.session_state:
    st.session_state.db_summary = None
if 'analysis_started' not in st.session_state:
    st.session_state.analysis_started = False
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'db_path' not in st.session_state:
    st.session_state.db_path = 'ecommerce.db'

# 自动检测data1文件夹并加载数据
data1_path = "data/data1"
if os.path.exists(data1_path) and not st.session_state.data_loaded:
    csv_files = glob.glob(os.path.join(data1_path, "*.csv"))
    if csv_files:
        st.info(f"检测到data1文件夹，包含 {len(csv_files)} 个CSV文件，正在自动加载...")
        try:
            # 处理data1文件
            results = process_files(csv_files)
            # 获取数据库概览
            db_path = results.get('db_path', 'ecommerce.db')
            summary = get_database_summary(db_path)
            st.session_state.db_summary = summary
            st.session_state.data_loaded = True
            st.session_state.db_path = db_path
            st.success(f"✅ 成功加载data1数据，包含 {results['success']}/{results['total_files']} 个文件！")
        except Exception as e:
            st.error(f"加载data1数据失败: {str(e)}")

# 页面标题
st.title("AutoDA-Agent 企业级商业分析助手")

# 左侧边栏
with st.sidebar:
    st.header("数据上传")

    # 提示信息
    st.markdown("**支持的文件类型：**")
    st.markdown("- CSV / Excel 文件")
    st.markdown("- 可上传多个文件")

    # 数据处理说明
    st.markdown("**系统特点：**")
    st.markdown("- 支持任意CSV/Excel文件")
    st.markdown("- 自动识别字段类型")
    st.markdown("- 智能发现表关联关系")
    st.markdown("- 自动数据清洗和转换")

    # 文件上传
    uploaded_files = st.file_uploader(
        "上传数据文件",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        help="可上传多个CSV或Excel文件，系统会自动识别文件类型并建表"
    )

    # 处理数据按钮
    if uploaded_files:
        col1, col2 = st.columns(2)
        with col1:
            process_btn = st.button("处理数据", type="primary")
        with col2:
            clear_btn = st.button("清空")

        if clear_btn:
            st.session_state.data_loaded = False
            st.session_state.db_summary = None
            st.rerun()

        if process_btn:
            with st.spinner("正在处理数据..."):
                try:
                    # 保存上传的文件到临时目录
                    file_paths = []
                    for uploaded_file in uploaded_files:
                        file_path = f"temp_{uploaded_file.name}"
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_paths.append(file_path)

                    # 处理数据
                    results = process_files(file_paths)

                    # 清理临时文件
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            os.remove(file_path)

                    # 获取数据库概览
                    db_path = results.get('db_path', 'ecommerce.db')
                    summary = get_database_summary(db_path)
                    st.session_state.db_summary = summary
                    st.session_state.data_loaded = True
                    st.session_state.db_path = db_path

                    st.success(f"✅ 成功处理 {results['success']}/{results['total_files']} 个文件！")
                    st.balloons()
                except Exception as e:
                    st.error(f"数据处理失败: {str(e)}")
                    st.info("💡 提示：请确保上传的文件格式正确，并且没有被其他程序占用。")

    # 显示已加载的数据概览
    if st.session_state.data_loaded and st.session_state.db_summary:
        st.markdown("---")
        st.header("数据概览")

        # 过滤掉特殊键（_relationships 和 _tables_metadata）
        table_infos = {k: v for k, v in st.session_state.db_summary.items() if not k.startswith('_')}
        total_records = sum(info['rows'] for info in table_infos.values())
        total_tables = len(table_infos)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("数据表", total_tables)
        with col2:
            st.metric("总记录数", f"{total_records:,}")

        # 显示每个表的详情
        for table_name, info in table_infos.items():
            with st.expander(f"{table_name}"):
                st.write(f"记录数: {info['rows']:,}")
                st.write(f"列数: {info['columns']}")
                st.write(f"列名: {', '.join(info['column_names'][:5])}" + ("..." if len(info['column_names']) > 5 else ""))

    st.markdown("---")
    st.header("配置")

    # API Key输入
    api_key = st.text_input("API Key", type="password", placeholder="请输入你的API密钥")

    # 模型选择
    model_type = st.selectbox(
        "模型选择",
        ["deepseek", "wenxin", "xinghuo", "qwen", "kimi"],
        help="选择要使用的大语言模型"
    )

    # 分析模式选择
    analysis_mode = st.selectbox(
        "分析模式",
        ["智能分析", "快速分析", "企业级商业分析", "新工作流分析"],
        help="智能分析：通过AI对话进行分析；快速分析：直接展示结果；企业级商业分析：基于SOP的完整分析流程；新工作流分析：基于Planner-SQLGenerator-Executor-Guardrail-Reporter流程的模块化分析"
    )

    # 快速分析选项
    if analysis_mode == "快速分析":
        quick_analysis = st.selectbox(
            "分析类型",
            ["转化漏斗", "A/B测试结果", "RFM用户分层", "销售趋势", "产品分析"]
        )

    # 显示示例问题
    st.markdown("---")
    st.header("示例问题")
    st.markdown("- 分析销售趋势和关键指标")
    st.markdown("- 分析用户行为转化漏斗")
    st.markdown("- 对客户进行RFM分群")
    st.markdown("- 分析不同营销渠道的效果")
    st.markdown("- 生成企业级商业分析报告")

# 右侧主区域
# 检查数据是否已加载
if not st.session_state.data_loaded:
    st.info("欢迎使用 AutoDA-Agent 企业级商业分析助手！\n\n请在左侧上传您的数据文件（支持CSV或Excel格式），系统会自动识别文件类型并建立数据库。\n\n**系统将自动：**\n- 识别字段类型（ID、日期、金额、数量等）\n- 发现表之间的关联关系\n- 清洗和转换数据\n- 建立优化的数据库结构")
else:
    # 数据已加载，显示主界面
    st.success("数据已加载完成，可以开始分析！")

    # 企业级商业分析工作流
    if analysis_mode == "企业级商业分析":
        st.markdown("---")
        st.header("🏢 企业级商业分析工作流")
        
        # 分析需求输入
        analysis_input = st.text_area(
            "请输入您的分析需求",
            placeholder="例如：分析最近三个月的销售数据，找出增长缓慢的原因并提出改进建议",
            height=100
        )
        
        # 分析按钮
        if st.button("🚀 开始企业级分析", type="primary"):
            if not analysis_input:
                st.warning("请输入分析需求")
            elif not api_key:
                st.error("请在左侧边栏输入API Key")
            else:
                st.session_state.analysis_started = True
                st.session_state.analysis_result = None
                st.rerun()

        # 执行分析
        if st.session_state.analysis_started and st.session_state.analysis_result is None:
            with st.spinner("正在执行企业级商业分析工作流..."):
                try:
                    # 运行工作流
                    # 导入WorkflowManager
                    from workflow import WorkflowManager
                    workflow_manager = WorkflowManager()
                    result = workflow_manager.run_workflow(analysis_input, api_key=api_key, model_type=model_type)
                    st.session_state.analysis_result = result
                    st.session_state.analysis_started = False
                    st.rerun()
                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    st.info("💡 提示：请检查API Key是否正确，网络连接是否正常，或尝试简化分析需求。")
                    st.session_state.analysis_started = False
                    st.session_state.analysis_result = None

        # 显示分析结果
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            if result['success']:
                # 提取核心指标
                data_results = {}
                # 尝试从阶段 1 获取数据结果
                if 'stages' in result and len(result['stages']) > 1:
                    stage1_output = result['stages'][1].get('output', {})
                    data_results = stage1_output.get('data_results', {})
                
                # 只有当数据结果中包含渠道相关数据时，才显示渠道指标
                if 'channel_data' in data_results and 'orders_data' in data_results:
                    channel_df = data_results['channel_data']
                    orders_df = data_results['orders_data']
                    
                    if not channel_df.empty and not orders_df.empty:
                        # 合并数据计算转化率
                        merged_df = channel_df.merge(orders_df, on='source', how='left')
                        merged_df['conversion_rate'] = merged_df['orders'] / merged_df['sessions'] * 100
                        
                        # 计算总GMV
                        total_gmv = orders_df['gmv'].sum()
                        
                        # 计算平均转化率
                        avg_conversion = merged_df['conversion_rate'].mean()
                        
                        # 找出最高转化渠道
                        top_conversion_channel = merged_df.loc[merged_df['conversion_rate'].idxmax()]
                        
                        # 找出流量最高的渠道
                        top_session_channel = channel_df.loc[channel_df['sessions'].idxmax()]
                        top_channel = top_session_channel['source']
                        top_channel_sessions = top_session_channel['sessions']
                
                        # 显示核心指标
                        col1, col2, col3 = st.columns(3)
                        col1.metric("总 GMV", f"{total_gmv:,.2f}", "+5% 环比")
                        col2.metric("最高转化渠道", f"{top_conversion_channel['source']}", f"{top_conversion_channel['conversion_rate']:.2f}%")
                        col3.metric("流量Top渠道", f"{top_channel}", f"{top_channel_sessions:,} 会话")
                
                        # 添加可视化图表
                        st.markdown("---")
                        st.subheader("📊 数据可视化")
                        
                        # 绘制渠道综合效能气泡图
                        # 合并数据
                        merged_df = channel_df.merge(orders_df, on='source', how='left')
                        merged_df['conversion_rate'] = merged_df['orders'] / merged_df['sessions'] * 100
                        
                        # 绘制气泡图
                        fig = px.scatter(
                            merged_df,
                            x="conversion_rate",
                            y="sessions",
                            size="gmv",
                            color="source",
                            title="各渠道综合效能气泡图",
                            labels={
                                "conversion_rate": "转化率 (%)",
                                "sessions": "会话数",
                                "gmv": "GMV",
                                "source": "渠道"
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # 💡 探针 1：查看传给大模型的数据
                with st.expander("🔍 调试信息：传给大模型的数据", expanded=False):
                    # 显示数据结果的结构
                    st.write("🕵️‍♂️[Debug] 数据结果结构：", data_results.keys())
                    
                    # 显示每个数据集的字段
                    for key, df in data_results.items():
                        if hasattr(df, 'columns'):
                            st.write(f"\n📋 {key} 字段：", df.columns.tolist())
                            st.write(f"📊 {key} 数据样本：")
                            st.write(df.head())
                        else:
                            st.write(f"\n📋 {key}：", df)
                
                # 显示分析报告
                st.subheader("📋 企业级商业分析报告")
                
                # 尝试解析JSON报告
                try:
                    # 检查是否有JSON格式的报告
                    if 'json_report' in result:
                        # 假设 llm_response_text 是大模型返回的内容
                        llm_response_text = result['json_report']
                        report_data = json.loads(llm_response_text)
                        
                        # 🌟 新增的容错拦截逻辑 🌟
                        if report_data.get("status") == "error":
                            st.error("🚨 需求与数据源不匹配 (数据诊断拦截)")
                            st.warning(report_data.get("message", "当前数据集不支持您的分析需求。"))
                            st.info("💡 建议：请检查您上传的数据集字段，或尝试更改提问方式（例如：改为'分析当前数据中各品类的销售额贡献'）。")
                            
                            # 提供下载按钮
                            st.download_button(
                                label="📥 下载JSON格式报告",
                                data=llm_response_text,
                                file_name="enterprise_analysis_report.json",
                                mime="application/json"
                            )
                            st.stop() # 停止渲染后续空白内容
                        
                        # === 如果状态是 success，正常渲染 ===
                        
                        st.subheader("📊 核心数据表现")
                        metrics = report_data.get("key_metrics",[])
                        if metrics:
                            cols = st.columns(len(metrics))
                            for i, m in enumerate(metrics):
                                cols[i].metric(label=m["name"], value=m["value"], delta=m["trend"])

                        st.subheader("🔍 深度诊断")
                        for idx, insight in enumerate(report_data.get("deep_insights",[])):
                            with st.expander(f"💡 洞察 {idx+1}: {insight['conclusion']}", expanded=True):
                                st.markdown(f"**📊 数据印证:** {insight['data_proof']}")
                                st.markdown(f"**🧠 深度归因:** {insight['why']}")
                                st.markdown(f"**❓ 下一步验证:** {insight['next_step']}")

                        st.subheader("🎯 业务决策与 ROI 估算")
                        for action in report_data.get("actionable_decisions",[]):
                            st.markdown(f"#### 🚀 {action['strategy_name']} (优先级: {action['priority']})")
                            st.markdown(f"- **🎯 针对痛点**: {action['target_pain_point']}")
                            st.markdown(f"- **🛠️ 落地动作**: {action['action']}")
                            st.success(f"**💰 ROI 推演逻辑**: {action['roi_calc_logic']}")
                            st.divider()

                        # 4. 渲染追踪计划
                        st.subheader("📈 监控与预警")
                        tracking_plan = report_data.get("tracking_plan", [])
                        if tracking_plan:
                            st.dataframe(tracking_plan, use_container_width=True)
                        else:
                            st.info("本次分析未生成监控与预警计划。")
                        
                        # 提供下载按钮
                        st.download_button(
                            label="📥 下载JSON格式报告",
                            data=llm_response_text,
                            file_name="enterprise_analysis_report.json",
                            mime="application/json"
                        )
                    else:
                        # 回退到旧的Markdown报告
                        st.markdown(result.get('report', '未生成报告'))
                        
                        # 提供下载按钮
                        st.download_button(
                            label="📥 下载分析报告",
                            data=result.get('report', ''),
                            file_name="enterprise_analysis_report.md",
                            mime="text/markdown"
                        )
                except json.JSONDecodeError:
                    st.error("❌ 大模型生成的 JSON 格式异常，无法解析。")
                    with st.expander("查看大模型原始返回"):
                        st.text(result.get('json_report', ''))
                    # 回退到旧的Markdown报告
                    if 'report' in result:
                        st.markdown(result.get('report', '未生成报告'))
                        
                        # 提供下载按钮
                        st.download_button(
                            label="📥 下载分析报告",
                            data=result.get('report', ''),
                            file_name="enterprise_analysis_report.md",
                            mime="text/markdown"
                        )
                
                # 显示工作流生成的可视化图表
                if 'visualizations' in result and result['visualizations']:
                    st.markdown("---")
                    st.subheader("📊 数据可视化")
                    for viz in result['visualizations']:
                        fig = viz.get('figure')
                        title = viz.get('title', '图表')
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.write(f"**{title}** - 图表生成失败")
            
            else:
                st.error(result.get('message', '分析失败'))
                # 回退到旧的Markdown报告
                if 'report' in result:
                    st.markdown(result.get('report', '未生成报告'))
                    
                    # 提供下载按钮
                    st.download_button(
                        label="📥 下载分析报告",
                        data=result.get('report', ''),
                        file_name="enterprise_analysis_report.md",
                        mime="text/markdown"
                    )
                st.error(f"分析失败: {result['message']}")
    
    # 智能分析
    elif analysis_mode == "智能分析":
        st.markdown("---")
        st.header("🔍 智能分析")
        
        # 分析需求输入
        analysis_input = st.text_area(
            "请输入您的分析需求",
            placeholder="例如：分析销售数据的趋势，找出影响销售额的关键因素",
            height=100
        )
        
        # 分析按钮
        if st.button("🚀 开始分析", type="primary"):
            if not analysis_input:
                st.warning("请输入分析需求")
            elif not api_key:
                st.error("请在左侧边栏输入API Key")
            else:
                st.session_state.analysis_started = True
                st.session_state.analysis_result = None
                st.rerun()

        # 执行分析
        if st.session_state.analysis_started and st.session_state.analysis_result is None:
            with st.spinner("AI正在分析数据..."):
                try:
                    # 调用Agent进行分析
                    response_text, fig = asyncio.run(run_agent(analysis_input, api_key, model_type))
                    st.session_state.analysis_result = {"response_text": response_text, "fig": fig}
                    st.session_state.analysis_started = False
                    st.rerun()
                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    st.info("💡 提示：请检查API Key是否正确，网络连接是否正常，或尝试简化分析需求。")
                    st.session_state.analysis_started = False
                    st.session_state.analysis_result = None

        # 显示分析结果
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            # 显示分析结果
            st.subheader("📋 分析报告")
            st.markdown(result["response_text"])
            
            # 添加报告下载功能
            st.download_button(
                label="📥 下载分析报告",
                data=result["response_text"],
                file_name="analysis_report.md",
                mime="text/markdown"
            )
    
    # 快速分析
    elif analysis_mode == "快速分析":
        st.markdown("---")
        st.header("⚡ 快速分析")

        if st.button("执行快速分析"):
            with st.spinner("正在生成分析结果..."):
                try:
                    if quick_analysis == "转化漏斗":
                        from tools import calculate_funnel
                        funnel_df = calculate_funnel()
                        if not funnel_df.empty and 'error' not in funnel_df.columns:
                            st.subheader("📊 转化漏斗分析")
                            with st.expander("查看原始聚合数据"):
                                st.dataframe(funnel_df, use_container_width=True)
                        elif 'error' in funnel_df.columns:
                            st.error(f"查询失败: {funnel_df['error'].iloc[0]}")
                        else:
                            st.warning("暂无转化漏斗数据")

                    elif quick_analysis == "A/B测试结果":
                        from tools import get_ab_conversion
                        ab_df = get_ab_conversion()
                        if not ab_df.empty and 'error' not in ab_df.columns:
                            st.subheader("🧪 A/B测试结果分析")
                            with st.expander("查看原始聚合数据"):
                                st.dataframe(ab_df, use_container_width=True)
                        elif 'error' in ab_df.columns:
                            st.error(f"查询失败: {ab_df['error'].iloc[0]}")
                        else:
                            st.warning("暂无A/B测试数据")

                    elif quick_analysis == "RFM用户分层":
                        from tools import calculate_rfm
                        rfm_df = calculate_rfm()
                        if not rfm_df.empty and 'error' not in rfm_df.columns:
                            segment_counts = rfm_df['segment'].value_counts().reset_index()
                            segment_counts.columns = ['segment', 'count']
                            st.subheader("👥 RFM用户分层分析")
                            with st.expander("查看原始聚合数据"):
                                st.dataframe(segment_counts, use_container_width=True)
                        elif 'error' in rfm_df.columns:
                            st.error(f"查询失败: {rfm_df['error'].iloc[0]}")
                        else:
                            st.warning("暂无RFM数据")

                    elif quick_analysis == "销售趋势":
                        from tools import run_sql_query
                        import pandas as pd
                        query = """
                        SELECT DATE(order_time) as date, COUNT(*) as orders, SUM(total_usd) as revenue
                        FROM orders
                        GROUP BY DATE(order_time)
                        ORDER BY date
                        LIMIT 30
                        """
                        sales_df = run_sql_query(query)
                        if not sales_df.empty and 'error' not in sales_df.columns:
                            st.subheader("📈 销售趋势分析")
                            # 绘制销售趋势图
                            fig = px.line(
                                sales_df,
                                x="date",
                                y=["orders", "revenue"],
                                title="销售趋势",
                                labels={
                                    "date": "日期",
                                    "value": "数值",
                                    "variable": "指标"
                                }
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            with st.expander("查看原始聚合数据"):
                                st.dataframe(sales_df, use_container_width=True)
                        elif 'error' in sales_df.columns:
                            st.error(f"查询失败: {sales_df['error'].iloc[0]}")
                        else:
                            st.warning("暂无销售数据")

                    elif quick_analysis == "产品分析":
                        from tools import run_sql_query
                        query = """
                        SELECT p.category, COUNT(DISTINCT oi.product_id) as products,
                               SUM(oi.quantity) as total_sales, SUM(oi.line_total_usd) as revenue
                        FROM order_items oi
                        JOIN products p ON oi.product_id = p.product_id
                        GROUP BY p.category
                        ORDER BY revenue DESC
                        LIMIT 10
                        """
                        product_df = run_sql_query(query)
                        if not product_df.empty and 'error' not in product_df.columns:
                            st.subheader("🏷️ 产品分析")
                            # 绘制产品收入图
                            fig = px.bar(
                                product_df,
                                x="category",
                                y="revenue",
                                title="各品类收入",
                                labels={
                                    "category": "品类",
                                    "revenue": "收入"
                                }
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            with st.expander("查看原始聚合数据"):
                                st.dataframe(product_df, use_container_width=True)
                        elif 'error' in product_df.columns:
                            st.error(f"查询失败: {product_df['error'].iloc[0]}")
                        else:
                            st.warning("暂无产品数据")

                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    st.info("💡 提示：请确保数据已正确加载，并且选择的分析类型与数据结构匹配。")
    
    # 新工作流分析
    elif analysis_mode == "新工作流分析":
        st.markdown("---")
        st.header("🔄 模块化工作流分析")
        
        # 显示工作流信息
        workflow_info = get_workflow_info()
        with st.expander("📋 工作流说明"):
            st.markdown("**工作流阶段：**")
            for stage in workflow_info['stages']:
                st.markdown(f"  {stage['order']}. **{stage['name']}**：{stage['description']}")
            
            st.markdown("\n**支持的分析类型：**")
            for at in workflow_info['supported_analysis_types']:
                st.markdown(f"  - **{at['name']}**：{at['description']}")
        
        # 分析需求输入
        analysis_input = st.text_area(
            "请输入您的分析需求",
            placeholder="例如：分析用户行为转化漏斗\n分析不同年龄段的折扣偏好\n分析销售趋势",
            height=100
        )
        
        # 分析按钮
        if st.button("🚀 执行工作流分析", type="primary"):
            if not analysis_input:
                st.warning("请输入分析需求")
            else:
                with st.spinner("正在执行模块化工作流分析..."):
                    try:
                        # 执行新的工作流
                        result = run_analysis_workflow(
                            user_input=analysis_input,
                            db_path=st.session_state.db_path
                        )
                        
                        # 显示执行进度
                        if result.get('success'):
                            st.success("✅ 分析完成！")
                            
                            # 显示分析计划
                            if result.get('analysis_plan'):
                                with st.expander("📋 分析计划"):
                                    analysis_plan = result['analysis_plan']
                                    st.markdown("**分析类型：**")
                                    for analysis_type in analysis_plan.get('analysis_types', []):
                                        st.markdown(f"  - {analysis_type}")
                                    
                                    st.markdown("\n**分析步骤：**")
                                    for step in analysis_plan.get('steps', []):
                                        st.markdown(f"  {step['step_id']}. **{step['name']}** - {step['tool']}")
                                        st.markdown(f"    描述：{step['description']}")
                            
                            # 显示标准DSL
                            if result.get('standard_dsl'):
                                with st.expander("📝 标准DSL"):
                                    standard_dsl = result['standard_dsl']
                                    st.json(standard_dsl)
                            
                            # 显示生成的SQL
                            if result.get('stages', {}).get('sql_generator', {}).get('sql'):
                                with st.expander("⚙️ 生成的SQL"):
                                    sql = result['stages']['sql_generator']['sql']
                                    st.code(sql, language='sql')
                            
                            # 显示分析结果
                            if result.get('stages', {}).get('executor', {}).get('data'):
                                with st.expander("📊 分析结果"):
                                    # 显示数据预览
                                    data = result['stages']['executor']['data']
                                    if data is not None:
                                        st.markdown("**数据预览**")
                                        st.dataframe(data.head())
                            
                            # 显示图表规划
                            if result.get('visualization_plan'):
                                with st.expander("📈 图表规划"):
                                    visualization_plan = result['visualization_plan']
                                    charts = visualization_plan.get('charts', [])
                                    if charts:
                                        st.markdown("**规划的图表**")
                                        for i, chart in enumerate(charts):
                                            st.markdown(f"{i+1}. **{chart['title']}**")
                                            st.markdown(f"   类型: {chart['type']}")
                                            st.markdown(f"   X轴: {chart['x']}")
                                            st.markdown(f"   Y轴: {chart['y']}")
                                    else:
                                        st.markdown("暂无图表规划")
                            
                            # 显示实际图表
                            if result.get('visualization_plan'):
                                visualization_plan = result['visualization_plan']
                                charts = visualization_plan.get('charts', [])
                                if charts:
                                    st.subheader("📊 数据可视化")
                                    for i, chart in enumerate(charts):
                                        try:
                                            # 创建图表数据
                                            chart_data = {}
                                            chart_data[chart['x']] = chart.get('x', [])
                                            chart_data[chart['y']] = chart.get('y', [])
                                            df = pd.DataFrame(chart_data)
                                            
                                            # 根据图表类型渲染
                                            if chart['type'] == 'bar':
                                                fig = px.bar(df, x=chart['x'], y=chart['y'], title=chart['title'])
                                            elif chart['type'] == 'line':
                                                fig = px.line(df, x=chart['x'], y=chart['y'], title=chart['title'])
                                            elif chart['type'] == 'pie':
                                                fig = px.pie(df, values=chart['y'], names=chart['x'], title=chart['title'])
                                            elif chart['type'] == 'scatter':
                                                fig = px.scatter(df, x=chart['x'], y=chart['y'], title=chart['title'])
                                            elif chart['type'] == 'funnel':
                                                fig = px.funnel(df, x=chart['y'], y=chart['x'], title=chart['title'])
                                            else:
                                                # 默认使用柱状图
                                                fig = px.bar(df, x=chart['x'], y=chart['y'], title=chart['title'])
                                            
                                            # 显示图表
                                            st.plotly_chart(fig, use_container_width=True)
                                        except Exception as e:
                                            st.error(f"图表渲染失败: {str(e)}")
                                            st.info("💡 提示：请确保数据格式正确，并且图表类型与数据匹配。")
                            
                            # 显示Guardrail检查结果
                            if result.get('guardrail_result'):
                                with st.expander("🛡 数据质量检查"):
                                    guardrail_result = result['guardrail_result']
                                    is_valid = guardrail_result.get('valid', False)
                                    issues = guardrail_result.get('issues', [])
                                    
                                    if is_valid:
                                        st.markdown("✅ **数据质量检查通过**")
                                        st.markdown("未发现明显问题，分析结果可靠")
                                    else:
                                        st.markdown("❌ **数据质量检查未通过**")
                                        st.markdown("**发现的问题：**")
                                        for i, issue in enumerate(issues):
                                            st.markdown(f"{i+1}. {issue}")
                            
                            # 显示Self-Check结果
                            if result.get('self_check_result'):
                                with st.expander("🔍 报告自检"):
                                    self_check_result = result['self_check_result']
                                    quality_score = self_check_result.get('quality_score', 0)
                                    issues = self_check_result.get('issues', [])
                                    
                                    st.markdown(f"**质量评分**：{quality_score}/100")
                                    
                                    if issues:
                                        st.markdown("**发现的问题：**")
                                        for i, issue in enumerate(issues):
                                            st.markdown(f"{i+1}. {issue}")
                                    else:
                                        st.markdown("**未发现明显问题**")
                            
                            # 显示各阶段执行情况
                            with st.expander("📊 执行详情"):
                                for stage_name, stage_result in result.get('stages', {}).items():
                                    if isinstance(stage_result, dict):
                                        status = "✅" if stage_result.get('success', False) else "❌"
                                        st.markdown(f"{status} **{stage_name.upper()}**：{stage_result.get('message', stage_result.get('error', '完成'))}")
                                        if stage_result.get('sql'):
                                            st.code(stage_result.get('sql'), language="sql")
                                        if stage_result.get('dsl_string'):
                                            st.text(stage_result.get('dsl_string'))
                            
                            # 显示分析报告
                            st.subheader("📋 分析报告")
                            st.markdown(result.get('report', '暂无报告内容'))
                            
                            # 显示原始数据（如果有）
                            if result.get('data') is not None and not result['data'].empty:
                                with st.expander("📈 原始数据"):
                                    st.dataframe(result['data'], use_container_width=True)
                            
                            # 下载报告
                            st.download_button(
                                label="📥 下载分析报告",
                                data=result.get('report', ''),
                                file_name="workflow_analysis_report.md",
                                mime="text/markdown"
                            )
                        else:
                            st.error(f"分析失败: {result.get('message', '未知错误')}")
                            
                            # 显示执行详情
                            if 'stages' in result:
                                with st.expander("🔍 调试信息"):
                                    for stage_name, stage_result in result.get('stages', {}).items():
                                        if isinstance(stage_result, dict) and not stage_result.get('success', False):
                                            st.markdown(f"❌ **{stage_name.upper()}**：{stage_result.get('error', '失败')}")
                    except Exception as e:
                        st.error(f"分析失败: {str(e)}")
                        import traceback
                        with st.expander("🔍 错误详情"):
                            st.code(traceback.format_exc(), language="python")

# 页脚
st.markdown("---")
st.markdown("© 2026 AutoDA-Agent 企业级商业分析助手 | 基于 LangChain + Streamlit 构建")
