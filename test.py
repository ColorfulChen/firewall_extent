import unittest
import time
import os
import requests
import base64

#from test_function.paddle_ocr import image_detection 

API_BASE_URL = "http://localhost:5000"

def image_detection(image_path,filter_words = []):
    with open(image_path, "rb") as f:
        image_data = f.read()
    base64_image = base64.b64encode(image_data).decode('utf-8')

    payload = {
        "image": base64_image,
        "filter_words": filter_words
    }
    api_url = f"{API_BASE_URL}/image_detection_paddle_ocr"
    api_resp = requests.post(api_url, json=payload, timeout=10)
    api_resp.raise_for_status()
    result = api_resp.json()
    return result if result else None

class TestImageClassification(unittest.TestCase):
    def setUp(self):
        # 前置条件：加载测试图片
        self.image_dir = "test_image/testing_words"  # 图片文件夹路径
        self.image_paths = [os.path.join(self.image_dir, f) for f in os.listdir(self.image_dir) if os.path.isfile(os.path.join(self.image_dir, f))]
        self.expected_label = "cat" 
        self.max_count = 30

    def test_classification(self):
        # 创建 results 文件夹（如果不存在）
        os.makedirs("results", exist_ok=True)
        # 获取当前时间戳
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        result_file = f"results/result-{timestamp}.txt"
        with open(result_file, "a", encoding="utf-8") as f:
            cnt = 0
            for image_path in self.image_paths:
                cnt = cnt + 1
                if cnt > self.max_count:
                    break
                
                start_time = time.time()
                try:
                    result = image_detection(image_path)
                    end_time = time.time()
                    duration = end_time - start_time
                    print(f"图片: {image_path} 运行时间: {duration:.4f} 秒")
                    f.write(f"图片: {image_path} | 运行时间: {duration:.4f} 秒 | 分类结果: {result}\n")
                except Exception as e:
                    print(f"图片: {image_path} 运行时出错: {e}")
                    f.write(f"图片: {image_path} | 运行时出错: {e}\n")
                #self.assertEqual(result, self.expected_label)

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()