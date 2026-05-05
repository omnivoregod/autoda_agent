"""
配置加载模块
统一从环境变量或配置文件加载配置，避免硬编码
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config.yaml"
CONFIG_ENV_KEY = "CONFIG_PATH"

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，默认从环境变量CONFIG_PATH读取
        
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = os.getenv(CONFIG_ENV_KEY, DEFAULT_CONFIG_PATH)
    
    if not os.path.exists(config_path):
        logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
        return get_default_config()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logger.info(f"成功加载配置文件: {config_path}")
            return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置
    
    Returns:
        默认配置字典
    """
    return {
        'database': {
            'type': 'sqlite',
            'path': 'ecommerce.db',
            'timeout': 30
        },
        'llm': {
            'mode': os.getenv('LLM_MODE', 'public'),
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'base_url': os.getenv('PRIVATE_LLM_URL', ''),
            'model': os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
            'temperature': 0.7
        },
        'cache': {
            'enabled': False,
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': 0,
            'expire_seconds': 3600
        },
        'masking': {
            'enabled': True,
            'rules': {
                'phone': {
                    'enabled': True,
                    'pattern': r'^(\d{3})\d{4}(\d{4})$',
                    'replacement': r'\1****\2'
                },
                'email': {
                    'enabled': True,
                    'pattern': r'^(\w)\w+@(\w+\.\w+)$',
                    'replacement': r'\1**@\2'
                },
                'order_id': {
                    'enabled': True,
                    'pattern': r'^(\w{4})\w+(\w{4})$',
                    'replacement': r'\1****\2'
                }
            }
        },
        'retry': {
            'max_attempts': 3,
            'wait_multiplier': 1,
            'wait_min': 2,
            'wait_max': 10
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

def save_config(config: Dict[str, Any], config_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
        
    Returns:
        是否保存成功
    """
    try:
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        logger.info(f"配置已保存到: {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False

def update_config(updates: Dict[str, Any], config_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """
    更新配置（合并到现有配置）
    
    Args:
        updates: 要更新的配置项
        config_path: 配置文件路径
        
    Returns:
        是否更新成功
    """
    current_config = load_config(config_path)
    
    def deep_merge(base: Dict, updates: Dict) -> Dict:
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    merged_config = deep_merge(current_config, updates)
    return save_config(merged_config, config_path)

def get_database_config() -> Dict[str, Any]:
    """获取数据库配置（便捷方法）"""
    config = load_config()
    return config.get('database', {})

def get_llm_config() -> Dict[str, Any]:
    """获取LLM配置（便捷方法）"""
    config = load_config()
    return config.get('llm', {})

def get_cache_config() -> Dict[str, Any]:
    """获取缓存配置（便捷方法）"""
    config = load_config()
    return config.get('cache', {})

def get_masking_config() -> Dict[str, Any]:
    """获取脱敏配置（便捷方法）"""
    config = load_config()
    return config.get('masking', {})

def get_retry_config() -> Dict[str, Any]:
    """获取重试配置（便捷方法）"""
    config = load_config()
    return config.get('retry', {})
