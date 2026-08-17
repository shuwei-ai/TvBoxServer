import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendChatCompletionApi } from '@/api/chat'
import type { ChatMessage } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([
    {
      id: 'init-1',
      role: 'assistant',
      content: '欢迎使用 TVBox AI 控制中心！选择目标设备并输入语音或文本控制指令（例如：“播放狂飙第 3 集”、“打开设置”、“暂停”）。',
      timestamp: Date.now()
    }
  ])
  const sending = ref<boolean>(false)

  function addMessage(msg: Omit<ChatMessage, 'id' | 'timestamp'>) {
    const newMessage: ChatMessage = {
      id: 'msg-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7),
      timestamp: Date.now(),
      ...msg
    }
    messages.value.push(newMessage)
    return newMessage
  }

  async function sendMessage(text: string, targetDeviceId: string | null, targetDeviceName?: string) {
    if (!text.trim() || sending.value) return

    // 插入用户消息
    addMessage({
      role: 'user',
      content: text.trim(),
      targetDeviceName
    })

    sending.value = true
    try {
      const res = await sendChatCompletionApi({
        model: targetDeviceId || 'auto',
        device_id: targetDeviceId || null,
        messages: [{ role: 'user', content: text.trim() }],
        stream: false
      })

      const replyContent = res.choices?.[0]?.message?.content || '指令已下发'
      addMessage({
        role: 'assistant',
        content: replyContent,
        status: 'success'
      })
    } catch (err: any) {
      addMessage({
        role: 'error',
        content: err.message || '指令执行失败',
        status: 'error'
      })
      throw err
    } finally {
      sending.value = false
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    sending,
    addMessage,
    sendMessage,
    clearMessages
  }
})
