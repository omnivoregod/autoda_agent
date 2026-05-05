import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import os
import re
import json

# 中英双语字段模式配置
FIELD_PATTERNS = {
    'id': {
        'zh': ['id', '编号', '序号'],
        'en': ['_id', 'id_'],
        'patterns': [r'.*_id$', r'^.*_id$', r'.*_no$', r'^id$', r'.*编号$', r'.*序号$']
    },
    'date': {
        'zh': ['日期', '时间', '时间戳', '创建时间', '更新时间', '注册日期', '订单时间', '购买时间'],
        'en': ['date', 'time', 'timestamp', 'datetime', 'created_at', 'updated_at', 'created', 'modified', 'signup_date', 'order_time', 'purchase_time'],
        'patterns': [r'.*_date$', r'.*_time$', r'.*_at$', r'.*日期$', r'.*时间$']
    },
    'amount': {
        'zh': ['价格', '金额', '成本', '利润', '总计', '小计', '单价', '总价', '销售额', '收入'],
        'en': ['price', 'cost', 'amount', 'total', 'subtotal', 'revenue', 'profit', 'margin', 'sales', 'value', 'usd', 'rmb'],
        'patterns': [r'.*_usd$', r'.*_price$', r'.*_cost$', r'.*_total$', r'.*_amount$', r'.*金额$', r'.*价格$', r'.*销售额$']
    },
    'quantity': {
        'zh': ['数量', '数量', '数目', '销量', '购买数量', '订单数量'],
        'en': ['quantity', 'qty', 'count', 'num', 'number', 'amount', 'items'],
        'patterns': [r'.*_qty$', r'.*_count$', r'.*_num$', r'.*数量$', r'.*销量$']
    },
    'category': {
        'zh': ['类别', '分类', '类型', '品类', '商品类别', '产品类别'],
        'en': ['category', 'type', 'kind', 'class', 'group', 'segment'],
        'patterns': [r'.*_category$', r'.*_type$', r'.*类别$', r'.*分类$', r'.*类型$']
    },
    'name': {
        'zh': ['名称', '姓名', '名字', '产品名称', '商品名称', '用户名', '客户名'],
        'en': ['name', 'title', 'product_name', 'customer_name', 'user_name', 'full_name'],
        'patterns': [r'.*_name$', r'.*名称$', r'.*姓名$', r'.*商品名$']
    },
    'text': {
        'zh': ['描述', '说明', '文本', '内容', '评论', '备注', '备注信息'],
        'en': ['description', 'desc', 'text', 'content', 'comment', 'note', 'memo', 'review'],
        'patterns': [r'.*_desc$', r'.*_text$', r'.*_comment$', r'.*描述$', r'.*评论$']
    },
    'country': {
        'zh': ['国家', '地区', '地域', '省市', '城市', '省份', '国家/地区'],
        'en': ['country', 'region', 'city', 'state', 'province', 'location', 'area'],
        'patterns': [r'.*_country$', r'.*_region$', r'.*_city$', r'.*_state$', r'.*国家$', r'.*地区$', r'.*城市$']
    },
    'device': {
        'zh': ['设备', '终端', '平台', '操作系统', '设备类型'],
        'en': ['device', 'platform', 'os', 'operating_system', 'device_type', 'client'],
        'patterns': [r'.*_device$', r'.*_platform$', r'.*设备$', r'.*平台$']
    },
    'source': {
        'zh': ['来源', '渠道', '来源渠道', '流量来源', '来源网站'],
        'en': ['source', 'channel', 'referrer', 'utm_source', 'traffic_source'],
        'patterns': [r'.*_source$', r'.*_channel$', r'.*来源$', r'.*渠道$']
    },
    'boolean': {
        'zh': ['是否', '有没有', '已否', '已标记'],
        'en': ['is_', 'has_', 'have_', 'opt_in', 'is_active', 'is_deleted', 'is_valid'],
        'patterns': [r'^is_', r'^has_', r'^have_', r'.*_flag$', r'.*_active$', r'.*是否$']
    },
    'rating': {
        'zh': ['评分', '得分', '星级', '满意度', '评级'],
        'en': ['rating', 'score', 'star', 'grade', 'point'],
        'patterns': [r'.*_rating$', r'.*_score$', r'.*评分$', r'.*得分$', r'.*星级$']
    },
    'email': {
        'zh': ['邮箱', '电子邮件', '邮件地址'],
        'en': ['email', 'mail', 'e-mail', 'email_address'],
        'patterns': [r'.*_email$', r'.*邮箱$', r'.*邮件$']
    },
    'age': {
        'zh': ['年龄', '年齡'],
        'en': ['age'],
        'patterns': [r'^age$', r'.*年龄$']
    },
    'event': {
        'zh': ['事件', '行为', '动作', '事件类型', '操作'],
        'en': ['event', 'action', 'event_type', 'activity', 'behavior'],
        'patterns': [r'.*_event$', r'.*_action$', r'.*事件$', r'.*行为$']
    },
    'payment': {
        'zh': ['支付', '付款', '支付方式', '付款方式'],
        'en': ['payment', 'pay', 'payment_method', 'pay_method'],
        'patterns': [r'.*_payment$', r'.*_pay$', r'.*支付$', r'.*付款$']
    },
    'discount': {
        'zh': ['折扣', '优惠', '打折', '折扣率', '优惠率'],
        'en': ['discount', 'discount_pct', 'coupon', 'promotion'],
        'patterns': [r'.*_discount$', r'.*_pct$', r'.*折扣$', r'.*优惠$']
    }
}

