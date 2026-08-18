<template>
  <div class="chat-card bento-card">
    <div class="chat-header">
      <div class="header-left">
        <div class="title-with-icon">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <h2>AI 电视指令调度</h2>
        </div>
        <span class="chat-tip">输入自然语言下发指令，AI 将自动识别意图并路由控制 TVBox</span>
      </div>

      <div class="header-right">
        <!-- 目标设备选择 -->
        <el-select
          v-model="deviceStore.selectedDeviceId"
          placeholder="控制目标"
          style="width: 155px"
          size="small"
        >
          <el-option label="🌐 智能自动路由" value="" />
          <el-option
            v-for="d in deviceStore.devices"
            :key="d.device_id"
            :label="`${d.online ? '🟢' : '⚪'} ${d.device_name}`"
            :value="d.device_id"
          />
        </el-select>

        <el-tooltip content="清空历史对话" placement="top">
          <button class="clear-btn" @click="chatStore.clearMessages">
            <el-icon :size="13"><Delete /></el-icon>
          </button>
        </el-tooltip>
      </div>
    </div>

    <!-- 快捷指令标签 -->
    <div class="quick-prompts">
      <span class="quick-label">快捷指令:</span>
      <button
        v-for="(prompt, idx) in quickPrompts"
        :key="idx"
        class="prompt-chip"
        @click="fillAndSend(prompt)"
      >
        {{ prompt }}
      </button>
    </div>

    <!-- 消息对话流容器 -->
    <div ref="messagesContainerRef" class="messages-stream">
      <div v-if="chatStore.messages.length === 0" class="chat-welcome">
        <div class="ai-avatar-pulse">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="2" />
            <path d="M12 7v4" />
            <line x1="8" y1="16" x2="8" y2="16" />
            <line x1="16" y1="16" x2="16" y2="16" />
          </svg>
        </div>
        <p class="welcome-title">TVBox AI 语音遥控已就绪</p>
        <p class="welcome-desc">您可以尝试说：“打开设置”、“播放狂飙第三集” 或 “音量增加 20%”</p>
      </div>

      <div
        v-for="msg in chatStore.messages"
        :key="msg.id"
        class="message-wrapper"
        :class="msg.role"
      >
        <div class="message-bubble">
          <div v-if="msg.targetDeviceName" class="device-tag">
            🎯 {{ msg.targetDeviceName }}
          </div>
          <div class="message-text">{{ msg.content }}</div>
        </div>
      </div>

      <!-- 发送中加载状态 -->
      <div v-if="chatStore.sending" class="message-wrapper assistant">
        <div class="message-bubble loading-bubble">
          <span class="dot-typing"></span>
          <span class="dot-typing"></span>
          <span class="dot-typing"></span>
        </div>
      </div>
    </div>

    <!-- 输入发送栏 -->
    <form class="chat-input-bar" @submit.prevent="handleSend">
      <div class="input-container">
        <input
          v-model="inputQuery"
          type="text"
          placeholder="输入控制指令，如：播放狂飙、音量调大、返回主页..."
          :disabled="chatStore.sending"
          class="custom-chat-input"
          @keydown.enter.prevent="handleSend"
        />
        <button
          type="button"
          class="send-action-btn"
          :disabled="!inputQuery.trim() || chatStore.sending"
          @click="handleSend"
        >
          <span v-if="!chatStore.sending">发送</span>
          <span v-else class="sending-spinner"></span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useDeviceStore, useChatStore } from '@/stores'
import { Delete } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const chatStore = useChatStore()

const inputQuery = ref('')
const messagesContainerRef = ref<HTMLElement>()

const quickPrompts = [
  '播放狂飙第 1 集',
  '音量增加 10%',
  '返回电视主页',
  '暂停播放'
]

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainerRef.value) {
      messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
    }
  })
}

watch(
  () => chatStore.messages.length,
  () => {
    scrollToBottom()
  }
)

function fillAndSend(prompt: string) {
  inputQuery.value = prompt
  handleSend()
}

async function handleSend() {
  const query = inputQuery.value.trim()
  if (!query || chatStore.sending) return

  inputQuery.value = ''
  const targetId = deviceStore.selectedDeviceId || null
  const targetDevice = deviceStore.devices.find((d) => d.device_id === targetId)
  const targetName = targetDevice ? targetDevice.device_name : (targetId ? targetId : '自动路由')

  scrollToBottom()

  try {
    await chatStore.sendMessage(query, targetId, targetName)
  } catch {
    // 错误在 store 内部转换为 error message
  } finally {
    scrollToBottom()
  }
}
</script>

