import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
import numpy as np
import cv2
from typing import List,  Union
from pydantic import BaseModel
from enum import Enum
import uvicorn
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PaddleOCR-Server")

app = FastAPI(
    title="PaddleOCR",
    description="支持单图识别",
)

# 语言支持配置
class OcrLanguage(str, Enum):
    CH = "ch"  # 中文
    EN = "en"  # 英文
    MULTI = "ml"  # 多语言

class OcrConfig(BaseModel):
    use_gpu: bool = False
    language: OcrLanguage = OcrLanguage.CH
    enable_angle_cls: bool = True

def process_image_data(image_data: Union[str, bytes, np.ndarray], ocr_instance) -> List[dict]:
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

                formatted.append({
                    "text": text,
                    "confidence": float(confidence),
                    "position": position
                })
        return formatted
    except Exception as e:
        logger.error(f"图片处理失败: {str(e)}")
        raise

def image_detection_sync(image_source: Union[str, bytes], config: OcrConfig = OcrConfig()) -> dict:
    """用于test.py本地测试"""
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
        result = process_image_data(image_source, ocr_instance)

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
            "filename": getattr(image_source, 'filename', 'unknown')
        }

async def image_detection_async(image_source: Union[UploadFile, bytes, str], config: OcrConfig = OcrConfig()) -> dict:
    """用于本地服务器api接口"""
    try:
        # 初始化OCR实例
        ocr_instance = PaddleOCR(
            lang=config.language,
            use_angle_cls=config.enable_angle_cls,
            use_gpu=config.use_gpu,
            show_log=False
        )

        # 处理不同输入类型
        if isinstance(image_source, UploadFile):
            contents = await image_source.read()
            result = process_image_data(contents, ocr_instance)
            filename = image_source.filename
        elif isinstance(image_source, str):
            result = process_image_data(image_source, ocr_instance)
            filename = os.path.basename(image_source)
        elif isinstance(image_source, bytes):
            result = process_image_data(image_source, ocr_instance)
            filename = "from_bytes.jpg"
        else:
            raise ValueError("不支持的输入类型")

        return {
            "success": True,
            "filename": filename,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filename": getattr(image_source, 'filename', 'unknown')
        }

# 兼容接口
# {'success': True, 'filename': '102.png', 'result': [{'text': 'Boehhone', 'confidence': 0.6342410445213318, 'position': [[26.0, 24.0], [211.0, 0.0], [215.0, 41.0], [31.0, 65.0]]}]}

def image_detection_paddle_ocr(image_source: Union[str, bytes], config: OcrConfig = OcrConfig(), filter_words = []) -> dict:
    """兼容接口，自动选择本地测试或本地服务器api"""
    ocr_results = image_detection_sync(image_source, config)
    contain_bad_word = False
    if ocr_results['success'] == True:
        ocr_text = ''
        for text in ocr_results['result']:
            ocr_text = ocr_text + text['text']

        if any(re.search(word, text) for word in filter_words):
            contain_bad_word = True

    return_json = {
        'filter_result': contain_bad_word,
        'ocr_result': ocr_results
    }

    return return_json

@app.post("/ocr/single")
async def api_image_detection(
        image: UploadFile = File(...),
        config: OcrConfig = OcrConfig()
):
    """API接口"""
    result = await image_detection_async(image, config)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return JSONResponse(result)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