def normalize_text(text):
    """文本标准化（小写+去除下划线）"""
    if isinstance(text, str):
        return text.lower().replace('_', '').replace('-', '').replace(' ', '')
    return str(text).lower()

def detect_field_type(column_name, sample_data, column_values=None):
    """检测字段类型（支持中英双语）"""
    col_lower = normalize_text(column_name)

    # 1. 优先通过列名匹配
    for field_type, config in FIELD_PATTERNS.items():
        # 中文匹配
        for zh_term in config.get('zh', []):
            if zh_term in col_lower or zh_term in column_name:
                # 进一步验证
                if field_type == 'amount' and sample_data is not None:
                    if pd.api.types.is_numeric_dtype(sample_data):
                        return 'amount'
                if field_type == 'quantity' and sample_data is not None:
                    if pd.api.types.is_numeric_dtype(sample_data):
                        return 'quantity'
                return field_type

        # 英文匹配
        for en_term in config.get('en', []):
            if en_term in col_lower:
                if field_type == 'amount' and sample_data is not None:
                    if pd.api.types.is_numeric_dtype(sample_data):
                        return 'amount'
                if field_type == 'quantity' and sample_data is not None:
                    if pd.api.types.is_numeric_dtype(sample_data):
                        return 'quantity'
                return field_type

        # 正则模式匹配
        for pattern in config.get('patterns', []):
            if re.match(pattern, col_lower, re.IGNORECASE):
                return field_type

    # 2. 通过数据内容推断
    if sample_data is not None and len(sample_data) > 0:
        # 检查是否全为数字
        if pd.api.types.is_numeric_dtype(sample_data):
            non_null = sample_data.dropna()
            if len(non_null) > 0:
                # 检查是否为ID类型（通常是整数且值域较大）
                if non_null.max() > 10000 and column_values is not None:
                    # 检查是否有重复（ID应该有较高重复度用于关联）
                    if non_null.value_counts().max() > 1:
                        return 'id'
                # 检查是否为金额（有小数或值域大）
                if non_null.max() > 100 or (non_null != non_null.astype(int)).any():
                    return 'amount'
                return 'quantity'

        # 检查是否为日期
        if pd.api.types.is_datetime64_any_dtype(sample_data):
            return 'date'

        # 检查是否为布尔值
        unique_vals = set(sample_data.dropna().unique())
        if unique_vals.issubset({True, False, 0, 1, 'true', 'false', 'yes', 'no', 'Y', 'N'}):
            return 'boolean'

        # 检查是否为评分（1-5或1-10）
        numeric_vals = pd.to_numeric(sample_data, errors='coerce').dropna()
        if len(numeric_vals) > 0:
            if set(numeric_vals.unique()).issubset({1, 2, 3, 4, 5}) or set(numeric_vals.unique()).issubset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10}):
                return 'rating'

        # 检查是否为邮箱
        if sample_data.dtype == 'object':
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if sample_data.dropna().str.match(email_pattern, na=False).sum() > len(sample_data) * 0.5:
                return 'email'

    # 3. 默认为text
    return 'text'

