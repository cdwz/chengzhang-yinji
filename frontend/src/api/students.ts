// 学生管理相关API
import { http } from '@/utils/request'
import type { Student, StudentListResponse, StudyGroup, MessageResponse } from './types'

// 获取学生列表
export function getStudents(params: { class_id?: string; grade_id?: string; keyword?: string; page?: number; page_size?: number }) {
  return http.get<StudentListResponse>('/students', params)
}

// 创建学生
export function createStudent(data: { class_id: string; name: string; gender?: string; student_number?: string }) {
  return http.post<Student>('/students', data)
}

// 批量导入学生
export function importStudents(formData: FormData) {
  return http.upload<MessageResponse>('/students/import', formData)
}

// 获取学生详情
export function getStudent(id: string) {
  return http.get<Student>(`/students/${id}`)
}

// 编辑学生
export function updateStudent(id: string, data: { name?: string; student_number?: string; study_group_id?: string; status?: string }) {
  return http.put<Student>(`/students/${id}`, data)
}

// 转班
export function transferStudent(id: string, targetClassId: string) {
  return http.put<MessageResponse>(`/students/${id}/transfer`, { target_class_id: targetClassId })
}

// 删除学生
export function deleteStudent(id: string) {
  return http.delete<MessageResponse>(`/students/${id}`)
}

// ==================== 学习小组 ====================

// 获取班级的学习小组列表
export function getStudyGroups(classId: string) {
  return http.get<StudyGroup[]>('/students/groups', { class_id: classId })
}

// 创建学习小组
export function createStudyGroup(data: { class_id: string; name: string }) {
  return http.post<StudyGroup>('/students/groups', data)
}

// 将学生添加到学习小组
export function addStudentToGroup(groupId: string, studentId: string) {
  const formData = new FormData()
  formData.append('student_id', studentId)
  return http.upload<MessageResponse>(`/students/groups/${groupId}/members`, formData)
}

// 将学生从学习小组移除
export function removeStudentFromGroup(groupId: string, studentId: string) {
  return http.delete<MessageResponse>(`/students/groups/${groupId}/members/${studentId}`)
}

// 删除学习小组
export function deleteStudyGroup(id: string) {
  return http.delete<MessageResponse>(`/students/groups/${id}`)
}
