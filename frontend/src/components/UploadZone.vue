<script setup>
import { ref } from 'vue'

const emit = defineEmits(['file-selected', 'url-submitted'])
const isDragging = ref(false)
const isProcessing = ref(false)
const fileInput = ref(null)
const urlInput = ref('')
const urlError = ref('')
const uploadMode = ref('file') // 'file' | 'url'

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    validateAndUpload(file)
  }
}

const handleDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    validateAndUpload(file)
  }
}

const validateAndUpload = (file) => {
  const validExtensions = ['.pptx', '.pdf']
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase()

  if (!validExtensions.includes(fileExtension)) {
    alert('请上传 .pptx 或 .pdf 格式的文件')
    return
  }

  if (file.size > 50 * 1024 * 1024) {
    alert('文件大小不能超过 50MB')
    return
  }

  emit('file-selected', file)
}

const submitUrl = () => {
  const trimmed = urlInput.value.trim()
  if (!trimmed) {
    urlError.value = '请输入文件链接（需包含 .pptx 或 .pdf）'
    return
  }
  const lower = trimmed.toLowerCase()
  if (!lower.startsWith('http://') && !lower.startsWith('https://')) {
    urlError.value = '链接需以 http:// 或 https:// 开头'
    return
  }
  if (!lower.includes('.pptx') && !lower.includes('.pdf')) {
    urlError.value = '当前仅支持 .pptx / .pdf 链接'
    return
  }
  urlError.value = ''
  emit('url-submitted', trimmed)
  isProcessing.value = true
  setTimeout(() => {
    isProcessing.value = false
  }, 400)
}


const handleUploadBoxClick = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}
</script>

<template>
  <section class="welcome-area">
    <div class="hero-section">
      <div class="hero-text">
        <h1 class="hero-title">
          <span class="gradient-text">将枯燥 PPT 转化为</span>
          <br>
          <span class="highlight-text">深度复习笔记</span>
        </h1>
        <p class="hero-description">
          AI 驱动的智能解析系统，自动识别 PPT 逻辑层级，
          <br>
          联动权威知识库补全公式推导与背景知识
        </p>
      </div>

      <div class="feature-grid">
        <div class="feature-item">
          <div class="feature-icon">🧠</div>
          <h3>语义解析</h3>
          <p>智能识别文档结构，提取关键信息</p>
        </div>

        <div class="feature-item">
          <div class="feature-icon">📚</div>
          <h3>知识扩充</h3>
          <p>调用 LLM 补充原理说明与代码示例</p>
        </div>

        <div class="feature-item">
          <div class="feature-icon">🔍</div>
          <h3>多维搜索</h3>
          <p>联动 Wikipedia、Arxiv 获取权威资料</p>
        </div>
      </div>
    </div>

    <div class="upload-area-wrapper">
      <div class="mode-tabs">
        <button 
          class="tab-btn" 
          :class="{ active: uploadMode === 'file' }"
          @click="uploadMode = 'file'"
        >
          📁 本地上传
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: uploadMode === 'url' }"
          @click="uploadMode = 'url'"
        >
          🌐 URL 解析
        </button>
      </div>

      <!-- 文件上传模式 -->
      <div
        v-if="uploadMode === 'file'"
        class="upload-box dashed-border"
        :class="{ 'dragging': isDragging, 'processing': isProcessing }"
        @click="handleUploadBoxClick"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <input type="file" ref="fileInput" hidden @change="handleFileChange" accept=".pptx,.pdf" />

        <div class="upload-content">
          <div class="upload-icon">
            <div v-if="!isProcessing">📤</div>
            <div v-else class="mini-spinner"></div>
          </div>

          <div v-if="!isProcessing">
            <p class="upload-text">点击或拖拽 PPT 文件到此处</p>
            <p class="upload-hint">支持 .pptx 和 .pdf 格式，最大 50MB</p>
          </div>
          <div v-else>
            <p class="upload-text">正在上传文件...</p>
          </div>

          <div class="upload-features">
            <div class="feature-tag">✓ AI 自动解析语义层级</div>
            <div class="feature-tag">✓ 智能检索学术引用</div>
            <div class="feature-tag">✓ 生成可导出笔记</div>
          </div>
        </div>
      </div>

      <!-- URL 上传模式 -->
      <div v-else-if="uploadMode === 'url'" class="upload-box dashed-border url-mode-box">
        <div class="upload-content">
          <div class="upload-icon">🔗</div>
          
          <div v-if="!isProcessing">
            <p class="upload-text">输入远程 PPT/PDF 链接</p>
          </div>
          <div v-else>
            <div class="mini-spinner center-spinner"></div>
            <p class="upload-text">正在解析链接...</p>
          </div>
          
          <div class="url-input-wrapper" v-if="!isProcessing">
            <input
              v-model="urlInput"
              class="url-input-large"
              type="url"
              placeholder="https://example.com/presentation.pptx"
              @keyup.enter="submitUrl"
              @click.stop
            />
            <button class="btn-url-large" @click.stop="submitUrl">解析</button>
          </div>
          
          <p class="upload-hint left-align-hint" v-if="!isProcessing">系统将自动下载并提取文档结构与知识点</p>
          <p v-if="urlError" class="url-error">{{ urlError }}</p>

          <div class="upload-features" v-if="!isProcessing">
            <div class="feature-tag">✓ 支持 HTTP/HTTPS 协议</div>
            <div class="feature-tag">✓ 自动识别文件类型</div>
            <div class="feature-tag">✓ 生成可导出笔记</div>
          </div>
        </div>
      </div>
    </div>

    <div class="usage-guide">
      <h3>📖 使用指南</h3>
      <div class="guide-steps">
        <div class="step-item">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>上传 PPT 文件</h4>
            <p>支持拖拽或点击上传，系统自动解析文档结构</p>
          </div>
        </div>
        <div class="step-item">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>AI 智能扩展</h4>
            <p>自动识别知识点并调用知识库补充内容</p>
          </div>
        </div>
        <div class="step-item">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>导出复习笔记</h4>
            <p>生成包含公式、引用的完整学习资料</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.welcome-area {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.hero-section {
  text-align: center;
  margin-bottom: 3rem;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
  line-height: 1.3;
}

.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.highlight-text {
  color: #1e293b;
  position: relative;
}

.highlight-text::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 2px;
}

