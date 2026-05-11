"""
消息通知 API
站内消息、系统通知、任务提醒
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import Message, User, TaskSubmission, Student

router = APIRouter(prefix="/messages", tags=["消息通知"])


# ============ Schemas ============

class SendMessageRequest(BaseModel):
    """发送消息请求"""
    receiver_id: UUID
    title: str
    content: str


class MessageResponse(BaseModel):
    """消息响应"""
    id: UUID
    sender_id: Optional[UUID]
    sender_name: Optional[str]
    receiver_id: UUID
    title: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """消息列表响应"""
    items: List[MessageResponse]
    total: int
    unread_count: int


# ============ WebSocket 连接管理 ============

class ConnectionManager:
    """WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)


manager = ConnectionManager()


# ============ API 端点 ============

@router.post("", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息
    """
    # 验证接收者存在
    result = await db.execute(
        select(User).where(User.id == request.receiver_id)
    )
    receiver = result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接收者不存在"
        )
    
    # 创建消息
    message = Message(
        sender_id=current_user.id,
        receiver_id=request.receiver_id,
        title=request.title,
        content=request.content,
        is_read=False
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # 尝试 WebSocket 推送
    await manager.send_personal_message(
        str(request.receiver_id),
        {
            "type": "new_message",
            "data": {
                "id": str(message.id),
                "title": message.title,
                "content": message.content,
                "sender_name": current_user.name,
                "created_at": message.created_at.isoformat()
            }
        }
    )
    
    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=current_user.name,
        receiver_id=message.receiver_id,
        title=message.title,
        content=message.content,
        is_read=message.is_read,
        created_at=message.created_at
    )


@router.get("", response_model=MessageListResponse)
async def get_messages(
    is_read: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取消息列表
    """
    # 构建查询
    query = select(Message).where(Message.receiver_id == current_user.id)
    count_query = select(func.count(Message.id)).where(Message.receiver_id == current_user.id)
    
    if is_read is not None:
        query = query.where(Message.is_read == is_read)
        count_query = count_query.where(Message.is_read == is_read)
    
    # 排序和分页
    query = query.order_by(Message.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 执行查询
    result = await db.execute(query)
    messages = result.scalars().all()
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 获取未读数量
    unread_result = await db.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.receiver_id == current_user.id,
                Message.is_read == False
            )
        )
    )
    unread_count = unread_result.scalar()
    
    # 获取发送者信息
    items = []
    for msg in messages:
        sender_name = None
        if msg.sender_id:
            sender_result = await db.execute(
                select(User).where(User.id == msg.sender_id)
            )
            sender = sender_result.scalar_one_or_none()
            sender_name = sender.name if sender else "系统"
        
        items.append(MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_name=sender_name,
            receiver_id=msg.receiver_id,
            title=msg.title,
            content=msg.content,
            is_read=msg.is_read,
            created_at=msg.created_at
        ))
    
    return MessageListResponse(
        items=items,
        total=total,
        unread_count=unread_count
    )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取未读消息数量
    """
    result = await db.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.receiver_id == current_user.id,
                Message.is_read == False
            )
        )
    )
    count = result.scalar()
    
    return {"unread_count": count}


@router.put("/{message_id}/read")
async def mark_message_read(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    标记消息已读
    """
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    if message.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作"
        )
    
    message.is_read = True
    await db.commit()
    
    return {"message": "已标记为已读"}


@router.put("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    标记所有消息已读
    """
    result = await db.execute(
        select(Message).where(
            and_(
                Message.receiver_id == current_user.id,
                Message.is_read == False
            )
        )
    )
    messages = result.scalars().all()
    
    for msg in messages:
        msg.is_read = True
    
    await db.commit()
    
    return {"message": "已全部标记为已读", "count": len(messages)}


@router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除消息
    """
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    if message.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作"
        )
    
    await db.delete(message)
    await db.commit()
    
    return {"message": "消息已删除"}


# ============ WebSocket 端点 ============

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket 连接端点
    用于实时推送消息
    """
    await manager.connect(user_id, websocket)
    try:
        while True:
            # 保持连接，等待客户端心跳
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(user_id)


# ============ 内部服务函数 ============

async def send_system_message(
    db: AsyncSession,
    receiver_id: UUID,
    title: str,
    content: str
):
    """
    发送系统消息（内部调用）
    """
    message = Message(
        sender_id=None,  # 系统消息
        receiver_id=receiver_id,
        title=title,
        content=content,
        is_read=False
    )
    db.add(message)
    await db.commit()
    
    # WebSocket 推送
    await manager.send_personal_message(
        str(receiver_id),
        {
            "type": "system_message",
            "data": {
                "id": str(message.id),
                "title": title,
                "content": content,
                "sender_name": "系统",
                "created_at": message.created_at.isoformat()
            }
        }
    )
    
    return message


async def send_task_reminder(
    db: AsyncSession,
    parent_id: UUID,
    task_title: str,
    student_name: str
):
    """
    发送任务提醒
    """
    await send_system_message(
        db=db,
        receiver_id=parent_id,
        title="任务提醒",
        content=f"您的孩子 {student_name} 有新的学习任务：{task_title}，请及时查看并协助完成。"
    )


async def send_evaluation_notice(
    db: AsyncSession,
    parent_id: UUID,
    student_name: str,
    dimension_name: str
):
    """
    发送评价通知
    """
    await send_system_message(
        db=db,
        receiver_id=parent_id,
        title="评价更新",
        content=f"您的孩子 {student_name} 获得了新的评价：{dimension_name}，请查看详情。"
    )
