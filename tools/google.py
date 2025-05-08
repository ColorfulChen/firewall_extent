import json
import re
import brotli
import gzip
import io
from bs4 import BeautifulSoup
import hashlib

TARGET_CONTAINERS = [
    {
        # 容器选择器
        'container': 'div.s6JM6d.ufC5Cb',
        # 要删除的元素选择器列表
        'remove_rules': [
            'div.xfX4Ac.JI5uCe.qB9BY.yWNJXb.qzPQNd',
            'div.xfX4Ac.JI5uCe.qB9BY.yWNJXb.tQtKhb',
            'div.PmEWq.wHYlTd.vt6azd.Ww4FFb',
            'div.SoaBEf'
        ],
        'preserve_rules': []
    },
    {   # 过滤people also ask 下的内容
        'container': 'div.LQCGqc',
        'remove_rules': [
            'div[jsname="yEVEwb"]',
        ],
        'preserve_rules': []
    },
    { # 过滤全部页面下的video下的内容
        'container': 'div.Ea5p3b',
        'remove_rules': [
            'div.sHEJob',
        ],
        'preserve_rules': []
    },
    {  # 过滤people also search for 下的内容
        'container': 'div.AJLUJb',
        'remove_rules': [
            'div.b2Rnsc.vIifob',
        ],
        'preserve_rules': []
    },
    {
        'container': 'div.MjjYud ',
        'remove_rules': [
            'div.wHYlTd.Ww4FFb.vt6azd.tF2Cxc.asEBEc' # # 过滤 Forums 和web 页面下的内容
        ],
        'preserve_rules': []
    },
{   # 过滤侧边栏下的内容
        'container': 'div.MBdbL',
        'remove_rules': [
            'div.vNFaUb.uJyGcf',
        ],
        'preserve_rules': []
    },
    {  #过滤video页面
        'container': 'div.MjjYud > div ',
        'remove_rules': [
            'div.PmEWq.wHYlTd.vt6azd.Ww4FFb',
        ],
        'preserve_rules': []
    },
    {   #过滤book页面
        'container': 'div[data-hveid="CAMQAA"]',
        'remove_rules': [
            'div.Yr5TG',
        ],
        'preserve_rules': []
    }

]

VIDEO_PAGE_CONFIG = {
    'container': 'div.MjjYud > div',
    'remove_rules': [
        'div.PmEWq.wHYlTd.vt6azd.Ww4FFb',
    ],
    'preserve_rules': []
}

def google_search_filter(response,filter_words):
    """
    过滤谷歌联想词的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response.body
    prefix = b")]}'\n"
    if decompressed.startswith(prefix):
        json_bytes = decompressed[len(prefix):]
    else:
        json_bytes = decompressed
    data = json.loads(json_bytes)
    filtered = []
    for item in data[0]:
        text = item[0]
        if not any(re.search(word, text) for word in filter_words):
            filtered.append(item)
        else:
            print(f"Filtered out: {text}")
    data[0] = filtered
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8")
    new_body = prefix + new_json
    return new_body

def google_search_page_filter(response, filter_words):
    """
    多目标深度删除
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    try:
        html = response.body.decode('utf-8')
    except UnicodeDecodeError:
        html = response.body.decode('latin-1', errors='ignore')

    soup = BeautifulSoup(html, 'html.parser')
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
                        print(f"ID: {element_info['id']}")
                        print("-" * 40)

                        # 删除元素
                        element.decompose()
                        container_removed += 1
                        total_removed += 1

        # print(f"本容器删除元素数: {container_removed}")

    # print(f"\n总共删除 {total_removed} 个元素")

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def google_search_video_page_filter(response, filter_words):
    """
    多目标深度删除
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    try:
        html = response.body.decode('utf-8')
    except UnicodeDecodeError:
        html = response.body.decode('latin-1', errors='ignore')

    soup = BeautifulSoup(html, 'html.parser')
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
