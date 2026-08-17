<template>
  <div class="api-key-card glass-card">
    <div class="card-header">
      <h2>用户级 API Key</h2>
      <el-tag
        :type="statusTagType"
        size="small"
        effect="plain"
        round
      >
        {{ keyStatusText }}
      </el-tag>
    </div>

    <div class="card-body">
      <div class="code-box key-box">
        {{ keyDisplay }}
      </div>

      <p class="hint">
        同一个 Key 可供您名下的多台 TVBox 使用。出于安全考虑，完整 Key 仅在首次生成或重置时展示一次。
      </p>

      <div class="actions">
        <el-button
          type="danger"
          plain
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
import { RefreshRight } from '@element-plus/icons-vue'
import KeyModal from './KeyModal.vue'

const deviceStore = useDeviceStore()
const resetting = ref(false)
const keyModalRef = ref<InstanceType<typeof KeyModal>>()

const apiKeyInfo = computed(() => deviceStore.apiKeyInfo)

const keyStatusText = computed(() => {
  if (!apiKeyInfo.value) return '未生成'
  return apiKeyInfo.value.status === 'ACTIVE' ? '正常生效' : apiKeyInfo.value.status
})

const statusTagType = computed(() => {
  if (!apiKeyInfo.value) return 'info'
  return apiKeyInfo.value.status === 'ACTIVE' ? 'success' : 'danger'
})

const keyDisplay = computed(() => {
  if (!apiKeyInfo.value || !apiKeyInfo.value.key_prefix) {
    return '首次绑定 TVBox 设备后自动生成'
  }
  return `${apiKeyInfo.value.key_prefix}••••••••••••••••`
})

async function handleReset() {
  try {
    await ElMessageBox.confirm(
      '重置 API Key 后，已配置旧 Key 的所有电视必须更新为新 Key 才能继续连接，是否确认继续？',
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
  padding: 22px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h2 {
      font-size: 16px;
      font-weight: 700;
      margin: 0;
    }
  }

  .card-body {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .key-box {
      font-size: 13px;
    }

    .hint {
      font-size: 12px;
      color: var(--app-text-muted);
      line-height: 1.5;
      margin: 0;
    }

    .actions {
      display: flex;
      justify-content: flex-end;
      margin-top: 4px;
    }
  }
}
</style>
