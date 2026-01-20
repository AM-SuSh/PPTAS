<script setup>
import { ref, computed, onMounted } from 'vue'
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

// 生命周期：当 slides 加载完成后，自动分析第一页
onMounted(async () => {
  if (props.slides && props.slides.length > 0) {
    console.log('📋 Workspace 挂载，slides 数量:', props.slides.length)
    // 自动分析第一页
    setTimeout(() => {
      selectSlide(0)
    }, 500)
  }
})

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
  if (!currentSlide.value) {
    console.warn('⚠️ currentSlide 为空，无法分析')
    return
  }

  const pageId = currentSlideIndex.value + 1

  // 检查缓存
  if (analysisCache.value[pageId]) {
    const cached = analysisCache.value[pageId]
    Object.assign(currentSlide.value, cached)
    console.log('✅ 使用缓存数据 (页面 ' + pageId + '):', {
      deep_analysis_length: (cached.deep_analysis || '').length,
      key_concepts: cached.key_concepts?.length || 0,
      learning_objectives: cached.learning_objectives?.length || 0
    })
    return
  }

  isAnalyzing.value = true
  console.log('🔄 开始分析页面:', pageId, '| 标题:', currentSlide.value.title)

  try {
    // 1. 分析页面
    console.log('📤 发送分析请求到后端 /api/v1/analyze-page')
    console.log('   参数: pageId=' + pageId + ', title="' + currentSlide.value.title + '"')
    
    const analysisRes = await pptApi.analyzePage(
      pageId,
      currentSlide.value.title || '',
      currentSlide.value.raw_content || '',
      currentSlide.value.raw_points || []
    )

    console.log('📥 后端响应状态:', analysisRes.status)
    console.log('📥 后端响应:', JSON.stringify(analysisRes.data).substring(0, 200) + '...')
    
    // 处理响应数据
    let analysisData = null
    if (analysisRes.data?.data) {
      analysisData = analysisRes.data.data
    } else if (analysisRes.data?.success) {
      // 可能返回的是其他格式
      analysisData = analysisRes.data
    }
    
    if (!analysisData || !analysisData.deep_analysis) {
      console.error('❌ 响应格式错误或缺少 deep_analysis 字段')
      console.error('完整响应:', analysisRes.data)
      throw new Error('后端返回的数据格式不正确，缺少 deep_analysis 字段')
    }
    
    console.log('✅ 成功提取分析数据:')
    console.log('   - deep_analysis 长度:', analysisData.deep_analysis.length, '字符')
    console.log('   - key_concepts 数量:', analysisData.key_concepts?.length || 0)
    console.log('   - learning_objectives 数量:', analysisData.learning_objectives?.length || 0)
    console.log('   - references 数量:', analysisData.references?.length || 0)

    // 2. 更新页面数据
    const enrichedSlide = {
      ...currentSlide.value,
      deep_analysis: analysisData.deep_analysis,
      deep_analysis_html: markdownToHtml(analysisData.deep_analysis),
      key_concepts: analysisData.key_concepts || [],
      learning_objectives: analysisData.learning_objectives || [],
      references: analysisData.references || [],
      raw_points: analysisData.raw_points || currentSlide.value.raw_points || []
    }

    console.log('📝 页面数据已更新，准备显示在 UI 中')

    // 3. 缓存结果
    analysisCache.value[pageId] = enrichedSlide
    Object.assign(currentSlide.value, enrichedSlide)
    console.log('💾 分析结果已缓存')

    // 4. 初始化助教
    try {
      console.log('🤖 初始化 AI 助教 (页面 ' + pageId + ')')
      await pptApi.setTutorContext(
        pageId,
        currentSlide.value.title || '',
        currentSlide.value.raw_content || '',
        analysisData.key_concepts || []
      )
      console.log('✅ AI 助教初始化成功')
    } catch (err) {
      console.warn('⚠️ 初始化助教失败（非致命错误）:', err.message)
    }
  } catch (error) {
    console.error('❌ 页面分析失败:', error)
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
    console.log('✅ 使用缓存数据:', cached)
    return
  }

  // 如果没有 deep_analysis，执行分析
  if (!props.slides[index]?.deep_analysis) {
    console.log('🔄 页面 ' + pageId + ' 需要分析，触发 analyzeCurrentPage...')
    await analyzeCurrentPage()
  } else {
    console.log('✅ 页面 ' + pageId + ' 已有分析数据，无需重新分析')
  }
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
        <!-- 内容展示 -->
        <ContentView
          :slide="currentSlide"
          :active-tool="activeTool"
          :mindmap="mindmap"
          :mindmap-loading="mindmapLoading"
          :mindmap-error="mindmapError"
          :is-analyzing="isAnalyzing"
        />
        
        <!-- 加载状态浮层 -->
        <div v-if="isAnalyzing" class="loading-overlay">
          <div class="spinner"></div>
          <p>🤖 AI 正在深度分析...</p>
        </div>
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
