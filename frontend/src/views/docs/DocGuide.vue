<template>
  <div class="doc-guide-container">
    <!-- 顶部快速操作与指引横幅 -->
    <div class="doc-hero bento-card">
      <div class="hero-content">
        <div class="hero-badge">
          <el-icon><Document /></el-icon>
          <span>官方使用手册与连接配置指南</span>
        </div>
        <h1 class="hero-title">TVBox & 遥控器配置使用说明</h1>
        <p class="hero-desc">
          本指南涵盖微信扫码入驻、Web 控制台设备绑定、TVBox 电视端长连接配置、手机 TBC 遥控器接入及大模型智能指令调用全流程。
        </p>
      </div>

      <!-- 快速复制配置卡片 -->
      <div class="quick-endpoints">
        <div class="endpoint-item">
          <div class="endpoint-meta">
            <span class="endpoint-label">TVBox WebSocket 服务地址</span>
            <span class="endpoint-proto ws">WSS</span>
          </div>
          <div class="endpoint-value-row">
            <code>wss://shuwei.iepose.cn/tvbox/ws/tvbox</code>
            <el-button size="small" :icon="CopyDocument" circle @click="copyText('wss://shuwei.iepose.cn/tvbox/ws/tvbox')" />
          </div>
        </div>

        <div class="endpoint-item">
          <div class="endpoint-meta">
            <span class="endpoint-label">手机遥控器 TBC API 服务地址</span>
            <span class="endpoint-proto http">HTTPS</span>
          </div>
          <div class="endpoint-value-row">
            <code>https://shuwei.iepose.cn/tvbox/</code>
            <el-button size="small" :icon="CopyDocument" circle @click="copyText('https://shuwei.iepose.cn/tvbox/')" />
          </div>
        </div>
      </div>
    </div>

    <!-- 主体区域：左侧 Markdown 渲染内容，右侧目录导航 -->
    <div class="doc-layout">
      <!-- 正文内容区 -->
      <article class="doc-article bento-card">
        <div class="article-inner markdown-body" v-html="renderedHtml" @click="handleArticleClick"></div>
      </article>

      <!-- 侧边目录导航栏 (TOC) -->
      <aside class="doc-toc-sidebar">
        <div class="toc-card bento-card">
          <div class="toc-header">
            <el-icon><List /></el-icon>
            <span>本页目录</span>
          </div>
          <nav class="toc-list" v-if="tocItems.length > 0">
            <a
              v-for="item in tocItems"
              :key="item.id"
              :href="`#${item.id}`"
              class="toc-item"
              :class="[`level-${item.level}`, { active: activeHeadingId === item.id }]"
              @click.prevent="scrollToHeading(item.id)"
            >
              {{ item.text }}
            </a>
          </nav>
          <div class="toc-footer">
            <el-button type="primary" plain size="small" class="w-full" :icon="Top" @click="scrollToTop">
              回到顶部
            </el-button>
          </div>
        </div>
      </aside>
    </div>

    <!-- 图片点击全屏预览 -->
    <el-image-viewer
      v-if="previewViewerVisible"
      :url-list="previewImages"
      :initial-index="previewIndex"
      @close="previewViewerVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import { Document, CopyDocument, List, Top } from '@element-plus/icons-vue'
import rawDocMarkdown from '@/assets/docs/设备连接配置使用说明.md?raw'

interface TocItem {
  id: string
  text: string
  level: number
}

const previewViewerVisible = ref(false)
const previewImages = ref<string[]>([])
const previewIndex = ref(0)
const activeHeadingId = ref<string>('')
const tocItems = ref<TocItem[]>([])

// 复制文本辅助函数
function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

