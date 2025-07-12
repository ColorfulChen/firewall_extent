import time
import random
import os
from datetime import datetime
from tools.google_scholar import google_scholar_search_filter,google_scholar_search_page_filter
from tools.web import setup_driver
import time
import argparse 

filter_words = ["airlines","news","Airlines","airline","习近平","六四","防火墙技术"]

def response_interceptor(request, response):
    # google scholar
    if 'scholar.google.com' in request.url: 
        # 1. 过滤搜索建议
        if "scholar.google.com/scholar_complete" in request.url:
            try:
                start_time = time.time()
                response.body = google_scholar_search_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤搜索建议耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        # 2. 过滤搜索结果
        elif "scholar.google.com/scholar" in request.url and "text/html" in response.headers.get('Content-Type', ''):
            #过滤主页面
            try:
                start_time = time.time()
                response.body = google_scholar_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤主页面耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Google Scholar with optional proxy.")
    parser.add_argument('--proxy', type=str, help='Proxy server port in format host:port (e.g., 127.0.0.1:10809)',default='127.0.0.1:10809')
    args = parser.parse_args()
    driver = setup_driver(proxy=args.proxy)
    driver.response_interceptor = response_interceptor
    driver.get('https://scholar.google.com/')  # 访问目标网站
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