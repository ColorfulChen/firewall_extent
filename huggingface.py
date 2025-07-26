import time
import random
import re
import os
from datetime import datetime
from tools.hugging_face import hugging_face_quick_search_filter,hugging_face_card_page_filter,hugging_face_models_search_json_filter,hugging_face_models_search_page_filter,hugging_face_datasets_search_json_filter,hugging_face_datasets_search_page_filter,hugging_face_spaces_search_json_filter,hugging_face_spaces_search_page_filter,hugging_face_collections_search_json_filter,hugging_face_collections_search_page_filter,hugging_face_blogs_search_page_filter,hugging_face_blogs_community_page_filter,hugging_face_posts_search_page_filter,hugging_face_posts_search_json_filter,hugging_face_discuss_topics_search_json_filter,hugging_face_discuss_topics_search_page_filter,hugging_face_discuss_posts_json_filter,hugging_face_discuss_posts_page_filter,hugging_face_index_page_filter,hugging_face_organizations_page_filter,hugging_face_fulltext_search_page_filter,hugging_face_fulltext_search_json_filter
from tools.web import setup_driver
import time
import argparse 

filter_words = ["airlines","news","Airlines","airline","习近平","六四","防火墙技术","chatgpt","gpt","kimi"]

def response_interceptor(request, response):
    # hugging face
    if 'huggingface.co' in request.url: 
        # 1. 过滤顶部快速搜索推荐条目
        if "huggingface.co/api/quicksearch" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_quick_search_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤quick搜索建议耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        # 过滤全文搜索结果页面
        elif "huggingface.co/search/full-text" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_fulltext_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤full-search页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass
        #过滤全文搜索结果json
        elif "huggingface.co/api/search/full-text" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_fulltext_search_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤full-search json耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
        # 2. 过滤models搜索结果条目、models首页trending元素
        elif "huggingface.co/models-json" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_models_search_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤models-json耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        elif "huggingface.co/models" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_models_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤models-page耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        # 3. 过滤datasets搜索结果条目
        elif "huggingface.co/datasets-json" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_datasets_search_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤datasets-json耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        elif "huggingface.co/datasets" in request.url and "datasets/" not in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_datasets_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤datasets-page耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        # 4. 过滤spaces搜索结果条目
        elif "huggingface.co/spaces-json" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_spaces_search_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤spaces-json耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        elif "huggingface.co/spaces" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_spaces_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤spaces-page耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        # 5. 过滤collentions搜索结果条目、collentions首页trending元素
        elif "huggingface.co/collections-json" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_collections_search_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤collections-json耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        elif "huggingface.co/collections" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_collections_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤collections-page耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理

        # 6. blogs过滤:展开侧边栏community页面和blogs首页
        elif "huggingface.co/blog/community" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_blogs_community_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤blog/community页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass

        elif "huggingface.co/blog" in request.url and "png" not in request.url and "jpg" not in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_blogs_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤blog页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass

        # 7. posts过滤
        elif "huggingface.co/api/posts" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_posts_search_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤posts-json耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass
        elif "huggingface.co/posts" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_posts_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤posts页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass

        # 8. 论坛页面过滤：首页帖子、帖子中的posts
        elif "discuss.huggingface.co/latest.json" in request.url or "discuss.huggingface.co/hot.json" in request.url or "discuss.huggingface.co/top.json" in request.url or "discuss.huggingface.co/categories_and_latest" in request.url or "discuss.huggingface.co/c/" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_discuss_topics_search_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤discuss-topic-json耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass
        elif "discuss.huggingface.co/t/" in request.url:
            try:
                start_time = time.time()
                print(request.url)
                if "json" in request.url:
                    response.body = hugging_face_discuss_posts_json_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                else:
                    response.body = hugging_face_discuss_posts_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤discuss-posts页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass
        elif "https://discuss.huggingface.co" in request.url and "text/html" in response.headers["Content-Type"]:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_discuss_topics_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤discuss首页耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass
        # 9. 过滤models\datasets card页面,含有违禁词则无法正常访问页面
        elif "https://huggingface.co/" in request.url and "text/html" in response.headers["Content-Type"] and re.search(re.compile(r'https://huggingface\.co/[^/]+/[^/]+',re.IGNORECASE),request.url) and "/models" not in request.url and "/datasets" not in request.url:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_card_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤model\dataset card页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass
        # 10. 过滤organizations页面的models、datasets、...条目
        elif "https://huggingface.co/" in request.url and "text/html" in response.headers["Content-Type"] and (re.search(re.compile(r'https://huggingface\.co/[^/]+',re.IGNORECASE),request.url) or (re.search(re.compile(r'https://huggingface\.co/[^/]+/[^/]+',re.IGNORECASE),request.url) and ("/models" in request.url or "/datasets" in request.url or "/spaces" in request.url or "/collections" in request.url))):
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_organizations_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤organization页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass

        # 11. 过滤huggingface.co首页
        elif "https://huggingface.co/" in request.url and "text/html" in response.headers["Content-Type"]:
            try:
                start_time = time.time()
                print(request.url)
                response.body = hugging_face_index_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤huggingface.co首页耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Hugging Face with optional proxy.")
    parser.add_argument('--proxy', type=str, help='Proxy server port in format host:port (e.g., 127.0.0.1:10809)',default='127.0.0.1:10809')
    args = parser.parse_args()
    driver = setup_driver(proxy=args.proxy)
    driver.response_interceptor = response_interceptor
    driver.get('https://huggingface.co')  # 访问目标网站
    input("Press Enter to continue...")

    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"response-{now}.txt"
    filepath = os.path.join("responses", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        for request in driver.requests:
            f.write(f'URL: {request.url}\n')
            f.write(f'Method: {request.method}\n')
            if request.response:
                f.write(f'Status code: {request.response.status_code}\n')
                f.write(f'Response headers: {request.response.headers}\n')
                f.write(f'Response body: {request.response.body}\n')
            f.write('-' * 60 + '\n')
    driver.quit()