// 学校相关API
import { http } from '@/utils/request'
import type { School, Grade, Class } from './types'

// 类型导出
export type { Class as ClassResponse }

// 获取学校详情
export function getSchool(id: string) {
  return http.get<School>(`/schools/${id}`)
}

// 创建学校
export function createSchool(data: { name: string; province_code?: string; city_code?: string; district_code?: string; address?: string }) {
  return http.post<School>('/schools', data)
}

// 搜索学校
export function searchSchools(keyword: string, province_code?: string) {
  return http.get<School[]>('/schools/search', { keyword, province_code })
}

// 获取年级列表
export function getGrades(schoolId: string) {
  return http.get<Grade[]>(`/schools/${schoolId}/grades`)
}

// 创建年级
export function createGrade(schoolId: string, data: { name: string; year: number }) {
  return http.post<Grade>(`/schools/${schoolId}/grades`, data)
}

// 获取班级列表
export function getClasses(gradeId?: string) {
  return http.get<Class[]>('/schools/classes', gradeId ? { grade_id: gradeId } : {})
}

// 创建班级
export function createClass(data: { grade_id: string; name: string }) {
  return http.post<Class>('/schools/classes', data)
}

// 获取班级详情
export function getClass(id: string) {
  return http.get<Class>(`/schools/classes/${id}`)
}

// 别名
export const getClassDetail = getClass
