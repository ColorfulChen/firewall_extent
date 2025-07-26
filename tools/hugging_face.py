import json
import re
import brotli
import gzip
import io
from bs4 import BeautifulSoup
import hashlib

CARD_TARGET_CONTAINERS=[
    {#过滤models card
        'container':'div.container.relative.flex.flex-col.md\\:grid.md\\:space-y-0.w-full.md\\:grid-cols-12.md\\:flex-1.md\\:grid-rows-full.space-y-4.md\\:gap-6',
        'remove_rules':['section.pt-8.border-gray-100.md\\:col-span-7.pb-24.relative.break-words.copiable-code-container',
                        'section.pt-8.border-gray-100.md\\:col-span-5.pt-6.md\\:pb-24.md\\:pl-6.md\\:border-l.order-first.md\\:order-none > div.relative.md\\:mt-2 > div.model-card-content.prose.md\\:px-6.md\\:-mx-6.lg\\:-mr-20.lg\\:pr-20.xl\\:-mr-24.xl\\:pr-24.\\32 xl\\:-mr-36.\\32 xl\\:pr-36.hf-sanitized.hf-sanitized-q_6B_bVJaRj-SwIZrPR70'],
        'preserve_rules':[]
    },
    {#过滤datasets card
        'container':'div.container.relative.flex.flex-col.md\\:space-y-0.w-full.md\\:grid-cols-12.md\\:flex-1.md\\:grid-rows-full.space-y-4.md\\:gap-6',
        'remove_rules':['section.pt-6.border-gray-100.md\\:col-span-8.pb-24.relative.break-words.copiable-code-container > div.SVELTE_HYDRATER.contents > div.flex.flex-col.overflow-hidden.shadow-xs.mx-auto.mb-10.rounded-lg.border.pt-2.px-2\\.5',
                        'section.pt-6.border-gray-10.md\\:pb-24.md\\:pl-6.md\\:w-64.lg\\:w-80.xl\\:w-96.flex-none.order-first.md\\:order-none.md\\:border-l.pt-3\\!.md\\:pt-6\\!'], #body > div > main > div.container.relative.flex.flex-col.md\:grid.md\:space-y-0.w-full.md\:grid-cols-12.md\:flex-1.md\:grid-rows-full.space-y-4.md\:gap-6 > section.pt-6.border-gray-100.md\:pb-24.md\:pl-6.md\:w-64.lg\:w-80.xl\:w-96.flex-none.order-first.md\:order-none.md\:border-l.pt-3\!.md\:pt-6\!
        'preserve_rules':[]
    }
]

