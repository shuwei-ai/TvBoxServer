import { httpGet, httpPost, httpDelete } from '@/utils/request'
import type { BindDeviceParams, BindDeviceResponse, DevicesResponse } from '@/types'

export function getDevicesApi(): Promise<DevicesResponse> {
  return httpGet<DevicesResponse>('/api/v1/devices')
}

export function bindDeviceApi(params: BindDeviceParams): Promise<BindDeviceResponse> {
  return httpPost<BindDeviceResponse>('/api/v1/devices/bind', params)
}

export function unbindDeviceApi(deviceIdOrDbId: string): Promise<{ success: boolean; message: string }> {
  return httpDelete<{ success: boolean; message: string }>(`/api/v1/devices/${deviceIdOrDbId}`)
}