// 预处理与增强 Markdown
function processMarkdown(content: string): { processed: string; toc: TocItem[] } {
  const toc: TocItem[] = []
  let headingCounter = 0

  // 1. 处理图片路径：将相对路径如 Screenshot_xxx.jpg 或 docs/Screenshot_xxx.jpg 替换为 /docs/Screenshot_xxx.jpg
  let text = content.replace(/!\[(.*?)\]\((.*?)\)/g, (_match, alt, src) => {
    let cleanSrc = src.trim()
    if (!cleanSrc.startsWith('http') && !cleanSrc.startsWith('/')) {
      cleanSrc = '/docs/' + cleanSrc.replace(/^docs\//, '')
    }
    return `![${alt}](${cleanSrc})`
  })

  // 2. 解析标题并生成 TOC
  text = text.replace(/^(#{1,3})\s+(.+)$/gm, (_match, hashes, title) => {
    headingCounter++
    const cleanTitle = title.trim()
    const id = `heading-${headingCounter}-${cleanTitle.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')}`
    const level = hashes.length
    toc.push({ id, text: cleanTitle, level })
    return `<h${level} id="${id}">${cleanTitle}</h${level}>`
  })

  // 3. 处理 GitHub 风格的 Blockquote Alerts (e.g. > [!IMPORTANT], > [!NOTE], > [!TIP], > [!WARNING])
  text = text.replace(
    />\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:>.*\n?)*)/gi,
    (_match, type, body) => {
      const cleanType = type.toUpperCase()
      const cleanBody = body
        .split('\n')
        .map((line: string) => line.replace(/^>\s?/, ''))
        .join('\n')
        .trim()

      const typeMap: Record<string, { title: string; class: string }> = {
        NOTE: { title: '提示 Note', class: 'alert-note' },
        TIP: { title: '技巧 Tip', class: 'alert-tip' },
        IMPORTANT: { title: '重要提示 Important', class: 'alert-important' },
        WARNING: { title: '注意事项 Warning', class: 'alert-warning' },
        CAUTION: { title: '特别警告 Caution', class: 'alert-danger' }
      }

      const info = typeMap[cleanType] || { title: cleanType, class: 'alert-note' }
      return `<div class="doc-alert-card ${info.class}">
        <div class="alert-header">
          <span class="alert-title">${info.title}</span>
        </div>
        <div class="alert-body">${marked.parse(cleanBody)}</div>
      </div>\n`
    }
  )

  return { processed: text, toc }
}

const { processed, toc } = processMarkdown(rawDocMarkdown)
tocItems.value = toc

const renderedHtml = computed(() => {
  return marked.parse(processed)
})

// 点击正文处理图片放大和代码复制
function handleArticleClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (target && target.tagName === 'IMG') {
    const imgEl = target as HTMLImageElement
    const src = imgEl.src
    if (src) {
      // 收集文章中所有图片
      const allImgs = Array.from(document.querySelectorAll('.doc-article .markdown-body img')) as HTMLImageElement[]
      previewImages.value = allImgs.map((img) => img.src)
      const foundIdx = previewImages.value.indexOf(src)
      previewIndex.value = foundIdx >= 0 ? foundIdx : 0
      previewViewerVisible.value = true
    }
  }
}