MODELS_TRENDING_TARGET_CONTAINERS=[
    {
        'container':'section.pt-8.border-gray-100.col-span-full.lg\\:col-span-6.xl\\:col-span-7.pb-12 > div.relative',
        'remove_rules':['div > article'], #body > div > main > div > div > section.pt-8.border-gray-100.col-span-full.lg\:col-span-6.xl\:col-span-7.pb-12 > div.relative > div > article:nth-child(1)
        'preserve_rules':[]
    }
]
DATASETS_TRENDING_TARGET_CONTAINERS=[
    {
        'container':'div.relative',
        'remove_rules':['div.grid.grid-cols-1.gap-5.xl\\:grid-cols-2 > article'],
        'preserve_rules':[]
    }
]
SPACES_TRENDING_TARGET_CONTAINERS=[
    {
        'container':'div.container.pt-4.sm\\:pt-6.lg\\:pt-7',
        'remove_rules':['div.grid.grid-cols-1.gap-x-4.gap-y-5.md\\:grid-cols-3.xl\\:grid-cols-4 > article',
                        'div.pb-12 > div.grid.grid-cols-1.gap-x-4.gap-y-5.md\\:grid-cols-3.xl\\:grid-cols-4 > article'],
        'preserve_rules':[]
    }
]
COLLECTIONS_TRENDING_TARGET_CONTAINERS=[
    {
        'container':'body > div > main > div > div > div.mt-12.flex.flex-col.gap-8 > div.\\@container > div.\\@max-xl\\:hidden.grid.grid-cols-2.gap-6',#body > div > main > div > div > div.mt-12.flex.flex-col.gap-8 > div.\@container > div.\@max-xl\:hidden.grid.grid-cols-2.gap-6 > div:nth-child(1) > article:nth-child(1)
        'remove_rules':['article > ul.flex.max-h-56.flex-col.gap-y-1\\.5.overflow-hidden.px-3\\.5.pb-2\\.5 > li'],
        'preserve_rules':[]
    }
]
BLOGS_TARGET_CONTAINERS=[
    {#过滤blog首页
        'container':'body > div > main > div',
        'remove_rules':['div.col-span-1.lg\\:col-span-7.lg\\:pr-12 > div.pb-6.pt-12 > div',
                        'div.col-span-1.lg\\:col-span-7.lg\\:pr-12 > div.grid.grid-cols-1.gap-12.pt-8.lg\\:grid-cols-2 > div',
                        'div.col-span-1.lg\\:col-span-7.lg\\:pr-12 > div.bg-linear-to-br.from-yellow-100\\/40.dark\\:border-yellow-500\\/5.dark\\:from-yellow-500\\/10.mb-2.mt-8.space-y-4.rounded-3xl.border.border-yellow-100.to-10\\%.p-4.lg\\:hidden > div.SVELTE_HYDRATER.contents > div > div.scrollbar-hidden.flex.w-full.snap-x.justify-start.gap-x-2.overflow-auto > div',
                        'div.hidden.lg\\:col-span-3.lg\\:block > div > div > div.mt-4.flex.flex-col.gap-y-6 > article'],
        'preserve_rules':[]
    },
    {#过滤具体的blog内容页面
        'container':'div.max-w-full.pb-16.pt-6.lg\\:max-w-3xl.lg\\:flex-1.lg\\:pt-16.\\32 xl\\:max-w-4xl',
        'remove_rules':['div.max-lg\\:overflow-hidden > div > h1', #title含违禁词则整个页面都过滤掉，正文中仅将含有违禁词的段落过滤掉body > div > main > div > div.max-w-full.pb-16.pt-6.lg\:max-w-3xl.lg\:flex-1.lg\:pt-16.\32 xl\:max-w-4xl > div.max-lg\:overflow-hidden > div > h1
                        'div.max-lg\\:overflow-hidden > div > *'],
        'preserve_rules':[]
    }
]
BLOGS_COMMUNITY_TARGET_CONTAINERS=[
    {
        'container':'body > div > main > div > div',
        'remove_rules':['div.mt-4.flex.flex-col.gap-y-6 > article'],
        'preserve_rules':[]
    }
]
POSTS_TARGET_CONTAINERS=[
    {
        'container':'body > div > main > div > div',
        'remove_rules':['div.overflow-hidden.py-8.lg\\:flex-1.lg\\:pb-14 > div > div.mt-7.flex.flex-col.gap-10 > div',
                        'div.from-gray-50-to-white.lg\\:bg-linear-to-r.flex-none.border-gray-100.py-8.lg\\:w-80.lg\\:border-l.lg\\:pb-14.lg\\:pl-4 > ul > li'],
        'preserve_rules':[]
    }
]
DISCUSS_TOPICS_TARGET_CONTAINERS=[
    {
        'container':'div#main-outlet > div.topic-list-container > table.topic-list',
        'remove_rules':['tbody > tr.topic-list-item'],
        'preserve_rules':[]
    }
]
DISCUSS_POSTS_TARGET_CONTAINERS=[
    {#过滤posts
        'container':'div#main-outlet',
        'remove_rules':['div > div.topic-body.crawler-post'],
        'preserve_rules':[]
    },
    {#过滤底部related topics
        'container':'div#related-topics > div.topic-list-container > table.topic-list',
        'remove_rules':['tbody > tr.topic-list-item'],
        'preserve_rules':[]
    }
]
INDEX_PAGE_TARGET_CONTAINERS=[
    {
        'container':'div.relative.grid.grid-cols-1.gap-6.lg\\:grid-cols-3',
        'remove_rules':['div.relative.col-span-1.flex.flex-col.items-stretch.text-center > div > article'],
        'preserve_rules':[]
    }
]
ORGANIZATIONS_PAGE_TARGET_CONTAINERS=[
    {#index : models/datasets
        'container':'div.container.relative.flex.flex-col.md\\:grid.md\\:space-y-0.w-full.md\\:grid-cols-10.space-y-4.md\\:gap-6',
        'remove_rules':['section.pt-8.border-gray-100.md\\:col-span-6.lg\\:col-span-7.max-md\\:pt-0\\! > div > div#models > div > div.grid.grid-cols-1.gap-5.xl\:grid-cols-2 > article',
                        'section.pt-8.border-gray-100.md\\:col-span-6.lg\\:col-span-7.max-md\\:pt-0\\! > div > div#datasets > div > div.grid.grid-cols-1.gap-5.xl\:grid-cols-2 > article',
                        'section.pt-8.border-gray-100.md\\:col-span-6.lg\\:col-span-7.max-md\\:pt-0\\! > div > div#spaces > div > div > article'], ##models > div > div.grid.grid-cols-1.gap-5.xl\:grid-cols-2 > article:nth-child(1)
        'preserve_rules':[]
    },
    {#view all : models/datasets/spaces/collections
        'container':'body > div > main > div > div',
        'remove_rules':['section.pt-8.border-gray-100.md\\:col-span-6.lg\\:col-span-7.max-md\\:pt-0\\! > div > div > div > article',
                        'section.pt-8.border-gray-100.md\\:col-span-6.lg\\:col-span-7.max-md\\:pt-0\\! > div > div > div > div.\\@xl\\:hidden.flex.flex-col.gap-6 > article'],
        'preserve_rules':[]
    }
]
FULLTEXT_SEARCH_TARGET_CONTAINERS=[
    {
        'container':'body > div > main > div > div',
        'remove_rules':['div.overflow-hidden.py-2.lg\\:flex-1.lg\\:px-8.lg\\:py-8.lg\\:pb-14 > div.mt-4.flex.flex-col.gap-5 > div'],
        'preserve_rules':[]
    }
]

