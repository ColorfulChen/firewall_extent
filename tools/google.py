import json
import re
import brotli
import gzip
import io
from bs4 import BeautifulSoup
import hashlib

from tools.config_loader import get_scholar_page_configs,get_video_page_config,get_target_containers
from tools.database import log_to_mongo

# 配置删除规则
TARGET_CONTAINERS = get_target_containers()
VIDEO_PAGE_CONFIG = get_video_page_config()
SCHOLAR_PAGE_CONFIGS = get_scholar_page_configs()


def filter_vet_response(response, filter_words, request_url=None):
    """专门处理 google.com/search?vet= 的响应包"""
    if not response:
        return None


    try:
        # 解码响应体
        body_text = response
        # 使用BeautifulSoup解析
        soup = BeautifulSoup(body_text, 'html.parser')

        # 定位目标容器
        containers = soup.select(VIDEO_PAGE_CONFIG['container'])
        pattern = re.compile('|'.join(filter_words), flags=re.IGNORECASE)

        removed_count = 0
        for container in containers:
            # 检查是否在保留规则中
            if any(container.select(preserve) for preserve in VIDEO_PAGE_CONFIG['preserve_rules']):
                continue

            # 检查是否匹配删除规则
            if any(container.select(rule) for rule in VIDEO_PAGE_CONFIG['remove_rules']):
                # 关键词检查
                text_content = container.get_text()
                if pattern.search(text_content):
                    # 记录删除的过滤条目
                    log_to_mongo({
                        "type": "vet_page_filter",
                        "action": "removed_container",
                        "content": str(container),
                        "filter_words": filter_words,
                        "container_selector": VIDEO_PAGE_CONFIG['container'],
                        "remove_rules": VIDEO_PAGE_CONFIG['remove_rules']
                    }, request_url)

                    container.decompose()  # 删除整个DOM块
                    removed_count += 1

        if removed_count > 0:
            print(f"已删除 {removed_count} 个包含关键词的区块")
            # 生成新HTML并编码
            filtered_body = str(soup)
            new_body = filtered_body.encode('utf-8')
        else:
            print("未检测到需要删除的内容")

        return new_body
    except Exception as e:
        print(f"处理失败: {str(e)}")
        return response  # 返回原始响应体

