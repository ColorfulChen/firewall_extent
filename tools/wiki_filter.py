import json
import re
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup,Tag

from tools.mongodb import log_to_mongo


WIKI_PAGE_CONTAINERS = [
    # 搜索页结果
    {
        # 容器选择器
        'container': 'div.mw-search-results-container > ul',
        # 要删除的元素选择器列表
        'remove_rules': [
            'li.mw-search-result',
            'li.mw-search-result-ns-0',
        ],
        'preserve_rules': []
    },
    {
        'container': 'div#mw-interwiki-results > ul',
        'remove_rules': [
            'li.iw-resultset',
        ],
        'preserve_rules': []
    },
    # wiki首页
    {
        'container': 'div#mp-2012-column-left > div',
        'remove_rules': [
            'div#mp-2012-column-feature-block',
            'div#mp-2012-column-dyk-block',
            'div#mp-2012-column-good-block',
            'div#mp-2012-column-featurepic-block'
        ],
        'preserve_rules': []

    },
    {
        'container': 'div#mp-2012-column-right-block-a',
        'remove_rules': [
            'div#mp-2012-column-itn-block',
            'div#mp-2012-column-otd-block',
            'div#mp-2012-column-uptrends-block',
        ],
        'preserve_rules': []

    },
    {
        'container': 'div#mp-2012-column-right > div',
        'remove_rules': [
            'div#mp-2012-column-right-block-b',
            'div#mp-2012-column-right-block-c'
        ],
        'preserve_rules': []

    },
{
        'container': 'div#mw-content-text > div',
        'remove_rules': [
            'p',
        ],
        'preserve_rules': []

    },

]

#定义Wiki内容页特定的容器配置
WIKI_CONTENT_CONFIG = [
    {
        'container': 'div.mw-content-ltr.mw-parser-output',  # 容器选择器
        'block_start': 'div.mw-heading',  # 块起始选择器
        'block_processing': True
    },
]

WIKI_CONTENT = [
    {
        'container': 'ul',
        'remove_rules': [
            'li',
        ],
        'preserve_rules': []

    },
    {
        'container': 'ol.references',
        'remove_rules': [
            'li',
        ],
        'preserve_rules': []

    },
    {
        'container': 'div.mw-content-ltr',
        'remove_rules': [
            'p',
            'table.infobox.vevent'
        ],
        'preserve_rules': []

    },


]



def wiki_search_filter(response, filter_words, request_url=None):
    """
    过滤Wiki首页搜索栏
    """
    json_data = response
    data = json.loads(json_data)
    if "pages" in data:
        filtered_pages = []
        for page in data["pages"]:
            should_filter = False
            # 检查标题、摘录或描述中是否出现任何过滤词
            for field in ["title", "excerpt", "description"]:
                if field in page and page[field]:
                    if any(re.search(word, page[field], re.IGNORECASE) for word in filter_words):
                        should_filter = True
                        break

            if not should_filter:
                filtered_pages.append(page)
            else:
                print(f"Filtered out: {page.get('title', 'No title')}")

                if request_url:
                    log_to_mongo({
                        "type": "wikipedia_search",
                        "action": "filtered",
                        "title": page.get("title"),
                        "filter_words": filter_words,
                        "original_data": page
                    }, request_url)

        data["pages"] = filtered_pages

    # 重建json结构
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8")
    print(new_json)
    new_body = new_json

    return new_body


def wiki_suggestions_filter(response, filter_words, request_url=None):
    """
    过滤Wiki搜索页搜索栏
    """
    # 解码响应数据
    if isinstance(response, bytes):
        json_data = response.decode('utf-8')
    else:
        json_data = response

    try:
        data = json.loads(json_data)
    except json.JSONDecodeError:
        print("Invalid JSON data")
        return response if isinstance(response, bytes) else response.encode('utf-8')

    # 验证数据结构 (Wiki搜索建议格式: [搜索词, [标题列表], [描述列表], [URL列表]])
    if not (isinstance(data, list) and len(data) >= 4
            and isinstance(data[1], list)
            and isinstance(data[3], list)):
        print("Unexpected data structure")
        return response if isinstance(response, bytes) else response.encode('utf-8')

    filtered_titles = []
    filtered_descriptions = []
    filtered_urls = []
    filtered_indices = []  # 记录被过滤的条目索引

    # 遍历所有建议项
    for idx, (title, desc, url) in enumerate(zip(data[1], data[2], data[3])):
        should_filter = False

        # 检查标题是否包含任何过滤词
        if any(re.search(re.escape(word), title, re.IGNORECASE) for word in filter_words):
            should_filter = True

        if should_filter:
            print(f"Filtered out: {title}")
            filtered_indices.append(idx)

            if request_url:
                log_to_mongo({
                    "type": "wikipedia_suggestions",
                    "action": "filtered",
                    "title": title,
                    "url": url,
                    "filter_words": filter_words,
                    "original_data": {
                        "title": title,
                        "description": desc,
                        "url": url
                    }
                }, request_url)
        else:
            filtered_titles.append(title)
            filtered_descriptions.append(desc)
            filtered_urls.append(url)

    # 重建数据结构
    filtered_data = [
        data[0],  # 原始搜索词
        filtered_titles,  # 过滤后的标题
        filtered_descriptions,  # 对应的描述
        filtered_urls  # 过滤后的URL
    ]

    # 转换为JSON并编码为bytes
    new_json = json.dumps(filtered_data, ensure_ascii=False)
    print(f"Filtered suggestions: {new_json}")
    new_body = new_json.encode('utf-8')

    return new_body