#1.过滤huggingface搜索框推荐条目的函数
def hugging_face_quick_search_filter(response,filter_words):
    """
    过滤huggingface搜索框推荐条目的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    #过滤datasets
    try:
        filtered_datasets = []
        for item in data['datasets']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_datasets.append(item)
            else:
                print(f"[datasets]Filtered out: {item['id']}")
        data['datasets'] = filtered_datasets    #替换过滤后的内容-datasets
    except KeyError as e:
        pass
    #过滤models
    try:
        filtered_models=[]
        for item in data['models']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_models.append(item)
            else:
                print(f"[models]Filtered out: {item['id']}")
        data['models']=filtered_models          #替换过滤后的内容-models
    except KeyError as e:
        pass
    #过滤orgs
    try:
        filtered_orgs=[]
        for item in data['orgs']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['name']) for word in filter_words):
                filtered_orgs.append(item)
            else:
                print(f"[orgs]Filtered out: {item['name']}")
        data['orgs']=filtered_orgs              #替换过滤后的内容-orgs
    except KeyError as e:
        pass
    #过滤spaces
    try:
        filtered_spaces=[]
        for item in data['spaces']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_spaces.append(item)
            else:
                print(f"[spaces]Filtered out: {item['id']}")
        data['spaces']=filtered_spaces          #替换过滤后的内容-spaces
    except KeyError as e:
        pass
    #过滤users
    try:
        filtered_users=[]
        for item in data['users']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['user']) for word in filter_words):
                filtered_users.append(item)
            else:
                print(f"[models]Filtered out: {item['user']}")
        data['users']=filtered_users            #替换过滤后的内容-users
    except KeyError as e:
        pass

    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body

def hugging_face_fulltext_search_json_filter(response,filter_words):
    """
    过滤huggingface full-text搜索框json结果条目的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    try:
        filtered_models = []
        for item in data['hits']:
            if (not any(re.search(re.compile(word,re.IGNORECASE), item['name']) for word in filter_words)) and (not any(re.search(re.compile(word,re.IGNORECASE), item['tags']) for word in filter_words)):
                #print(f"[full-text-json]not Filtered out: (name){item['name']} (tags){item['tags']}")
                filtered_models.append(item)
            else:
                print(f"[full-text-json]Filtered out: (name){item['name']} (tags){item['tags']}")
        data['hits'] = filtered_models
    except KeyError as e:
        print("keyerror:",e)
    
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body

