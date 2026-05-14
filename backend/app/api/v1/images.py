"""
图片代理API - 解决域名转发后图片无法访问的问题
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.core.storage import get_minio_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["图片"])


@router.get("/{bucket}/{path:path}")
async def get_image(bucket: str, path: str):
    """
    图片代理接口 - 通过后端代理访问MinIO中的图片
    解决域名转发后无法直接访问内网MinIO的问题
    """
    try:
        client = get_minio_client()
        
        # 验证bucket是否允许
        if bucket not in [settings.MINIO_BUCKET, "czyj-files"]:
            raise HTTPException(status_code=403, detail="无权访问此存储桶")
        
        # 从MinIO获取文件
        response = client.get_object(bucket, path)
        data = response.read()
        
        # 获取content-type
        content_type = response.headers.get("Content-Type", "image/jpeg")
        
        return Response(
            content=data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",  # 缓存1天
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logger.error(f"获取图片失败: {bucket}/{path}, 错误: {e}")
        raise HTTPException(status_code=404, detail="图片不存在")
