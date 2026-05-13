"""
MinIO 文件存储服务
"""
import hashlib
import uuid
import io
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from config.settings import settings

_client = None
BUCKET = "invoices"


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
    return _client


def ensure_bucket():
    client = get_client()
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)


def upload_file(file_bytes: bytes, original_filename: str) -> tuple[str, str, str]:
    """
    上传文件到 MinIO
    返回: (file_id, presigned_url, md5_hash)
    """
    ensure_bucket()
    client = get_client()

    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"
    file_id = f"{uuid.uuid4().hex}.{ext}"
    file_hash = hashlib.md5(file_bytes).hexdigest()

    # 上传
    client.put_object(BUCKET, file_id, io.BytesIO(file_bytes), len(file_bytes))

    # 生成 7 天有效的预签名访问 URL
    url = client.presigned_get_object(BUCKET, file_id, expires=timedelta(days=7))
    return file_id, url, file_hash


def get_presigned_url(file_id: str, expires_days: int = 1) -> str:
    """获取文件的临时访问 URL"""
    client = get_client()
    return client.presigned_get_object(BUCKET, file_id, expires=timedelta(days=expires_days))
