import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/api/types'

const TOKEN_KEY = 'czyj_token'
const REFRESH_TOKEN_KEY = 'czyj_refresh_token'
const USER_KEY = 'czyj_user'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))
  const user = ref<User | null>(null)
  
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const role = computed(() => user.value?.role || '')
  
  function setTokens(accessToken: string, refresh: string) {
    token.value = accessToken
    refreshToken.value = refresh
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  }
  
  function setUser(userData: User) {
    user.value = userData
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
  }
  
  function logout() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
  
  function initFromStorage() {
    const savedUser = localStorage.getItem(USER_KEY)
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch {
        logout()
      }
    }
  }
  
  return {
    token,
    refreshToken,
    user,
    isLoggedIn,
    role,
    setTokens,
    setUser,
    logout,
    initFromStorage
  }
})
