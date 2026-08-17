import { httpGet, httpPost } from '@/utils/request'
import type { AuthResponse, LoginParams, RegisterParams, UserInfo } from '@/types'

export function loginApi(params: LoginParams): Promise<AuthResponse> {
  return httpPost<AuthResponse>('/api/v1/auth/login', params)
}

export function registerApi(params: RegisterParams): Promise<AuthResponse> {
  return httpPost<AuthResponse>('/api/v1/auth/register', params)
}

export function getMeApi(): Promise<{ user: UserInfo }> {
  return httpGet<{ user: UserInfo }>('/api/v1/auth/me')
}
