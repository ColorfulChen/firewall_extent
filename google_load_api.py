import time
import random
import os
from datetime import datetime
import requests  # Added import
from tools.web import setup_driver

filter_words = ["airlines","news","Airlines","airline","习近平","六四"]

API_BASE_URL = "http://localhost:5000"  # Added API base URL

def response_interceptor(request, response):
    # google
    if 'google.com' in request.url:
        if "google.com/search?vet=12" in request.url:
            try:
                start_time = time.time()
                payload = {
                    "response": response.body.decode('utf-8', errors='ignore'),
                    "filter_words": filter_words
                }
                api_url = f"{API_BASE_URL}/filter_vet_response"
                api_resp = requests.post(api_url, json=payload, timeout=10)
                api_resp.raise_for_status()
                filtered_body_str = api_resp.json().get("filtered_response")
                if filtered_body_str is not None:
                    response.body = filtered_body_str.encode('utf-8')
                else:
                    response.body = b''
                duration = time.time() - start_time
                print(f"过滤vet请求耗时 (API): {duration:.4f}秒")
            except requests.exceptions.RequestException as e:
                print(f"API call to {api_url} failed: {e}")
                pass
            except Exception as e:
                print(f"Error processing API response for vet request: {e}")
                pass
            return None    
        # 1. 过滤搜索建议
        if "google.com/complete/search" in request.url:
            try:
                start_time = time.time()
                payload = {
                    "response": response.body.decode('utf-8', errors='ignore'),
                    "filter_words": filter_words
                }
                api_url = f"{API_BASE_URL}/google_search_filter"
                api_resp = requests.post(api_url, json=payload, timeout=10)
                api_resp.raise_for_status()
                filtered_body_str = api_resp.json().get("filtered_response")
                if filtered_body_str is not None:
                    response.body = filtered_body_str.encode('utf-8')
                else:
                    response.body = b''
                duration = time.time() - start_time
                print(f"过滤搜索建议耗时 (API): {duration:.4f}秒")
            except requests.exceptions.RequestException as e:
                print(f"API call to {api_url} failed: {e}")
                pass
            except Exception as e:
                print(f"Error processing API response for search suggestions: {e}")
                pass  # 失败时不做处理
        # 2. 过滤搜索结果
        elif "text/html" in response.headers.get('Content-Type', ''):
                #过滤视频页面
                if "udm=7" in request.url:
                    try:
                        start_time = time.time()
                        payload = {
                            "response": response.body.decode('utf-8', errors='ignore'),
                            "filter_words": filter_words
                        }
                        api_url = f"{API_BASE_URL}/google_search_video_page_filter"
                        api_resp = requests.post(api_url, json=payload, timeout=10)
                        api_resp.raise_for_status()
                        filtered_body_str = api_resp.json().get("filtered_response")
                        if filtered_body_str is not None:
                            response.body = filtered_body_str.encode('utf-8')
                        else:
                            response.body = b''
                        duration = time.time() - start_time
                        print(f"过滤视频页面耗时 (API): {duration:.4f}秒")
                    except requests.exceptions.RequestException as e:
                        print(f"API call to {api_url} failed: {e}")
                        pass
                    except Exception as e:
                        print(f"Error processing API response for video page: {e}")
                        pass
                #过滤主页面
                else:
                    try:
                        start_time = time.time()
                        payload = {
                            "response": response.body.decode('utf-8', errors='ignore'),
                            "filter_words": filter_words
                        }
                        api_url = f"{API_BASE_URL}/google_search_page_filter"
                        api_resp = requests.post(api_url, json=payload, timeout=10)
                        api_resp.raise_for_status()
                        filtered_body_str = api_resp.json().get("filtered_response")
                        if filtered_body_str is not None:
                            response.body = filtered_body_str.encode('utf-8')
                        else:
                            response.body = b''
                        duration = time.time() - start_time
                        print(f"过滤主页面耗时 (API): {duration:.4f}秒")
                    except requests.exceptions.RequestException as e:
                        print(f"API call to {api_url} failed: {e}")
                        pass
                    except Exception as e:
                        print(f"Error processing API response for main page: {e}")
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
