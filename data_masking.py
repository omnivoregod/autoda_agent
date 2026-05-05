# data_masking.py
"""
数据脱敏模块
对用户手机号、订单号等敏感字段脱敏
支持配置化规则定制
"""
import re
import yaml
import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config.yaml"
MASKING_CONFIG_KEY = "masking"

class DataMasker:
    """
    数据脱敏器
    
    支持：
    - 预定义脱敏规则（手机号、邮箱、订单号、身份证）
    - 自定义正则脱敏规则
    - DataFrame批量脱敏
    - 配置化规则管理
    """
    
    PRESET_RULES = {
        'phone': {
            'name': '手机号',
            'pattern': r'^(\d{3})\d{4}(\d{4})$',
            'replacement': r'\1****\2',
            'description': '手机号中间四位脱敏'
        },
        'email': {
            'name': '邮箱',
            'pattern': r'^(\w)\w+@(\w+\.\w+)$',
            'replacement': r'\1**@\2',
            'description': '邮箱用户名脱敏'
        },
        'order_id': {
            'name': '订单号',
            'pattern': r'^(\w{4})\w+(\w{4})$',
            'replacement': r'\1****\2',
            'description': '订单号首尾保留脱敏'
        },
        'id_card': {
            'name': '身份证号',
            'pattern': r'^(\d{6})\d+(\d{4})$',
            'replacement': r'\1********\2',
            'description': '身份证号中间部分脱敏'
        },
        'bank_card': {
            'name': '银行卡号',
            'pattern': r'^(\d{4})\d+(\d{4})$',
            'replacement': r'\1****\2',
            'description': '银行卡号首尾保留脱敏'
        },
        'address': {
            'name': '地址',
            'pattern': r'(.{6}).*(.{6})$',
            'replacement': r'\1****\2',
            'description': '地址首尾保留脱敏'
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化脱敏器
        
        Args:
            config_path: 配置文件路径，默认从config.yaml读取
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.rules = self._load_rules()
        self.column_map = self._load_column_map()
        self.enabled = self.rules.pop('enabled', True) if 'enabled' in self.rules else True
    
    def _load_rules(self) -> Dict[str, Any]:
        """从配置文件加载脱敏规则"""
        if not os.path.exists(self.config_path):
            logger.info("未找到配置文件，使用默认脱敏规则")
            return self._get_default_rules()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f) or {}
                masking_config = full_config.get(MASKING_CONFIG_KEY, {})
                
                if not masking_config:
                    return self._get_default_rules()
                
                rules = masking_config.get('rules', {})
                if masking_config.get('enabled', True) is False:
                    rules['enabled'] = False
                
                return rules
        except Exception as e:
            logger.error(f"加载脱敏配置失败: {str(e)}，使用默认规则")
            return self._get_default_rules()
    
    def _load_column_map(self) -> Dict[str, Dict[str, str]]:
        """从配置文件加载字段映射"""
        if not os.path.exists(self.config_path):
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f) or {}
                return full_config.get('masking_columns', {})
        except Exception:
            return {}
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """获取默认脱敏规则"""
        return {
            'enabled': True,
            'phone': self.PRESET_RULES['phone'],
            'email': self.PRESET_RULES['email'],
            'order_id': self.PRESET_RULES['order_id']
        }
    
    def mask_phone(self, value: str) -> str:
        """
        脱敏手机号：138****8888
        
        Args:
            value: 手机号
            
        Returns:
            脱敏后的手机号
        """
        if not self.enabled:
            return str(value)
        
        rule = self.rules.get('phone', self.PRESET_RULES['phone'])
        if not rule.get('enabled', True):
            return str(value)
        
        pattern = rule.get('pattern', self.PRESET_RULES['phone']['pattern'])
        replacement = rule.get('replacement', self.PRESET_RULES['phone']['replacement'])
        
        return re.sub(pattern, replacement, str(value))
    
    def mask_email(self, value: str) -> str:
        """
        脱敏邮箱：z**@example.com
        
        Args:
            value: 邮箱地址
            
        Returns:
            脱敏后的邮箱
        """
        if not self.enabled:
            return str(value)
        
        rule = self.rules.get('email', self.PRESET_RULES['email'])
        if not rule.get('enabled', True):
            return str(value)
        
        pattern = rule.get('pattern', self.PRESET_RULES['email']['pattern'])
        replacement = rule.get('replacement', self.PRESET_RULES['email']['replacement'])
        
        return re.sub(pattern, replacement, str(value))
    
    def mask_order_id(self, value: str) -> str:
        """
        脱敏订单号：ORD****2345
        
        Args:
            value: 订单号
            
        Returns:
            脱敏后的订单号
        """
        if not self.enabled:
            return str(value)
        
        rule = self.rules.get('order_id', self.PRESET_RULES['order_id'])
        if not rule.get('enabled', True):
            return str(value)
        
        pattern = rule.get('pattern', self.PRESET_RULES['order_id']['pattern'])
        replacement = rule.get('replacement', self.PRESET_RULES['order_id']['replacement'])
        
        return re.sub(pattern, replacement, str(value))
    
    def mask_id_card(self, value: str) -> str:
        """
        脱敏身份证号：110****1988
        
        Args:
            value: 身份证号
            
        Returns:
            脱敏后的身份证号
        """
        if not self.enabled:
            return str(value)
        
        rule = self.rules.get('id_card', self.PRESET_RULES['id_card'])
        if not rule.get('enabled', True):
            return str(value)
        
        pattern = rule.get('pattern', self.PRESET_RULES['id_card']['pattern'])
        replacement = rule.get('replacement', self.PRESET_RULES['id_card']['replacement'])
        
        return re.sub(pattern, replacement, str(value))
    
    def mask_bank_card(self, value: str) -> str:
        """
        脱敏银行卡号：6228****1234
        
        Args:
            value: 银行卡号
            
        Returns:
            脱敏后的银行卡号
        """
        if not self.enabled:
            return str(value)
        
        rule = self.rules.get('bank_card', self.PRESET_RULES['bank_card'])
        if not rule.get('enabled', True):
            return str(value)
        
        pattern = rule.get('pattern', self.PRESET_RULES['bank_card']['pattern'])
        replacement = rule.get('replacement', self.PRESET_RULES['bank_card']['replacement'])
        
        return re.sub(pattern, replacement, str(value))
    
    def mask_custom(self, value: str, pattern: str, replacement: str) -> str:
        """
        自定义正则脱敏
        
        Args:
            value: 原始值
            pattern: 正则表达式
            replacement: 替换表达式
            
        Returns:
            脱敏后的值
        """
        if not self.enabled:
            return str(value)
        
        return re.sub(pattern, replacement, str(value))
    
    def mask_dataframe(self, df: pd.DataFrame, table_name: Optional[str] = None) -> pd.DataFrame:
        """
        批量脱敏DataFrame
        
        Args:
            df: 原始DataFrame
            table_name: 表名（用于查找字段映射规则）
            
        Returns:
            脱敏后的DataFrame
        """
        if not self.enabled or df.empty:
            return df.copy()
        
        masked_df = df.copy()
        
        if table_name and table_name in self.column_map:
            for column, rule_name in self.column_map[table_name].items():
                if column in masked_df.columns:
                    mask_method = self._get_mask_method(rule_name)
                    if mask_method:
                        masked_df[column] = masked_df[column].apply(mask_method)
                        logger.info(f"字段 {column} 已使用规则 {rule_name} 脱敏")
        
        return masked_df
    
    def mask_dict(self, data: Dict[str, Any], columns: List[str], rule_name: str) -> Dict[str, Any]:
        """
        脱敏字典中的指定字段
        
        Args:
            data: 原始字典
            columns: 要脱敏的字段列表
            rule_name: 脱敏规则名称
            
        Returns:
            脱敏后的字典
        """
        masked_data = data.copy()
        mask_method = self._get_mask_method(rule_name)
        
        if mask_method:
            for column in columns:
                if column in masked_data:
                    masked_data[column] = mask_method(masked_data[column])
        
        return masked_data
    
    def _get_mask_method(self, rule_name: str):
        """获取脱敏方法"""
        mask_methods = {
            'phone': self.mask_phone,
            'email': self.mask_email,
            'order_id': self.mask_order_id,
            'id_card': self.mask_id_card,
            'bank_card': self.mask_bank_card
        }
        return mask_methods.get(rule_name)
    
    def add_rule(self, name: str, pattern: str, replacement: str, description: str = ""):
        """
        添加自定义脱敏规则
        
        Args:
            name: 规则名称
            pattern: 正则表达式
            replacement: 替换表达式
            description: 规则描述
        """
        self.rules[name] = {
            'pattern': pattern,
            'replacement': replacement,
            'description': description,
            'enabled': True
        }
        logger.info(f"已添加脱敏规则: {name}")
    
    def get_available_rules(self) -> List[str]:
        """获取所有可用的脱敏规则名称"""
        return list(self.rules.keys())
    
    def is_enabled(self) -> bool:
        """检查脱敏是否启用"""
        return self.enabled


def mask_sensitive_data(df: pd.DataFrame, table_name: Optional[str] = None, 
                       config_path: Optional[str] = None) -> pd.DataFrame:
    """
    便捷函数：脱敏DataFrame
    
    Args:
        df: 原始DataFrame
        table_name: 表名
        config_path: 配置文件路径
        
    Returns:
        脱敏后的DataFrame
    """
    masker = DataMasker(config_path)
    return masker.mask_dataframe(df, table_name)