def analyze_table(df, table_name):
    """分析单张表，返回元数据"""
    metadata = {
        'table_name': table_name,
        'rows': len(df),
        'columns': len(df.columns),
        'fields': {}
    }

    for col in df.columns:
        sample_data = df[col].head(100) if len(df) > 0 else None
        field_type = detect_field_type(col, sample_data, df[col])

        # 统计基本信息
        non_null_count = df[col].count()
        null_count = df[col].isnull().sum()
        unique_count = df[col].nunique()

        # 类型特定统计
        stats = {
            'original_name': col,
            'type': field_type,
            'non_null': int(non_null_count),
            'null': int(null_count),
            'null_pct': round(null_count / len(df) * 100, 2) if len(df) > 0 else 0,
            'unique': int(unique_count)
        }

        # 根据类型添加特定统计
        if field_type == 'amount' and pd.api.types.is_numeric_dtype(df[col]):
            stats['min'] = float(df[col].min()) if non_null_count > 0 else 0
            stats['max'] = float(df[col].max()) if non_null_count > 0 else 0
            stats['avg'] = float(df[col].mean()) if non_null_count > 0 else 0
            stats['median'] = float(df[col].median()) if non_null_count > 0 else 0

        elif field_type == 'quantity' and pd.api.types.is_numeric_dtype(df[col]):
            stats['min'] = int(df[col].min()) if non_null_count > 0 else 0
            stats['max'] = int(df[col].max()) if non_null_count > 0 else 0
            stats['avg'] = float(df[col].mean()) if non_null_count > 0 else 0
            stats['sum'] = float(df[col].sum()) if non_null_count > 0 else 0

        elif field_type == 'date':
            try:
                dates = pd.to_datetime(df[col], errors='coerce').dropna()
                if len(dates) > 0:
                    stats['min_date'] = str(dates.min())
                    stats['max_date'] = str(dates.max())
                    stats['date_range_days'] = (dates.max() - dates.min()).days
            except:
                pass

        elif field_type == 'rating':
            if pd.api.types.is_numeric_dtype(df[col]):
                stats['min_rating'] = int(df[col].min()) if non_null_count > 0 else 0
                stats['max_rating'] = int(df[col].max()) if non_null_count > 0 else 0
                stats['avg_rating'] = float(df[col].mean()) if non_null_count > 0 else 0

        elif field_type == 'category':
            top_values = df[col].value_counts().head(5).to_dict()
            stats['top_values'] = top_values
            stats['categories_count'] = unique_count

        metadata['fields'][col] = stats

    return metadata

def discover_relationships(tables_metadata):
    """发现表之间的外键关系"""
    relationships = []

    tables = list(tables_metadata.keys())

    for i, table1 in enumerate(tables):
        for j, table2 in enumerate(tables):
            if i >= j:
                continue

            metadata1 = tables_metadata[table1]
            metadata2 = tables_metadata[table2]

            # 查找可能的关联字段
            for field1_name, field1_info in metadata1['fields'].items():
                if field1_info['type'] == 'id':
                    # 检查是否表2中有对应的ID字段
                    for field2_name, field2_info in metadata2['fields'].items():
                        # 检查列名匹配
                        field1_base = field1_name.lower().replace('_id', '').replace('id', '')
                        field2_base = field2_name.lower().replace('_id', '').replace('id', '')

                        if field1_base and field2_base:
                            # 匹配：customer_id <-> customers.id 或 customer_id <-> customer_id
                            if field1_base in field2_base or field2_base in field1_base:
                                relationships.append({
                                    'from_table': table1,
                                    'from_field': field1_name,
                                    'to_table': table2,
                                    'to_field': field2_name,
                                    'relationship_type': 'many_to_one',
                                    'confidence': 0.8
                                })
                            # 直接匹配：order_id <-> order_id
                            elif field1_name.lower() == field2_name.lower():
                                relationships.append({
                                    'from_table': table1,
                                    'from_field': field1_name,
                                    'to_table': table2,
                                    'to_field': field2_name,
                                    'relationship_type': 'many_to_one',
                                    'confidence': 0.95
                                })

    # 去重并合并相似关系
    unique_relationships = []
    seen = set()
    for rel in relationships:
        key = (rel['from_table'], rel['to_table'])
        if key not in seen:
            seen.add(key)
            unique_relationships.append(rel)

    return unique_relationships

