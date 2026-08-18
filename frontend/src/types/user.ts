export type UserRole = 'USER' | 'ADMIN'

export interface UserInfo {
  id: string
  username: string
  role: UserRole
  status: number // 1: active, 0: disabled
  openid?: string
  device_count?: number
  invite_generated_count?: number
  created_at?: string
  updated_at?: string
  last_login_at?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface WxSessionData {
  session_no: string
  scene: string
  qrcode: string
  expire_at: string
  app_code?: string
}

export interface WxStatusData {
  session_no: string
  scene?: string
  status: number // 1: waiting, 2: scanned, 3: authorized, 4: canceled, 6: consumed, 7: expired
  expire_at?: string
  auth_time?: string
  member_role?: number
}

export interface WxCompleteParams {
  session_no: string
  invite_code?: string
}
