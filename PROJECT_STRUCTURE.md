# AutoDA-Agent 项目结构

## 项目精简状态：已完成 ✅
## 企业级功能优化：已完成 ✅

---

## 核心应用文件

### `app.py` (主应用入口)
**作用**：Streamlit主应用入口，整合所有分析功能
**依赖**：
- `workflow.py` - WorkflowManager（主工作流）
- `analysis_workflow.py` - 模块化工作流
- `agent.py` - LLM代理
- `tools.py` - SQL查询和可视化工具
- `data_processor.py` - 数据处理
- `report_generator.py` - 报告生成
- `reporter.py` - LLM报告生成

---

## 核心业务逻辑文件

### `workflow.py` (主工作流) ✅ 主要使用
**作用**：六阶段工作流管理器

#### 六阶段工作流详细流程

**阶段1️⃣：需求诊断与目标对齐**
- 调用 `context_agent.clarify_requirement()` 解析用户输入
- 调用 `metric_tree.build_metric_tree()` 构建业务指标体系
- 输出：user_input、business_context（analysis_type、metrics）、metric_tree

**阶段2️⃣：字段语义分析与需求匹配**
- 扫描数据库所有表的字段结构
- 调用 `field_semantic.analyze_field_semantics()` 分析字段语义
- 调用 `guardrail._extract_required_fields()` 提取用户需求字段类型
- 调用 `guardrail._check_data_match()` 校验数据是否支持需求
- 输出：field_match_report（available_fields、required_fields、can_answer）

**阶段3️⃣：数据获取与质检验证**
- 根据analysis_type调用 `tools.run_sql_query()` 获取数据
- 调用 `data_qa` 模块进行质量检测
- 支持 Redis 缓存加速
- 输出：data_results（rfm_data、payment_data、channel_data、sales_trend_data等）

**阶段4️⃣：深度诊断与根因推演**
- 调用 `root_cause_analysis.RootCauseAnalyzer.analyze_root_causes()` 生成根因洞察
- 根据analysis_type进行专项分析（渠道、支付、用户、产品、RFM等）
- 输出：insights（根因分析洞察+专项分析洞察）

**阶段5️⃣：方案输出与商业决策**
- 合并orders和order_items表获取完整数据
- 调用 `reporter.generate_json_report_with_llm()` 生成LLM结构化报告
- 调用 `report_generator.generate_comprehensive_report()` 生成综合报告
- **阶段五扩展：数据可视化生成** ✨
  - 判断是否需要可视化（关键词检测 + 分析类型判断）
  - 根据需求筛选数据（原始数据 + 二次处理数据）
  - 调用 `visualization_planner.plan()` 规划图表
  - 调用 `tools.plot_*()` 生成实际图表
- 输出：json_report、report、visualizations

**阶段6️⃣：效果追踪闭环**
- 调用 `tracking.generate_performance_report()` 生成追踪配置
- 输出：tracking_config

**最终输出**：
```python
{
    'success': True,
    'message': '工作流执行完成',
    'result': stage6_result['output'],
    'report': markdown报告,
    'json_report': LLM的JSON报告,
    'visualizations': [图表列表],
    'stages': {1: stage1, 2: stage2, 3: stage3, 4: stage4, 5: stage5, 6: stage6}
}
```

**依赖模块**：
- `context_agent.py` - 上下文代理（阶段1）
- `metric_tree.py` - 指标体系（阶段1）
- `guardrail.py` - 数据校验（阶段2）
- `field_semantic.py` - 字段语义分析（阶段2）
- `tools.py` - 数据获取（阶段3）
- `data_qa.py` - 数据质量（阶段3）
- `root_cause_analysis.py` - 根因分析（阶段4）
- `report_generator.py` - 综合报告生成（阶段5）
- `reporter.py` - LLM报告生成（阶段5）
- `visualization_planner.py` - 可视化规划（阶段5扩展）
- `tracking.py` - 绩效追踪（阶段6）

---

## 数据可视化集成

