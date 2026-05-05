---
name: "field-semantic-analyzer"
description: "Analyzes database field semantics to generate meaningful business insights. Invoke when user selects fields for EDA or needs field meaning interpretation."
---

# Field Semantic Analyzer

This skill analyzes database field names and data to understand their business semantics, then generates appropriate analysis strategies based on field meanings.

## When to Use

**Invoke this skill when:**
- User selects fields for exploratory data analysis (EDA)
- User needs to understand what fields mean for business analysis
- Building analysis report and need field context
- Generating business insights from selected fields

## Skill Flow

### 1. Field Semantic Analysis

When you receive selected fields, perform semantic analysis:

**Input Example:**
```
user selects: ["user_id", "purchase_amount", "purchase_date", "product_category", "customer_age"]
```

**Analysis Process:**
```python
field_semantics = {
    "user_id": {
        "type": "identifier",
        "category": "用户识别",
        "description": "唯一标识用户身份",
        "analysis_angle": "用户行为追踪、用户分层",
        "recommended_charts": ["用户分布图"],
        "business_questions": ["用户活跃度", "用户留存", "用户价值"]
    },
    "purchase_amount": {
        "type": "numeric",
        "category": "交易金额",
        "description": "单次购买支付金额",
        "analysis_angle": "消费能力、购买力分析",
        "recommended_charts": ["分布直方图", "箱线图"],
        "business_questions": ["客单价分析", "消费升级/降级"]
    },
    "purchase_date": {
        "type": "datetime",
        "category": "时间维度",
        "description": "购买发生的时间",
        "analysis_angle": "趋势分析、周期性分析",
        "recommended_charts": ["趋势折线图", "热力图日历"],
        "business_questions": ["GMV趋势", "季节性波动", "活动效果"]
    },
    "product_category": {
        "type": "categorical",
        "category": "产品分类",
        "description": "商品所属品类",
        "analysis_angle": "品类结构、品类偏好",
        "recommended_charts": ["饼图", "堆叠柱状图"],
        "business_questions": ["品类结构", "品类贡献", "品类趋势"]
    },
    "customer_age": {
        "type": "numeric",
        "category": "用户属性",
        "description": "用户年龄",
        "analysis_angle": "用户画像、人群特征",
        "recommended_charts": ["年龄分布直方图", "年龄分群箱线图"],
        "business_questions": ["目标用户群", "用户生命周期"]
    }
}
```

### 2. Common Field Patterns

**E-commerce Fields:**
| Field Pattern | Semantic Category | Analysis Angle |
|--------------|-------------------|----------------|
| user_id, customer_id, member_id | 用户标识 | 用户行为、用户分层 |
| order_id, transaction_id | 订单标识 | 订单分析、转化漏斗 |
| purchase_amount, order_amount, GMV, revenue | 交易金额 | 营收分析、客单价 |
| purchase_date, order_time, create_time | 时间维度 | 趋势分析、周期性 |
| product_id, sku_id, item_id | 商品标识 | 商品分析、SKU分析 |
| category, product_category | 品类维度 | 品类结构、品类偏好 |
| age, birth_date | 用户属性 | 用户画像 |
| gender | 用户属性 | 性别差异分析 |
| location, city, region | 地域维度 | 地域分析 |
| discount, coupon | 促销维度 | 促销效果分析 |
| channel, source, platform | 渠道维度 | 渠道分析 |
| status, order_status | 状态维度 | 流程分析 |

**Social Media Fields:**
| Field Pattern | Semantic Category |
|--------------|-------------------|
| user_id, author_id | 用户标识 |
| post_id, content_id | 内容标识 |
| likes, shares, comments | 互动指标 |
| engagement_rate | 互动率 |
| followers, following | 社交关系 |
| post_time, publish_time | 发布时间 |

### 3. Generate Field Analysis Report

Based on field semantics, generate structured analysis report:

