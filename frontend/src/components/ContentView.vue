<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { pptApi } from '../api/index.js'
import MindmapGraph from './MindmapGraph.vue'

const props = defineProps({
  slide: Object,
  activeTool: String,
  mindmap: Object,
  mindmapLoading: Boolean,
  mindmapError: String,
  isAnalyzing: Boolean  // 新增：是否正在分析
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

// 检查后端连接
const checkBackendConnection = async () => {
  try {
    const response = await pptApi.checkHealth()
    if (response.status === 200) {
      alert('✅ 后端连接正常！\n\n版本: ' + response.data.version + '\n状态: ' + response.data.status)
    }
  } catch (error) {
    alert('❌ 后端连接失败！\n\n请确保：\n1. 后端服务已启动 (uvicorn main:app --reload)\n2. 服务地址为 http://localhost:8000\n3. 防火墙未阻止连接\n\n错误信息：' + error.message)
  }
}

// 检查 LLM 连接
const checkLLMConnection = async () => {
  try {
    const response = await pptApi.checkLLMConnection()
    const data = response.data
    
    if (data.status === 'ok') {
      alert('✅ LLM 连接正常！\n\n模型: ' + data.model + '\n示例回复: ' + data.response_preview)
    } else {
      let errorMsg = '❌ LLM 连接失败\n\n'
      errorMsg += '消息: ' + data.message + '\n'
      if (data.detail) errorMsg += '详情: ' + data.detail + '\n'
      errorMsg += '\n解决方案：\n'
      
      if (!data.configured) {
        errorMsg += '1. 检查 config.json 中的 api_key 是否正确配置\n'
        errorMsg += '2. 确认 API Key 有效期未过期\n'
        errorMsg += '3. 检查网络连接是否正常'
      } else {
        errorMsg += '1. 检查 API Key 是否有效\n'
        errorMsg += '2. 确认 API 配额未超限\n'
        errorMsg += '3. 检查选择的模型是否可用\n'
        errorMsg += '4. 尝试更换模型测试'
      }
      
      alert(errorMsg)
    }
  } catch (error) {
    let errorMsg = '❌ LLM 检查失败\n\n'
    
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      errorMsg += '原因: 请求超时（30秒）\n\n'
      errorMsg += '这通常表示：\n'
      errorMsg += '1. LLM 服务响应缓慢\n'
      errorMsg += '2. API Key 无效导致被拒\n'
      errorMsg += '3. 网络连接不稳定\n\n'
      errorMsg += '建议：\n'
      errorMsg += '• 检查 config.json 中的 API Key\n'
      errorMsg += '• 确认 base_url 是否正确\n'
      errorMsg += '• 检查网络连接\n'
      errorMsg += '• 查看后端日志: echo $LAST_COMMAND (backend 终端)'
    } else {
      errorMsg += '原因: ' + error.message + '\n\n'
      errorMsg += '请检查：\n'
      errorMsg += '1. 后端服务是否运行\n'
      errorMsg += '2. 网络连接是否正常'
    }
    
    alert(errorMsg)
  }
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

          <!-- 深度解析内容 -->
          <div class="analysis-section">
            <h4 class="section-title">🤖 AI 深度解析内容</h4>
            
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

            <!-- 正在分析或等待分析状态 - 显示原始内容 -->
            <div v-else class="pending-box">
              <div v-if="props.isAnalyzing" class="analyzing-badge">
                <span class="spinner-small"></span> 正在生成 AI 分析...
              </div>
              <div v-else class="pending-icon">⏳</div>
              <p v-if="!props.isAnalyzing"><strong>等待 AI 解析...</strong></p>
              
              <!-- 显示原始内容作为占位符 -->
              <div v-if="slide.raw_content || slide.content" class="original-content-section">
                <h5 class="subsection-title">📄 页面原始内容</h5>
                <div class="original-content">
                  {{ (slide.raw_content || slide.content || '').substring(0, 300) }}
                  <span v-if="(slide.raw_content || slide.content || '').length > 300">...</span>
                </div>
              </div>
              
              <p v-if="!props.isAnalyzing" class="hint-text">如果长时间未显示结果，请检查以下连接状态：</p>
              
              <!-- AI连接状态面板 - 仅在非分析时显示 -->
              <div v-if="!props.isAnalyzing" class="ai-connection-panel">
                <div class="connection-header">🔗 AI 连接诊断</div>
                
                <!-- 基本信息 -->
                <div class="connection-group">
                  <div class="connection-item">
                    <span class="item-label">📄 当前页面:</span>
                    <span class="item-value">{{ slide.page_num || '未知' }} - {{ slide.title }}</span>
                  </div>
                  
                  <div class="connection-item">
                    <span class="item-label">📊 数据状态:</span>
                    <span class="item-value" :class="!slide.deep_analysis ? 'status-empty' : slide.deep_analysis.includes('待补充') ? 'status-pending' : 'status-ok'">
                      <span v-if="!slide.deep_analysis">❌ deep_analysis 字段为空</span>
                      <span v-else-if="slide.deep_analysis.includes('待补充')">⏳ 标记为"待补充"</span>
                      <span v-else>✓ 已有内容 ({{ slide.deep_analysis.length }} 字符)</span>
                    </span>
                  </div>
                </div>

                <!-- 后端连接状态 -->
                <div class="connection-group">
                  <div class="group-title">🖥️ 后端服务状态</div>
                  <div class="connection-item">
                    <span class="item-label">服务器地址:</span>
                    <span class="item-value code">http://localhost:8000</span>
                  </div>
                  <div class="connection-item">
                    <span class="item-label">状态检查:</span>
                    <span class="item-value">
                      <code class="inline-code">curl http://localhost:8000/docs</code>
                      或浏览器访问该地址
                    </span>
                  </div>
                  <div class="connection-item check-method">
                    <button class="check-btn" @click="checkBackendConnection">🔍 检查后端连接</button>
                  </div>
                </div>

                <!-- LLM连接状态 -->
                <div class="connection-group">
                  <div class="group-title">🤖 LLM 服务状态</div>
                  <div class="connection-item">
                    <span class="item-label">API 配置:</span>
                    <span class="item-value">检查 .env 或 config.json 中的 API Key</span>
                  </div>
                  <div class="connection-item">
                    <span class="item-label">问题排查:</span>
                    <span class="item-value">
                      • API Key 是否正确<br>
                      • 是否超过 API 配额限制<br>
                      • 网络是否能访问 LLM 服务
                    </span>
                  </div>
                  <div class="connection-item check-method">
                    <button class="check-btn llm-btn" @click="checkLLMConnection">🤖 检查 LLM 连接</button>
                  </div>
                </div>
              </div>
              
              <!-- 详细调试信息 -->
              <div class="debug-info-inline">
                
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
      <div class="mindmap-header">
        <div>
          <div class="content-header">
            <h2 class="slide-title">思维导图</h2>
            <span class="ai-badge">🧠 自动构建</span>
          </div>
          <p class="text-hint">基于整个 PPT 的层级要点生成</p>
        </div>
      </div>

      <div v-if="mindmapLoading" class="mindmap-loading">
        <div class="mini-spinner"></div>
        <p>正在生成思维导图...</p>
      </div>

      <div v-else-if="mindmapError" class="mindmap-error">
        <p>生成失败：{{ mindmapError }}</p>
      </div>

      <div v-else-if="mindmap?.root" class="mindmap-tree-wrapper">
        <MindmapGraph :root="mindmap.root" />
      </div>

      <div v-else class="mindmap-empty">
        <p>暂无思维导图数据，请先上传 PPT。</p>
      </div>
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
  align-items: stretch;
  justify-content: flex-start;
  height: 100%;
  min-height: 60vh;
}

.mindmap-header {
  margin-bottom: 1rem;
}

.mindmap-tree-wrapper {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0;
  background: #f8fafc;
  overflow: hidden;
  height: calc(100vh - 280px);
  min-height: 500px;
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.mindmap-loading,
.mindmap-error,
.mindmap-empty {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

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

.analyzing-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  color: #d97706;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.spinner-small {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid #f59e0b;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.original-content-section {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 1rem;
  margin: 1rem 0;
  text-align: left;
}

.original-content-section .subsection-title {
  font-size: 0.9rem;
  color: #666;
  margin-top: 0;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.original-content {
  color: #555;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
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

/* AI 连接状态面板样式 */
.ai-connection-panel {
  background: linear-gradient(135deg, #f0f7ff 0%, #f8fafc 100%);
  border: 2px solid #3b82f6;
  border-radius: 8px;
  padding: 1.2rem;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.connection-header {
  font-weight: 700;
  color: #1e293b;
  font-size: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #3b82f6;
  margin-bottom: 1rem;
}

.connection-group {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #0066cc;
}

.group-title {
  font-weight: 600;
  color: #0066cc;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid #e2e8f0;
}

.connection-item {
  padding: 0.5rem 0;
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: flex-start;
}

.connection-item.check-method {
  justify-content: center;
  padding-top: 0.75rem;
}

.item-label {
  font-weight: 600;
  color: #1e293b;
  min-width: 120px;
  flex-shrink: 0;
}

.item-value {
  color: #475569;
  flex: 1;
  line-height: 1.5;
}

.item-value.status-empty {
  color: #dc2626;
  font-weight: 500;
}

.item-value.status-pending {
  color: #f59e0b;
  font-weight: 500;
}

.item-value.status-ok {
  color: #059669;
  font-weight: 500;
}

.item-value.code {
  background: #f3f4f6;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.85rem;
}

.item-value .inline-code {
  background: #f3f4f6;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.85rem;
  color: #dc2626;
}

.check-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.check-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

.check-btn:active {
  transform: translateY(0);
}

.check-btn.llm-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
}

.check-btn.llm-btn:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
}
</style>