<style scoped lang="scss">
.chat-card {
  display: flex;
  flex-direction: column;
  padding: 18px 20px;
  min-height: 460px;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--app-hairline);
  gap: 12px;

  .header-left {
    .title-with-icon {
      display: flex;
      align-items: center;
      gap: 7px;

      .header-icon {
        color: var(--app-accent);
      }

      h2 {
        font-size: 14.5px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.01em;
      }
    }

    .chat-tip {
      font-size: 11.5px;
      color: var(--app-text-muted);
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;

    .clear-btn {
      width: 28px;
      height: 28px;
      display: grid;
      place-items: center;
      border-radius: 6px;
      background: var(--app-surface-subtle);
      border: 1px solid var(--app-hairline);
      color: var(--app-text-muted);
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover {
        background: var(--app-danger-subtle);
        color: var(--app-danger);
        border-color: rgba(239, 68, 68, 0.2);
      }
    }
  }
}

.quick-prompts {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 0 6px;
  flex-wrap: wrap;

  .quick-label {
    font-size: 11px;
    color: var(--app-text-muted);
    font-weight: 500;
  }

  .prompt-chip {
    font-size: 11.5px;
    padding: 2px 8px;
    border-radius: 6px;
    background: var(--app-surface-subtle);
    border: 1px solid var(--app-hairline);
    color: var(--app-text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      background: var(--app-accent-subtle);
      color: var(--app-accent);
      border-color: var(--app-accent);
    }
  }
}

.messages-stream {
  flex: 1;
  height: 280px;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 2px;
}

.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--app-text-muted);

  .ai-avatar-pulse {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: var(--app-accent-subtle);
    border: 1px solid rgba(94, 106, 210, 0.2);
    display: grid;
    place-items: center;
    color: var(--app-accent);
    margin-bottom: 8px;
  }

  .welcome-title {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--app-text-primary);
    margin-bottom: 4px;
  }

  .welcome-desc {
    font-size: 12px;
    max-width: 320px;
  }
}

.message-wrapper {
  display: flex;
  width: 100%;

  &.user {
    justify-content: flex-end;

    .message-bubble {
      background: var(--app-accent);
      color: #ffffff;
      border-bottom-right-radius: 4px;
      box-shadow: 0 2px 8px var(--app-accent-glow);
    }
  }

  &.assistant {
    justify-content: flex-start;

    .message-bubble {
      background: var(--app-surface-subtle);
      border: 1px solid var(--app-hairline);
      border-bottom-left-radius: 4px;
      color: var(--app-text-primary);
    }
  }

  &.error {
    justify-content: flex-start;

    .message-bubble {
      background: var(--app-danger-subtle);
      border: 1px solid rgba(239, 68, 68, 0.25);
      color: var(--app-danger);
    }
  }
}

.message-bubble {
  max-width: 82%;
  padding: 8px 14px;
  border-radius: var(--app-radius-md);
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;

  .device-tag {
    font-size: 10.5px;
    font-family: 'JetBrains Mono', monospace;
    opacity: 0.85;
    margin-bottom: 3px;
    font-weight: 500;
  }
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 10px 14px;

  .dot-typing {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background-color: var(--app-accent);
    animation: bounce 1.2s infinite ease-in-out;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.chat-input-bar {
  margin-top: 10px;

  .input-container {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--app-surface-subtle);
    border: 1px solid var(--app-hairline);
    padding: 4px 6px 4px 12px;
    border-radius: var(--app-radius-md);
    transition: border-color 0.15s ease;

    &:focus-within {
      border-color: var(--app-accent);
      box-shadow: 0 0 0 1px var(--app-accent);
    }

    .custom-chat-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      font-size: 13px;
      color: var(--app-text-primary);
      font-family: inherit;

      &::placeholder {
        color: var(--app-text-muted);
      }
    }

    .send-action-btn {
      padding: 6px 14px;
      border-radius: 6px;
      background: var(--app-accent);
      color: #fff;
      border: none;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover:not(:disabled) {
        background: var(--app-accent-hover);
      }

      &:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
    }
  }
}

.sending-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@media (max-width: 768px) {
  .chat-header {
    flex-direction: column;
    align-items: flex-start;

    .header-right {
      width: 100%;
      justify-content: space-between;
    }
  }
}
</style>
