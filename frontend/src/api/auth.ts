import { http } from '@/utils/request'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/api/types'

export const authApi = {
  /**
   * 发送验证码
   */
  sendCode(phone: string) {
    return http.get<{ message: string }>(`/auth/send-code`, { params: { phone } })
  },

  /**
   * 用户注册
   */
  register(data: RegisterRequest) {
    return http.post<TokenResponse>('/auth/register', data)
  },

  /**
   * 用户登录
   */
  login(data: LoginRequest) {
    return http.post<TokenResponse>('/auth/login', data)
  },

  /**
   * 刷新令牌
   */
  refresh(refreshToken: string) {
    return http.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
  },

  /**
   * 获取当前用户信息
   */
  getMe() {
    return http.get<User>('/auth/me')
  }
}
