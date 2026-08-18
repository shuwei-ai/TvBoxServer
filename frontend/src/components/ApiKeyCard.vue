<template>
  <div class="api-key-card bento-card">
    <div class="card-header">
      <div class="header-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
          <path d="M21 2l-2 2m-1.5 1.5L16 7l-1.5-1.5M16 7l-2 2-2-2 2-2 2 2z" />
          <circle cx="7.5" cy="15.5" r="5.5" />
          <path d="M11.5 11.5l7 7" />
        </svg>
        <h2>用户级 API Key</h2>
      </div>
      <span class="status-pill" :class="statusPillClass">
        <span class="status-dot-mini"></span>
        {{ keyStatusText }}
      </span>
    </div>

    <div class="card-body">
      <div class="key-box-container">
        <div class="code-box key-display-wrapper">
          <span class="key-text">{{ keyDisplay }}</span>
          <div v-if="hasKey" class="key-tools">
            <el-tooltip :content="showFullKey ? '隐藏 API Key' : '查看完整 API Key'" placement="top">
              <button class="tool-btn" @click="handleToggleShow">
                <el-icon :size="14">
                  <component :is="showFullKey ? Hide : View" />
                </el-icon>
              </button>
            </el-tooltip>
            <el-tooltip content="复制完整 API Key" placement="top">
              <button class="tool-btn" @click="handleCopy">
                <el-icon :size="14"><DocumentCopy /></el-icon>
              </button>
            </el-tooltip>
          </div>
        </div>
      </div>

      <div class="key-info-tip">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="tip-icon">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <span>用于 TVBox 客户端鉴权及兼容 OpenAI 协议的第三方智能体接入，支持随时查看与复制。</span>
      </div>

      <div class="card-actions">
        <el-button
          type="danger"
          plain
          size="small"
          :icon="RefreshRight"
          :loading="resetting"
          @click="handleReset"
        >
          重置 API Key
        </el-button>
      </div>
    </div>

    <!-- 重置后展示完整 Key 的弹窗 -->
    <KeyModal ref="keyModalRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDeviceStore } from '@/stores'
import { ElMessageBox, ElMessage } from 'element-plus'
import { RefreshRight, DocumentCopy, View, Hide } from '@element-plus/icons-vue'
import KeyModal from './KeyModal.vue'

const deviceStore = useDeviceStore()
const resetting = ref(false)
const showFullKey = ref(false)
const keyModalRef = ref<InstanceType<typeof KeyModal>>()

const apiKeyInfo = computed(() => deviceStore.apiKeyInfo)

const hasKey = computed(() => {
  return Boolean(apiKeyInfo.value && (apiKeyInfo.value.api_key || apiKeyInfo.value.key_prefix))
})

const keyStatusText = computed(() => {
  if (!apiKeyInfo.value) return '未生成'
  return apiKeyInfo.value.status === 'ACTIVE' ? '正常生效' : apiKeyInfo.value.status
})

const statusPillClass = computed(() => {
  if (!apiKeyInfo.value) return 'inactive'
  return apiKeyInfo.value.status === 'ACTIVE' ? 'active' : 'revoked'
})

const isLegacyKey = computed(() => {
  return Boolean(apiKeyInfo.value && !apiKeyInfo.value.api_key && apiKeyInfo.value.key_prefix)
})

const keyDisplay = computed(() => {
  if (!apiKeyInfo.value || (!apiKeyInfo.value.key_prefix && !apiKeyInfo.value.api_key)) {
    return '首次绑定 TVBox 设备后自动生成'
  }
  if (showFullKey.value && apiKeyInfo.value.api_key) {
    return apiKeyInfo.value.api_key
  }
  const prefix = apiKeyInfo.value.key_prefix || (apiKeyInfo.value.api_key ? apiKeyInfo.value.api_key.slice(0, 12) : 'sk-tvbox-')
  return `${prefix}••••••••••••••••`
})

function handleToggleShow() {
  if (isLegacyKey.value) {
    ElMessageBox.alert(
      '当前 API Key 属于历史版本（系统此前未在云端保存明文）。请点击下方「重置 API Key」一次，生成新 Key 后即可永久支持随时显示与复制明文。',
      '旧版 Key 提示',
      { confirmButtonText: '我知道了', type: 'info' }
    )
    return
  }
  showFullKey.value = !showFullKey.value
}

async function handleCopy() {
  if (apiKeyInfo.value?.api_key) {
    try {
      await navigator.clipboard.writeText(apiKeyInfo.value.api_key)
      ElMessage.success('完整 API Key 已复制到剪贴板！')
    } catch {
      ElMessage.error('复制失败，请手动选中文本复制')
    }
  } else if (isLegacyKey.value) {
    ElMessageBox.alert(
      '当前 API Key 为旧版本，云端无完整明文记录。请点击下方「重置 API Key」一次，生成新 Key 后即可随时一键复制完整 Key。',
      '无法复制完整 Key',
      { confirmButtonText: '我知道了', type: 'warning' }
    )
  }
}

async function handleReset() {
  try {
    await ElMessageBox.confirm(
      '重置 API Key 后，已配置旧 Key 的所有电视及第三方客户端必须更新为新 Key 才能继续连接，是否确认继续？',
      '重置 API Key 警告',
      {
        confirmButtonText: '确认重置',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
        type: 'warning'
      }
    )

    resetting.value = true
    const res = await deviceStore.resetApiKey()
    showFullKey.value = true
    ElMessage.success('API Key 重置成功！')
    if (res.api_key) {
      keyModalRef.value?.open(res.api_key)
    }
  } catch (err: any) {
    if (err !== 'cancel') {
      // handled
    }
  } finally {
    resetting.value = false
  }
}
</script>

<style scoped lang="scss">
.api-key-card {
  padding: 18px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .header-title {
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
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);
  color: var(--app-text-muted);

  .status-dot-mini {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }

  &.active {
    background: var(--app-success-subtle);
    border-color: rgba(16, 185, 129, 0.25);
    color: var(--app-success);
  }

  &.revoked {
    background: var(--app-danger-subtle);
    border-color: rgba(239, 68, 68, 0.25);
    color: var(--app-danger);
  }
}

.key-box-container {
  margin-bottom: 10px;

  .key-display-wrapper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;

    .key-text {
      font-size: 12px;
      letter-spacing: 0.04em;
      word-break: break-all;
      color: var(--app-text-primary);
    }

    .key-tools {
      display: flex;
      align-items: center;
      gap: 4px;
      flex-shrink: 0;

      .tool-btn {
        width: 26px;
        height: 26px;
        display: grid;
        place-items: center;
        border-radius: 6px;
        background: transparent;
        border: 1px solid transparent;
        color: var(--app-text-muted);
        cursor: pointer;
        transition: all 0.15s ease;

        &:hover {
          background: var(--app-surface-hover);
          color: var(--app-text-primary);
          border-color: var(--app-hairline);
        }
      }
    }
  }
}

.key-info-tip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 11.5px;
  color: var(--app-text-muted);
  line-height: 1.4;
  margin-bottom: 14px;

  .tip-icon {
    flex-shrink: 0;
    margin-top: 2px;
  }
}

.card-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
