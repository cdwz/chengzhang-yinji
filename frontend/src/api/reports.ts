// 报告导出 API

import { http } from '@/utils/request'

export interface ReportRequest {
  student_id: string
  start_date?: string
  end_date?: string
  include_tasks?: boolean
  include_evaluations?: boolean
}

export interface ClassReportRequest {
  class_id: string
  period: 'week' | 'month' | 'semester'
}

export interface TaskSummary {
  total_tasks: number
  completed_tasks: number
  completion_rate: number
  by_subject: Record<string, number>
}

export interface EvaluationSummary {
  total_evaluations: number
  dimensions_count: number
  average_scores: Record<string, number>
  recent_records: any[]
}

export interface ClassOverview {
  total_students: number
  active_students: number
  task_completion: number
  avg_duration: number
}

export interface TrendItem {
  label: string
  count: number
  percentage: number
}

export interface DistributionItem {
  level: string
  count: number
  percentage: number
  color: string
}

export interface SubjectStat {
  name: string
  task_count: number
  completion_rate: number
}

export interface StudentRanking {
  id: string
  name: string
  task_count: number
  rating: number
}

export interface ClassReportData {
  overview: ClassOverview
  trend: TrendItem[]
  distribution: DistributionItem[]
  subjects: SubjectStat[]
  ranking: StudentRanking[]
}

export interface StudentReport {
  student_name: string
  class_name: string
  period_start: string
  period_end: string
  generated_at: string
  task_summary?: TaskSummary
  evaluation_summary?: EvaluationSummary
}

export interface ReportResponse {
  format: string
  content: string
  filename: string
}

// 获取班级报告数据
export async function getClassReport(payload: ClassReportRequest): Promise<ClassReportData> {
  return http.post<ClassReportData>('/reports/class', payload)
}

// 预览报告
export async function previewReport(payload: ReportRequest): Promise<StudentReport> {
  return http.post<StudentReport>('/reports/preview', payload)
}

// 生成报告
export async function generateReport(payload: ReportRequest): Promise<ReportResponse> {
  return http.post<ReportResponse>('/reports/generate', payload)
}

// 导出CSV
export async function exportCsv(payload: ReportRequest): Promise<ReportResponse> {
  return http.post<ReportResponse>('/reports/export-csv', payload)
}

// 导出班级PDF报告
export async function exportClassPdf(payload: ClassReportRequest): Promise<Blob> {
  const response = await fetch('/api/reports/class/pdf', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify(payload)
  })
  
  if (!response.ok) {
    throw new Error('导出失败')
  }
  
  return response.blob()
}
