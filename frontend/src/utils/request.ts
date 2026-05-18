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

// 重试配置
const RETRY_CONFIG = {
  maxRetries: 5,
  retryDelay: 5 * 60 * 1000, // 5分钟
  retryStatusCodes: [429, 503, 502, 504], // 需要重试的状态码
}

// 重试状态管理
const retryState = new Map<string, { count: number; timer: ReturnType<typeof setTimeout> | null }>()

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
  async (error) => {
    const { response, config } = error
    const requestKey = `${config.method}-${config.url}`
    
    if (response) {
      const status = response.status
      
      switch (status) {
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
      
      // 429 或服务不可用，自动重试
      if (RETRY_CONFIG.retryStatusCodes.includes(status)) {
        return handleRetry(config, requestKey)
      }
    } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      // 超时错误，自动重试
      return handleRetry(config, requestKey)
    }
    
    return Promise.reject(error)
  }
)

// 处理重试逻辑
async function handleRetry(config: AxiosRequestConfig, requestKey: string): Promise<any> {
  const state = retryState.get(requestKey) || { count: 0, timer: null }
  
  if (state.count >= RETRY_CONFIG.maxRetries) {
    // 超过最大重试次数
    retryState.delete(requestKey)
    return Promise.reject(new Error('请求失败，已达到最大重试次数'))
  }
  
  state.count++
  retryState.set(requestKey, state)
  
  // 显示重试提示
  console.log(`请求失败，${RETRY_CONFIG.retryDelay / 60000}分钟后自动重试 (${state.count}/${RETRY_CONFIG.maxRetries})`)
  
  // 等待重试延迟
  await new Promise(resolve => {
    const timer = setTimeout(resolve, RETRY_CONFIG.retryDelay)
    state.timer = timer
  })
  
  // 重新发起请求
  return request.request(config)
}

// 获取重试状态（用于UI显示）
export function getRetryStatus(requestKey: string): { count: number; maxRetries: number } | null {
  const state = retryState.get(requestKey)
  if (!state) return null
  return { count: state.count, maxRetries: RETRY_CONFIG.maxRetries }
}

// 取消重试
export function cancelRetry(requestKey: string): void {
  const state = retryState.get(requestKey)
  if (state?.timer) {
    clearTimeout(state.timer)
  }
  retryState.delete(requestKey)
}

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
  
  upload<T = any>(url: string, file: File | FormData, config?: AxiosRequestConfig): Promise<T> {
    const formData = file instanceof FormData ? file : new FormData()
    if (file instanceof File) {
      formData.append('file', file)
    }
    return request.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

export default request
