<template>
  <div class="admin-view">
    <!-- 概览指标卡片 -->
    <div class="stats-row">
      <div class="stat-card glass-card">
        <div class="stat-icon user-icon">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-content">
          <div class="label">已注册用户 / 上限</div>
          <div class="value">
            {{ configData.current_registered_users ?? '-' }}
            <span class="sub">/ {{ configData.max_registered_users ?? '-' }}</span>
          </div>
        </div>
      </div>

      <div class="stat-card glass-card">
        <div class="stat-icon device-icon">
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="stat-content">
          <div class="label">系统设备总数</div>
          <div class="value">{{ totalDevicesCount }} 台</div>
        </div>
      </div>

      <div class="stat-card glass-card">
        <div class="stat-icon online-icon">
          <el-icon><VideoPlay /></el-icon>
        </div>
        <div class="stat-content">
          <div class="label">当前在线设备</div>
          <div class="value highlight">{{ onlineDevicesCount }} 台</div>
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
import { User, Monitor, VideoPlay } from '@element-plus/icons-vue'
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
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;

  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 18px 20px;

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      font-size: 22px;

      &.user-icon {
        background: rgba(96, 165, 250, 0.15);
        color: var(--app-blue);
      }

      &.device-icon {
        background: rgba(148, 163, 184, 0.15);
        color: var(--app-text-muted);
      }

      &.online-icon {
        background: rgba(52, 211, 153, 0.15);
        color: var(--app-success);
      }
    }

    .stat-content {
      display: flex;
      flex-direction: column;

      .label {
        font-size: 12px;
        color: var(--app-text-muted);
        margin-bottom: 2px;
      }

      .value {
        font-size: 22px;
        font-weight: 700;

        .sub {
          font-size: 14px;
          font-weight: 400;
          color: var(--app-text-muted);
        }

        &.highlight {
          color: var(--app-success);
        }
      }
    }
  }
}

.admin-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.85fr;
  gap: 20px;
  align-items: start;

  .left-section,
  .right-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
}

@media (max-width: 900px) {
  .admin-grid {
    grid-template-columns: 1fr;
  }
}
</style>
