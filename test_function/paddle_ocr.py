import os
import logging
import cv2
import numpy as np
from paddleocr import PaddleOCR
from typing import List, Union
from pydantic import BaseModel
from enum import Enum


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PaddleOCR-Service")


# 语言支持配置
class OcrLanguage(str, Enum):
    CH = "ch"  # 中文
    EN = "en"  # 英文
    MULTI = "ml"  # 多语言

class OcrConfig(BaseModel):
    use_gpu: bool = False
    language: OcrLanguage = OcrLanguage.CH
    enable_angle_cls: bool = True

def process_image_data(image_data: Union[str, bytes, np.ndarray], ocr_instance, filter_words: List[str] = None) -> List[dict]:
    """统一图像处理函数"""
    try:
        if isinstance(image_data, str):  # 文件路径
            img = cv2.imread(image_data)
            if img is None:
                raise ValueError(f"无法读取图片文件: {image_data}")
        elif isinstance(image_data, bytes):  # 字节流
            img = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        elif isinstance(image_data, np.ndarray):  # numpy数组
            img = image_data
        else:
            raise ValueError("不支持的图像输入类型")

        if img is None:
            raise ValueError("无法解码图片数据")

        result = ocr_instance.ocr(img, cls=True)

        # 处理结果为None或空的情况
        if not result or not result[0]:
            return []

        formatted = []
        for line in result[0]:
            if line:
                points, (text, confidence) = line
                position = []
                for point in points:
                    if hasattr(point, 'tolist'):  # 如果是numpy数组
                        position.append(point.tolist())
                    else:  # 已经是列表形式
                        position.append(list(map(float, point)))

                # 应用过滤词
                if filter_words and any(word.lower() in text.lower() for word in filter_words):
                    continue

                formatted.append({
                    "text": text,
                    "confidence": float(confidence),
                    "position": position
                })
        return formatted
    except Exception as e:
        logger.error(f"图片处理失败: {str(e)}")
        raise

def image_detection_paddle_ocr(image_source: Union[str, bytes], filter_words: List[str] = None, config: OcrConfig = OcrConfig()) -> dict:
    """OCR识别主函数"""
    try:
        # 初始化OCR实例
        ocr_instance = PaddleOCR(
            # 使用默认模型，也可指定模型，paddle会自动下载模型
            lang=config.language,
            # 示例指定模型，没有也会自动下载
            # det_model_dir='./paddle_models/det',  # 检测模型路径
            # rec_model_dir='./paddle_models/rec',  # 识别模型路径

            use_angle_cls=config.enable_angle_cls,
            use_gpu=config.use_gpu,
            show_log=False
        )

        # 处理图像
        result = process_image_data(image_source, ocr_instance, filter_words)

        # 获取文件名
        if isinstance(image_source, str):
            filename = os.path.basename(image_source)
        else:
            filename = "from_bytes.jpg"

        return {
            "success": True,
            "filename": filename,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filename": "unknown"
        }