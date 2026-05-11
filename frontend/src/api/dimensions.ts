// 评价维度管理API
import { http } from '@/utils/request'
import type { MessageResponse } from './types'

// 评价维度类型
export interface EvaluationDimension {
  id: string
  class_id: string
  name: string
  subject?: string
  type: 'star' | 'grade' | 'boolean' | 'score' | 'text'
  sort_order: number
  is_active: boolean
  created_at: string
}

export interface DimensionCreate {
  name: string
  type: 'star' | 'grade' | 'boolean' | 'score' | 'text'
  subject?: string
}

export interface DimensionUpdate {
  name?: string
  type?: 'star' | 'grade' | 'boolean' | 'score' | 'text'
  subject?: string
  is_active?: boolean
  sort_order?: number
}

// 获取班级评价维度
export function getDimensions(classId: string) {
  return http.get<EvaluationDimension[]>(`/dimensions/class/${classId}`)
}

// 创建评价维度
export function createDimension(classId: string, data: DimensionCreate) {
  return http.post<EvaluationDimension>(`/dimensions/class/${classId}`, data)
}

// 更新评价维度
export function updateDimension(dimensionId: string, data: DimensionUpdate) {
  return http.patch<EvaluationDimension>(`/dimensions/${dimensionId}`, data)
}

// 删除评价维度
export function deleteDimension(dimensionId: string) {
  return http.delete<MessageResponse>(`/dimensions/${dimensionId}`)
}

// 批量更新维度排序
export function updateDimensionOrder(data: { dimensions: Array<{ id: string; sort_order: number }> }) {
  return http.patch<MessageResponse>('/dimensions/order', data)
}