def hugging_face_fulltext_search_page_filter(response, filter_words):
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in FULLTEXT_SEARCH_TARGET_CONTAINERS:
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

    init_info_fulltext=json.loads(soup.select("main > div")[0].attrs['data-props'])
    final_init_info_fulltext=json.dumps(hugging_face_fulltext_init_page_filter(init_info_fulltext,filter_words))
    soup.select("main > div")[0].attrs['data-props']=final_init_info_fulltext

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_fulltext_init_page_filter(init_info,filter_words):
    try:
        filtered_fulltext = []
        for item in init_info['docs']:
            if not any(re.search(re.compile(word,re.IGNORECASE), json.dumps(item)) for word in filter_words):
                filtered_fulltext.append(item)
            else:
                print(f"[fulltext-search-init-page]Filtered out: {item}")
        init_info['docs'] = filtered_fulltext
    except KeyError as e:
        print("keyerror:",e)
    
    return init_info

#2. models过滤
    #model-json过滤
def hugging_face_models_search_json_filter(response,filter_words):
    """
    过滤huggingface models搜索框json结果条目的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    try:
        filtered_models = []
        for item in data['models']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_models.append(item)
            else:
                print(f"[models-json]Filtered out: {item['id']}")
        data['models'] = filtered_models
    except KeyError as e:
        pass
    
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body
   
    #model首页元素过滤
def hugging_face_models_search_page_filter(response, filter_words):
    """
    过滤huggingface models首页trending部分的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in MODELS_TRENDING_TARGET_CONTAINERS:
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
                        #container.decompose()
                        #break
    #过滤首页models初始数据
    init_info_model=json.loads(soup.select("main > div")[0].attrs['data-props'])
    #print(init_info_model)
    final_init_info_model=json.dumps(hugging_face_models_init_page_filter(init_info_model,filter_words))#, ensure_ascii=False).encode("utf-8") #json转换为字符串
    soup.select("main > div")[0].attrs['data-props']=final_init_info_model
    
    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_models_init_page_filter(init_info,filter_words):
    try:
        filtered_models = []
        for item in init_info['initialValues']['models']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_models.append(item)
            else:
                print(f"[models-init-page]Filtered out: {item['id']}")
        init_info['initialValues']['models'] = filtered_models
    except KeyError as e:
        pass
    
    return init_info

    #models\datasets card过滤
