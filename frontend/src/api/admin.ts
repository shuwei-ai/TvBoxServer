import { httpGet, httpPost, httpPut } from '@/utils/request'
import type {
  AdminDevicesResponse,
  AdminUsersResponse,
  GenerateAdminInvitesParams,
  GenerateAdminInvitesResponse,
  SystemConfig
} from '@/types'

export function getAdminUsersApi(): Promise<AdminUsersResponse> {
  return httpGet<AdminUsersResponse>('/api/v1/admin/users')
}

export function updateAdminUserStatusApi(userId: string, status: number): Promise<{ success: boolean }> {
  return httpPut<{ success: boolean }>(`/api/v1/admin/users/${userId}/status`, { status })
}

export function getAdminDevicesApi(): Promise<AdminDevicesResponse> {
  return httpGet<AdminDevicesResponse>('/api/v1/admin/devices')
}

export function getSystemConfigApi(): Promise<SystemConfig> {
  return httpGet<SystemConfig>('/api/v1/admin/system/config')
}

export function updateSystemConfigApi(config: SystemConfig): Promise<{ success: boolean }> {
  return httpPut<{ success: boolean }>('/api/v1/admin/system/config', config)
}

export function generateAdminInvitesApi(params: GenerateAdminInvitesParams): Promise<GenerateAdminInvitesResponse> {
  return httpPost<GenerateAdminInvitesResponse>('/api/v1/admin/invite/generate', params)
}
