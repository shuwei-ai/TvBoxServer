<template>
  <div class="system-config-card bento-card">
    <div class="card-header">
      <div class="header-left">
        <div class="title-with-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <h2>系统运行参数</h2>
        </div>
        <span class="sub-text">准入策略与多租户设备配额管控</span>
      </div>
    </div>

    <el-form
      ref="formRef"
      v-loading="loading"
      :model="config"
      label-position="top"
      class="config-form"
      @submit.prevent="handleSubmit"
    >
      <div class="switches-grid">
        <div class="switch-item">
          <div class="switch-info">
            <span class="title">开放公开注册</span>
            <span class="desc">允许新用户自行注册平台账号</span>
          </div>
          <el-switch v-model="config.allow_user_registration" />
        </div>

        <div class="switch-item">
          <div class="switch-info">
            <span class="title">强制邀请码</span>
            <span class="desc">注册时必须填写有效邀请码</span>
          </div>
          <el-switch v-model="config.require_invite_code" />
        </div>
      </div>

      <div class="inputs-grid">
        <div class="input-cell">
          <label>全站注册上限</label>
          <el-input-number
            v-model="config.max_registered_users"
            :min="1"
            :max="10000"
            size="small"
            style="width: 100%"
          />
        </div>

        <div class="input-cell">
          <label>单用户设备上限</label>
          <el-input-number
            v-model="config.max_devices_per_user"
            :min="1"
            :max="100"
            size="small"
            style="width: 100%"
          />
        </div>

        <div class="input-cell">
          <label>单用户邀请配额</label>
          <el-input-number
            v-model="config.max_invites_per_user"
            :min="0"
            :max="100"
            size="small"
            style="width: 100%"
          />
        </div>
      </div>

      <div class="form-actions">
        <el-button
          type="primary"
          size="small"
          :loading="saving"
          :icon="Check"
          @click="handleSubmit"
        >
          保存配置
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getSystemConfigApi, updateSystemConfigApi } from '@/api/admin'
import type { SystemConfig } from '@/types'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'

const loading = ref(false)
const saving = ref(false)

const config = reactive<SystemConfig>({
  allow_user_registration: true,
  require_invite_code: false,
  max_registered_users: 100,
  max_devices_per_user: 5,
  max_invites_per_user: 3
})

async function loadConfig() {
  loading.value = true
  try {
    const res = await getSystemConfigApi()
    Object.assign(config, res)
  } catch {
    // handled
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  saving.value = true
  try {
    await updateSystemConfigApi(config)
    ElMessage.success('系统参数配置已成功保存！')
    await loadConfig()
  } catch {
    // handled
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})

defineExpose({
  loadConfig
})
</script>

<style scoped lang="scss">
.system-config-card {
  padding: 18px 20px;
}

.card-header {
  margin-bottom: 14px;

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

    .sub-text {
      font-size: 11.5px;
      color: var(--app-text-muted);
    }
  }
}

.switches-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;

  .switch-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    border-radius: var(--app-radius-md);
    background: var(--app-surface-subtle);
    border: 1px solid var(--app-hairline);

    .switch-info {
      display: flex;
      flex-direction: column;

      .title {
        font-size: 12.5px;
        font-weight: 600;
        color: var(--app-text-primary);
      }

      .desc {
        font-size: 11px;
        color: var(--app-text-muted);
      }
    }
  }
}

.inputs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin-bottom: 14px;

  .input-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;

    label {
      font-size: 11.5px;
      color: var(--app-text-secondary);
      font-weight: 500;
    }
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
