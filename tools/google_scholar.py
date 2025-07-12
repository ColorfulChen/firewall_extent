import json
import re
import brotli
import gzip
import io
from bs4 import BeautifulSoup
import hashlib

TARGET_CONTAINERS=[
    {#过滤普通条目
        'container':'div#gs_res_ccl_mid',
        'remove_rules':['div.gs_r.gs_or.gs_scl'],
        'preserve_rules':[]
    },
    {#过滤相关搜索mid
        'container':'div.gs_qsuggest_wrap.gs_r',
        'remove_rules':['div.gs_qsuggest.gs_qsuggest_regular ul li'],
        'preserve_rules':[]
    },
    {#过滤相关搜索bottom
        'container':'div.gs_qsuggest_wrap',
        'remove_rules':['div.gs_qsuggest.gs_qsuggest_regular.gs_qsuggest_bottom ul li'],
        'preserve_rules':[]
    }
]

def google_scholar_search_filter(response,filter_words):
    """
    过滤谷歌学术联想词的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    filtered = []
    for item in data['l']:
        if not any(re.search(word, item) for word in filter_words):
            filtered.append(item)
        else:
            print(f"Filtered out: {item}")
    data['l'] = filtered    #替换过滤后的内容
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body

def google_scholar_search_page_filter(response, filter_words):
    """
    多目标深度删除
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in TARGET_CONTAINERS:
        container_selector = container_config['container']
        containers = soup.select(container_selector)

        if not containers:
            print(f"未找到容器: {container_selector}")
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

                        # 删除元素
                        element.decompose()
                        container_removed += 1
                        total_removed += 1

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