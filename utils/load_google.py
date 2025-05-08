from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def google_search_selenium(query, num_pages=5):
    # 启动浏览器
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")  # 无头模式
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.google.com")
    time.sleep(2)

    # 输入搜索关键词
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(2)
    
    results = []

    driver.quit()
    return results

if __name__ == "__main__":
    # 示例调用
    query = "台湾"
    google_search_selenium(query)