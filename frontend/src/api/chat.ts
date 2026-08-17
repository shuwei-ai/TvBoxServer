import { httpPost } from '@/utils/request'
import type { ChatCompletionParams, ChatCompletionResponse } from '@/types'

export function sendChatCompletionApi(params: ChatCompletionParams): Promise<ChatCompletionResponse> {
  return httpPost<ChatCompletionResponse>('/api/v1/chat/completions', params)
}
