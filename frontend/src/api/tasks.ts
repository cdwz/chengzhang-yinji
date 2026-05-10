// 任务管理相关API
import { http } from '@/utils/request'
import type { Task, TaskSubmission, MessageResponse } from './types'

// ==================== 任务 ====================

// 获取任务列表
export function getTasks(params?: { class_id?: string; task_date?: string; student_id?: string }) {
  return http.get<Task[]>('/tasks', params)
}

// 获取任务详情
export function getTask(id: string) {
  return http.get<Task>(`/tasks/${id}`)
}

// 创建任务（教师端）
export function createTask(data: {
  class_id: string
  subject: string
  title: string
  content?: string
  suggested_duration?: number
  task_date: string
  group_id?: string
}) {
  return http.post<Task>('/tasks', data)
}

// 删除任务
export function deleteTask(id: string) {
  return http.delete<MessageResponse>(`/tasks/${id}`)
}

// ==================== 任务提交 ====================

// 提交任务记录（家长端）
export function submitTask(taskId: string, data: { feedback?: string }) {
  return http.post<TaskSubmission>(`/tasks/${taskId}/submit`, data)
}

// 上传提交图片
export function uploadSubmissionImage(submissionId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return http.upload<MessageResponse>(`/tasks/submissions/${submissionId}/images`, formData)
}

// 获取提交列表（教师端）
export function getSubmissions(params?: { task_id?: string; class_id?: string; date?: string }) {
  return http.get<TaskSubmission[]>('/tasks/submissions', params)
}

// ==================== 任务统计 ====================

export interface TaskStats {
  total: number
  submitted: number
  pending: number
  completionRate: number
  bySubject: Array<{
    subject: string
    count: number
    completionRate: number
  }>
  weeklyTrend: Array<{
    label: string
    count: number
    percentage: number
  }>
}

// 获取任务统计（教师端）
export function getTaskStats(classId?: string) {
  return http.get<TaskStats>('/tasks/stats', classId ? { class_id: classId } : {})
}
