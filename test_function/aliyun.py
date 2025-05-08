from alibabacloud_green20220302.client import Client
from alibabacloud_green20220302 import models
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_tea_util import models as util_models
import json
import uuid
import oss2
import time

# 服务是否部署在vpc上
is_vpc = False
# 文件上传token endpoint->token
token_dict = dict()
# 上传文件客户端
bucket = None


def create_client(access_key_id, access_key_secret, endpoint):
    config = Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint=endpoint
    )
    return Client(config)


def create_oss_bucket(is_vpc, upload_token):
    global token_dict
    global bucket
    auth = oss2.StsAuth(upload_token.access_key_id, upload_token.access_key_secret, upload_token.security_token)

    if (is_vpc):
        end_point = upload_token.oss_internal_end_point
    else:
        end_point = upload_token.oss_internet_end_point
    bucket = oss2.Bucket(auth, end_point, upload_token.bucket_name)


def upload_file(file_name, upload_token):
    create_oss_bucket(is_vpc, upload_token)
    object_name = upload_token.file_name_prefix + str(uuid.uuid1()) + '.' + file_name.split('.')[-1]
    bucket.put_object_from_file(object_name, file_name)
    return object_name


def image_detection(image_path):
    # 阿里云账号AccessKey
    access_key_id = 'LTAI5tSStwTSk68oCK3Aebaw'
    access_key_secret = '9wNLiaxKOh6Uxf2faCBA9nRsUK7x9v'
    endpoint = 'green-cip.cn-shanghai.aliyuncs.com'

    # 创建客户端
    client = create_client(access_key_id, access_key_secret, endpoint)
    runtime = util_models.RuntimeOptions()

    # 获取文件上传token
    upload_token = token_dict.setdefault(endpoint, None)
    if (upload_token is None) or int(upload_token.expiration) <= int(time.time()):
        response = client.describe_upload_token()
        upload_token = response.body.data
        token_dict[endpoint] = upload_token

    # 上传文件
    object_name = upload_file(image_path, upload_token)

    # 检测参数构造
    service_parameters = {
        'ossBucketName': upload_token.bucket_name,
        'ossObjectName': object_name,
        'dataId': str(uuid.uuid1())
    }

    image_moderation_request = models.ImageModerationRequest(
        service='baselineCheck',
        service_parameters=json.dumps(service_parameters)
    )

    try:
        response = client.image_moderation_with_options(image_moderation_request, runtime)

        # 自动路由
        if response is not None:
            if UtilClient.equal_number(500, response.status_code) or (
                    response.body is not None and 200 != response.body.code):
                # 区域切换到cn-beijing
                endpoint = 'green-cip.cn-beijing.aliyuncs.com'
                client = create_client(access_key_id, access_key_secret, endpoint)
                response = client.image_moderation_with_options(image_moderation_request, runtime)

            if response.status_code == 200:
                result = response.body
                if result.code == 200:
                    return result.data
                else:
                    return f"Error: {result.message}"
            else:
                return f"API request failed with status: {response.status_code}"
    except Exception as err:
        return f"Error occurred: {str(err)}"

    return "No result returned"