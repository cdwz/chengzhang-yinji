// 成就系统 API

import { http } from '@/utils/request'

export interface Achievement {
  id: string
  achievement_type: string
  achievement_name: string
  achievement_description: string
  achievement_icon: string
  achievement_data?: Record<string, any>
  earned_at: string
}

export interface AchievementType {
  type: string
  name: string
  description: string
  icon: string
  condition: Record<string, number>
}

export interface AchievementTypeStatus {
  type: string
  name: string
  description: string
  icon: string
  earned: boolean
  earned_at?: string
}

export interface AchievementStats {
  total_achievements: number
  recent_achievements: Achievement[]
  all_types: AchievementTypeStatus[]
}

// 获取所有成就类型
export async function getAchievementTypes(): Promise<{ types: AchievementType[] }> {
  return http.get<{ types: AchievementType[] }>('/achievements/types')
}

// 获取学生成就
export async function getStudentAchievements(studentId: string): Promise<AchievementStats> {
  return http.get<AchievementStats>(`/achievements/student/${studentId}`)
}

// 检查成就触发
export async function checkAchievements(studentId: string): Promise<{
  new_achievements: number
  achievements: any[]
}> {
  return http.post<{ new_achievements: number; achievements: any[] }>(`/achievements/check/${studentId}`)
}
