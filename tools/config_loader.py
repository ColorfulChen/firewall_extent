# config_loader.py
import yaml
import os
from typing import Dict, List

def load_filter_rules() -> Dict:
    """加载过滤规则配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'filter_rules.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 全局配置
FILTER_CONFIG = load_filter_rules()

def get_target_containers() -> List[Dict]:
    """获取目标容器配置"""
    return FILTER_CONFIG.get('TARGET_CONTAINERS', [])

def get_video_page_config() -> Dict:
    """获取视频页面配置"""
    return FILTER_CONFIG.get('VIDEO_PAGE_CONFIG', {})

def get_scholar_page_configs() -> List[Dict]:
    """获取学术页面配置"""
    return FILTER_CONFIG.get('SCHOLAR_PAGE_CONFIGS', [])

def get_wiki_page_config() -> Dict:
    """获取wiki过滤配置"""
    return FILTER_CONFIG.get('WIKI_PAGE_CONFIG', {})

def get_wiki_content_config() -> Dict:
    """获取wiki过滤配置"""
    return FILTER_CONFIG.get('WIKI_CONTENT_CONFIG', {})