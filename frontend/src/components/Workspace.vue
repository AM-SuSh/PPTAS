<script setup>
import { ref, computed } from 'vue'
import { pptApi } from '../api/index.js'
import ToolSidebar from './ToolSidebar.vue'
import PPTPreview from './PPTPreview.vue'
import ContentView from './ContentView.vue'

const props = defineProps({
  slides: Array,
  mindmap: Object,
  mindmapLoading: Boolean,
  mindmapError: String
})

const currentSlideIndex = ref(0)
const activeTool = ref('explain')
const isAnalyzing = ref(false)
const analysisCache = ref({})  // 缓存分析结果

const currentSlide = computed(() => props.slides[currentSlideIndex.value])

// 将 Markdown 转换为 HTML（简单版本）
const markdownToHtml = (markdown) => {
  if (!markdown) return ''
  return markdown
    .replace(/^### (.*)/gm, '<h3>$1</h3>')
    .replace(/^## (.*)/gm, '<h2>$1</h2>')
    .replace(/^# (.*)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n/g, '<br>')
}

// 分析页面
const analyzeCurrentPage = async () => {
  if (!currentSlide.value) return

  const pageId = currentSlideIndex.value + 1

  // 检查缓存
  if (analysisCache.value[pageId]) {
    const cached = analysisCache.value[pageId]
    Object.assign(currentSlide.value, cached)
    console.log('使用缓存数据:', cached)
    return
  }

  isAnalyzing.value = true
  console.log('🔄 开始分析页面:', pageId, '标题:', currentSlide.value.title)

  try {
    // 1. 分析页面
    console.log('📤 发送分析请求到后端...')
    console.log('   - 页面ID:', pageId)
    console.log('   - 标题:', currentSlide.value.title)
    console.log('   - 内容长度:', (currentSlide.value.raw_content || '').length, '字符')
    
    const analysisRes = await pptApi.analyzePage(
      pageId,
      currentSlide.value.title || '',
      currentSlide.value.raw_content || '',
      currentSlide.value.raw_points || []
    )

    console.log('📥 后端响应状态:', analysisRes.status)
    console.log('📥 后端响应内容:', analysisRes.data)
    
    // 处理响应数据
    let analysisData = null
    if (analysisRes.data && analysisRes.data.data) {
      analysisData = analysisRes.data.data
    } else if (analysisRes.data) {
      analysisData = analysisRes.data
    }
    
    if (!analysisData) {
      throw new Error('后端响应格式错误：无法提取分析数据')
    }
    
    console.log('✅ 提取的分析数据:', analysisData)
    console.log('   - deep_analysis 长度:', (analysisData.deep_analysis || '').length)
    console.log('   - key_concepts:', analysisData.key_concepts)
    console.log('   - learning_objectives:', analysisData.learning_objectives)

    // 2. 更新页面数据
    const enrichedSlide = {
      ...currentSlide.value,
      deep_analysis: analysisData.deep_analysis || '❌ 未获取到 AI 分析内容',
      deep_analysis_html: markdownToHtml(analysisData.deep_analysis || '❌ 未获取到 AI 分析内容'),
      key_concepts: analysisData.key_concepts || [],
      learning_objectives: analysisData.learning_objectives || [],
      references: analysisData.references || []
    }

    console.log('📝 富化后的页面数据:', enrichedSlide)

    // 3. 缓存结果
    analysisCache.value[pageId] = enrichedSlide
    Object.assign(currentSlide.value, enrichedSlide)

    // 4. 初始化助教
    try {
      console.log('🤖 初始化 AI 助教...')
      await pptApi.setTutorContext(
        pageId,
        currentSlide.value.title || '',
        currentSlide.value.raw_content || '',
        analysisData.key_concepts || []
      )
      console.log('✅ AI 助教初始化成功')
    } catch (err) {
      console.warn('⚠️ 初始化助教失败:', err)
    }
  } catch (error) {
    console.error('❌ 分析失败:', error)
    // 显示错误信息
    if (currentSlide.value) {
      currentSlide.value.deep_analysis = `❌ 分析失败: ${error.message || '未知错误'}`
      currentSlide.value.deep_analysis_html = `<div style="color: red; padding: 1rem; background: #ffe0e0; border-radius: 4px;"><strong>分析错误：</strong><br>${error.message || '未知错误'}</div>`
    }
  } finally {
    isAnalyzing.value = false
  }
}

const selectSlide = async (index) => {
  currentSlideIndex.value = index
  const pageId = index + 1

  // 已缓存则跳过分析
  if (analysisCache.value[pageId]) {
    const cached = analysisCache.value[pageId]
    Object.assign(props.slides[index], cached)
    return
  }

  // 执行分析
  await analyzeCurrentPage()
}

const handleToolChange = (toolName) => {
  activeTool.value = toolName
}
</script>

<template>
  <div class="workspace-layout">
    <div class="workspace-main">
      <div class="left-panel">
        <PPTPreview
          :slides="slides"
          :current-index="currentSlideIndex"
          @select="selectSlide"
        />
      </div>

      <div class="right-panel">
        <!-- 加载状态 -->
        <div v-if="isAnalyzing" class="loading-overlay">
          <div class="spinner"></div>
          <p>🤖 AI 正在深度分析...</p>
        </div>
        
        <!-- 内容展示 -->
        <ContentView
          v-else
          :slide="currentSlide"
          :active-tool="activeTool"
          :mindmap="mindmap"
          :mindmap-loading="mindmapLoading"
          :mindmap-error="mindmapError"
        />
      </div>
    </div>

    <!-- 工具栏 -->
    <ToolSidebar
      :active-tool="activeTool"
      @tool-change="handleToolChange"
    />
  </div>
</template>

<style scoped>
.workspace-layout {
  flex: 1;
  display: flex;
  height: calc(100vh - 64px);
  overflow: hidden;
  width: 100vw;
}
.workspace-container {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* 假设你使用了 Tab 切换或者分栏，确保导图容器撑满 */
.graph-wrapper {
  flex: 1;
  height: 100%;
  position: relative;
}
.workspace-main {
  flex: 1;
  display: flex;
  min-width: 0;
}

.left-panel {
  width: 40%;
  border-right: 1px solid #e2e8f0;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.right-panel {
  width: 60%;
  background: #ffffff;
  overflow-y: auto;
  position: relative;
  min-width: 0;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 100;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #0066cc;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-overlay p {
  font-size: 1rem;
  color: #666;
  margin: 0;
}
</style>
