import { DeviceItem } from './device'
import { UserInfo } from './user'

export interface AdminUserItem extends UserInfo {
  device_count: number
}

export interface AdminUsersResponse {
  users: AdminUserItem[]
}

export interface SystemConfig {
  allow_user_registration: boolean
  require_invite_code: boolean
  max_registered_users: number
  current_registered_users?: number
  max_devices_per_user: number
  max_invites_per_user: number
}

export interface GenerateAdminInvitesParams {
  count: number
}

export interface GenerateAdminInvitesResponse {
  codes: string[]
}

export type AdminDevicesResponse = DeviceItem[]
