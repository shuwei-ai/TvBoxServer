<template>
  <el-dialog
    v-model="visible"
    title="请妥善保存您的 API Key"
    width="500px"
    destroy-on-close
    append-to-body
    :close-on-click-modal="false"
  >
    <div class="key-dialog-content">
      <el-alert
        title="重要安全提示"
        type="warning"
        description="出于安全原因，完整 API Key 仅在此处展示一次。请立即复制并在您的 TVBox 设备或客户端中完成配置。"
        show-icon
        :closable="false"
      />

      <div class="key-display-section">
        <div class="code-box key-value">{{ apiKey }}</div>
      </div>

      <p class="desc">
        同一个 API Key 可供您名下的所有 TVBox 设备使用。如遇泄露可随时在控制台“重置 API Key”。
      </p>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">我已保存</el-button>
        <el-button type="primary" :icon="DocumentCopy" @click="handleCopy">
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
    ElMessage.success('API Key 已复制到剪贴板！')
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
  gap: 16px;

  .key-display-section {
    margin-top: 6px;

    .key-value {
      font-size: 14px;
      font-weight: 600;
      line-height: 1.5;
      padding: 14px;
      user-select: all;
    }
  }

  .desc {
    font-size: 13px;
    color: var(--app-text-muted);
    line-height: 1.5;
    margin: 0;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
