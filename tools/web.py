import gzip
import brotli
import io
from seleniumwire import webdriver 
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """配置浏览器驱动"""
    wire_options = {
        'disable_encoding': True,
        'ignore_http_methods': ['OPTIONS', 'POST'],
        'suppress_connection_errors': True,
        'proxy': {  # 代理设置（如果需要）
            'http': 'http://127.0.0.1:10809',
            'https': 'http://127.0.0.1:10809',
            'no_proxy': 'localhost,127.0.0.1'
        }
    }

    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option("detach", True)

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    driver = webdriver.Chrome(
        seleniumwire_options=wire_options,
        options=chrome_options
    )

    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver