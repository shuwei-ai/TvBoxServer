<template>
  <div class="batch-invite-card bento-card">
    <div class="card-header">
      <div class="header-left">
        <div class="title-with-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <h2>邀请码批量签发</h2>
        </div>
        <span class="sub-text">管理员直接生成全站通用的注册邀请码</span>
      </div>
    </div>

    <div class="generator-body">
      <div class="input-row">
        <span class="label">签发数量:</span>
        <el-input-number
          v-model="count"
          :min="1"
          :max="20"
          size="small"
        />
        <el-button
          type="primary"
          size="small"
          :icon="Plus"
          :loading="generating"
          @click="handleGenerate"
        >
          批量签发
        </el-button>
      </div>

      <div v-if="generatedCodes.length > 0" class="generated-result">
        <div class="result-header">
          <span>本次签发 ({{ generatedCodes.length }} 个):</span>
          <el-button
            type="primary"
            link
            size="small"
            :icon="DocumentCopy"
            @click="handleCopyAll"
          >
            一键复制全部
          </el-button>
        </div>

        <div class="code-chips">
          <span
            v-for="(code, idx) in generatedCodes"
            :key="idx"
            class="code-tag"
          >
            {{ code }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { generateAdminInvitesApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import { Plus, DocumentCopy } from '@element-plus/icons-vue'

const count = ref(5)
const generating = ref(false)
const generatedCodes = ref<string[]>([])

async function handleGenerate() {
  generating.value = true
  try {
    const res = await generateAdminInvitesApi({ count: count.value })
    generatedCodes.value = res.codes || []
    ElMessage.success(`成功签发 ${generatedCodes.value.length} 个系统邀请码！`)
    handleCopyAll()
  } catch {
    // handled
  } finally {
    generating.value = false
  }
}

async function handleCopyAll() {
  if (!generatedCodes.value.length) return
  try {
    await navigator.clipboard.writeText(generatedCodes.value.join('\n'))
    ElMessage.success('邀请码已全部复制到剪贴板！')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped lang="scss">
.batch-invite-card {
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

.generator-body {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .input-row {
    display: flex;
    align-items: center;
    gap: 10px;

    .label {
      font-size: 12.5px;
      color: var(--app-text-secondary);
      font-weight: 500;
    }
  }

  .generated-result {
    padding: 12px;
    background: var(--app-surface-subtle);
    border: 1px solid var(--app-hairline);
    border-radius: var(--app-radius-md);

    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 12px;
      font-weight: 500;
      color: var(--app-text-secondary);
    }

    .code-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;

      .code-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 5px;
        background: var(--app-success-subtle);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: var(--app-success);
      }
    }
  }
}
</style>
