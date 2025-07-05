import unittest
import time
import os
import requests
import base64
from typing import List, Optional, Dict, Any

API_BASE_URL = "http://localhost:5000"
RESULTS_DIR = "results"
IMAGE_DIR = "test_image/testing_words"
MAX_COUNT = 30

def image_detection(image_path: str, filter_words: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Sends an image to the image_detection_paddle_ocr API endpoint for processing.
    """
    filter_words = filter_words or []
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')

        payload = {
            "image": base64_image,
            "filter_words": filter_words
        }
        api_url = f"{API_BASE_URL}/image_detection_paddle_ocr"
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json() or None
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

class TestImageClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up resources shared across all tests."""
        if not os.path.exists(IMAGE_DIR):
            raise FileNotFoundError(f"Image directory not found: {IMAGE_DIR}")
        cls.image_paths = [
            os.path.join(IMAGE_DIR, f)
            for f in os.listdir(IMAGE_DIR)
            if os.path.isfile(os.path.join(IMAGE_DIR, f))
        ]
        os.makedirs(RESULTS_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        cls.result_file = os.path.join(RESULTS_DIR, f"result-{timestamp}.txt")

    def test_image_classification(self):
        cnt = 0
        with open(self.result_file, "a", encoding="utf-8") as f:
            for image_path in self.image_paths:
                cnt += 1
                if cnt > MAX_COUNT:
                    break
                start_time = time.time()
                result = image_detection(image_path)
                duration = time.time() - start_time

                if result is not None:
                    print(f"Image: {image_path} | Time: {duration:.4f} s | Result: {result}")
                    f.write(f"Image: {image_path} | Time: {duration:.4f} s | Result: {result}\n")
                    # Optionally, assert something about result here
                    # self.assertEqual(result, self.expected_label)
                else:
                    print(f"Image: {image_path} | Error during processing")
                    f.write(f"Image: {image_path} | Error during processing\n")

    @classmethod
    def tearDownClass(cls):
        """Clean up resources if needed."""
        pass

if __name__ == "__main__":
    unittest.main()
