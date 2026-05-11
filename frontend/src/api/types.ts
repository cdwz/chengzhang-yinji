// API 类型定义

export interface User {
  id: string
  phone: string
  name: string
  role: 'super_admin' | 'school_admin' | 'teacher' | 'parent'
  avatar_url?: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  phone: string
  password: string
}

export interface RegisterRequest {
  phone: string
  password: string
  name: string
  role: 'teacher' | 'parent'
  verification_code: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface School {
  id: string
  name: string
  province_code?: string
  city_code?: string
  district_code?: string
  address?: string
  is_verified: boolean
  created_at: string
}

export interface Grade {
  id: string
  name: string
  year: number
  sort_order: number
  created_at: string
}

export interface Class {
  id: string
  name: string
  invite_code: string
  grade: Grade
  student_count: number
}

export interface Student {
  id: string
  name: string
  gender: string
  student_number?: string
  class_id: string
  study_group_id?: string
  created_at: string
}

export interface StudyGroup {
  id: string
  name: string
  class_id: string
  sort_order: number
  students: Student[]
}

export interface StudentListResponse {
  total: number
  page: number
  page_size: number
  items: Student[]
}

export interface Task {
  id: string
  subject: string
  title: string
  content?: string
  suggested_duration?: number
  task_date: string
  is_optional: boolean
  group_name?: string
  created_at: string
}

export interface SubmissionImage {
  id: string
  submission_id: string
  image_url: string
  thumbnail_url?: string
  sort_order: number
  created_at: string
}

export interface TaskSubmission {
  id: string
  task_id: string
  student_id: string
  student?: Student
  feedback?: string
  submitted_at: string
  images: SubmissionImage[]
  annotations?: any[]
}

export interface EvaluationDimension {
  id: string
  name: string
  subject?: string
  type: 'star' | 'grade' | 'boolean' | 'score' | 'text'
  sort_order: number
  is_active: boolean
}

export interface EvaluationRecord {
  id: string
  dimension_id: string
  student_id: string
  record_date: string
  value: string
  updated_at: string
}

export interface MessageResponse {
  message: string
}

export interface ErrorResponse {
  detail: string
  errors?: Array<{
    field: string
    message: string
  }>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