def hugging_face_card_page_filter(response, filter_words):
    """
    过滤huggingface models\datasets card的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    error_soup=BeautifulSoup("<h1>Warning!!!: include filter words</h1>", 'html.parser')
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in CARD_TARGET_CONTAINERS:
        container_selector = container_config['container']
        containers = soup.select(container_selector)

        if not containers:
            print(f"未找到容器: {container_selector}")
            continue

        # print(f"\n处理容器: {container_selector}")
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
                        print(f"删除页面 [规则: {remove_rule}]")
                        print(f"标签: {element_info['tag']}")
                        print(f"类: {element_info['classes']}")
                        print(f"内容: {str(element)}")
                        print("-" * 40)

                        # 替换整个页面
                        soup=error_soup
                        break

    modified_html = str(soup)
    return modified_html.encode('utf-8')



#3. datasets过滤
    #datasets-json过滤
def hugging_face_datasets_search_json_filter(response,filter_words):
    """
    过滤huggingface datasets搜索框json结果条目的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    try:
        filtered_models = []
        for item in data['datasets']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_models.append(item)
            else:
                print(f"[datasets-json]Filtered out: {item['id']}")
        data['datasets'] = filtered_models
    except KeyError as e:
        pass
    
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body
    #datasets-首页元素过滤
def hugging_face_datasets_search_page_filter(response, filter_words):
    """
    过滤huggingface datasets首页trending部分的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in DATASETS_TRENDING_TARGET_CONTAINERS:
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
    #过滤首页datasets初始数据
    init_info_dataset=json.loads(soup.select("main > div")[0].attrs['data-props'])
    #print(init_info_dataset)
    final_init_info_dataset=json.dumps(hugging_face_datasets_init_page_filter(init_info_dataset,filter_words))#, ensure_ascii=False).encode("utf-8") #json转换为字符串
    soup.select("main > div")[0].attrs['data-props']=final_init_info_dataset

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_datasets_init_page_filter(init_info,filter_words):
    try:
        filtered_datasets = []
        for item in init_info['initialValues']['datasets']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_datasets.append(item)
            else:
                print(f"[datasets-init-page]Filtered out: {item['id']}")
        init_info['initialValues']['datasets'] = filtered_datasets
    except KeyError as e:
        pass
    
    return init_info

#4. spaces过滤
    #spaces-json过滤
def hugging_face_spaces_search_json_filter(response,filter_words):
    """
    过滤huggingface spaces搜索框json结果条目的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    try:
        filtered_spaces = []
        for item in data['spaces']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['title']) for word in filter_words):
                filtered_spaces.append(item)
            else:
                print(f"[spaces-json]Filtered out: {item['title']}")
        data['spaces'] = filtered_spaces
    except KeyError as e:
        pass
    
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body
    #spaces-首页元素过滤
