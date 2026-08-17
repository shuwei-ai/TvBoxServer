export type UserRole = 'USER' | 'ADMIN'

export interface UserInfo {
  id: string
  username: string
  role: UserRole
  status: number // 1: active, 0: disabled
  created_at?: string
  last_login?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  invite_code?: string
}
