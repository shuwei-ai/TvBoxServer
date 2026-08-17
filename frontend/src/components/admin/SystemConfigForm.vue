<template>
  <div class="system-config-card glass-card">
    <div class="card-header">
      <div class="header-left">
        <h2>系统参数配置</h2>
        <span class="sub-text">设置注册准入、邀请码策略及多租户配额限制</span>
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
      <div class="form-row-switches">
        <el-form-item label="开放用户注册">
          <el-switch
            v-model="config.allow_user_registration"
            active-text="允许新用户注册"
            inactive-text="关闭公开注册"
          />
        </el-form-item>

        <el-form-item label="强制使用邀请码">
          <el-switch
            v-model="config.require_invite_code"
            active-text="注册必须填邀请码"
            inactive-text="无需邀请码"
          />
        </el-form-item>
      </div>

      <div class="form-row-inputs">
        <el-form-item label="系统用户注册上限" prop="max_registered_users">
          <el-input-number
            v-model="config.max_registered_users"
            :min="1"
            :max="10000"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="单用户最大绑定设备数" prop="max_devices_per_user">
          <el-input-number
            v-model="config.max_devices_per_user"
            :min="1"
            :max="100"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="单用户最大邀请码数" prop="max_invites_per_user">
          <el-input-number
            v-model="config.max_invites_per_user"
            :min="0"
            :max="100"
            style="width: 100%"
          />
        </el-form-item>
      </div>

      <div class="form-actions">
        <el-button
          type="primary"
          :loading="saving"
          :icon="Check"
          @click="handleSubmit"
        >
          保存系统配置
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
  padding: 22px;

  .card-header {
    margin-bottom: 18px;

    .header-left {
      h2 {
        font-size: 16px;
        font-weight: 700;
        margin: 0 0 4px;
      }

      .sub-text {
        font-size: 12px;
        color: var(--app-text-muted);
      }
    }
  }

  .form-row-switches {
    display: flex;
    gap: 32px;
    margin-bottom: 12px;
  }

  .form-row-inputs {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 10px;
  }
}

@media (max-width: 640px) {
  .form-row-switches {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
