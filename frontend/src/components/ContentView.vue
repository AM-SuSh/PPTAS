<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { pptApi } from '../api/index.js'

const props = defineProps({
  slide: Object,
  activeTool: String
})

// Chat 相关
const chatMessages = ref([])
const userChatInput = ref('')
const isChatting = ref(false)
const messagesContainer = ref(null)

// Search 相关
const searchQuery = ref('')
const isSearching = ref(false)
const searchResults = ref([])
const searchType = ref('all')

// Markdown 转 HTML 工具函数
const markdownToHtml = (markdown) => {
  if (!markdown) return ''
  return markdown
    .replace(/^### (.*)/gm, '<h3>$1</h3>')
    .replace(/^## (.*)/gm, '<h2>$1</h2>')
    .replace(/^# (.*)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n- (.*)/gm, '\n<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[^>]*>)/gm, '<p>')
    .replace(/$/gm, '</p>')
    .replace(/\n/g, '<br>')
}

// 初始化聊天
onMounted(() => {
  if (props.slide?.page_id) {
    initChat()
  }
})

const initChat = async () => {
  if (!props.slide?.title) return
  
  chatMessages.value = [
    {
      role: 'assistant',
      content: `你好！我是基于当前 PPT 的助教。关于 "${props.slide.title}" 你有什么疑问吗？`,
      timestamp: new Date().toISOString()
    }
  ]
}

// 发送聊天消息
const sendChatMessage = async () => {
  if (!userChatInput.value.trim() || !props.slide) return
  
  const pageId = props.slide.page_num || 1
  const message = userChatInput.value
  
  chatMessages.value.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })
  
  userChatInput.value = ''
  isChatting.value = true
  
  try {
    const response = await pptApi.chat(pageId, message)
    
    chatMessages.value.push({
      role: 'assistant',
      content: response.data.response || response.data.data?.response || 'AI 助教无法回答',
      timestamp: new Date().toISOString()
    })
    
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  } catch (error) {
    console.error('聊天失败:', error)
    chatMessages.value.push({
      role: 'assistant',
      content: '❌ 对不起，AI 暂时无法回答。请检查网络连接或稍后重试。',
      timestamp: new Date().toISOString()
    })
  } finally {
    isChatting.value = false
  }
}

const handleChatKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendChatMessage()
  }
}

