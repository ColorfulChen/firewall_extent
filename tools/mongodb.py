import os
import urllib.parse
import re

from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# MongoDB 配置
MONGO_CONNECTION_STRING = os.environ.get("DATABASE_BASE_URL", "mongodb://localhost:27017/")
MONGO_DB_NAME = "google_filter_logs"

# 初始化MongoDB连接
try:
    mongo_client = MongoClient(MONGO_CONNECTION_STRING)
    db = mongo_client[MONGO_DB_NAME]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    collection = None

def get_collection_for_url(url):
    """根据URL生成有效的集合名称"""
    if not url:
        return "default_collection"

    try:
        # 提取URL中有意义的部分
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.replace('.', '_')
        path = parsed.path.replace('/', '_').strip('_') or 'root'
        query = parsed.query.replace('&', '_').replace('=', '_') or 'noquery'

        # 构建基础集合名
        base_name = f"page_{netloc}_{path}_{query}"

        # 确保名称符合MongoDB规则
        valid_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)

        # 截断过长的名称(限制为120字符)
        return valid_name[:120]
    except:
        return "invalid_url_collection"


def log_to_mongo(data, request_url=None):
    """将数据记录到MongoDB，按URL分集合存储"""
    if db is None:
        return None

    try:
        collection_name = get_collection_for_url(request_url)
        collection = db[collection_name]

        # 添加元数据
        data["timestamp"] = datetime.utcnow()
        if request_url:
            data["page_url"] = request_url

        # 创建索引(如果不存在)
        if "timestamp_1" not in collection.index_information():
            collection.create_index("timestamp")

        # 插入记录
        result = collection.insert_one(data)
        return result.inserted_id
    except Exception as e:
        print(f"Failed to log to MongoDB: {e}")
        return None


def cleanup_old_collections(days=30):
    """清理超过指定天数的旧集合"""
    if db is None:
        return

    cutoff = datetime.utcnow() - timedelta(days=days)
    for col_name in db.list_collection_names():
        if col_name.startswith('page_'):
            try:
                last_record = db[col_name].find_one(sort=[("timestamp", -1)])
                if last_record is None or last_record["timestamp"] < cutoff:
                    db[col_name].drop()
                    print(f"Dropped old collection: {col_name}")
            except Exception as e:
                print(f"Error checking collection {col_name}: {e}")
