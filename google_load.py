import os
import time
import argparse
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
from tools.web import setup_driver

FILTER_WORDS: List[str] = ["airlines", "news", "Airlines", "airline", "习近平", "六四"]

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
          # 2. 过滤搜索结果
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
        if "google.com/search?vet=12" in request.url:
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