.hero-description {
  font-size: 1.1rem;
  color: #64748b;
  max-width: 700px;
  margin: 0 auto 2rem;
  line-height: 1.8;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.feature-item {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.feature-item h3 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
  font-size: 1.1rem;
}

.feature-item p {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.upload-area-wrapper {
  position: relative;
  max-width: 1000px;
  margin: 0 auto;
}

.mode-tabs {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 20px;
}

.tab-btn {
  background: transparent;
  border: none;
  font-size: 1rem;
  font-weight: 600;
  color: #64748b;
  padding-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: #3b82f6;
}

.tab-btn.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.upload-box {
  background: white;
  padding: 60px 60px;
  border-radius: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); /* 轻微阴影，增加层次感 */
  min-height: 420px; /* 固定最小高度，保证切换无跳动 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.dashed-border {
  border: 2px dashed #3b82f6; /* 统一样式为蓝色虚线，配合截图 */
  background-color: #f8fafc; /* 淡背景色 */
}

.url-mode-box {
  /* URL模式下特定样式，如果不需额外样式可留空 */
}

/* Specific restoration for file upload box to be clickable */
.upload-box:not(.url-mode-box) {
    cursor: pointer;
    border-color: #cbd5e0; /* 默认灰色虚线，hover变蓝 */
    background: white;
}

.upload-box:not(.url-mode-box):hover {
  border-color: #3b82f6;
  background: #f0f7ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
}

.url-input-wrapper {
  display: flex;
  gap: 10px;
  max-width: 90%; /* 使用相对宽度，占用更多空间 */
  min-width: 600px; /* 保持最小宽度 */
  margin: 0 auto 2rem;
  position: relative;
  z-index: 5;
}

.url-input-large {
  flex: 1;
  padding: 12px 20px;
  font-size: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  outline: none;
  transition: border-color 0.2s;
  background: white;
}

.url-input-large:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn-url-large {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0 24px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-url-large:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.left-align-hint {
    text-align: center; /* 保持居中更好看，虽然截图似乎是左对齐，但整体居中布局下居中更协调 */
    margin-bottom: 2rem;
    margin-top: 0;
}

.center-spinner {
    margin: 0 auto 1.5rem;
    display: flex;
    justify-content: center;
}

/* Remove old Tab and URL card styles to clean up */
/* Keeping spinner and other utilities */

.upload-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 2rem;
}

.mini-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #10b981;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.upload-text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 1.5rem 0;
}

.upload-hint {
  color: #64748b;
  font-size: 0.9rem;
  margin: 0 0 1.5rem 0;
}

.upload-features {
  display: flex;
  flex-wrap: wrap;
  gap: 1.2rem;
  justify-content: center;
  margin-top: 1.5rem;
}

.feature-tag {
  background: #f1f5f9;
  color: #64748b;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.url-error {
  margin: 0.4rem 0 0 0;
  color: #ef4444;
  font-size: 0.9rem;
  font-weight: 500;
}

.usage-guide {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-top: 3rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.usage-guide h3 {
  color: #1e293b;
  margin-bottom: 1.5rem;
  font-size: 1.3rem;
}

.guide-steps {
  display: flex;
  gap: 2rem;
  justify-content: center;
}

.step-item {
  flex: 1;
  text-align: center;
}

.step-number {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  margin-bottom: 1rem;
}

.step-content h4 {
  color: #1e293b;
  margin: 0 0 0.3rem 0;
  font-size: 1rem;
}

.step-content p {
  color: #64748b;
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 1.8rem;
  }

  .hero-description {
    font-size: 1rem;
  }

  .upload-box {
    padding: 40px 20px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .guide-steps {
    flex-direction: column;
  }

  .url-input-wrapper {
      flex-direction: column;
  }

  .btn-url-large {
    width: 100%;
  }
}
</style>