### `_stage5_visualization()` 方法
**作用**：根据用户需求自动生成数据可视化图表

**工作流程**：
1. **判断是否需要可视化**
   - 关键词检测：图表、可视化、展示、趋势、对比、分布、占比、转化等
   - 分析类型判断：funnel、channel、sales、trend、rfm、ab_test、comparison

2. **数据筛选**
   - 支持原始数据和二次处理数据
   - 根据分析类型选择最合适的数据源

3. **图表选择**
   - 调用 `visualization_planner.plan()` 进行智能图表规划
   - 支持图表类型：bar、line、pie、funnel、scatter

4. **图表生成**
   - 使用 `tools.plot_*()` 系列函数生成Plotly图表

**触发条件**：
- 用户输入包含可视化相关关键词
- 分析类型为：漏斗分析、渠道分析、销售趋势、RFM分析、A/B测试、对比分析

---

## 报告生成模块

### `reporter.py` (LLM JSON报告生成) ✅ 主要使用
**作用**：基于LLM的JSON结构化报告生成
**核心方法**：
- `generate_json_report_with_llm()`：生成JSON格式的分析报告

### `report_generator.py` (Markdown综合报告生成) ✅ 主要使用
**作用**：Markdown格式报告生成
**核心方法**：
- `generate_comprehensive_report()`：生成综合分析报告（包含可视化部分）
- `generate_funnel_report()`：生成漏斗分析报告
- `generate_ab_test_report()`：生成A/B测试报告
- `generate_rfm_report()`：生成RFM分析报告

---

## 数据校验与分析模块

### `guardrail.py` (数据需求匹配校验) ✅ 主要使用
**作用**：数据需求匹配校验
**核心方法**：
- `_extract_required_fields()`：从用户输入中提取需求字段类型
- `_check_data_match()`：检查数据是否支持需求
**特殊处理**：支持流量转化分析的events表检查（session_id、event_type、timestamp）

### `field_semantic.py` (字段语义分析) ✅ 主要使用
**作用**：基于正则和关键词的字段语义分析
**分析能力**：会话标识、事件类型、交易金额、用户标识、订单标识、交易时间

### `root_cause_analysis.py` (根因分析) ✅ 主要使用
**作用**：深度诊断与根因分析（漏斗断点识别、关键断点定位）
**核心方法**：
- `analyze_root_causes()`：整合多种数据源进行综合分析
- `_analyze_funnel()`：计算各阶段转化率，识别转化率低的环节
- `_analyze_user_behavior()`：分析用户行为模式

### `data_qa.py` (数据质量检测) ✅ 主要使用
**作用**：辛普森悖论检测、异常值检测、数据质量评分
**核心方法**：
- `detect_simpson_paradox()`：检测辛普森悖论
- `detect_anomalies()`：检测数据异常值
- `run_comprehensive_qa()`：综合数据质量检测

---

## 工具模块

### `tools.py` ✅ 主要使用
**作用**：SQL查询、可视化图表（Plotly）、漏斗计算、A/B测试
**核心方法**：
- `run_sql_query()`：执行SQL查询并返回DataFrame（支持缓存）
- `calculate_funnel()`：计算转化漏斗
- `get_ab_conversion()`：计算A/B测试转化率
- `plot_bar()`、`plot_line()`、`plot_pie()`、`plot_funnel()`、`plot_scatter()`、`plot_box()`、`plot_heatmap()`：各种Plotly图表

### `data_processor.py` ✅ 主要使用
**作用**：CSV数据加载、数据库写入、数据清洗

### `agent.py` ✅ 使用
**作用**：LangChain LLM代理

---

## 辅助模块

### `context_agent.py` ✅ 主要使用
**作用**：用户意图澄清、业务上下文填充
**核心方法**：
- `clarify_requirement()`：解析用户输入，确定分析类型和业务目标

### `metric_tree.py` ✅ 主要使用
**作用**：业务指标体系拆解
**核心方法**：
- `build_metric_tree()`：根据业务上下文构建指标层级结构

