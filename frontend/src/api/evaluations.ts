// 评价管理相关API
import { http } from '@/utils/request'
import type { EvaluationDimension, EvaluationRecord, MessageResponse } from './types'

// ==================== 评价维度 ====================

// 获取评价维度列表
export function getDimensions(classId: string) {
  return http.get<EvaluationDimension[]>('/evaluations/dimensions', { class_id: classId })
}

// 创建评价维度
export function createDimension(data: {
  class_id: string
  name: string
  subject?: string
  type: 'star' | 'grade' | 'boolean' | 'score' | 'text'
}) {
  return http.post<EvaluationDimension>('/evaluations/dimensions', data)
}

// 更新评价维度
export function updateDimension(id: string, data: Partial<{
  name: string
  subject: string
  type: string
  sort_order: number
  is_active: boolean
}>) {
  return http.put<EvaluationDimension>(`/evaluations/dimensions/${id}`, data)
}

// 删除评价维度
export function deleteDimension(id: string) {
  return http.delete<MessageResponse>(`/evaluations/dimensions/${id}`)
}

// ==================== 评价记录 ====================

export interface EvaluationInput {
  dimension_id: string
  student_id: string
  record_date: string
  value: string
}

// 提交评价记录
export function saveEvaluation(data: EvaluationInput) {
  return http.post<MessageResponse>('/evaluations/records', data)
}

// 批量提交评价记录
export function saveBatchEvaluations(records: EvaluationInput[]) {
  return http.post<MessageResponse>('/evaluations/records/batch', { records })
}

// 获取评价记录列表
export function getEvaluations(params: {
  class_id: string
  dimension_id?: string
  student_id?: string
  start_date?: string
  end_date?: string
}) {
  return http.get<EvaluationRecord[]>('/evaluations/records', params)
}

// 获取家长端评价记录
export function getMyEvaluations(params: {
  student_id: string
  start_date?: string
  end_date?: string
}) {
  return http.get<EvaluationRecord[]>('/evaluations/my', params)
}
