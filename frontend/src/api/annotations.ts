// 教师批注 API

import { http } from '@/utils/request'

export interface AnnotationData {
  version: string
  objects: any[]
}

export interface Annotation {
  id: string
  image_id: string
  teacher_id: string
  teacher_name: string
  annotation_data: AnnotationData
  is_viewed: boolean
  is_example: boolean
  created_at: string
  updated_at?: string
}

export interface ImageAnnotationsResponse {
  image_id: string
  image_url: string
  annotations: Annotation[]
}

export interface CreateAnnotationRequest {
  image_id: string
  annotation_data: AnnotationData
}

// 创建批注
export async function createAnnotation(payload: CreateAnnotationRequest): Promise<Annotation> {
  return http.post<Annotation>('/annotations', payload)
}

// 获取图片的所有批注
export async function getImageAnnotations(imageId: string): Promise<ImageAnnotationsResponse> {
  return http.get<ImageAnnotationsResponse>(`/annotations/image/${imageId}`)
}

// 更新批注
export async function updateAnnotation(annotationId: string, annotationData: AnnotationData): Promise<Annotation> {
  return http.put<Annotation>(`/annotations/${annotationId}`, { annotation_data: annotationData })
}

// 删除批注
export async function deleteAnnotation(annotationId: string): Promise<{ message: string }> {
  return http.delete<{ message: string }>(`/annotations/${annotationId}`)
}

// 设置/取消典型例
export async function setAsExample(annotationId: string): Promise<{ message: string; is_example: boolean }> {
  return http.post<{ message: string; is_example: boolean }>(`/annotations/${annotationId}/set-example`)
}

// 标记已查看
export async function markAnnotationViewed(annotationId: string): Promise<{ message: string }> {
  return http.post<{ message: string }>(`/annotations/${annotationId}/mark-viewed`)
}

// 获取班级典型例
export async function getClassExamples(classId: string): Promise<{ examples: any[] }> {
  return http.get<{ examples: any[] }>(`/annotations/examples/${classId}`)
}
