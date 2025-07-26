import os
import time
import argparse
import re
from datetime import datetime
from typing import List
from tools.google import (
    google_search_filter,
    google_search_page_filter,
    google_search_video_page_filter,
    filter_vet_response,
)
from tools.google_scholar import (
  google_scholar_search_filter,
  google_scholar_search_page_filter
)
from tools.wiki_filter import (
    wiki_search_filter, 
    wiki_suggestions_filter, 
    wiki_search_page_filter, 
    extract_wiki_title, 
    inject_content, 
    wiki_content_filter
)
from tools.hugging_face import (
    hugging_face_quick_search_filter,
    hugging_face_card_page_filter,
    hugging_face_models_search_json_filter,
    hugging_face_models_search_page_filter,
    hugging_face_datasets_search_json_filter,
    hugging_face_datasets_search_page_filter,
    hugging_face_spaces_search_json_filter,
    hugging_face_spaces_search_page_filter,
    hugging_face_collections_search_json_filter,
    hugging_face_collections_search_page_filter,
    hugging_face_blogs_search_page_filter,
    hugging_face_blogs_community_page_filter,
    hugging_face_posts_search_page_filter,
    hugging_face_posts_search_json_filter,
    hugging_face_discuss_topics_search_json_filter,
    hugging_face_discuss_topics_search_page_filter,
    hugging_face_discuss_posts_json_filter,
    hugging_face_discuss_posts_page_filter,
)
from tools.mongodb import cleanup_old_collections
from tools.web import setup_driver

FILTER_WORDS: List[str] = ["airlines","news","Airlines","airline","习近平","六四","防火墙技术","chatgpt","gpt","kimi",'GPT','Kimi']

