<template>
  <div class="user-table-card glass-card">
    <div class="card-header">
      <div class="header-left">
        <h2>用户管理</h2>
        <span class="sub-text">查看并管理系统内所有注册用户及其设备配额与启停状态</span>
      </div>
      <el-button :icon="Refresh" circle size="small" @click="loadUsers" />
    </div>

    <el-table
      v-loading="loading"
      :data="users"
      stripe
      style="width: 100%"
      class="custom-table"
    >
      <el-table-column prop="username" label="用户名" min-width="140">
        <template #default="{ row }">
          <div class="username-cell">
            <el-avatar :size="24" class="user-mini-avatar">
              {{ row.username.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="name">{{ row.username }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="role" label="角色" width="110">
        <template #default="{ row }">
          <el-tag
            :type="row.role === 'ADMIN' ? 'danger' : 'info'"
            size="small"
            round
          >
            {{ row.role }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="device_count" label="绑定设备数" width="120" align="center">
        <template #default="{ row }">
          <span class="count-badge">{{ row.device_count }} 台</span>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="账号状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.status ? 'success' : 'danger'" size="small" round>
            {{ row.status ? '正常启用' : '已被禁用' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="130" align="right">
        <template #default="{ row }">
          <el-button
            :type="row.status ? 'danger' : 'success'"
            size="small"
            plain
            round
            @click="handleToggleStatus(row)"
          >
            {{ row.status ? '禁用账号' : '解禁账号' }}
          </el-button>
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
  padding: 22px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

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

  .username-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .user-mini-avatar {
      background: var(--app-accent);
      color: #04202b;
      font-weight: bold;
      font-size: 11px;
    }

    .name {
      font-weight: 500;
    }
  }

  .count-badge {
    font-weight: 600;
    font-size: 13px;
  }
}
</style>