### `roi_calculator.py` ✅ 使用
**作用**：营销ROI计算
**依赖**：被 `report_generator.py` 调用

### `tracking.py` ✅ 使用
**作用**：绩效追踪报告
**核心方法**：
- `generate_performance_report()`：生成绩效追踪配置

---

## 企业级模块 ✨ 新增

### `config_loader.py` ✅ 新增
**作用**：统一配置管理，从 config.yaml 加载所有配置
**功能**：
- 环境变量 / 配置文件双重配置源
- 默认值回退机制
- 配置热加载
**核心方法**：
- `load_config()`：加载配置
- `get_default_config()`：获取默认配置

### `data_masking.py` ✅ 新增
**作用**：可配置的数据脱敏
**支持规则**：
- 手机号：`138****8888`
- 邮箱：`z**@example.com`
- 订单号：`ORD2****2345`
**核心方法**：
- `mask_phone()`：手机号脱敏
- `mask_email()`：邮箱脱敏
- `mask_order_id()`：订单号脱敏
- `mask_dataframe()`：DataFrame批量脱敏

### `redis_cache.py` ✅ 新增
**作用**：Redis缓存层
**功能**：
- DataFrame序列化缓存
- 查询结果缓存
- 自动过期管理
**核心方法**：
- `set()` / `get()`：基本存取
- `cache_query_result()` / `get_cached_query_result()`：查询缓存

### `sql_dialect_adapter.py` ✅ 新增
**作用**：多数据库SQL方言适配
**支持方言**：MySQL、PostgreSQL、SQLite、ClickHouse
**功能**：
- LIMIT/OFFSET 语法转换
- 字符串函数转换（IFNULL → COALESCE）
- 日期函数转换（DATE_FORMAT → STRFTIME/TO_CHAR）
- 字符串拼接转换（CONCAT → ||）
**核心方法**：
- `adapt_sql()`：SQL方言转换
- `QueryBuilder`：查询构建器

### `data_connector/` ✅ 新增
**作用**：统一的数据源连接接口

#### `base_connector.py`
**作用**：连接器基类
**功能**：
- 连接重试机制（指数退避）
- 错误处理和日志
- 查询执行抽象
**核心方法**：
- `connect()`：带重试的连接
- `execute_query()`：查询执行
- `test_connection()`：连接测试

#### `sqlite_connector.py`
**作用**：SQLite连接器
**继承自**：BaseConnector
**功能**：
- SQLite特有连接管理
- pandas DataFrame直接返回

---

## Docker部署模块 ✨ 新增

### `Dockerfile` ✅ 新增
**作用**：Docker镜像构建
**特性**：
- Python 3.9-slim 基础镜像
- 健康检查配置
- 服务依赖等待（wait-for-it.sh）

### `docker-compose.yml` ✅ 新增
**作用**：多服务编排
**包含服务**：
- `autoda-agent`：主应用（Streamlit）
- `redis`：缓存服务
- `mysql`：MySQL 8.0 数据库
**特性**：
- 服务健康检查
- 依赖启动顺序
- 数据卷持久化

### `wait-for-it.sh` ✅ 新增
**作用**：服务依赖就绪等待脚本
**功能**：
- TCP端口检测
- 超时控制
- 日志输出

### `init.sql` ✅ 新增
**作用**：MySQL数据库初始化脚本
**功能**：
- 表结构创建
- 索引定义
- 字符集配置

### `config.yaml` ✅ 新增
**作用**：配置文件模板
**配置项**：
- 数据库配置
- LLM配置
- 缓存配置
- 脱敏规则
- 重试策略

---

## 备用/模块化工作流系统

### `analysis_workflow.py` ⚠️ 备用
**作用**：模块化工作流（Planner→Clarifier→DSL→SQL→Analysis→Visualization）

### `workflow_core.py` ⚠️ 备用
**作用**：Planner、Clarifier、DSL Generator组件

### `sql_generator.py` ⚠️ 备用
**作用**：DSL转SQL

