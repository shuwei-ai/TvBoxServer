export interface ApiResponse<T = any> {
  code?: number
  message?: string
  detail?: string
  data: T
}

export interface ApiKeyInfo {
  id?: string
  user_id?: string
  key_prefix: string
  api_key?: string
  status: 'ACTIVE' | 'REVOKED' | string
  created_at?: string
  updated_at?: string
}
