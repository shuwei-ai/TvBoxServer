export type MessageRole = 'user' | 'assistant' | 'system' | 'error'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: number
  targetDeviceName?: string
  status?: 'pending' | 'success' | 'error'
}

export interface ChatCompletionParams {
  model?: string
  device_id?: string | null
  messages: Array<{
    role: string
    content: string
  }>
  stream?: boolean
}

export interface ChatChoice {
  index: number
  message: {
    role: string
    content: string
  }
  finish_reason: string
}

export interface ChatCompletionResponse {
  id?: string
  object?: string
  created?: number
  model?: string
  choices: ChatChoice[]
}
