// 消息通知 API

import { http } from '@/utils/request'
import type { MessageResponse } from './types'

export interface Message {
  id: string
  sender_id?: string
  sender_name?: string
  receiver_id: string
  title: string
  content: string
  is_read: boolean
  created_at: string
}

export interface MessageListResponse {
  items: Message[]
  total: number
  unread_count: number
}

export interface SendMessageRequest {
  receiver_id: string
  title: string
  content: string
}

// 获取消息列表
export async function getMessages(params?: {
  is_read?: boolean
  page?: number
  page_size?: number
}): Promise<MessageListResponse> {
  return http.get<MessageListResponse>('/messages', params)
}

// 获取未读数量
export async function getUnreadCount(): Promise<{ unread_count: number }> {
  return http.get<{ unread_count: number }>('/messages/unread-count')
}

// 发送消息
export async function sendMessage(payload: SendMessageRequest): Promise<Message> {
  return http.post<Message>('/messages', payload)
}

// 标记已读
export async function markMessageRead(messageId: string): Promise<MessageResponse> {
  return http.put<MessageResponse>(`/messages/${messageId}/read`)
}

// 全部标记已读
export async function markAllRead(): Promise<MessageResponse> {
  return http.put<MessageResponse>('/messages/read-all')
}

// 删除消息
export async function deleteMessage(messageId: string): Promise<MessageResponse> {
  return http.delete<MessageResponse>(`/messages/${messageId}`)
}
