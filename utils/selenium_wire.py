import json
import os
import time
import random
import logging
from datetime import datetime
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib.parse import urlparse

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('request_capture.log'),
        logging.StreamHandler()
    ]
)


class RequestCapturer:
    def __init__(self):
        # 浏览器配置
        self.chrome_options = Options()
        self._setup_browser_options()

        # Selenium Wire配置
        self.seleniumwire_options = {
            'disable_capture': False,
            'request_storage': 'memory',
            'request_storage_max_size': 2000,
            'verify_ssl': False,
            'ignore_http_methods': [],
            'suppress_connection_errors': False,
            'connection_timeout': 30,
            'proxy': {
                'http': 'http://127.0.0.1:10809',
                'https': 'http://127.0.0.1:10809',
                'no_proxy': 'localhost,127.0.0.1'
            },
        }

        # 目标网站列表
        self.websites = [
            #{"url": "https://github.com", "name": "github"},
            #{"url": "https://www.wikipedia.org", "name": "wikipedia"},
            #{"url": "https://huggingface.co", "name": "huggingface"},
            #{"url": "https://hub.docker.com", "name": "dockerhub"},
            #{"url": "https://www.youtube.com", "name": "youtube"},
            #{"url": "https://twitter.com", "name": "twitter"},
            #{"url": "https://www.facebook.com", "name": "facebook"},
            {"url": "https://www.google.com/search?q=selenium", "name": "google_search"},
            #{"url": "https://scholar.google.com", "name": "google_scholar"},
            #{"url": "https://patents.google.com", "name": "google_patents"},
        ]

        # 请求捕获范围
        self.scopes = [
            r'.*github\.com.*',
            r'.*wikipedia\.org.*',
            r'.*huggingface\.co.*',
            r'.*docker\.com.*',
            r'.*youtube\.com.*',
            r'.*twitter\.com.*',
            r'.*facebook\.com.*',
            r'.*google\.com.*',
            r'.*googleapis\.com.*',
            r'.*gstatic\.com.*',
            r'.*cloudflare\.com.*',
            r'.*akamaihd\.net.*'
        ]

        # 初始化浏览器
        self.driver = None
        self._init_browser()

    def _setup_browser_options(self):
        """配置浏览器选项"""
        #self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


    def _init_browser(self):
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service,
                options=self.chrome_options,
                seleniumwire_options=self.seleniumwire_options
            )
            self.driver.scopes = self.scopes
            logging.info("浏览器初始化成功")
        except Exception as e:
            logging.error(f"浏览器初始化失败: {str(e)}")
            raise

    def _random_delay(self, min_sec=1, max_sec=5):
        """随机延迟"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _scroll_page(self):
        """滚动页面以触发更多请求"""
        try:
            for _ in range(3):
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                current_pos = 0
                while current_pos < scroll_height:
                    self.driver.execute_script(f"window.scrollTo(0, {current_pos});")
                    current_pos += random.randint(200, 500)
                    self._random_delay(0.5, 1.5)
                self._random_delay()
        except Exception as e:
            logging.warning(f"滚动页面时出错: {str(e)}")

    def _wait_for_page_load(self, timeout=30):
        """等待页面加载完成"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logging.warning("页面加载超时")

    def _capture_requests(self, site_name):


        os.makedirs("responses", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"responses/{site_name}_{timestamp}.json"

        requests_data = []
        for request in self.driver.requests:
            if request.response:
                try:
                    request_data = {
                        "timestamp": datetime.now().isoformat(),
                        "url": request.url,
                        "method": request.method,
                        "status_code": request.response.status_code,
                        "request_headers": dict(request.headers),
                        "response_headers": dict(request.response.headers),
                        "body_size": len(request.response.body) if request.response.body else 0,
                        "domain": urlparse(request.url).netloc,
                        "path": urlparse(request.url).path,
                        "params": urlparse(request.url).query,
                        "is_ajax": "XMLHttpRequest" in dict(request.headers).get("X-Requested-With", ""),
                        "content_type": dict(request.response.headers).get("Content-Type", "")
                    }

                    # 只保存文本类型的响应体
                    content_type = request_data["content_type"].lower()
                    if any(t in content_type for t in ["text", "json", "xml", "javascript"]):
                        try:
                            request_data["response_body"] = request.response.body.decode("utf-8", errors="ignore")
                        except:
                            request_data["response_body"] = "Binary content"

                    requests_data.append(request_data)
                except Exception as e:
                    logging.warning(f"处理请求 {request.url} 时出错: {str(e)}")

            # 保存到文件
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(requests_data, f, ensure_ascii=False, indent=2)
                logging.info(f"已保存 {len(requests_data)} 个请求到 {filename}")
            except Exception as e:
                logging.error(f"保存文件时出错: {str(e)}")
                # 可选：将错误数据保存到临时文件
                temp_filename = f"{site_name}_error_{timestamp}.json"
                with open(temp_filename, "w", encoding="utf-8") as f:
                    json.dump({"error": str(e), "data": requests_data}, f)

    def capture_all_sites(self):
        if not self.driver:
            logging.error("浏览器未初始化")
            return False

        try:
            for site in self.websites:
                logging.info(f"开始处理网站: {site['name']} ({site['url']})")

                try:
                    # 清除之前的请求记录
                    del self.driver.requests

                    # 访问网站
                    self.driver.get(site["url"])
                    self._random_delay(2, 4)

                    # 等待页面加载
                    self._wait_for_page_load()

                    # 滚动页面
                    self._scroll_page()

                    # 捕获请求
                    self._capture_requests(site["name"])

                    # 随机延迟
                    self._random_delay(3, 7)

                except WebDriverException as e:
                    logging.error(f"访问网站 {site['url']} 时出错: {str(e)}")
                    continue

                except Exception as e:
                    logging.error(f"处理网站 {site['name']} 时发生未知错误: {str(e)}")
                    continue

            return True

        finally:
            self.driver.quit()
            logging.info("浏览器已关闭")

    def analyze_requests(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 基本统计
            total_requests = len(data)
            domains = {}
            status_codes = {}
            content_types = {}

            for req in data:
                domains[req["domain"]] = domains.get(req["domain"], 0) + 1
                status_codes[str(req["status_code"])] = status_codes.get(str(req["status_code"]), 0) + 1
                ct = req["content_type"].split(";")[0] if req["content_type"] else "unknown"
                content_types[ct] = content_types.get(ct, 0) + 1

            # 打印报告
            print(f"\n{'=' * 50}")
            print(f"请求分析报告 - {filename}")
            print(f"总请求数: {total_requests}")

            print("\n按域名统计:")
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"{domain}: {count}")

            print("\n按状态码统计:")
            for code, count in sorted(status_codes.items(), key=lambda x: x[1], reverse=True):
                print(f"{code}: {count}")

            print("\n按内容类型统计:")
            for ct, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"{ct}: {count}")
            print('=' * 50)

        except Exception as e:
            print(f"分析请求时出错: {str(e)}")


if __name__ == "__main__":
    try:
        capturer = RequestCapturer()
        if capturer.capture_all_sites():
            logging.info("所有网站请求捕获完成")

            # 示例：分析其中一个捕获的文件
            capturer.analyze_requests("responses/github_20230501_143022.json")

    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")