def hugging_face_spaces_search_page_filter(response, filter_words):
    """
    过滤huggingface spaces首页trending部分的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in SPACES_TRENDING_TARGET_CONTAINERS:
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
    #过滤首页spaces初始数据
    init_info_space=json.loads(soup.select("main > div.SVELTE_HYDRATER.contents")[0].attrs['data-props'])
    #print(init_info_space)
    final_init_info_space=json.dumps(hugging_face_spaces_init_page_filter(init_info_space,filter_words))#, ensure_ascii=False).encode("utf-8") #json转换为字符串
    soup.select("main > div.SVELTE_HYDRATER.contents")[0].attrs['data-props']=final_init_info_space

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_spaces_init_page_filter(init_info,filter_words):
    try:
        filtered_spaces = []
        for item in init_info['initialValues']['spaces']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['title']) for word in filter_words):
                filtered_spaces.append(item)
            else:
                print(f"[spaces-init-page]Filtered out: {item['title']}")
        init_info['initialValues']['spaces'] = filtered_spaces
    except KeyError as e:
        pass
    
    return init_info

# 5. collections过滤
    #collections-json过滤
def hugging_face_collections_search_json_filter(response,filter_words):
    """
    过滤huggingface collections搜索框json结果条目的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    datas = json.loads(decompressed) #字符串转换为json
    try:
        for index,data in enumerate(datas['collections'],start=0):
            filtered_collections = []
            for item in data['items']:
                if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                    filtered_collections.append(item)
                else:
                    print(f"[collections-json]Filtered out: {item['id']}")
            datas['collections'][index]['items'] = filtered_collections
    except Exception as e:
        print("Error:",e)
    
    new_json = json.dumps(datas, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body
    #collections-首页元素过滤
def hugging_face_collections_search_page_filter(response, filter_words):
    """
    过滤huggingface collections首页trending部分的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in COLLECTIONS_TRENDING_TARGET_CONTAINERS:
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
    #过滤首页collections初始数据
    init_info_collection=json.loads(soup.select("main > div.SVELTE_HYDRATER.contents")[0].attrs['data-props'])
    #print(init_info_collection)
    final_init_info_collection=json.dumps(hugging_face_collections_init_page_filter(init_info_collection,filter_words))#, ensure_ascii=False).encode("utf-8") #json转换为字符串
    soup.select("main > div.SVELTE_HYDRATER.contents")[0].attrs['data-props']=final_init_info_collection

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_collections_init_page_filter(init_info,filter_words):
    try:
        for index,data in enumerate(init_info['collections'],start=0):
            filtered_collections = []
            for item in data['items']:
                if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                    filtered_collections.append(item)
                else:
                    print(f"[collections-init-page]Filtered out: {item['id']}")
            init_info['collections'][index]['items'] = filtered_collections
    except Exception as e:
        print("Error:",e)
    
    return init_info

# 6. blogs过滤
    #blogs展开侧边栏community页面过滤
def hugging_face_blogs_community_page_filter(response, filter_words):
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in BLOGS_COMMUNITY_TARGET_CONTAINERS:
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

    #过滤侧边栏blogs community展开页面初始数据
    init_info_blog_community=json.loads(soup.select("main > div.SVELTE_HYDRATER.contents")[0].attrs['data-props'])
    #print(init_info_blog_community)
    final_init_info_blog_community=json.dumps(hugging_face_blogs_community_init_page_filter(init_info_blog_community,filter_words))#, ensure_ascii=False).encode("utf-8") #json转换为字符串
    soup.select("main > div.SVELTE_HYDRATER.contents")[0].attrs['data-props']=final_init_info_blog_community

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_blogs_community_init_page_filter(init_info,filter_words):
    try:
        filtered_blogs_community = []
        for item in init_info['posts']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['title']) for word in filter_words):
                filtered_blogs_community.append(item)
            else:
                print(f"[blogs-community-init-page]Filtered out: {item['title']}")
        init_info['posts'] = filtered_blogs_community
    except KeyError as e:
        pass
    
    return init_info

    #blogs-首页元素过滤
def hugging_face_blogs_search_page_filter(response, filter_words):
    """
    过滤huggingface blogs首页trending部分的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    error_soup=BeautifulSoup("<h1>Warning!!!: Blog includes filter words</h1>", 'html.parser')
    soup_sign=0
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for num,container_config in enumerate(BLOGS_TARGET_CONTAINERS,start=0):
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
            for index,remove_rule in enumerate(container_config['remove_rules'],start=0):
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
                        if num==1 and index == 0:   #blog页面标题含有违禁词，直接返回错误页面
                            soup_sign=1
                            break
                        # 删除元素
                        element.decompose()
                        container_removed += 1
                        total_removed += 1
    if soup_sign==1:
        modified_html = str(error_soup)
        return modified_html.encode('utf-8')
    try:
        #过滤首页blogs初始数据
        init_info_blog=json.loads(soup.select("div.bg-linear-to-br.from-yellow-100\\/40.dark\\:border-yellow-500\\/5.dark\\:from-yellow-500\\/10.mb-2.mt-8.space-y-4.rounded-3xl.border.border-yellow-100.to-10\\%.p-4.lg\\:hidden > div.SVELTE_HYDRATER.contents")[0].attrs['data-props'])
        #print(init_info_blog)
        final_init_info_blog=json.dumps(hugging_face_blogs_init_page_filter(init_info_blog,filter_words))#, ensure_ascii=False).encode("utf-8") #json转换为字符串
        soup.select("div.bg-linear-to-br.from-yellow-100\\/40.dark\\:border-yellow-500\\/5.dark\\:from-yellow-500\\/10.mb-2.mt-8.space-y-4.rounded-3xl.border.border-yellow-100.to-10\\%.p-4.lg\\:hidden > div.SVELTE_HYDRATER.contents")[0].attrs['data-props']=final_init_info_blog
        #过滤首页blogs-2初始数据
        init_info_blog=json.loads(soup.select("div.hidden.lg\\:col-span-3.lg\\:block > div.SVELTE_HYDRATER.contents")[0].attrs['data-props'])
        #print(init_info_blog)
        final_init_info_blog=json.dumps(hugging_face_blogs_init_page_filter(init_info_blog,filter_words))#, ensure_ascii=False).encode("utf-8") #json转换为字符串
        soup.select("div.hidden.lg\\:col-span-3.lg\\:block > div.SVELTE_HYDRATER.contents")[0].attrs['data-props']=final_init_info_blog
    except Exception as e:
        print("Error:",e)
    
    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_blogs_init_page_filter(init_info,filter_words):
    try:
        filtered_blogs = []
        for item in init_info['posts']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['title']) for word in filter_words):
                filtered_blogs.append(item)
            else:
                print(f"[blogs-init-page]Filtered out: {item['title']}")
        init_info['posts'] = filtered_blogs
    except KeyError as e:
        pass
    
    return init_info