// 搜索参考文献
const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  isSearching.value = true
  
  try {
    const response = await pptApi.searchReferences(
      searchQuery.value,
      10,
      searchType.value === 'all' ? null : searchType.value
    )
    
    searchResults.value = response.data.references || response.data.data?.references || []
  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

// 学习目标列表
const learningObjectives = computed(() => {
  return props.slide?.learning_objectives || []
})

// 关键概念列表
const keyConcepts = computed(() => {
  return props.slide?.key_concepts || []
})

const handleSearch = () => {
  isSearching.value = true
  setTimeout(() => {
    isSearching.value = false
  }, 1000)
}
</script>

<template>
  <div class="content-view">
    <div v-if="activeTool === 'explain' && slide" class="view-section">
      <div class="content-header">
        <h2 class="slide-title">{{ slide.title }}</h2>
        <span class="ai-badge">✨ AI 自动扩展</span>
      </div>

      <div class="content-body">
        <div class="card">
          <h3 class="card-title">原始逻辑</h3>
          <div class="point-container">
            <template v-for="(point, idx) in slide.raw_points" :key="idx">
              <!-- 文本段落 -->
              <div 
                v-if="point.type === 'text'" 
                class="point-item"
                :class="`level-${point.level || 0}`"
              >
                <div class="point-marker">
                   <span v-if="(point.level || 0) === 0">•</span>
                   <span v-else-if="(point.level || 0) === 1">◦</span>
                   <span v-else>-</span>
                </div>
                <div class="point-content">{{ point.text }}</div>
              </div>
              
              <!-- 表格 -->
              <div v-else-if="point.type === 'table'" class="point-table-wrapper">
                 <table class="simple-table">
                   <tbody>
                     <tr v-for="(row, rIdx) in point.data" :key="rIdx">
                       <td v-for="(cell, cIdx) in row" :key="cIdx">{{ cell }}</td>
                     </tr>
                   </tbody>
                 </table>
              </div>
            </template>
          </div>
          <!-- 图片信息展示区域 -->
          <div v-if="slide.images && slide.images.length > 0" class="image-info-section">
            <div class="info-label">🖼️ 幻灯片图像信息:</div>
            <ul class="image-list">
              <li v-for="(imgInfo, index) in slide.images" :key="index" class="image-item">
                {{ imgInfo }}
              </li>
            </ul>
          </div>
        </div>

        <!-- AI 深度分析 -->
        <div class="card ai-card">
          <h3 class="card-title">🤖 AI 深度解析</h3>
          
          <!-- 学习目标 -->
          <div v-if="learningObjectives.length > 0" class="analysis-section">
            <h4 class="section-title">📚 学习目标</h4>
            <ul class="objectives-list">
              <li v-for="(obj, idx) in learningObjectives" :key="idx" class="objective-item">
                {{ obj }}
              </li>
            </ul>
          </div>

          <!-- 关键概念 -->
          <div v-if="keyConcepts.length > 0" class="analysis-section">
            <h4 class="section-title">🎯 关键概念</h4>
            <div class="concepts-tags">
              <span v-for="concept in keyConcepts" :key="concept" class="tag">
                {{ concept }}
              </span>
            </div>
          </div>

          <!-- 深度分析内容 -->
          <div class="analysis-section">
            <h4 class="section-title">🤖 AI 深度分析</h4>
            
            <!-- 成功加载的分析内容 -->
            <div v-if="slide.deep_analysis && !slide.deep_analysis.includes('待补充') && !slide.deep_analysis.includes('❌')" class="markdown-body">
              <div v-html="slide.deep_analysis_html || markdownToHtml(slide.deep_analysis)"></div>
            </div>

            <!-- 错误状态 -->
            <div v-else-if="slide.deep_analysis && slide.deep_analysis.includes('❌')" class="error-box">
              <strong>⚠️ 分析失败</strong>
              <p>{{ slide.deep_analysis }}</p>
              <details class="error-details">
                <summary>查看错误详情</summary>
                <pre>{{ slide.deep_analysis }}</pre>
              </details>
            </div>

            <!-- 等待分析状态 -->
            <div v-else class="pending-box">
              <div class="pending-icon">⏳</div>
              <p><strong>等待 AI 分析...</strong></p>
              <p class="hint-text">如果长时间未显示结果，请检查以下调试信息：</p>
              
              <!-- 详细调试信息 -->
              <div class="debug-info-inline">
                <div class="debug-item">
                  <strong>📄 当前页面:</strong> 
                  <span>{{ slide.page_num || '未知' }} - {{ slide.title }}</span>
                </div>
                
                <div class="debug-item">
                  <strong>📊 数据状态:</strong>
                  <span v-if="!slide.deep_analysis">❌ deep_analysis 字段为空</span>
                  <span v-else-if="slide.deep_analysis.includes('待补充')">⏳ 标记为"待补充"</span>
                  <span v-else>✓ 已有内容 ({{ slide.deep_analysis.length }} 字符)</span>
                </div>
                
                <div class="debug-item">
                  <strong>🔍 后端连接:</strong>
                  <span>检查 http://localhost:8000 是否运行</span>
                </div>
                
                <div class="debug-item">
                  <strong>🔑 API 配置:</strong>
                  <span>检查 OpenAI API Key 是否正确配置</span>
                </div>
                
                <div class="debug-item">
                  <strong>📡 网络请求:</strong>
                  <span>打开浏览器控制台 (F12) → Network 标签</span>
                </div>
                
                <!-- 查看发送到 LLM 的 Prompt -->
                <details class="prompt-details">
                  <summary>🎯 查看发送给 LLM 的 Prompt 信息</summary>
                  <div class="prompt-content">
                    <div class="prompt-section">
                      <h5>📝 输入内容 (Input):</h5>
                      <div class="code-block">
                        <strong>页面标题:</strong> {{ slide.title }}<br>
                        <strong>原始要点:</strong>
                        <pre>{{ JSON.stringify(slide.raw_points, null, 2) }}</pre>
                        <strong>图像信息:</strong> {{ slide.images?.join(', ') || '无' }}
                      </div>
                    </div>
                    
                    <div class="prompt-section">
                      <h5>💬 预期 Prompt 模板:</h5>
                      <div class="code-block">
                        <pre>基于以下 PPT 内容，提供深度分析：

标题: {{ slide.title }}

内容要点:
{{ slide.raw_points?.map(p => p.text).join('\n') }}

图像: {{ slide.images?.join(', ') || '无' }}

请提供:
1. 详细的概念解释
2. 实际应用案例
3. 相关理论背景
4. 学习建议</pre>
                      </div>
                    </div>
                    
                    <div class="prompt-section">
                      <h5>🔧 后端 API 调用信息:</h5>
                      <div class="code-block">
                        <strong>API 端点:</strong> POST /api/ppt/analyze<br>
                        <strong>请求参数:</strong>
                        <pre>{
  "page_id": {{ slide.page_num }},
  "title": "{{ slide.title }}",
  "content": {{ JSON.stringify(slide.raw_points) }}
}</pre>
                      </div>
                    </div>
                    
                    <div class="prompt-section">
                      <h5>📋 检查清单:</h5>
                      <ul class="checklist">
                        <li>✓ 检查后端日志中是否有此页面的处理记录</li>
                        <li>✓ 确认 LLM API 调用是否成功（查看后端日志）</li>
                        <li>✓ 检查是否有 rate limit 或配额限制</li>
                        <li>✓ 验证返回的 JSON 格式是否正确</li>
                        <li>✓ 查看控制台 Console 标签是否有 JavaScript 错误</li>
                      </ul>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>

          <!-- 原始数据调试（始终显示） -->
          <div class="debug-section">
            <details>
              <summary>📊 完整调试信息 - 原始数据</summary>
              <div class="debug-content">
                <div class="debug-item">
                  <strong>页面 ID:</strong> {{ slide.page_num || '未知' }}
                </div>
                <div class="debug-item">
                  <strong>标题:</strong> {{ slide.title }}
                </div>
                <div class="debug-item">
                  <strong>AI 分析内容长度:</strong> {{ slide.deep_analysis?.length || 0 }} 字符
                </div>
                <div class="debug-item">
                  <strong>关键概念:</strong> {{ slide.key_concepts?.join(', ') || '无' }}
                </div>
                <div class="debug-item">
                  <strong>学习目标:</strong> {{ slide.learning_objectives?.join(', ') || '无' }}
                </div>
                <div class="debug-item">
                  <strong>参考文献数:</strong> {{ slide.references?.length || 0 }}
                </div>
                <hr>
                <strong>原始 AI 分析（Markdown）:</strong>
                <pre class="raw-content">{{ slide.deep_analysis || '(空)' }}</pre>
                <hr>
                <strong>完整 Slide 对象:</strong>
                <pre class="raw-content">{{ JSON.stringify(slide, null, 2) }}</pre>
              </div>
            </details>
          </div>
        </div>

        <!-- 参考文献 -->
        <div v-if="slide.references && slide.references.length > 0" class="card references-card">
          <h3 class="card-title">📚 参考文献</h3>
          <div class="references-list">
            <a 
              v-for="(ref, idx) in slide.references" 
              :key="idx" 
              :href="ref.url" 
              target="_blank"
              rel="noopener noreferrer"
              class="reference-link"
            >
              <div class="ref-header">
                <span class="ref-title">{{ ref.title }}</span>
                <span class="ref-source">{{ ref.source }}</span>
              </div>
              <p v-if="ref.snippet" class="ref-snippet">{{ ref.snippet }}</p>
            </a>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTool === 'state-of-art'" class="view-section mindmap-view">
      <div class="placeholder-graphic">
        <div class="node center">"{{ slide?.title }}"</div>
        <div class="branches">
          <div class="node branch">核心概念</div>
          <div class="node branch">应用场景</div>
          <div class="node branch">相关论文</div>
        </div>
      </div>
      <p class="text-hint">正在根据当前页内容生成动态思维导图...</p>
    </div>

    <div v-if="activeTool === 'search'" class="view-section search-view">
      <div class="search-bar">
        <input v-model="searchQuery" type="text" placeholder="输入关键词搜索学术资源..." class="search-input" />
        <button @click="handleSearch" class="search-btn">🔍</button>
      </div>

      <div v-if="!isSearching" class="search-results">
        <div class="result-item">
          <div class="result-source">Arxiv</div>
          <h4 class="result-title">Attention Is All You Need</h4>
          <p class="result-snippet">The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...</p>
          <a href="#" class="result-link">Read Paper →</a>
        </div>
        <div class="result-item">
          <div class="result-source wiki">Wikipedia</div>
          <h4 class="result-title">Transformer (machine learning model)</h4>
          <p class="result-snippet">A transformer is a deep learning model that adopts the mechanism of self-attention...</p>
          <a href="#" class="result-link">Read Article →</a>
        </div>
      </div>

      <div v-else class="loading-state">
        <div class="mini-spinner"></div>
        <p>正在搜索知识库...</p>
      </div>
    </div>

    <div v-if="activeTool === 'chat'" class="view-section chat-view">
      <div class="chat-container">
        <div class="message ai">
          <span class="avatar">🤖</span>
          <div class="bubble">你好！我是基于当前 PPT 的助教。关于 "{{ slide?.title }}" 你有什么疑问吗？</div>
        </div>
      </div>
      <div class="chat-input-area">
        <input type="text" placeholder="向 AI 提问..." class="chat-input" />
        <button class="send-btn">发送</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content-view {
  height: 100%;
  overflow-y: auto;
  padding: 2rem;
  background: #ffffff;
}

.view-section {
  animation: fadeIn 0.3s ease;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  border-bottom: 2px solid #f1f5f9;
  padding-bottom: 1rem;
}

.slide-title {
  font-size: 1.8rem;
  color: #1e293b;
  margin: 0;
}

.ai-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.content-body {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  background: #fff;
}

.ai-card {
  border-left: 4px solid #3b82f6;
  background: #f8fafc;
}

.card-title {
  font-size: 1rem;
  color: #64748b;
  margin: 0 0 1rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.point-list {
  padding-left: 1.2rem;
  color: #475569;
  line-height: 1.8;
}

.image-info-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dashed #e2e8f0;
}

.info-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.image-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.image-item {
  font-size: 0.85rem;
  color: #059669;
  background: #ecfdf5;
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 4px;
  display: inline-block;
  margin-right: 6px;
}

.markdown-body {
  color: #334155;
  line-height: 1.8;
  word-wrap: break-word;
}

.ai-analysis-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.analysis-section {
  padding: 1rem;
  background: #f0f7ff;
  border-left: 4px solid #0066cc;
  border-radius: 6px;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #0066cc;
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.objectives-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.objective-item {
  padding: 0.5rem 0.75rem;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #3b82f6;
  color: #334155;
  font-size: 0.9rem;
}

.concepts-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  background: #e0e7ff;
  color: #4338ca;
  padding: 0.35rem 0.9rem;
  border-radius: 16px;
  font-size: 0.85rem;
  border: 1px solid #c7d2fe;
  font-weight: 500;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: #999;
  background: #f9fafb;
  border-radius: 6px;
}

.no-data p {
  margin: 0.5rem 0;
  font-size: 0.95rem;
}

.hint {
  color: #666;
  font-size: 0.85rem;
  margin-top: 1rem !important;
}

.hint-list {
  text-align: left;
  display: inline-block;
  color: #666;
  font-size: 0.85rem;
  padding: 0.5rem 1.5rem;
  list-style-type: disc;
}

.hint-list li {
  margin: 0.25rem 0;
}

.debug-info {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #f5f5f5;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.debug-info summary {
  cursor: pointer;
  color: #666;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0.5rem;
  user-select: none;
}

.debug-info summary:hover {
  color: #0066cc;
}

.debug-info pre {
  margin: 0.75rem 0 0 0;
  padding: 0.75rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #ddd;
  overflow-x: auto;
  font-size: 0.75rem;
  line-height: 1.4;
  color: #333;
  max-height: 200px;
  overflow-y: auto;
}

.references-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  background: #fff;
}

