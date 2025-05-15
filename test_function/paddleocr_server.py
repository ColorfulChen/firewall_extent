import torch
import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
import numpy as np
import cv2
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PaddleOCR-Server")

app = FastAPI(
    title="PaddleOCR",
    description="支持单图和文件夹批量识别",
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


# 初始化默认OCR实例
default_ocr = PaddleOCR(
    lang="ch", # 使用默认模型
    use_angle_cls=True,
    use_gpu=True,
    show_log=False
)

async def process_image(image_data: bytes, ocr_instance) -> List[dict]:
    """OCR处理函数"""
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
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
                # 修复点坐标转换问题
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


@app.post("/ocr/single")
async def recognize_single(
        image: UploadFile = File(...),
        config: OcrConfig = OcrConfig()
):
    """单张图片识别接口"""
    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        raise HTTPException(400, detail="仅支持PNG/JPG/JPEG/BMP格式")

    try:
        contents = await image.read()
        ocr_instance = PaddleOCR(
            lang=config.language,
            use_angle_cls=config.enable_angle_cls,
            use_gpu=config.use_gpu,
            #det_model_dir='./paddle_models/ch_PP-OCRv4_det_server_infer',  # 检测模型路径
            #rec_model_dir='./paddle_models/PP-OCRv4_server_rec_doc_infer',  # 识别模型路径
        )
        result = await process_image(contents, ocr_instance)
        return JSONResponse({
            "success": True,
            "filename": image.filename,
            "result": result
        })
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/ocr/batch")
async def recognize_batch(
        request: dict  # 改为接收原生dict而不是BaseModel
):
    try:
        folder_path = request.get("folder_path")
        config_data = request.get("config", {})

        # 手动验证参数
        if not folder_path or not isinstance(folder_path, str):
            raise HTTPException(422, detail="folder_path必须是非空字符串")

        # 处理config参数
        config = OcrConfig(
            use_gpu=config_data.get("use_gpu", False),
            language=config_data.get("language", "ch"),
            enable_angle_cls=config_data.get("enable_angle_cls", True),

        )
        if not os.path.isdir(folder_path):
            raise HTTPException(400, detail="文件夹路径不存在")

        valid_exts = ('.png', '.jpg', '.jpeg', '.bmp')

        try:
            image_files = [
                f for f in os.listdir(folder_path)
                if f.lower().endswith(valid_exts)
            ]
        except Exception as e:
            raise HTTPException(400, detail=f"读取文件夹失败: {str(e)}")

        if not image_files:
            raise HTTPException(400, detail="文件夹中未找到支持的图片文件")

        # 初始化OCR实例
        ocr_instance = PaddleOCR(
            use_angle_cls=config.enable_angle_cls,
            use_gpu=config.use_gpu,
            #det_model_dir='./paddle_models/ch_PP-OCRv4_det_server_infer',  # 检测模型路径
            #rec_model_dir='./paddle_models/PP-OCRv4_server_rec_doc_infer',  # 识别模型路径
        )

        results = {}
        success_count = 0
        for filename in image_files:
            try:
                filepath = os.path.join(folder_path, filename)
                with open(filepath, 'rb') as f:
                    contents = f.read()
                results[filename] = await process_image(contents, ocr_instance)
                success_count += 1
            except Exception as e:
                results[filename] = {"error": str(e)}
                logger.error(f"文件 {filename} 处理失败: {str(e)}")

        return {
            "success": True,
            "processed_count": len(image_files),
            "success_count": success_count,
            "failed_count": len(image_files) - success_count,
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理异常: {str(e)}")
        raise HTTPException(500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)