import unittest
import time
import os

from test_function.azure_ocr import image_detection 

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