def wiki_search_page_filter(response, filter_words,request_url=None):
    """
    """
    if not response:
        return None
    try:
        soup = BeautifulSoup(response, 'html.parser')
        # 创建关键词正则表达式
        pattern = re.compile('|'.join(filter_words), re.IGNORECASE)
        total_removed = 0

        # 处理每个目标容器
        for config in WIKI_PAGE_CONTAINERS:
            container_selector = config['container']
            containers = soup.select(container_selector)

            if not containers:
                print(f"未找到容器: {config['container']}")
            else:
                print(f"\n处理容器: {config['container']}")

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
        print(f"结果处理失败: {str(e)}")
        return response.encode('utf-8') if isinstance(response, str) else response

def extract_wiki_title(url):
    """从维基百科URL中提取并解码标题"""
    # 匹配/wiki/后面的部分（直到遇到/、?、#或结尾）
    match = re.search(r'/wiki/([^/?#]+)', url)
    if match:
        return unquote(match.group(1))
    return None

#
def inject_content(response):
    print("注入拦截内容")
    # 预编译要注入的内容
    INJECTED_CONTENT = """
        <div style="padding: 20px; text-align: center;">
            <h3>没有找到相关内容</h3>
            <p>您请求的页面不存在或已被移除</p>
        </div>
        """.encode('utf-8')  # 预先编码

    # 如果不需要完整解析，可以使用更快的解析器
    soup = BeautifulSoup(response, 'lxml')  # lxml比html.parser更快

    # 使用更高效的查找方法
    target_div = soup.find('div', class_='mw-page-container-inner')

    if target_div:
        # 直接替换而不是先清空再添加
        target_div.replace_with(BeautifulSoup(INJECTED_CONTENT, 'lxml'))

    # 返回修改后的内容
    modified_html = str(soup)

    return modified_html.encode('utf-8')


def wiki_content_filter(response, filter_words, request_url=None):
    """
    处理普通条目页
    """
    print("普通条目页面过滤开始")
    if not response:
        return None
    try:
        soup = BeautifulSoup(response, 'html.parser')
        # 创建关键词正则表达式
        pattern = re.compile('|'.join(filter_words), re.IGNORECASE)
        total_removed = 0

        for config in WIKI_CONTENT_CONFIG:
            if config.get('block_processing', False):
                            soup, removed = process_html_blocks(
                                soup,
                                config['container'],
                                config['block_start'],
                                filter_words,
                                request_url
                            )
                            total_removed += removed
        print("块html处理结束")
        # 处理每个目标容器
        for config in WIKI_CONTENT:
            container_selector = config['container']
            containers = soup.select(container_selector)

            if not containers:
                print(f"未找到容器: {config['container']}")
            else:
                print(f"\n处理容器: {config['container']}")

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
            print(f"已删除 {total_removed} 个普通条目页面HTML块")
            return str(soup).encode('utf-8')
        return response.encode('utf-8') if isinstance(response, str) else response
    except Exception as e:
        print(f"普通条目页面过滤结果处理失败: {str(e)}")
        return response.encode('utf-8') if isinstance(response, str) else response


def process_html_blocks(soup, container_selector, block_start_selector, filter_words, request_url=None):
    try:
        # 初始化
        pattern = re.compile('|'.join(filter_words), re.IGNORECASE) if filter_words else None
        total_removed = 0

        # 安全文本获取
        def get_element_text(element):
            try:
                if element is None or not hasattr(element, 'get_text'):
                    return ''
                text = element.get_text()
                return text if text is not None else ''
            except:
                return ''

        # 安全元素处理
        containers = soup.select(container_selector) if container_selector else []

        for container in containers:
            block_starts = container.select(block_start_selector) if block_start_selector else []

            for i, start_element in enumerate(block_starts):
                try:
                    # 收集块元素
                    block_elements = []
                    if start_element:
                        block_elements.append(start_element)
                        next_sib = start_element.next_sibling
                        next_start = block_starts[i + 1] if i + 1 < len(block_starts) else None

                        while next_sib and next_sib != next_start:
                            if isinstance(next_sib, Tag):
                                block_elements.append(next_sib)
                            next_sib = next_sib.next_sibling

                    # 检查文本
                    combined_text = ''.join(get_element_text(el) for el in block_elements)
                    if pattern and pattern.search(combined_text):
                        for el in block_elements:
                            try:
                                el.decompose()
                            except:
                                pass
                        total_removed += 1

                except Exception as e:
                    print(f"处理块时出错: {str(e)}")
                    continue

        return soup, total_removed

    except Exception as e:
        print(f"处理HTML块时发生全局错误: {str(e)}")
        return soup, 0
