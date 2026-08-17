import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getMeApi } from '@/api/auth'
import { storage } from '@/utils/storage'
import type { LoginParams, RegisterParams, UserInfo, UserRole } from '@/types'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(storage.getToken())
  const userInfo = ref<UserInfo | null>(storage.getUser<UserInfo>())

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'ADMIN')
  const username = computed(() => userInfo.value?.username || '')
  const role = computed<UserRole>(() => userInfo.value?.role || 'USER')

  async function login(params: LoginParams) {
    const res = await loginApi(params)
    token.value = res.access_token
    userInfo.value = res.user
    storage.setToken(res.access_token)
    storage.setUser(res.user)
    return res
  }

  async function register(params: RegisterParams) {
    const res = await registerApi(params)
    token.value = res.access_token
    userInfo.value = res.user
    storage.setToken(res.access_token)
    storage.setUser(res.user)
    return res
  }

  async function fetchUserInfo() {
    if (!token.value) return null
    try {
      const res = await getMeApi()
      userInfo.value = res.user
      storage.setUser(res.user)
      return res.user
    } catch (err) {
      logout()
      throw err
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    storage.clearAuth()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    username,
    role,
    login,
    register,
    fetchUserInfo,
    logout
  }
})
