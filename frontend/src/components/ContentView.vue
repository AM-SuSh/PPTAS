<script setup>
import { ref } from 'vue'

const props = defineProps({
  slide: Object,
  activeTool: String
})

const searchQuery = ref('')
const isSearching = ref(false)

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
          <ul class="point-list">
            <li v-for="point in slide.raw_points" :key="point">{{ point }}</li>
          </ul>
        </div>

        <div class="card ai-card">
          <div class="card-title">深度解析</div>
          <div class="markdown-body" v-html="slide.expanded_html"></div>
        </div>

        <div v-if="slide.references" class="card">
          <h3 class="card-title">参考文献</h3>
          <a v-for="ref in slide.references" :key="ref.url" :href="ref.url" class="content-link">
            {{ ref.title }} <span class="tag">[{{ ref.source }}]</span>
          </a>
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

.markdown-body {
  color: #334155;
  line-height: 1.8;
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
</style>