.references-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reference-link {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f9fafb;
  text-decoration: none;
  transition: all 0.2s ease;
  display: block;
  cursor: pointer;
}

.reference-link:hover {
  border-color: #3b82f6;
  background: #f0f7ff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
  transform: translateY(-2px);
}

.ref-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.ref-title {
  color: #0066cc;
  font-weight: 600;
  font-size: 0.95rem;
  flex: 1;
}

.ref-source {
  background: #e0e7ff;
  color: #4338ca;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.ref-snippet {
  color: #64748b;
  font-size: 0.85rem;
  line-height: 1.5;
  margin: 0;
}

.content-link {
  display: block;
  padding: 10px;
  background: #f1f5f9;
  border-radius: 6px;
  margin-bottom: 8px;
  color: #3b82f6;
  text-decoration: none;
  transition: 0.2s;
}

.content-link:hover {
  background: #e2e8f0;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
  background: #cbd5e1;
  color: #475569;
  margin-left: 8px;
}

.mindmap-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 80%;
}

.placeholder-graphic {
  position: relative;
  width: 300px;
  height: 300px;
  border: 2px dashed #cbd5e1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node {
  padding: 8px 16px;
  border-radius: 20px;
  background: white;
  border: 2px solid #3b82f6;
  font-weight: 600;
  position: absolute;
}

