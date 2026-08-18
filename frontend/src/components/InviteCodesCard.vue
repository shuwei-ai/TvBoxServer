<template>
  <div class="invite-card bento-card">
    <div class="card-header">
      <div class="header-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <line x1="19" y1="8" x2="19" y2="14" />
          <line x1="22" y1="11" x2="16" y2="11" />
        </svg>
        <h2>我的邀请码</h2>
      </div>
      <el-button
        type="primary"
        size="small"
        plain
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
            <span class="status-badge" :class="item.status === 'UNUSED' ? 'unused' : 'used'">
              {{ item.status === 'UNUSED' ? '未使用' : '已核销' }}
            </span>
          </div>

          <el-tooltip content="复制邀请码" placement="top">
            <button class="copy-btn" @click="handleCopyCode(item.code)">
              <el-icon :size="13"><DocumentCopy /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-tip">
        <p>暂无邀请码记录</p>
        <span>点击上方「生成邀请码」可获取新凭证分享给好友</span>
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
  padding: 18px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .header-title {
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
}

.invite-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 2px;
}

.invite-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: var(--app-radius-md);
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--app-hairline-strong);
  }

  .code-info {
    display: flex;
    align-items: center;
    gap: 8px;

    .code-text {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--app-text-primary);
    }

    .status-badge {
      font-size: 10px;
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 600;

      &.unused {
        background: var(--app-success-subtle);
        color: var(--app-success);
      }

      &.used {
        background: var(--app-hairline);
        color: var(--app-text-muted);
      }
    }
  }

  .copy-btn {
    width: 24px;
    height: 24px;
    display: grid;
    place-items: center;
    border-radius: 5px;
    background: transparent;
    border: 1px solid transparent;
    color: var(--app-text-muted);
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      background: var(--app-surface-hover);
      color: var(--app-accent);
      border-color: var(--app-hairline);
    }
  }
}

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 12px;
  text-align: center;

  p {
    font-size: 13px;
    font-weight: 600;
    color: var(--app-text-primary);
    margin-bottom: 2px;
  }

  span {
    font-size: 11.5px;
    color: var(--app-text-muted);
  }
}
</style>