def clean_field(df, col, field_type):
    """根据字段类型清洗数据"""
    df_clean = df.copy()

    if field_type == 'id':
        # ID字段：填充缺失值，转换为字符串
        df_clean[col] = df_clean[col].fillna('0').astype(str)
        df_clean[col] = df_clean[col].replace('nan', '0', regex=False)

    elif field_type == 'date':
        # 日期字段：转换日期格式
        df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        # 删除无法解析的日期
        invalid_count = df_clean[col].isnull().sum() - df[col].isnull().sum()
        if invalid_count > 0:
            print(f"  Warning: {col} has {invalid_count} invalid dates removed")

    elif field_type == 'amount':
        # 金额字段：标准化为数值
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        median_val = df_clean[col].median()
        if pd.isna(median_val):
            median_val = 0
        df_clean[col] = df_clean[col].fillna(median_val)

        # 处理负数（金额不应为负）
        negative_count = (df_clean[col] < 0).sum()
        if negative_count > 0:
            df_clean = df_clean[df_clean[col] >= 0]
            print(f"  Warning: {col} has {negative_count} negative amounts removed")

    elif field_type == 'quantity':
        # 数量字段：标准化为整数
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        df_clean[col] = df_clean[col].astype(int)
        # 处理负数
        negative_count = (df_clean[col] < 0).sum()
        if negative_count > 0:
            df_clean = df_clean[df_clean[col] >= 0]
            print(f"  Warning: {col} has {negative_count} negative quantities removed")

    elif field_type == 'boolean':
        # 布尔字段：标准化为True/False
        df_clean[col] = df_clean[col].map({
            'true': True, 'false': False, 'yes': True, 'no': False,
            'Y': True, 'N': False, '1': True, '0': False,
            True: True, False: False
        }).fillna(False).astype(bool)

    elif field_type == 'rating':
        # 评分字段：标准化为1-5
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)
        df_clean[col] = df_clean[col].clip(1, 5)

    elif field_type == 'category':
        # 类别字段：填充缺失值，标准化
        df_clean[col] = df_clean[col].fillna('Unknown').astype(str)
        df_clean[col] = df_clean[col].str.strip().str.title()

    elif field_type == 'email':
        # 邮箱字段：填充缺失值，标准化
        df_clean[col] = df_clean[col].fillna('unknown@example.com').astype(str)
        df_clean[col] = df_clean[col].str.lower().str.strip()

    elif field_type == 'text':
        # 文本字段：填充缺失值
        df_clean[col] = df_clean[col].fillna('').astype(str)
        df_clean[col] = df_clean[col].str.strip()

    # 其他类型：填充缺失值
    if df_clean[col].isnull().any():
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].fillna(0)
        else:
            df_clean[col] = df_clean[col].fillna('Unknown')

    return df_clean

def clean_table(df, table_name, metadata):
    """清洗整张表"""
    df_clean = df.copy()
    original_rows = len(df_clean)

    print(f"\nCleaning table: {table_name}")
    print(f"Original rows: {original_rows}")

    # 根据元数据清洗每个字段
    for col, field_info in metadata['fields'].items():
        if col in df_clean.columns:
            df_clean = clean_field(df_clean, col, field_info['type'])

    # 删除完全重复的行
    duplicates = df_clean.duplicated().sum()
    if duplicates > 0:
        df_clean = df_clean.drop_duplicates()
        print(f"Removed duplicates: {duplicates}")

    # 删除字段全为空的行
    null_rows = df_clean.dropna(how='all').shape[0]
    if null_rows < len(df_clean):
        df_clean = df_clean.dropna(how='all')
        print(f"Removed null rows: {len(df_clean) - null_rows}")

    print(f"After cleaning: {len(df_clean)} rows")

    return df_clean

def infer_sql_type(field_type, original_dtype):
    """根据字段类型推断SQL类型"""
    type_mapping = {
        'id': 'TEXT',
        'date': 'TEXT',  # SQLite不原生支持datetime，用TEXT存储ISO格式
        'amount': 'REAL',
        'quantity': 'INTEGER',
        'boolean': 'INTEGER',
        'rating': 'INTEGER',
        'category': 'TEXT',
        'email': 'TEXT',
        'text': 'TEXT',
        'name': 'TEXT',
        'country': 'TEXT',
        'device': 'TEXT',
        'source': 'TEXT',
        'event': 'TEXT',
        'payment': 'TEXT',
        'discount': 'REAL',
        'age': 'INTEGER'
    }

    sql_type = type_mapping.get(field_type, 'TEXT')

    # 如果原类型是浮点，但字段类型不是amount/quantity，保持REAL
    if pd.api.types.is_float_dtype(original_dtype) and field_type in ['amount', 'quantity']:
        sql_type = 'REAL'

    return sql_type