# 7. posts过滤
    #过滤post-json
def hugging_face_posts_search_json_filter(response, filter_words):
    """
    过滤huggingface posts learn more json结果条目的函数
    :param response: 响应对象
    :param filter_words: 需要过滤的词列表
    """
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    try:
        filtered_posts = []
        for item in data['socialPosts']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['rawContent']) for word in filter_words):
                filtered_posts.append(item)
            else:
                print(f"[posts-json]Filtered out: {item['rawContent']}")
            data['socialPosts'] = filtered_posts
    except KeyError as e:
        pass
    
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body
    #过滤post首页
def hugging_face_posts_search_page_filter(response, filter_words):
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in POSTS_TARGET_CONTAINERS:
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

    #过滤首页posts初始数据
    init_info_post=json.loads(soup.select("main > div")[0].attrs['data-props'])
    #print(init_info_post)
    final_init_info_post=json.dumps(hugging_face_posts_init_page_filter(init_info_post,filter_words))
    soup.select("main > div")[0].attrs['data-props']=final_init_info_post

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_posts_init_page_filter(init_info,filter_words):
    try:
        filtered_posts = []
        for item in init_info['socialPosts']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['rawContent']) for word in filter_words):
                filtered_posts.append(item)
            else:
                print(f"[posts-init-page]Filtered out: {item['rawContent']}")
        init_info['socialPosts'] = filtered_posts
    except KeyError as e:
        pass
    
    return init_info

#论坛页面过滤
    #过滤首页帖子
def hugging_face_discuss_topics_search_json_filter(response, filter_words):
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    try:
        filtered_topics = []
        for item in data['topic_list']['topics']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['title']) for word in filter_words):
                filtered_topics.append(item)
            else:
                print(f"[topics-json]Filtered out: {item['title']}")
            data['topic_list']['topics'] = filtered_topics
    except KeyError as e:
        pass
    
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body

def hugging_face_discuss_topics_search_page_filter(response, filter_words):
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in DISCUSS_TOPICS_TARGET_CONTAINERS:
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
    #过滤帖子中的posts