### `analysis_executor.py` ⚠️ 备用
**作用**：SQL执行和结果分析

### `visualization_planner.py` ⚠️ 备用
**作用**：可视化方案规划
**注意**：主工作流的 `_stage5_visualization()` 方法会调用此模块

---

## 数据文件

### `ecommerce.db` ✅ 主数据库
**作用**：SQLite数据库，包含orders、order_items、events、sessions等表

### `data/data1/*.csv` ✅ 原始数据
**作用**：CSV格式原始数据，用于导入到数据库

---

## 架构特点

### 双工作流架构
1. **主工作流** (`workflow.py`)：端到端分析流程，简单直接
2. **模块化工作流** (`analysis_workflow.py`)：高度模块化，支持用户交互澄清

### 数据可视化流程
```
用户需求 → 判断是否需要可视化 → 筛选数据 → 选择图表类型 → 生成图表 → 输出报告
```

### 可视化触发机制
- 关键词触发：图表、可视化、展示、趋势、对比、分布、占比、转化
- 分析类型触发：funnel、channel、sales、trend、rfm、ab_test、comparison

### 企业级架构
```
┌─────────────────────────────────────────────────────────────────┐
│                        配置管理层                                │
│  config.yaml → config_loader.py → 统一配置分发                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        数据访问层                                │
│  data_connector/ → BaseConnector → SQLite/MySQL/PostgreSQL      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        缓存层                                    │
│  redis_cache.py → Redis → 查询结果缓存 / DataFrame缓存           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        安全层                                    │
│  data_masking.py → 配置化脱敏 → 手机/邮箱/订单号等敏感数据        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        适配层                                    │
│  sql_dialect_adapter.py → MySQL/PostgreSQL/SQLite/ClickHouse    │
└─────────────────────────────────────────────────────────────────┘
```

### Docker部署架构
```
┌──────────────────────────────────────────────────────┐
│              docker-compose.yml                      │
├──────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │autoda-agent │  │    redis   │  │    mysql    │  │
│  │  (Streamlit)│←→│  (Cache)   │  │  (Database) │  │
│  │             │  │            │  │             │  │
│  │wait-for-it │  │  Health    │  │  Health     │  │
│  │  → 依赖就绪 │  │  Check     │  │  Check      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│         ↑                ↑                ↑        │
│         └────────────────┼────────────────┘        │
│                          ↓                          │
│              autoda-network (bridge)               │
└──────────────────────────────────────────────────────┘
```

---

## 精简后文件清单

| 类别 | 文件数 | 说明 |
|------|--------|------|
| 核心应用 | 1 | app.py |
| 主工作流 | 1 | workflow.py |
| 报告生成 | 2 | reporter.py, report_generator.py |
| 数据校验与分析 | 4 | guardrail.py, field_semantic.py, root_cause_analysis.py, data_qa.py |
| 工具模块 | 3 | tools.py, data_processor.py, agent.py |
| 辅助模块 | 4 | context_agent.py, metric_tree.py, roi_calculator.py, tracking.py |
| **企业级模块** ✨ | 5+3 | config_loader.py, data_masking.py, redis_cache.py, sql_dialect_adapter.py, data_connector/(3文件) |
| **Docker部署** ✨ | 4 | Dockerfile, docker-compose.yml, wait-for-it.sh, init.sql |
| 备用工作流 | 5 | analysis_workflow.py, workflow_core.py, sql_generator.py, analysis_executor.py, visualization_planner.py |
| **配置** ✨ | 1 | config.yaml |
| 数据文件 | 1 | ecommerce.db + data/data1/*.csv |
| **总计** | **34+** | |

---

## 技术栈

- **前端**：Streamlit
- **后端**：Python
- **数据处理**：Pandas、SQLite
- **统计分析**：SciPy、StatsModels
- **可视化**：Plotly
- **大模型集成**：LangChain、OpenAI API格式（支持DeepSeek等）
- **缓存**：Redis
- **容器化**：Docker、Docker Compose