def create_table_sql(table_name, metadata, relationships):
    """生成CREATE TABLE SQL语句"""
    columns_def = []
    primary_keys = []

    for col, field_info in metadata['fields'].items():
        sql_type = infer_sql_type(field_info['type'], pd.Series(dtype=field_info.get('original_type', 'object')))
        columns_def.append(f'"{col}" {sql_type}')

        # ID字段作为主键
        if field_info['type'] == 'id' and len(primary_keys) == 0:
            primary_keys.append(col)

    columns_str = ',\n    '.join(columns_def)

    # 添加外键约束
    for rel in relationships:
        if rel['from_table'] == table_name and rel['from_field'] in metadata['fields']:
            fk_col = rel['from_field']
            ref_table = rel['to_table']
            ref_col = rel['to_field']
            columns_str += f',\n    FOREIGN KEY ("{fk_col}") REFERENCES "{ref_table}"("{ref_col}")'

    sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n    {columns_str}\n)'

    return sql

def get_table_name_from_filename(filename):
    """从文件名推断表名"""
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name.lower()

def process_files(file_paths, db_path="ecommerce.db"):
    """
    核心处理函数：处理用户上传的文件

    Args:
        file_paths: 文件路径列表
        db_path: 数据库路径

    Returns:
        dict: 处理结果和元数据
    """
    # 确保数据库连接被正确关闭
    def safe_remove_db(db_path):
        """安全删除数据库文件"""
        import time
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                    print(f"Deleted old database: {db_path}")
                    return True
            except Exception as e:
                print(f"Attempt {attempt+1}/{max_attempts} failed: {str(e)}")
                time.sleep(1)
        return False

    # 删除旧数据库
    if not safe_remove_db(db_path):
        print(f"Warning: Could not delete old database: {db_path}")
        # 尝试使用不同的数据库名称
        import random
        db_path = f"ecommerce_{random.randint(1000, 9999)}.db"
        print(f"Using alternative database path: {db_path}")

    # 使用with语句管理数据库连接
    try:
        with sqlite3.connect(db_path) as conn:
            results = {
                'total_files': len(file_paths),
                'success': 0,
                'failed': 0,
                'tables': {},
                'errors': []
            }

            all_metadata = {}
            all_relationships = []

            # 第一遍：加载所有文件并分析
            print("\n" + "="*60)
            print("第一阶段：数据加载与智能分析")
            print("="*60)

            table_data = {}
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                table_name = get_table_name_from_filename(filename)

                try:
                    # 加载数据
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    elif file_path.endswith('.xlsx'):
                        df = pd.read_excel(file_path)
                    else:
                        raise ValueError(f"不支持的文件格式: {filename}")

                    # 分析表结构
                    metadata = analyze_table(df, table_name)
                    all_metadata[table_name] = metadata
                    table_data[table_name] = df

                    print(f"\n[OK] {filename} -> {table_name}")
                    print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
                    print(f"  Field types:")
                    for col, info in metadata['fields'].items():
                        print(f"    - {col}: {info['type']}")

                    results['success'] += 1
                    results['tables'][table_name] = {
                        'rows': len(df),
                        'columns': len(df.columns),
                        'filename': filename
                    }

                except Exception as e:
                    print(f"\n[FAIL] {filename}: {str(e)}")
                    results['failed'] += 1
                    results['errors'].append(f"{filename}: {str(e)}")

            # 发现表关系
            print("\n" + "="*60)
            print("第二阶段：发现表关联关系")
            print("="*60)

            relationships = discover_relationships(all_metadata)
            all_relationships = relationships

            if relationships:
                print(f"\nDiscovered {len(relationships)} table relationships:")
                for rel in relationships:
                    print(f"  {rel['from_table']}.{rel['from_field']} -> {rel['to_table']}.{rel['to_field']}")
            else:
                print("\nNo obvious table relationships found")

            # 第三遍：清洗数据并导入
            print("\n" + "="*60)
            print("第三阶段：数据清洗与导入")
            print("="*60)

            for table_name, df in table_data.items():
                metadata = all_metadata[table_name]

                try:
                    # 清洗数据
                    df_clean = clean_table(df, table_name, metadata)

                    # 创建表
                    create_sql = create_table_sql(table_name, metadata, relationships)
                    conn.executescript(create_sql)

                    # 导入数据
                    df_clean.to_sql(table_name, conn, if_exists='replace', index=False)
                    print(f"[OK] Imported {table_name}: {len(df_clean)} rows")

                except Exception as e:
                    print(f"[FAIL] Import {table_name} failed: {str(e)}")

            # 创建索引
            print("\n" + "="*60)
            print("第四阶段：创建索引优化查询")
            print("="*60)

            cursor = conn.cursor()
            index_count = 0

            for table_name, metadata in all_metadata.items():
                for col, field_info in metadata['fields'].items():
                    # 为ID和日期字段创建索引
                    if field_info['type'] in ['id', 'date']:
                        try:
                            index_name = f"idx_{table_name}_{col}"
                            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({col})")
                            index_count += 1
                        except:
                            pass

            conn.commit()
            print(f"创建了 {index_count} 个索引")

            # 保存元数据到数据库
            metadata_json = {
                'tables': all_metadata,
                'relationships': all_relationships
            }

            cursor.execute("DROP TABLE IF EXISTS _metadata")
            cursor.execute("CREATE TABLE _metadata (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT INTO _metadata VALUES (?, ?)", ('schema', json.dumps(metadata_json, ensure_ascii=False)))
            conn.commit()

            # 打印汇总
            print("\n" + "="*60)
            print("Data Processing Summary")
            print("="*60)
            print(f"Total files: {results['total_files']}")
            print(f"Success: {results['success']}")
            print(f"Failed: {results['failed']}")
            print(f"\nImported tables:")
            for table, info in results['tables'].items():
                print(f"  - {table}: {info['rows']:,} rows, {info['columns']} columns")

            results['relationships'] = all_relationships
            results['metadata'] = all_metadata
            results['db_path'] = db_path

            return results
            
    except Exception as e:
        print(f"数据处理失败: {str(e)}")
        return {
            'total_files': len(file_paths),
            'success': 0,
            'failed': len(file_paths),
            'tables': {},
            'errors': [f"数据处理失败: {str(e)}"],
            'relationships': [],
            'metadata': {}
        }

