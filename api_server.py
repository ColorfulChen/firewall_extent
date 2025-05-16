from flask import Flask, request, jsonify, Response
from flask_compress import Compress
from tools.google import (
    filter_vet_response,
    google_search_filter,
    google_search_page_filter,
    google_search_video_page_filter,
)
from test_function.paddle_ocr import image_detection_paddle_ocr
import base64
import functools
import json
import time
from werkzeug.middleware.proxy_fix import ProxyFix
import traceback

# 性能优化: 创建一个更高效的JSON编码器
class FastJSONResponse(Response):
    """更高效的JSON响应处理"""
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, dict):
            response = json.dumps(response, ensure_ascii=False).encode('utf-8')
            return Response(response, mimetype='application/json; charset=utf-8')
        return super(FastJSONResponse, cls).force_type(response, environ)

# 创建Flask应用并启用压缩
app = Flask(__name__)
app.response_class = FastJSONResponse
app.wsgi_app = ProxyFix(app.wsgi_app)
Compress(app)  # 启用响应压缩

# 简单的内存缓存实现
cache = {}
CACHE_TIMEOUT = 300  # 缓存超时时间(秒)

def cache_result(func):
    """缓存装饰器，用于缓存API响应结果"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 生成缓存键
        request_data = request.get_json()
        cache_key = f"{func.__name__}:{hash(json.dumps(request_data, sort_keys=True))}"
        
        # 检查缓存
        current_time = time.time()
        if cache_key in cache:
            cached_result, timestamp = cache[cache_key]
            if current_time - timestamp < CACHE_TIMEOUT:
                return cached_result
        
        # 执行原始函数
        result = func(*args, **kwargs)
        
        # 缓存结果
        cache[cache_key] = (result, current_time)
        
        # 清理过期缓存
        expired_keys = [k for k, (_, t) in cache.items() if current_time - t > CACHE_TIMEOUT]
        for key in expired_keys:
            cache.pop(key, None)
            
        return result
    return wrapper

@app.route('/filter_vet_response', methods=['POST'])
@cache_result
def api_filter_vet_response():
    """
    API for filter_vet_response
    """
    try:
        data = request.get_json()
        response = data.get('response')
        filter_words = data.get('filter_words', [])
        result = filter_vet_response(response, filter_words)
        return {'filtered_response': result.decode('utf-8') if result else None}
    except Exception as e:
        app.logger.error(f"Error in filter_vet_response: {str(e)}\n{traceback.format_exc()}")
        return {'error': str(e)}, 500

@app.route('/google_search_filter', methods=['POST'])
@cache_result
def api_google_search_filter():
    """
    API for google_search_filter
    """
    try:
        data = request.get_json()
        response = data.get('response')
        filter_words = data.get('filter_words', [])
        result = google_search_filter(response, filter_words)
        return {'filtered_response': result.decode('utf-8') if result else None}
    except Exception as e:
        app.logger.error(f"Error in google_search_filter: {str(e)}\n{traceback.format_exc()}")
        return {'error': str(e)}, 500

@app.route('/google_search_page_filter', methods=['POST'])
@cache_result
def api_google_search_page_filter():
    """
    API for google_search_page_filter
    """
    try:
        data = request.get_json()
        response = data.get('response')
        filter_words = data.get('filter_words', [])
        result = google_search_page_filter(response, filter_words)
        return {'filtered_response': result.decode('utf-8') if result else None}
    except Exception as e:
        app.logger.error(f"Error in google_search_page_filter: {str(e)}\n{traceback.format_exc()}")
        return {'error': str(e)}, 500

@app.route('/google_search_video_page_filter', methods=['POST'])
@cache_result
def api_google_search_video_page_filter():
    """
    API for google_search_video_page_filter
    """
    try:
        data = request.get_json()
        response = data.get('response')
        filter_words = data.get('filter_words', [])
        result = google_search_video_page_filter(response, filter_words)
        return {'filtered_response': result.decode('utf-8') if result else None}
    except Exception as e:
        app.logger.error(f"Error in google_search_video_page_filter: {str(e)}\n{traceback.format_exc()}")
        return {'error': str(e)}, 500

@app.route('/image_detection_paddle_ocr', methods=['POST'])
def api_image_detection_paddle_ocr():
    """
    API for google_search_video_page_filter
    """
    try:
        data = request.get_json()
        image = data.get('image')
        image_bytes = base64.b64decode(image)
        filter_words = data.get('filter_words', [])
        result = image_detection_paddle_ocr(image_bytes, filter_words=filter_words)
        return result
    except Exception as e:
        app.logger.error(f"Error in image_detection_paddle_ocr: {str(e)}\n{traceback.format_exc()}")
        return {'error': str(e)}, 500

@app.route('/image_detection_paddle_ocr_local_file', methods=['POST'])
def api_image_detection_paddle_ocr_local_file():
    """
    API for google_search_video_page_filter
    """
    data = request.get_json()
    image = data.get('image')
    filter_words = data.get('filter_words', [])
    result = image_detection_paddle_ocr(image, filter_words=filter_words)
    return result

if __name__ == '__main__':
    # 开发模式
    app.run(debug=True, port=5000)
    
    # 生产模式 - 使用 gunicorn
    # 启动命令: gunicorn --worker-class=gevent --workers=4 --bind=0.0.0.0:5000 api_server:app