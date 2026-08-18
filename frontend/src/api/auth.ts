import { httpGet, httpPost } from '@/utils/request'
import type { AuthResponse, UserInfo, WxCompleteParams, WxSessionData, WxStatusData } from '@/types'

/**
 * 创建微信扫码登录会话
 */
export function createWxSessionApi(params?: { biz_state?: string; expire_seconds?: number }): Promise<WxSessionData> {
  return httpPost<WxSessionData>('/api/v1/auth/wechat/session', params || {})
}

/**
 * 轮询检查微信扫码状态
 */
export function checkWxStatusApi(sessionNo: string): Promise<WxStatusData> {
  return httpGet<WxStatusData>('/api/v1/auth/wechat/status', {
    params: { session_no: sessionNo }
  })
}

/**
 * 授权完成后，获取 Token 并完成登录/注册
 */
export function completeWxAuthApi(params: WxCompleteParams): Promise<AuthResponse> {
  return httpPost<AuthResponse>('/api/v1/auth/wechat/complete', params)
}

/**
 * 获取当前登录用户信息
 */
export function getMeApi(): Promise<{ user: UserInfo }> {
  return httpGet<{ user: UserInfo }>('/api/v1/auth/me')
}