def get_database_summary(db_path="ecommerce.db"):
    """获取数据库概览"""
    if not os.path.exists(db_path):
        return None

    # 使用with语句管理数据库连接
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != '_metadata'")
        tables = [row[0] for row in cursor.fetchall()]

        summary = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                rows = cursor.fetchone()[0]

                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()

                summary[table] = {
                    'rows': rows,
                    'columns': len(columns),
                    'column_names': [col[1] for col in columns]
                }
            except Exception as e:
                print(f"获取表 {table} 信息失败: {str(e)}")

        # 获取元数据
        cursor.execute("SELECT value FROM _metadata WHERE key = 'schema'")
        row = cursor.fetchone()
        if row:
            metadata = json.loads(row[0])
            summary['_relationships'] = metadata.get('relationships', [])
            summary['_tables_metadata'] = metadata.get('tables', {})

        return summary

def get_field_mappings(db_path="ecommerce.db"):
    """获取字段类型映射，用于后续分析"""
    summary = get_database_summary(db_path)
    if not summary or '_tables_metadata' not in summary:
        return {}

    mappings = {}
    for table, metadata in summary['_tables_metadata'].items():
        mappings[table] = {
            'id_fields': [],
            'date_fields': [],
            'amount_fields': [],
            'quantity_fields': [],
            'category_fields': [],
            'text_fields': []
        }

        for col, field_info in metadata['fields'].items():
            field_type = field_info['type']
            if field_type == 'id':
                mappings[table]['id_fields'].append(col)
            elif field_type == 'date':
                mappings[table]['date_fields'].append(col)
            elif field_type == 'amount':
                mappings[table]['amount_fields'].append(col)
            elif field_type == 'quantity':
                mappings[table]['quantity_fields'].append(col)
            elif field_type == 'category':
                mappings[table]['category_fields'].append(col)
            elif field_type in ['text', 'name', 'email']:
                mappings[table]['text_fields'].append(col)

    return mappings

if __name__ == "__main__":
    import glob

    # 测试用：处理data1文件夹
    data1_path = "data/data1"
    if os.path.exists(data1_path):
        csv_files = glob.glob(os.path.join(data1_path, "*.csv"))
        print(f"找到 {len(csv_files)} 个CSV文件\n")

        results = process_files(csv_files)

        print("\n\n数据库字段映射:")
        mappings = get_field_mappings()
        for table, fields in mappings.items():
            print(f"\n{table}:")
            for field_type, cols in fields.items():
                if cols:
                    print(f"  {field_type}: {cols}")
