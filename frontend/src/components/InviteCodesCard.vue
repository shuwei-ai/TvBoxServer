<template>
  <div class="invite-card glass-card">
    <div class="card-header">
      <h2>我的邀请码</h2>
      <el-button
        type="primary"
        size="small"
        plain
        round
        :icon="Plus"
        :loading="generating"
        @click="handleGenerate"
      >
        生成邀请码
      </el-button>
    </div>

    <div class="card-body">
      <!-- 邀请码列表 -->
      <div v-if="inviteCodes.length > 0" class="invite-list">
        <div
          v-for="(item, index) in inviteCodes"
          :key="index"
          class="invite-item"
        >
          <div class="code-info">
            <span class="code-text">{{ item.code }}</span>
            <el-tag
              :type="item.status === 'UNUSED' ? 'success' : 'info'"
              size="small"
              round
            >
              {{ item.status === 'UNUSED' ? '未使用' : '已使用' }}
            </el-tag>
          </div>

          <el-button
            size="small"
            circle
            :icon="DocumentCopy"
            @click="handleCopyCode(item.code)"
          />
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-tip">
        暂无邀请码，点击右上角「生成」可邀请新用户
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMyInvitesApi, generateInviteApi } from '@/api/invite'
import type { InviteCodeItem } from '@/types'
import { ElMessage } from 'element-plus'
import { Plus, DocumentCopy } from '@element-plus/icons-vue'

const inviteCodes = ref<InviteCodeItem[]>([])
const generating = ref(false)

async function loadInvites() {
  try {
    const res = await getMyInvitesApi()
    inviteCodes.value = res.codes || []
  } catch {
    // handled
  }
}

async function handleGenerate() {
  generating.value = true
  try {
    const res = await generateInviteApi()
    ElMessage.success(`邀请码生成成功: ${res.code}`)
    await loadInvites()
  } catch (err: any) {
    // handled
  } finally {
    generating.value = false
  }
}

async function handleCopyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success('邀请码已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

onMounted(() => {
  loadInvites()
})

defineExpose({
  loadInvites
})
</script>

<style scoped lang="scss">
.invite-card {
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
    .invite-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 220px;
      overflow-y: auto;
      padding-right: 4px;
    }

    .invite-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      border-radius: 10px;
      background: rgba(148, 163, 184, 0.05);
      border: 1px solid var(--app-card-border);

      .code-info {
        display: flex;
        align-items: center;
        gap: 10px;

        .code-text {
          font-family: 'JetBrains Mono', ui-monospace, monospace;
          font-weight: 600;
          font-size: 13px;
        }
      }
    }

    .empty-tip {
      font-size: 13px;
      color: var(--app-text-muted);
      text-align: center;
      padding: 20px 0;
    }
  }
}
</style>
