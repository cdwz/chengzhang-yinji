"""
成长印记 - MinIO 存储模块
"""
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
import io

from app.core.config import settings

# MinIO 客户端实例
_minio_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """获取 MinIO 客户端"""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
    return _minio_client


async def ensure_bucket():
    """确保存储桶存在"""
    client = get_minio_client()
    try:
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
    except S3Error as e:
        print(f"MinIO 错误: {e}")


async def upload_file(
    object_name: str,
    file_data: BinaryIO,
    content_type: str = "application/octet-stream",
    length: Optional[int] = None
) -> str:
    """上传文件到 MinIO"""
    client = get_minio_client()
    await ensure_bucket()
    
    if length is None:
        # 如果没有指定长度，读取所有数据
        data = file_data.read()
        length = len(data)
        file_data = io.BytesIO(data)
    
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        file_data,
        length,
        content_type=content_type
    )
    
    return object_name


async def get_file_url(object_name: str, expire_hours: int = 1) -> str:
    """获取文件签名URL"""
    client = get_minio_client()
    url = client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(hours=expire_hours)
    )
    return url


async def delete_file(object_name: str):
    """删除文件"""
    client = get_minio_client()
    client.remove_object(settings.MINIO_BUCKET, object_name)
