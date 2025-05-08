import time
import random
import os
from datetime import datetime
from tools.google import google_search_filter,google_search_page_filter,google_search_video_page_filter
from tools.web import setup_driver

filter_words = ["airlines","news","Airlines","airline"]

def response_interceptor(request, response):
    # google
    if 'google.com' in request.url:
        # if "google.com/search?vet=12" in request.url:
        #     response.body = ''
        #     return None    
        # 1. 过滤搜索建议
        if "google.com/complete/search" in request.url:
            try:
                response.body = google_search_filter(response, filter_words)
            except Exception as e:
                print("Error:", e)
                pass  # 失败时不做处理
        # 2. 过滤搜索结果
        elif "text/html" in response.headers.get('Content-Type', ''):
                #过滤视频页面
                if "udm=7" in request.url:
                    try:
                        response.body = google_search_video_page_filter(response, filter_words)
                    except Exception as e:
                        print("Error:", e)
                        pass
                #过滤主页面
                else:
                    try:
                        response.body = google_search_page_filter(response, filter_words)
                    except Exception as e:
                        print("Error:", e)
                        pass

if __name__ == "__main__":
    driver = setup_driver() 
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