```markdown
## 字段语义分析报告

### 📊 字段概览

| 字段名称 | 语义类别 | 业务含义 | 分析角度 |
|---------|---------|---------|---------|
| user_id | 用户标识 | 唯一识别用户身份 | 用户行为追踪 |
| purchase_amount | 交易金额 | 单次购买支付金额 | 消费能力分析 |

### 🎯 核心分析维度

根据字段语义，系统自动识别以下核心分析维度：

1. **用户维度** (user_id, customer_id)
   - 用户行为分析
   - 用户价值分层
   - 用户生命周期

2. **交易维度** (purchase_amount, order_count)
   - GMV/营收分析
   - 客单价分析
   - 交易频次

3. **时间维度** (purchase_date, order_time)
   - 趋势分析
   - 季节性分析
   - 周期性分析

4. **商品维度** (product_category, sku_id)
   - 商品结构分析
   - SKU表现
   - 品类贡献

### 📈 推荐的图表类型

| 分析目的 | 推荐图表 | 适用字段 |
|---------|---------|---------|
| 分布分析 | 直方图、箱线图 | purchase_amount, customer_age |
| 趋势分析 | 折线图 | purchase_date |
| 构成分析 | 饼图、堆叠柱状图 | product_category |
| 对比分析 | 柱状图 | 不同品类的销售额 |

### 💡 基于字段语义的业务洞察

根据字段语义分析，系统建议关注以下业务洞察：

1. **用户价值分析**
   - 基于user_id追踪用户购买行为
   - 计算用户生命周期价值(LTV)
   - 识别高价值用户群体

2. **消费趋势分析**
   - 基于purchase_date分析GMV趋势
   - 识别销售旺季和淡季
   - 评估营销活动效果

3. **品类结构分析**
   - 基于product_category分析品类贡献
   - 识别主力销售品类
   - 发现增长潜力品类

4. **客单价分析**
   - 基于purchase_amount分析客单价分布
   - 识别消费升级/降级趋势
   - 优化定价策略

### 🔧 下一步分析建议

根据字段语义，推荐以下分析方向：

1. **用户画像分析**
   - 使用用户属性字段构建用户画像
   - 进行用户分群
   - 制定差异化营销策略

2. **交易漏斗分析**
   - 分析从浏览到购买的转化漏斗
   - 识别流失环节
   - 优化用户体验

3. **时序预测分析**
   - 基于历史交易数据进行趋势预测
   - 预测未来销售
   - 优化库存管理

4. **关联规则挖掘**
   - 分析商品关联性
   - 发现交叉销售机会
   - 优化商品推荐
```

### 4. Integration with Analysis Report

When generating the final EDA report, incorporate field semantics:

```markdown
## 📋 1. 数据感知与理解

### 字段语义分析

本次分析选择了以下字段进行分析：

| 字段名称 | 语义类别 | 业务含义 | 分析价值 |
|---------|---------|---------|---------|
| user_id | 用户标识 | 唯一识别用户身份 | ⭐⭐⭐⭐⭐ |
| purchase_amount | 交易金额 | 单次购买支付金额 | ⭐⭐⭐⭐⭐ |
| purchase_date | 时间维度 | 购买发生时间 | ⭐⭐⭐⭐ |
| product_category | 品类维度 | 商品所属品类 | ⭐⭐⭐ |

### 核心分析维度

基于字段语义，系统自动识别以下核心分析维度：
- **用户维度**：通过user_id追踪和分析用户行为
- **交易维度**：通过purchase_amount分析营收和客单价
- **时间维度**：通过purchase_date分析趋势和季节性
- **商品维度**：通过product_category分析品类结构

### 推荐的图表类型

| 分析目的 | 推荐图表 | 适用字段 |
|---------|---------|---------|
| 分布分析 | 直方图、箱线图 | purchase_amount, customer_age |
| 趋势分析 | 折线图 | purchase_date |
| 构成分析 | 饼图、堆叠柱状图 | product_category |
```

## Output Format

The skill should output a structured field semantic analysis that:

1. **Field Semantic Table**: Lists all selected fields with semantic categories
2. **Analysis Dimension Mapping**: Maps fields to business analysis dimensions
3. **Recommended Charts**: Suggests appropriate visualizations for each field
4. **Business Insight Angles**: Provides business-focused analysis questions
5. **Integration Guide**: Shows how to incorporate into final EDA report

## Important Notes

- Always match field names to known business patterns
- Infer business meaning from field names and data types
- Provide industry-specific analysis angles
- Suggest appropriate visualizations based on field semantics
- Generate actionable business questions based on field meanings