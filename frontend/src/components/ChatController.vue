<template>
  <div class="chat-card glass-card">
    <div class="chat-header">
      <div class="header-left">
        <h2>AI 电视控制对话</h2>
        <span class="chat-tip">输入自然语言控制电视，例如“播放狂飙第 3 集”、“打开设置”</span>
      </div>

      <div class="header-right">
        <!-- 目标设备选择 -->
        <el-select
          v-model="deviceStore.selectedDeviceId"
          placeholder="选择控制目标设备"
          style="width: 180px"
          size="default"
        >
          <el-option label="🌐 自动路由 (Auto)" value="" />
          <el-option
            v-for="d in deviceStore.devices"
            :key="d.device_id"
            :label="`${d.online ? '🟢' : '⚪'} ${d.device_name}`"
            :value="d.device_id"
          />
        </el-select>

        <el-tooltip content="清空对话记录" placement="top">
          <el-button
            circle
            size="small"
            :icon="Delete"
            @click="chatStore.clearMessages"
          />
        </el-tooltip>
      </div>
    </div>

    <!-- 消息对话流容器 -->
    <div ref="messagesContainerRef" class="messages-stream">
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
      <el-input
        v-model="inputQuery"
        placeholder="输入电视控制指令..."
        clearable
        size="large"
        :disabled="chatStore.sending"
        @keydown.enter.prevent="handleSend"
      >
        <template #append>
          <el-button
            type="primary"
            :icon="Position"
            :loading="chatStore.sending"
            @click="handleSend"
          >
            发送
          </el-button>
        </template>
      </el-input>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useDeviceStore, useChatStore } from '@/stores'
import { Delete, Position } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const chatStore = useChatStore()

const inputQuery = ref('')
const messagesContainerRef = ref<HTMLElement>()

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
  padding: 22px;
  min-height: 480px;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--app-card-border);
  gap: 12px;

  .header-left {
    h2 {
      font-size: 17px;
      font-weight: 700;
      margin: 0 0 4px;
    }

    .chat-tip {
      font-size: 12px;
      color: var(--app-text-muted);
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.messages-stream {
  flex: 1;
  height: 320px;
  max-height: 360px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 4px;
}

.message-wrapper {
  display: flex;
  width: 100%;

  &.user {
    justify-content: flex-end;

    .message-bubble {
      background: linear-gradient(135deg, #0d9488, #0f766e);
      color: #ffffff;
      border-bottom-right-radius: 4px;
      box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
    }
  }

  &.assistant {
    justify-content: flex-start;

    .message-bubble {
      background: rgba(148, 163, 184, 0.12);
      border: 1px solid var(--app-card-border);
      border-bottom-left-radius: 4px;
      color: var(--app-text-primary);
    }
  }

  &.error {
    justify-content: flex-start;

    .message-bubble {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: var(--app-danger);
    }
  }
}

.message-bubble {
  max-width: 80%;
  padding: 10px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;

  .device-tag {
    font-size: 11px;
    opacity: 0.85;
    margin-bottom: 4px;
    font-weight: 500;
  }
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 18px;

  .dot-typing {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--app-accent);
    animation: bounce 1.2s infinite ease-in-out;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

.chat-input-bar {
  margin-top: 14px;
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
