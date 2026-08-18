<template>
  <div class="admin-view">
    <!-- 概览指标卡片 (FlowAI / Linear 风格 KPI 卡片) -->
    <div class="stats-row">
      <div class="stat-card bento-card">
        <div class="stat-icon user-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
        </div>
        <div class="stat-content">
          <div class="label">已注册用户 / 上限</div>
          <div class="value">
            {{ configData.current_registered_users ?? '-' }}
            <span class="sub">/ {{ configData.max_registered_users ?? '-' }}</span>
          </div>
        </div>
      </div>

      <div class="stat-card bento-card">
        <div class="stat-icon device-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="7" width="20" height="15" rx="2" />
            <polyline points="17 2 12 7 7 2" />
          </svg>
        </div>
        <div class="stat-content">
          <div class="label">系统设备总数</div>
          <div class="value">{{ totalDevicesCount }} <span class="sub">台</span></div>
        </div>
      </div>

      <div class="stat-card bento-card highlight-card">
        <div class="stat-icon online-icon">
          <span class="online-dot active"></span>
        </div>
        <div class="stat-content">
          <div class="label">当前在线就绪设备</div>
          <div class="value online-val">{{ onlineDevicesCount }} <span class="sub">台在线</span></div>
        </div>
      </div>
    </div>

    <div class="admin-grid">
      <!-- 左侧：用户表格与设备监控 -->
      <div class="left-section">
        <UserTable ref="userTableRef" />
        <DeviceMonitor ref="deviceMonitorRef" />
      </div>

      <!-- 右侧：系统参数配置与批量邀请码 -->
      <div class="right-section">
        <SystemConfigForm ref="configFormRef" />
        <InviteBatchGenerator />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getSystemConfigApi, getAdminDevicesApi } from '@/api/admin'
import type { SystemConfig, DeviceItem } from '@/types'
import UserTable from '@/components/admin/UserTable.vue'
import DeviceMonitor from '@/components/admin/DeviceMonitor.vue'
import SystemConfigForm from '@/components/admin/SystemConfigForm.vue'
import InviteBatchGenerator from '@/components/admin/InviteBatchGenerator.vue'

const configData = ref<Partial<SystemConfig>>({})
const adminDevices = ref<DeviceItem[]>([])

const userTableRef = ref<InstanceType<typeof UserTable>>()
const deviceMonitorRef = ref<InstanceType<typeof DeviceMonitor>>()
const configFormRef = ref<InstanceType<typeof SystemConfigForm>>()

const totalDevicesCount = computed(() => adminDevices.value.length)
const onlineDevicesCount = computed(() => adminDevices.value.filter((d) => d.online).length)

async function loadOverview() {
  try {
    const [cfg, devs] = await Promise.all([
      getSystemConfigApi(),
      getAdminDevicesApi()
    ])
    configData.value = cfg
    adminDevices.value = devs || []
  } catch {
    // handled
  }
}

onMounted(() => {
  loadOverview()
})
</script>

<style scoped lang="scss">
.admin-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;

  .stat-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 18px;

    .stat-icon {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      font-size: 18px;

      &.user-icon {
        background: var(--app-blue-subtle);
        color: var(--app-blue);
      }

      &.device-icon {
        background: var(--app-accent-subtle);
        color: var(--app-accent);
      }

      &.online-icon {
        background: var(--app-success-subtle);
        color: var(--app-success);
      }
    }

    .stat-content {
      display: flex;
      flex-direction: column;

      .label {
        font-size: 11.5px;
        color: var(--app-text-muted);
        margin-bottom: 2px;
        font-weight: 500;
      }

      .value {
        font-size: 20px;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: var(--app-text-primary);

        .sub {
          font-size: 13px;
          font-weight: 400;
          color: var(--app-text-muted);
        }

        &.online-val {
          color: var(--app-success);
        }
      }
    }
  }
}

.admin-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
  align-items: start;

  .left-section,
  .right-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
}

@media (max-width: 960px) {
  .admin-grid {
    grid-template-columns: 1fr;
  }
}
</style>