def hugging_face_discuss_posts_json_filter(response, filter_words):
    decompressed = response
    data = json.loads(decompressed) #字符串转换为json
    #过滤posts-json
    try:
        filtered_posts = []
        for item in data['post_stream']['posts']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['cooked']) for word in filter_words):
                filtered_posts.append(item)
            else:
                print(f"[discuss-posts-json]Filtered out: {item['cooked']}")
            data['post_stream']['posts'] = filtered_posts
    except KeyError as e:
        pass
    #过滤related topics
    try:
        filtered_related_topics = []
        for item in data['related_topics']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['title']) for word in filter_words):
                filtered_related_topics.append(item)
            else:
                print(f"[discuss-related-topics-json]Filtered out: {item['title']}")
            data['related_topics'] = filtered_related_topics
    except KeyError as e:
        pass
    
    new_json = json.dumps(data, ensure_ascii=False).encode("utf-8") #json转换为字符串
    new_body = new_json
    return new_body

def hugging_face_discuss_posts_page_filter(response, filter_words):
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in DISCUSS_POSTS_TARGET_CONTAINERS:
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

#过滤huggingface.co首页
def hugging_face_index_page_filter(response, filter_words):
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in INDEX_PAGE_TARGET_CONTAINERS:
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

#过滤组织页面中的models、datasets、...
def hugging_face_organizations_page_filter(response, filter_words):
    soup = BeautifulSoup(response, 'html.parser')   #将字符串形式的html转换为BeautifulSoup对象
    total_removed = 0

    # 创建关键词正则表达式
    pattern = re.compile('|'.join(filter_words), re.IGNORECASE)

    # 处理每个目标容器
    for container_config in ORGANIZATIONS_PAGE_TARGET_CONTAINERS:
        container_selector = container_config['container']
        containers = soup.select(container_selector)

        if not containers:
            print(f"未找到容器: {container_selector}")
            continue

        # print(f"\n处理容器: {container_selector}")
        container_removed = 0

        for container in containers:
            # 先标记要保留的元素
            preserved_elements =[]
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
    
    init_info_organization=json.loads(soup.select("main > div")[0].attrs['data-props'])
    final_init_info_organization=json.dumps(hugging_face_organizations_init_page_filter(init_info_organization,filter_words))
    soup.select("main > div")[0].attrs['data-props']=final_init_info_organization

    modified_html = str(soup)
    return modified_html.encode('utf-8')

def hugging_face_organizations_init_page_filter(init_info,filter_words):
    try:
        filtered_models = []
        for item in init_info['models']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_models.append(item)
            else:
                print(f"[org-init-page-models]Filtered out: {item['id']}")
        init_info['models'] = filtered_models
    except KeyError as e:
        print("keyerror:",e)
    try:
        filtered_datasets = []
        for item in init_info['datasets']:
            if not any(re.search(re.compile(word,re.IGNORECASE), json.dumps(item)) for word in filter_words):
                filtered_datasets.append(item)
            else:
                print(f"[org-init-page-datasets]Filtered out: {item}")
        init_info['datasets'] = filtered_datasets
    except KeyError as e:
        print("keyerror:",e)
    try:
        filtered_collections = []
        for item in init_info['collections']:
            if not any(re.search(re.compile(word,re.IGNORECASE), json.dumps(item)) for word in filter_words):
                filtered_collections.append(item)
            else:
                print(f"[org-init-page-collections]Filtered out: {item}")
        init_info['collections'] = filtered_collections
    except KeyError as e:
        print("keyerror:",e)
    try:
        filtered_spaces = []
        for item in init_info['spaces']:
            if not any(re.search(re.compile(word,re.IGNORECASE), json.dumps(item)) for word in filter_words):
                filtered_spaces.append(item)
            else:
                print(f"[org-init-page-spaces]Filtered out: {item}")
        init_info['spaces'] = filtered_spaces
    except KeyError as e:
        print("keyerror:",e)
    try:
        filtered_repos = []
        for item in init_info['repos']:
            if not any(re.search(re.compile(word,re.IGNORECASE), item['id']) for word in filter_words):
                filtered_repos.append(item)
            else:
                print(f"[org-init-page-repos]Filtered out: {item['id']}")
        init_info['repos'] = filtered_repos
    except KeyError as e:
        print("keyerror:",e)

    return init_info
