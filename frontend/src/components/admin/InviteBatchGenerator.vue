<template>
  <div class="batch-invite-card glass-card">
    <div class="card-header">
      <div class="header-left">
        <h2>系统邀请码批量生成</h2>
        <span class="sub-text">管理员可直接批量签发系统级有效邀请码</span>
      </div>
    </div>

    <div class="generator-body">
      <div class="input-row">
        <span class="label">生成数量:</span>
        <el-input-number
          v-model="count"
          :min="1"
          :max="20"
          size="default"
        />
        <el-button
          type="primary"
          :icon="Plus"
          :loading="generating"
          @click="handleGenerate"
        >
          批量生成
        </el-button>
      </div>

      <div v-if="generatedCodes.length > 0" class="generated-result">
        <div class="result-header">
          <span>本次生成的邀请码 ({{ generatedCodes.length }} 个):</span>
          <el-button
            type="primary"
            link
            :icon="DocumentCopy"
            @click="handleCopyAll"
          >
            一键全部复制
          </el-button>
        </div>

        <div class="code-chips">
          <el-tag
            v-for="(code, idx) in generatedCodes"
            :key="idx"
            type="success"
            size="large"
            effect="plain"
          >
            {{ code }}
          </el-tag>
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
    ElMessage.success(`成功生成 ${generatedCodes.value.length} 个系统邀请码！`)
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
    ElMessage.success('已全部复制到剪贴板！')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped lang="scss">
.batch-invite-card {
  padding: 22px;

  .card-header {
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

  .generator-body {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .input-row {
      display: flex;
      align-items: center;
      gap: 12px;

      .label {
        font-size: 13px;
        font-weight: 500;
      }
    }

    .generated-result {
      padding: 14px;
      background: rgba(148, 163, 184, 0.05);
      border: 1px solid var(--app-card-border);
      border-radius: 12px;

      .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-size: 13px;
        font-weight: 500;
      }

      .code-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .el-tag {
          font-family: 'JetBrains Mono', ui-monospace, monospace;
          font-size: 13px;
        }
      }
    }
  }
}
</style>
