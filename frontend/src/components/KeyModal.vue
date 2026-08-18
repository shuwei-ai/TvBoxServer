<template>
  <el-dialog
    v-model="visible"
    title="请妥善保存您的 API Key"
    width="480px"
    destroy-on-close
    append-to-body
    :close-on-click-modal="false"
  >
    <div class="key-dialog-content">
      <div class="security-warning">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="warn-icon">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <div class="warn-text">
          <strong>重要安全提示：</strong>
          出于安全原因，完整 API Key 仅展示一次。请立即复制并在 TVBox 端或第三方客户端中配置。
        </div>
      </div>

      <div class="key-display-section">
        <div class="code-box key-value">{{ apiKey }}</div>
      </div>

      <p class="desc">
        同一个 API Key 可供您名下的所有 TVBox 设备使用。如遇泄露可随时在控制台“重置 API Key”。
      </p>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button size="small" @click="visible = false">我已保存</el-button>
        <el-button type="primary" size="small" :icon="DocumentCopy" @click="handleCopy">
          复制 API Key
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy } from '@element-plus/icons-vue'

const visible = ref(false)
const apiKey = ref('')

function open(key: string) {
  apiKey.value = key
  visible.value = true
}

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(apiKey.value)
    ElMessage.success('API Key 已成功复制到剪贴板！')
  } catch {
    ElMessage.error('复制失败，请手动选中文本复制')
  }
}

defineExpose({
  open
})
</script>

<style scoped lang="scss">
.key-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 14px;

  .security-warning {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    border-radius: var(--app-radius-md);
    background: var(--app-warning-subtle);
    border: 1px solid rgba(245, 158, 11, 0.25);
    color: var(--app-warning);

    .warn-icon {
      flex-shrink: 0;
      margin-top: 2px;
    }

    .warn-text {
      font-size: 12px;
      line-height: 1.45;
      color: var(--app-text-primary);

      strong {
        color: var(--app-warning);
      }
    }
  }

  .key-display-section {
    .key-value {
      font-size: 13.5px;
      font-weight: 600;
      line-height: 1.5;
      padding: 12px 14px;
      user-select: all;
      border-color: var(--app-accent);
      background: var(--app-accent-subtle);
    }
  }

  .desc {
    font-size: 12px;
    color: var(--app-text-muted);
    line-height: 1.45;
    margin: 0;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
