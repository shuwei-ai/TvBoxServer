import { httpPost } from '@/utils/request'
import type { ResetApiKeyResponse } from '@/types'

export function resetApiKeyApi(): Promise<ResetApiKeyResponse> {
  return httpPost<ResetApiKeyResponse>('/api/v1/api-key/reset')
}