// 滚动定位
function scrollToHeading(id: string) {
  const el = document.getElementById(id)
  if (el) {
    const top = el.getBoundingClientRect().top + window.scrollY - 80
    window.scrollTo({ top, behavior: 'smooth' })
    activeHeadingId.value = id
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 监听滚动更新目录高亮
function onScroll() {
  const scrollPos = window.scrollY + 120
  for (let i = tocItems.value.length - 1; i >= 0; i--) {
    const item = tocItems.value[i]
    const el = document.getElementById(item.id)
    if (el && el.offsetTop <= scrollPos) {
      activeHeadingId.value = item.id
      break
    }
  }
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  nextTick(() => {
    if (tocItems.value.length > 0) {
      activeHeadingId.value = tocItems.value[0].id
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped lang="scss">
.doc-guide-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 40px;
}

/* 顶部横幅 */
.doc-hero {
  padding: 24px 28px;
  background: var(--app-surface);
  border: 1px solid var(--app-hairline);
  border-radius: var(--app-radius-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  box-shadow: var(--app-shadow);

  .hero-content {
    flex: 1;
    min-width: 0;

    .hero-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 11.5px;
      font-weight: 600;
      background: var(--app-accent-subtle);
      color: var(--app-accent);
      margin-bottom: 10px;
    }

    .hero-title {
      font-size: 22px;
      font-weight: 700;
      color: var(--app-text-primary);
      margin: 0 0 8px;
      letter-spacing: -0.02em;
    }

    .hero-desc {
      font-size: 13px;
      line-height: 1.6;
      color: var(--app-text-secondary);
      margin: 0;
    }
  }

  .quick-endpoints {
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-width: 380px;

    .endpoint-item {
      padding: 10px 14px;
      border-radius: 8px;
      background: var(--app-surface-subtle);
      border: 1px solid var(--app-hairline);

      .endpoint-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;

        .endpoint-label {
          font-size: 11.5px;
          color: var(--app-text-muted);
          font-weight: 500;
        }

        .endpoint-proto {
          font-size: 10px;
          font-weight: 700;
          padding: 1px 6px;
          border-radius: 4px;
          font-family: 'JetBrains Mono', monospace;

          &.ws {
            background: rgba(94, 106, 210, 0.15);
            color: var(--app-accent);
          }

          &.http {
            background: rgba(16, 185, 129, 0.15);
            color: var(--app-success);
          }
        }
      }

      .endpoint-value-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;

        code {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          color: var(--app-text-primary);
          background: transparent;
          user-select: all;
          word-break: break-all;
        }
      }
    }
  }
}

/* 主体左右布局 */
.doc-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.doc-article {
  flex: 1;
  min-width: 0;
  padding: 36px 40px;
  background: var(--app-surface);
  border: 1px solid var(--app-hairline);
  border-radius: var(--app-radius-lg);
  box-shadow: var(--app-shadow);
}

/* 侧边 TOC */
.doc-toc-sidebar {
  width: 260px;
  position: sticky;
  top: 24px;
  flex-shrink: 0;

  .toc-card {
    padding: 16px;
    background: var(--app-surface);
    border: 1px solid var(--app-hairline);
    border-radius: var(--app-radius-lg);
    box-shadow: var(--app-shadow);
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 48px);

    .toc-header {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 700;
      color: var(--app-text-primary);
      padding-bottom: 10px;
      border-bottom: 1px solid var(--app-hairline);
      margin-bottom: 10px;
    }

    .toc-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
      overflow-y: auto;
      flex: 1;
      padding-right: 4px;

      .toc-item {
        display: block;
        padding: 5px 8px;
        font-size: 12px;
        color: var(--app-text-secondary);
        text-decoration: none;
        border-radius: 6px;
        line-height: 1.4;
        transition: all 0.15s ease;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;

        &:hover {
          color: var(--app-accent);
          background: var(--app-surface-hover);
        }

        &.active {
          color: var(--app-accent);
          background: var(--app-accent-subtle);
          font-weight: 600;
        }

        &.level-2 {
          font-weight: 600;
        }

        &.level-3 {
          padding-left: 18px;
          font-size: 11.5px;
          color: var(--app-text-muted);
        }
      }
    }

    .toc-footer {
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid var(--app-hairline);
    }
  }
}

.w-full {
  width: 100%;
}

@media (max-width: 992px) {
  .doc-hero {
    flex-direction: column;
    align-items: stretch;

    .quick-endpoints {
      min-width: 100%;
    }
  }

  .doc-layout {
    flex-direction: column;
  }

  .doc-toc-sidebar {
    display: none;
  }

  .doc-article {
    padding: 20px;
  }
}
</style>

<!-- 全局 Markdown 文章渲染样式 -->
<style lang="scss">
.doc-article .markdown-body {
  color: var(--app-text-primary);
  font-size: 14.5px;
  line-height: 1.75;

  h1, h2, h3, h4, h5, h6 {
    color: var(--app-text-primary);
    font-weight: 700;
    margin-top: 28px;
    margin-bottom: 14px;
    letter-spacing: -0.015em;
    scroll-margin-top: 80px;

    &:first-child {
      margin-top: 0;
    }
  }

  h1 {
    font-size: 24px;
    border-bottom: 1px solid var(--app-hairline);
    padding-bottom: 12px;
  }

  h2 {
    font-size: 18px;
    border-bottom: 1px solid var(--app-hairline);
    padding-bottom: 8px;
    margin-top: 36px;
  }

  h3 {
    font-size: 15.5px;
    margin-top: 24px;
  }

  p {
    margin: 10px 0 14px;
    color: var(--app-text-secondary);
  }

  ul, ol {
    padding-left: 24px;
    margin: 10px 0 14px;
    color: var(--app-text-secondary);

    li {
      margin-bottom: 6px;
    }
  }

  strong {
    color: var(--app-text-primary);
    font-weight: 600;
  }

  a {
    color: var(--app-accent);
    text-decoration: none;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }

  hr {
    height: 1px;
    background-color: var(--app-hairline);
    border: none;
    margin: 32px 0;
  }

  /* 表格美化 */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 18px 0 24px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--app-hairline);

    th, td {
      padding: 10px 16px;
      text-align: left;
      font-size: 13px;
      border-bottom: 1px solid var(--app-hairline);
    }

    th {
      background: var(--app-surface-subtle);
      color: var(--app-text-primary);
      font-weight: 600;
    }

    td {
      color: var(--app-text-secondary);
    }

    tr:last-child td {
      border-bottom: none;
    }
  }

  /* 代码块与行内代码 */
  code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 12.5px;
    padding: 2px 6px;
    border-radius: 5px;
    background: var(--app-surface-subtle);
    color: var(--app-accent);
    border: 1px solid var(--app-hairline);
  }

  pre {
    background: var(--app-surface-subtle);
    border: 1px solid var(--app-hairline);
    border-radius: 8px;
    padding: 14px 16px;
    overflow-x: auto;
    margin: 14px 0 18px;

    code {
      background: transparent;
      padding: 0;
      border: none;
      color: var(--app-text-primary);
      font-size: 13px;
    }
  }

  /* 图片展示与阴影 */
  img {
    max-width: 100%;
    height: auto;
    border-radius: 10px;
    border: 1px solid var(--app-hairline);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    margin: 14px 0 22px;
    cursor: zoom-in;
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
  }

  /* 自定义 Alert 卡片 */
  .doc-alert-card {
    border-radius: 8px;
    padding: 12px 16px;
    margin: 16px 0 20px;
    border-left: 4px solid;

    .alert-header {
      font-size: 12.5px;
      font-weight: 700;
      margin-bottom: 4px;
    }

    .alert-body {
      font-size: 13px;
      color: var(--app-text-secondary);

      p {
        margin: 0;
      }
    }

    &.alert-important {
      background: rgba(94, 106, 210, 0.08);
      border-color: var(--app-accent);
      .alert-header { color: var(--app-accent); }
    }

    &.alert-note {
      background: rgba(59, 130, 246, 0.08);
      border-color: var(--app-blue);
      .alert-header { color: var(--app-blue); }
    }

    &.alert-tip {
      background: rgba(16, 185, 129, 0.08);
      border-color: var(--app-success);
      .alert-header { color: var(--app-success); }
    }

    &.alert-warning {
      background: rgba(245, 158, 11, 0.08);
      border-color: var(--app-warning);
      .alert-header { color: var(--app-warning); }
    }

    &.alert-danger {
      background: rgba(239, 68, 68, 0.08);
      border-color: var(--app-danger);
      .alert-header { color: var(--app-danger); }
    }
  }
}
</style>
