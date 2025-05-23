import time
import random
import os
from datetime import datetime
from tools.google import google_search_filter,google_search_page_filter,google_search_video_page_filter,filter_vet_response
from tools.web import setup_driver
import time
import argparse 

filter_words = ["airlines","news","Airlines","airline","习近平","六四"]

def response_interceptor(request, response):
    # google
    if 'google.com' in request.url:
        if "google.com/search?vet=12" in request.url:
            start_time = time.time()
            response.body = filter_vet_response(response.body.decode('utf-8', errors='ignore'), filter_words)
            duration = time.time() - start_time
            print(f"过滤vet请求耗时: {duration:.4f}秒")
            return None    
        # 1. 过滤搜索建议
        if "google.com/complete/search" in request.url:
            try:
                start_time = time.time()
                response.body = google_search_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                duration = time.time() - start_time
                print(f"过滤搜索建议耗时: {duration:.4f}秒")
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        # 2. 过滤搜索结果
        elif "text/html" in response.headers.get('Content-Type', ''):
                #过滤视频页面
                if "udm=7" in request.url:
                    try:
                        start_time = time.time()
                        response.body = google_search_video_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                        duration = time.time() - start_time
                        print(f"过滤视频页面耗时: {duration:.4f}秒")
                    except Exception as e:
                        print("Error:", e)
                        pass
                #过滤主页面
                else:
                    try:
                        start_time = time.time()
                        response.body = google_search_page_filter(response.body.decode('utf-8', errors='ignore'), filter_words)
                        duration = time.time() - start_time
                        print(f"过滤主页面耗时: {duration:.4f}秒")
                    except Exception as e:
                        print("Error:", e)
                        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Google with optional proxy.")
    parser.add_argument('--proxy', type=str, help='Proxy server port in format host:port (e.g., 127.0.0.1:10809)',default='127.0.0.1:10809')
    args = parser.parse_args()
    driver = setup_driver(proxy=args.proxy)
    driver.response_interceptor = response_interceptor
    driver.get('https://www.google.com/')  # 访问目标网站
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