.node.center {
  background: #3b82f6;
  color: white;
  z-index: 2;
}

.branches .node.branch {
  top: 50%;
  left: 50%;
  font-size: 0.8rem;
  background: #fff;
  color: #3b82f6;
}

.branches .node:nth-child(1) { transform: translate(-40px, -120px); }
.branches .node:nth-child(2) { transform: translate(80px, -60px); }
.branches .node:nth-child(3) { transform: translate(20px, 80px); }

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 2rem;
}

.search-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
}

.search-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  width: 50px;
  cursor: pointer;
  font-size: 1.2rem;
}

.result-item {
  padding: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  transition: 0.2s;
}

.result-item:hover {
  background: #f8fafc;
}

.result-source {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: #cbd5e1;
  color: #475569;
}

.result-source.wiki {
  background: #dbeafe;
  color: #1e40af;
}

.result-title {
  font-size: 1.1rem;
  margin: 0 0 0.5rem 0;
  color: #1e293b;
}

.result-link {
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  display: inline-block;
  margin-top: 0.5rem;
}

.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 1rem;
}

.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.message.ai {
  flex-direction: row;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.bubble {
  background: #f1f5f9;
  padding: 1rem;
  border-radius: 12px;
  border-top-left-radius: 2px;
  max-width: 80%;
  line-height: 1.6;
}

.chat-input-area {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.chat-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  outline: none;
}

.send-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0 20px;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 600;
}

