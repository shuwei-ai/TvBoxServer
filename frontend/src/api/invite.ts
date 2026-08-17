import { httpGet, httpPost } from '@/utils/request'
import type { GenerateInviteResponse, MyInvitesResponse } from '@/types'

export function getMyInvitesApi(): Promise<MyInvitesResponse> {
  return httpGet<MyInvitesResponse>('/api/v1/invite/my-codes')
}

export function generateInviteApi(): Promise<GenerateInviteResponse> {
  return httpPost<GenerateInviteResponse>('/api/v1/invite/generate')
}
