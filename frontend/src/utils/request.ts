import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user'
import router from '@/router'

/** 将 MinIO 相对路径转换为代理URL */
export function getFileUrl(path: string | undefined | null): string {
  if (!path) return ''
  // 如果已经是完整URL，提取路径部分
  if (path.startsWith('http://') || path.startsWith('https://')) {
    // 从URL中提取路径，如 http://20.20.30.81:9002/czyj-files/submissions/xxx.jpg -> submissions/xxx.jpg
    const match = path.match(/\/czyj-files\/(.+)$/)
    if (match) {
      return `/api/images/czyj-files/${match[1]}`
    }
    return path
  }
  // 拼接代理API路径
  return `/api/images/czyj-files/${path}`
}

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const { response } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          // Token过期或无效
          const userStore = useUserStore()
          userStore.logout()
          router.push({ name: 'Login' })
          break
        case 403:
          console.error('无权限访问')
          break
        case 404:
          console.error('资源不存在')
          break
        case 422:
          // 验证错误，返回详细信息
          return Promise.reject(response.data)
        case 500:
          console.error('服务器错误')
          break
      }
    }
    
    return Promise.reject(error)
  }
)

// 请求方法封装
export const http = {
  get<T = any>(url: string, params?: Record<string, any>, config?: AxiosRequestConfig): Promise<T> {
    return request.get(url, { ...config, params })
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return request.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return request.put(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return request.delete(url, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return request.patch(url, data, config)
  },
  
  upload<T = any>(url: string, formData: FormData, onProgress?: (percent: number) => void): Promise<T> {
    return request.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      }
    })
  }
}

export default request