def google_search_filter(response,filter_words, request_url=None):
    """
    过滤谷歌联想词的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    prefix = b")]}'\n"
    # if decompressed.startswith(prefix):
    #     json_bytes = decompressed[len(prefix):]
    # else:
    #     json_bytes = decompressed
    data = json.loads(decompressed[len(prefix):])
    filtered = []
    for item in data[0]:
        text = item[0]
        if not any(re.search(word, text) for word in filter_words):
            filtered.append(item)
        else:
            print(f"Filtered out: {text}")

            # 记录删除的过滤条目
            log_to_mongo({
                "type": "search_suggestion",
                "action": "filtered",
                "text": text,
                "filter_words": filter_words,
                "original_data": item
            }, request_url)

    data[0] = filtered
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8")
    new_body = prefix + new_json
    return new_body

def google_search_page_filter(response, filter_words, request_url=None):
    """
    多目标深度删除
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in TARGET_CONTAINERS:
        container_selector = container_config['container']
        containers = soup.select(container_selector)

        if not containers:
            # print(f"未找到容器: {container_selector}")
            continue

        # print(f"\n处理容器: {container_selector}")
        container_removed = 0

        for container in containers:
            # 先标记要保留的元素
            preserved_elements = []
            for preserve_rule in container_config['preserve_rules']:
                preserved_elements.extend(container.select(preserve_rule))

            # 处理每个删除规则
            for remove_rule in container_config['remove_rules']:
                for element in container.select(remove_rule):
                    # 检查是否在保留列表中
                    if element in preserved_elements:
                        continue

                    # 检查是否包含关键词
                    if element.find(string=pattern):
                        # 获取元素信息
                        element_info = {
                            'tag': element.name,
                            'classes': element.get('class', []),
                            'id': element.get('id'),
                            'rule': remove_rule,
                            'container': container_selector
                        }

                        # 打印删除信息
                        print(f"删除元素 [规则: {remove_rule}]")
                        print(f"标签: {element_info['tag']}")
                        print(f"类: {element_info['classes']}")
                        print(f"内容: {str(element)}")
                        print("-" * 40)

                        # 记录删除的过滤条目
                        log_to_mongo({
                            "type": "search_page_filter",
                            "action": "removed_element",
                            "element_info": element_info,
                            "filter_words": filter_words,
                            "container_config": container_config
                        }, request_url)

                        # 删除元素
                        element.decompose()
                        container_removed += 1
                        total_removed += 1

        # print(f"本容器删除元素数: {container_removed}")

    # print(f"\n总共删除 {total_removed} 个元素")

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def google_search_video_page_filter(response, filter_words, request_url=None):
    """
    多目标深度删除
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in VIDEO_PAGE_CONFIG:
        container_selector = container_config['container']
        containers = soup.select(container_selector)

        if not containers:
            # print(f"未找到容器: {container_selector}")
            continue

        for container in containers:
            # 先标记要保留的元素
            preserved_elements = []
            for preserve_rule in container_config['preserve_rules']:
                preserved_elements.extend(container.select(preserve_rule))

            # 处理每个删除规则
            for remove_rule in container_config['remove_rules']:
                for element in container.select(remove_rule):
                    # 检查是否在保留列表中
                    if element in preserved_elements:
                        continue

                    # 检查是否包含关键词
                    if element.find(string=pattern):
                        # 获取元素信息
                        element_info = {
                            'tag': element.name,
                            'classes': element.get('class', []),
                            'id': element.get('id'),
                            'rule': remove_rule,
                            'container': container_selector
                        }

                        # 打印删除信息
                        print(f"删除元素 [规则: {remove_rule}]")
                        print(f"标签: {element_info['tag']}")
                        print(f"类: {element_info['classes']}")
                        print(f"ID: {element_info['id']}")
                        print("-" * 40)

                        # 记录删除的过滤条目
                        log_to_mongo({
                            "type": "video_page_filter",
                            "action": "removed_element",
                            "element_info": element_info,
                            "filter_words": filter_words,
                            "container_config": VIDEO_PAGE_CONFIG
                        }, request_url)

                        # 删除元素
                        element.decompose()
                        total_removed += 1

        # print(f"本容器删除元素数: {container_removed}")

    # print(f"\n总共删除 {total_removed} 个元素")

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def get_decoded_body(response):
    encoding = response.headers.get('content-encoding', '').lower()
    body = response.body
    if encoding == 'br':
        try:
            return brotli.decompress(body)
        except Exception as e:
            print(f"[get_decoded_body] brotli解压失败: {e}")
            return b""
    elif encoding == 'gzip':
        try:
            return gzip.decompress(body)
        except Exception as e:
            print(f"[get_decoded_body] gzip解压失败: {e}")
            return b""
    elif encoding == 'deflate':
        try:
            return io.BytesIO(body).read()
        except Exception as e:
            print(f"[get_decoded_body] deflate解压失败: {e}")
            return b""
    else:
        return body if body else b""
    
def calculate_hash(content):
# """计算内容的哈希值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def filter_scholar_response(response, filter_words, request_url=None):
    """专门处理Google学术搜索结果"""
    if not response:
        return None

    try:
        soup = BeautifulSoup(response, 'html.parser')
        pattern = re.compile('|'.join(filter_words), flags=re.IGNORECASE)
        total_removed = 0

        # 处理每个学术页面配置
        for config in SCHOLAR_PAGE_CONFIGS:
            containers = soup.select(config['container'])

            for container in containers:
                # 检查是否在保留规则中
                preserved_elements = []
                for preserve_rule in config['preserve_rules']:
                    preserved_elements.extend(container.select(preserve_rule))

                # 检查是否匹配删除规则
                for remove_rule in config['remove_rules']:
                    for element in container.select(remove_rule):
                        if element in preserved_elements:
                            continue

                        # 关键词检查
                        text_content = element.get_text()
                        if pattern.search(text_content):
                            log_to_mongo({
                                "type": "scholar_page_filter",
                                "action": "removed_element",
                                "element_info": {
                                    'tag': element.name,
                                    'classes': element.get('class', []),
                                    'id': element.get('id'),
                                    'rule': remove_rule,
                                    'container': config['container']
                                },
                                "filter_words": filter_words,
                                "container_config": config
                            }, request_url)

                            element.decompose()
                            total_removed += 1

        if total_removed > 0:
            print(f"已删除 {total_removed} 个学术搜索结果")
            return str(soup).encode('utf-8')
        return response.encode('utf-8') if isinstance(response, str) else response
    except Exception as e:
        print(f"学术结果处理失败: {str(e)}")
        return response.encode('utf-8') if isinstance(response, str) else response