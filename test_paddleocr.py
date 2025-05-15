import requests
import os
import json
from datetime import datetime


class PaddleOcrClient:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url

    def recognize_single(self, image_path: str):
        """识别单张图片"""
        with open(image_path, 'rb') as f:
            response = requests.post(
                f"{self.server_url}/ocr/single",
                files={"image": (os.path.basename(image_path), f)}
            )
        return response.json()

    def recognize_batch(self, folder_path: str, output_file=None):
        """批量识别图片"""
        try:
            start_time = datetime.now()

            # 确保路径存在
            if not os.path.exists(folder_path):
                return {"success": False, "error": "文件夹路径不存在"}

            # 转换为绝对路径并标准化
            folder_path = os.path.abspath(folder_path)

            # 构造符合服务器要求的JSON数据
            request_data = {
                "folder_path": folder_path,
                "config": {  # 必须包含config字段
                    "use_gpu": False,
                    "language": "ch",
                    "enable_angle_cls": True
                }
            }

            response = requests.post(
                f"{self.server_url}/ocr/batch",
                json=request_data,  # 使用json参数自动序列化
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            # 处理响应
            if response.status_code != 200:
                error_msg = response.json().get("detail", response.text)
                return {"success": False, "error": f"服务器错误: {error_msg}"}

            result = response.json()
            end_time = datetime.now()

            # 添加处理时间信息
            result["processing_time"] = {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds()
            }

            # 确保包含必要字段
            if "processed_count" not in result:
                result["processed_count"] = len(result.get("results", {}))

            # 保存结果到文件
            if output_file:
                self._save_results(result, output_file)

            return result

        except Exception as e:
            return {"success": False, "error": f"请求失败: {str(e)}"}

    def _save_results(self, result, output_file):
        """保存结果到文件"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"结果已保存到: {os.path.abspath(output_file)}")
        except Exception as e:
            print(f"保存结果失败: {str(e)}")


# 使用示例
if __name__ == "__main__":
    client = PaddleOcrClient()

    # 单图识别测试
    print("单图识别结果:", client.recognize_single("./test_image/testing_words/0.png"))

    # 批量识别测试
    output_file = "results/paddleocr_result.json"  # 指定输出文件路径
    batch_result = client.recognize_batch("./test_image/testing_words", output_file=output_file)
    print(f"批量识别完成，共处理 {batch_result['processed_count']} 张图片")
    print(f"处理耗时: {batch_result['processing_time']['duration_seconds']:.2f}秒")