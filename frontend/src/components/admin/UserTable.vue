<template>
  <div class="user-table-card bento-card">
    <div class="card-header">
      <div class="header-left">
        <div class="title-with-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <h2>用户管理</h2>
        </div>
        <span class="sub-text">全站注册用户、角色权限与启停状态审计</span>
      </div>
      <button class="refresh-icon-btn" :class="{ spinning: loading }" @click="loadUsers">
        <el-icon :size="13"><Refresh /></el-icon>
      </button>
    </div>

    <el-table
      v-loading="loading"
      :data="users"
      style="width: 100%"
      class="compact-table"
    >
      <el-table-column prop="username" label="用户名" min-width="130">
        <template #default="{ row }">
          <div class="username-cell">
            <el-avatar :size="22" class="user-mini-avatar">
              {{ row.username.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="name">{{ row.username }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="role" label="角色" width="90">
        <template #default="{ row }">
          <span class="role-badge" :class="row.role === 'ADMIN' ? 'admin' : 'user'">
            {{ row.role }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="device_count" label="设备数" width="90" align="center">
        <template #default="{ row }">
          <span class="count-pill">{{ row.device_count }} 台</span>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <span class="status-indicator" :class="row.status ? 'active' : 'disabled'">
            <span class="dot"></span>
            {{ row.status ? '正常' : '已禁用' }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" align="right">
        <template #default="{ row }">
          <button
            class="action-text-btn"
            :class="row.status ? 'danger' : 'success'"
            @click="handleToggleStatus(row)"
          >
            {{ row.status ? '禁用' : '解禁' }}
          </button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAdminUsersApi, updateAdminUserStatusApi } from '@/api/admin'
import type { AdminUserItem } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

const users = ref<AdminUserItem[]>([])
const loading = ref(false)

async function loadUsers() {
  loading.value = true
  try {
    const res = await getAdminUsersApi()
    users.value = res.users || []
  } catch {
    // handled
  } finally {
    loading.value = false
  }
}

async function handleToggleStatus(user: AdminUserItem) {
  const newStatus = user.status ? 0 : 1
  const actionText = newStatus ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(
      `确定要${actionText}用户「${user.username}」的账号吗？`,
      '确认提示',
      {
        confirmButtonText: `确认${actionText}`,
        cancelButtonText: '取消',
        type: newStatus ? 'info' : 'warning'
      }
    )

    await updateAdminUserStatusApi(user.id, newStatus)
    ElMessage.success(`用户「${user.username}」已成功${actionText}`)
    await loadUsers()
  } catch (err: any) {
    if (err !== 'cancel') {
      // handled
    }
  }
}

onMounted(() => {
  loadUsers()
})

defineExpose({
  loadUsers
})
</script>

<style scoped lang="scss">
.user-table-card {
  padding: 18px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

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

.refresh-icon-btn {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);
  color: var(--app-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--app-surface-hover);
    color: var(--app-text-primary);
  }

  &.spinning .el-icon {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.username-cell {
  display: flex;
  align-items: center;
  gap: 7px;

  .user-mini-avatar {
    background: var(--app-accent);
    color: #ffffff;
    font-weight: 600;
    font-size: 10px;
  }

  .name {
    font-weight: 600;
    font-size: 12.5px;
  }
}

.role-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;

  &.admin {
    background: var(--app-danger-subtle);
    color: var(--app-danger);
  }

  &.user {
    background: var(--app-hairline);
    color: var(--app-text-secondary);
  }
}

.count-pill {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: var(--app-text-secondary);
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 500;

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  &.active {
    color: var(--app-success);
    .dot { background: var(--app-success); }
  }

  &.disabled {
    color: var(--app-danger);
    .dot { background: var(--app-danger); }
  }
}

.action-text-btn {
  background: transparent;
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s ease;

  &.danger {
    color: var(--app-danger);
    &:hover { background: var(--app-danger-subtle); }
  }

  &.success {
    color: var(--app-success);
    &:hover { background: var(--app-success-subtle); }
  }
}
</style>