.mini-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* New Semantic Styles */
.point-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.point-item {
  display: flex;
  gap: 0.5rem;
  line-height: 1.6;
  color: #334155;
}
.point-marker {
  color: #64748b;
  font-weight: bold;
  min-width: 15px;
  text-align: center;
}
.level-0 { margin-left: 0; font-weight: 500; }
.level-1 { margin-left: 1.5rem; font-size: 0.95em; color: #475569; }
.level-2 { margin-left: 3rem; font-size: 0.9em; color: #64748b; }
.level-3 { margin-left: 4.5rem; }

.point-table-wrapper {
  margin: 1rem 0;
  overflow-x: auto;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}
.simple-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.simple-table td {
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
}
.simple-table tr:first-child td {
  background-color: #f1f5f9;
  font-weight: 600;
  color: #1e293b;
}

/* 分析状态样式 */
.analysis-status {
  padding: 1.5rem;
  border-radius: 8px;
  margin: 1rem 0;
}

.pending-box {
  background: #f0f7ff;
  border: 2px solid #0066cc;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
}

.pending-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.pending-box p {
  margin: 0.5rem 0;
  color: #334155;
}

.pending-box strong {
  color: #0066cc;
  font-size: 1.1rem;
}

.hint-text {
  font-size: 0.9rem;
  color: #666;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.hint-list {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
  display: inline-block;
  color: #555;
}

.hint-list li {
  padding: 0.3rem 0;
  font-size: 0.85rem;
}

.error-box {
  background: #ffe0e0;
  border: 2px solid #dc2626;
  border-radius: 8px;
  padding: 1.5rem;
  color: #991b1b;
}

.error-box strong {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.error-box p {
  margin: 0.5rem 0;
  line-height: 1.6;
}

.error-details {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #fecaca;
}

.error-details summary {
  cursor: pointer;
  color: #991b1b;
  font-weight: 600;
  user-select: none;
}

.error-details summary:hover {
  text-decoration: underline;
}

.error-details pre {
  background: #fff5f5;
  border: 1px solid #fecaca;
  border-radius: 4px;
  padding: 1rem;
  overflow-x: auto;
  font-size: 0.8rem;
  margin-top: 0.5rem;
  color: #7c2d12;
}

/* 调试信息样式 */
.debug-section {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 2px dashed #e2e8f0;
}

.debug-section summary {
  cursor: pointer;
  font-weight: 600;
  color: #64748b;
  user-select: none;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.debug-section summary:hover {
  background: #f1f5f9;
}

.debug-content {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 1rem;
  margin-top: 1rem;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.85rem;
}

.debug-item {
  padding: 0.5rem 0;
  color: #475569;
  line-height: 1.6;
}

.debug-item strong {
  color: #1e293b;
  min-width: 100px;
  display: inline-block;
}

.raw-content {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1rem;
  overflow-x: auto;
  line-height: 1.6;
  color: #333;
}

.markdown-body {
  color: #334155;
  line-height: 1.8;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #1e293b;
}

.markdown-body h1 { font-size: 1.8rem; }
.markdown-body h2 { font-size: 1.4rem; }
.markdown-body h3 { font-size: 1.1rem; }

.markdown-body p {
  margin: 0.5rem 0;
}

.markdown-body strong {
  font-weight: 600;
  color: #0066cc;
}

.markdown-body em {
  font-style: italic;
  color: #666;
}

.markdown-body ul {
  list-style: disc;
  padding-left: 1.5rem;
  margin: 0.5rem 0;
}

.markdown-body li {
  margin: 0.3rem 0;
}

.debug-info-inline {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  text-align: left;
}

.debug-info-inline .debug-item {
  padding: 0.5rem;
  margin: 0.3rem 0;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #3b82f6;
  font-size: 0.85rem;
}

.debug-info-inline .debug-item strong {
  color: #1e293b;
  margin-right: 0.5rem;
}

.debug-info-inline .debug-item span {
  color: #64748b;
}

.prompt-details {
  margin-top: 1rem;
  background: white;
  border: 2px solid #3b82f6;
  border-radius: 6px;
  padding: 1rem;
}

.prompt-details summary {
  cursor: pointer;
  font-weight: 600;
  color: #3b82f6;
  user-select: none;
  padding: 0.5rem;
}

.prompt-details summary:hover {
  background: #f0f7ff;
  border-radius: 4px;
}

.prompt-content {
  margin-top: 1rem;
}

.prompt-section {
  margin: 1rem 0;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 6px;
}

.prompt-section h5 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
  font-size: 0.9rem;
}

.code-block {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 0.75rem;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  overflow-x: auto;
}

.code-block pre {
  margin: 0.5rem 0 0 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #334155;
}

.code-block strong {
  color: #0066cc;
}

.checklist {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0;
}

.checklist li {
  padding: 0.4rem 0.5rem;
  margin: 0.3rem 0;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #10b981;
  font-size: 0.85rem;
  color: #334155;
}
</style>