def response_interceptor(request, response):
    """
    Intercepts responses from Google to filter out unwanted content.
    """
    url = request.url
    content_type = response.headers.get('Content-Type', '')
    try:
        # google scholar
        if 'scholar.google.com' in url: 
            # 1. 过滤搜索建议
            if "scholar.google.com/scholar_complete" in url:
                try:
                    start_time = time.time()
                    response.body = google_scholar_search_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                    duration = time.time() - start_time
                    print(f"过滤搜索建议耗时: {duration:.4f}秒")
                except Exception as e:
                    print("Error:", e)
                    pass  # 失败时不做处理
            # 2. 过滤搜索结果`
            elif "scholar.google.com/scholar" in url and "text/html" in content_type:
                #过滤主页面
                try:
                    start_time = time.time()
                    response.body = google_scholar_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                    duration = time.time() - start_time
                    print(f"过滤主页面耗时: {duration:.4f}秒")
                except Exception as e:
                    print("Error:", e)
                    pass
        # google search
        elif 'google.com' in url:
            if "google.com/search?vet=12" in url:
                start_time = time.time()
                response.body = filter_vet_response(
                    response.body.decode('utf-8', errors='ignore'),
                    FILTER_WORDS
                )
                print(f"过滤vet请求耗时: {time.time() - start_time:.4f}秒")
                return
            # 2. Filter search suggestions
            elif "google.com/complete/search" in url:
                start_time = time.time()
                response.body = google_search_filter(
                    response.body.decode('utf-8', errors='ignore'),
                    FILTER_WORDS
                )
                print(f"过滤搜索建议耗时: {time.time() - start_time:.4f}秒")
                return
            # 3. Filter HTML search results (main and video pages)
            if "text/html" in content_type:
                start_time = time.time()
                decoded_body = response.body.decode('utf-8', errors='ignore')
                if "udm=7" in url:
                    response.body = google_search_video_page_filter(decoded_body, FILTER_WORDS)
                    print(f"过滤视频页面耗时: {time.time() - start_time:.4f}秒")
                else:
                    response.body = google_search_page_filter(decoded_body, FILTER_WORDS)
                    print(f"过滤主页面耗时: {time.time() - start_time:.4f}秒")
        #wikipedia
        elif "/zh.wikipedia.org" in url:
            content_type
            #wiki百科首页搜索栏
            if "/search/title?q" in url:
                try:
                    start_time = time.time()
                    response.body = wiki_search_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS,
                                                       url)
                    duration = time.time() - start_time
                    print(f"过滤wiki百科搜索耗时: {duration:.4f}秒")
                except Exception as e:
                    print("Error:", e)
                    pass  # 失败时不做处理
            #wiki百科搜索页搜索栏
            if "w/api.php?action=" in url:
                try:
                    start_time = time.time()
                    response.body = wiki_suggestions_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS,
                                                            url)
                    duration = time.time() - start_time
                    print(f"过滤wiki百科搜索耗时: {duration:.4f}秒")
                except Exception as e:
                    print("Error:", e)
                    pass  # 失败时不做处理
            #wiki百科页面
            if "w/index.php?" in url:
                try:
                    start_time = time.time()
                    response.body = wiki_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS,
                                                            url)
                    duration = time.time() - start_time
                    print(f"过滤wiki百科搜索耗时: {duration:.4f}秒")
                except Exception as e:
                    print("Error:", e)
                    pass  # 失败时不做处理
            #wiki百科标题
            if "/wiki/" in url and 'text/html' in content_type:

                decoded_title = extract_wiki_title(url)

                for word in FILTER_WORDS:
                    if re.search(re.escape(word), decoded_title, re.IGNORECASE):
                        start_time = time.time()
                        response.body = inject_content(response.body.decode('utf-8', errors='ignore'))
                        duration = time.time() - start_time
                        print(f"注入耗时: {duration:.4f}秒")
                        break
                if "/Wikipedia:" in url:
                    response.body = wiki_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS,
                                                            url)
                else:
                    response.body = wiki_content_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS,
                                                        url)
        #huggingface
        elif 'huggingface.co' in url: 
            # 1. 过滤顶部快速搜索推荐条目
            if "huggingface.co/api/quicksearch" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_quick_search_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤quick搜索建议耗时: {duration:.4f}秒")

            # 2. 过滤models搜索结果条目、models首页trending元素
            elif "huggingface.co/models-json" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_models_search_json_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤models-json耗时: {duration:.4f}秒")

            elif "huggingface.co/models" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_models_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤models-page耗时: {duration:.4f}秒")

            # 3. 过滤datasets搜索结果条目
            elif "huggingface.co/datasets-json" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_datasets_search_json_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤datasets-json耗时: {duration:.4f}秒")

            elif "huggingface.co/datasets" in url and "datasets/" not in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_datasets_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤datasets-page耗时: {duration:.4f}秒")

            # 4. 过滤spaces搜索结果条目
            elif "huggingface.co/spaces-json" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_spaces_search_json_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤spaces-json耗时: {duration:.4f}秒")

            elif "huggingface.co/spaces" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_spaces_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤spaces-page耗时: {duration:.4f}秒")

            # 5. 过滤collentions搜索结果条目、collentions首页trending元素
            elif "huggingface.co/collections-json" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_collections_search_json_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤collections-json耗时: {duration:.4f}秒")

            elif "huggingface.co/collections" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_collections_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤collections-page耗时: {duration:.4f}秒")
        
            # 6. blogs过滤:展开侧边栏community页面和blogs首页
            elif "huggingface.co/blog/community" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_blogs_community_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤blog/community页面耗时: {duration:.4f}秒")

            elif "huggingface.co/blog" in url and "png" not in url and "jpg" not in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_blogs_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤blog页面耗时: {duration:.4f}秒")
            
            # 7. posts过滤
            elif "huggingface.co/api/posts" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_posts_search_json_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤posts-json耗时: {duration:.4f}秒")

            elif "huggingface.co/posts" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_posts_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤posts页面耗时: {duration:.4f}秒")
            
            # 8. 论坛页面过滤：首页帖子、帖子中的posts
            elif "discuss.huggingface.co/latest.json" in url or "discuss.huggingface.co/hot.json" in url or "discuss.huggingface.co/top.json" in url or "discuss.huggingface.co/categories_and_latest" in url:
                start_time = time.time()
                print(url)
                response.body = hugging_face_discuss_topics_search_json_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤discuss-topic-json耗时: {duration:.4f}秒")

            elif "discuss.huggingface.co/t/" in url:
                start_time = time.time()
                print(url)
                if "json" in url:
                    response.body = hugging_face_discuss_posts_json_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                else:
                    response.body = hugging_face_discuss_posts_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤discuss-posts页面耗时: {duration:.4f}秒")

            elif "https://discuss.huggingface.co" in url and "text/html" in content_type:
                start_time = time.time()
                print(url)
                response.body = hugging_face_discuss_topics_search_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤discuss首页耗时: {duration:.4f}秒")

            # 9. 过滤models\datasets card页面,含有违禁词则无法正常访问页面
            elif "https://huggingface.co/" in url and "text/html" in content_type:
                start_time = time.time()
                print(url)
                response.body = hugging_face_card_page_filter(response.body.decode('utf-8', errors='ignore'), FILTER_WORDS)
                duration = time.time() - start_time
                print(f"过滤model\dataset card页面耗时: {duration:.4f}秒")

    except Exception as e:
        print(f"Error in response_interceptor for URL {url}: {e}")

def save_responses(driver, output_dir="responses"):
    """
    Saves all requests and their responses to a timestamped file.
    """
    os.makedirs(output_dir, exist_ok=True)
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"response-{now}.txt"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for request in getattr(driver, 'requests', []):
                f.write(f'URL: {request.url}\n')
                f.write(f'Method: {getattr(request, "method", "N/A")}\n')
                if hasattr(request, 'response') and request.response:
                    resp = request.response
                    f.write(f'Status code: {getattr(resp, "status_code", "N/A")}\n')
                    f.write(f'Response headers: {getattr(resp, "headers", {})}\n')
                    f.write(f'Response body: {getattr(resp, "body", "")}\n')
                f.write('-' * 60 + '\n')
        print(f"Responses saved to {filepath}")
    except Exception as e:
        print(f"Failed to save responses: {e}")

def main():
    # 清理旧集合
    cleanup_old_collections(days=30)
    parser = argparse.ArgumentParser(description="Load Google with optional proxy.")
    parser.add_argument(
        '--proxy',
        type=str,
        default='127.0.0.1:10809',
        help='Proxy server in format host:port (e.g., 127.0.0.1:10809)'
    )
    args = parser.parse_args()

    try:
        driver = setup_driver(proxy=args.proxy)
        driver.response_interceptor = response_interceptor
        driver.get('https://www.google.com/')
        input("Press Enter to continue...")
        save_responses(driver)
    except Exception as e:
        print(f"Error running driver: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    main()
