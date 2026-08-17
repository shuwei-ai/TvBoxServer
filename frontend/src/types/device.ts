import { ApiKeyInfo } from './api'

export interface DeviceItem {
  id: string
  device_id: string
  device_name: string
  user_id: string
  owner_username?: string
  is_default?: boolean
  online?: boolean
  ip?: string
  last_seen?: string
  created_at?: string
  updated_at?: string
}

export interface DevicesResponse {
  devices: DeviceItem[]
  api_key: ApiKeyInfo | null
}

export interface BindDeviceParams {
  device_id: string
  device_name: string
}

export interface BindDeviceResponse {
  device: DeviceItem
  api_key?: string // generated on first device bind
}

export interface ResetApiKeyResponse {
  api_key: string
  prefix: string
  status: string
}
