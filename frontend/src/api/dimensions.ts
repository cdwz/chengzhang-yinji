// 评价维度 API
import { http } from '@/utils/request'
import type { EvaluationDimension } from './types'

export interface DimensionCreate {
  name: string
  type: 'star' | 'grade' | 'score' | 'ab_score' | 'boolean' | 'text'
  subject?: string
  config?: Record<string, any>
}

export interface DimensionUpdate {
  name?: string
  type?: string
  subject?: string
  config?: Record<string, any>
  is_active?: boolean
  sort_order?: number
}

// 获取班级维度列表
export async function getDimensions(classId: string): Promise<EvaluationDimension[]> {
  return http.get<EvaluationDimension[]>(`/dimensions/class/${classId}`)
}

// 创建维度
export async function createDimension(classId: string, data: DimensionCreate): Promise<EvaluationDimension> {
  return http.post<EvaluationDimension>(`/dimensions/class/${classId}`, data)
}

// 更新维度
export async function updateDimension(dimensionId: string, data: DimensionUpdate): Promise<EvaluationDimension> {
  return http.put<EvaluationDimension>(`/dimensions/${dimensionId}`, data)
}

// 删除维度
export async function deleteDimension(dimensionId: string): Promise<{ message: string }> {
  return http.delete<{ message: string }>(`/dimensions/${dimensionId}`)
}

// 更新排序
export async function updateDimensionOrder(dimensions: Array<{ id: string; sort_order: number }>): Promise<{ message: string }> {
  return http.put<{ message: string }>('/dimensions/order', { dimensions })
}
