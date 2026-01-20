<script setup>
import { ref, computed } from 'vue'
import { pptApi } from '../api/index.js'

const props = defineProps({
  currentFileName: String
})

const emit = defineEmits(['select-slide'])

const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const searchError = ref(null)
const showResults = ref(false)

const hasResults = computed(() => searchResults.value.length > 0)

const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchError.value = '请输入搜索关键词'
    return
  }

  isSearching.value = true
  searchError.value = null
  showResults.value = false

  try {
    const response = await pptApi.searchSemantic(
      searchQuery.value,
      10, // top_k
      props.currentFileName || null, // 可选：限制在当前文件
      null, // file_type
      0.3 // min_score
    )

    if (response.data.success) {
      searchResults.value = response.data.results || []
      showResults.value = true
    } else {
      searchError.value = response.data.error || '搜索失败'
    }
  } catch (error) {
    console.error('搜索错误:', error)
    searchError.value = error.response?.data?.error || '搜索请求失败，请检查网络连接'
  } finally {
    isSearching.value = false
  }
}

const handleKeyPress = (e) => {
  if (e.key === 'Enter') {
    performSearch()
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
  showResults.value = false
  searchError.value = null
}

const formatScore = (score) => {
  return (score * 100).toFixed(1) + '%'
}

const handleResultClick = (result) => {
  // 如果结果包含页码信息，可以跳转到对应幻灯片
  if (result.metadata && result.metadata.page_num) {
    emit('select-slide', result.metadata.page_num - 1) // 转换为 0-based 索引
  }
}
</script>

<template>
  <div class="semantic-search-container">
    <div class="search-header">
      <h3>🔍 语义搜索</h3>
      <p class="search-hint">基于向量数据库的智能语义检索，支持 PDF 和 PPTX 文件</p>
    </div>

    <div class="search-input-wrapper">
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="输入关键词进行语义搜索..."
        @keypress="handleKeyPress"
        :disabled="isSearching"
      />
      <button
        class="search-btn"
        @click="performSearch"
        :disabled="isSearching || !searchQuery.trim()"
      >
        <span v-if="!isSearching">搜索</span>
        <span v-else class="spinner">搜索中...</span>
      </button>
      <button
        v-if="showResults || searchQuery"
        class="clear-btn"
        @click="clearSearch"
      >
        清除
      </button>
    </div>

    <div v-if="searchError" class="error-message">
      ⚠️ {{ searchError }}
    </div>

    <div v-if="showResults && hasResults" class="search-results">
      <div class="results-header">
        <span>找到 {{ searchResults.length }} 个相关结果</span>
      </div>

      <div class="results-list">
        <div
          v-for="(result, index) in searchResults"
          :key="index"
          class="result-item"
          @click="handleResultClick(result)"
        >
          <div class="result-header">
            <span class="result-score">相似度: {{ formatScore(result.score) }}</span>
            <span class="result-meta">
              {{ result.metadata?.file_name || '未知文件' }} - 
              第 {{ result.metadata?.page_num || '?' }} 页
            </span>
          </div>
          <div class="result-content">
            {{ result.content }}
          </div>
          <div class="result-footer">
            <span class="result-type">{{ result.metadata?.slide_type || 'content' }}</span>
            <span v-if="result.metadata?.slide_title" class="result-title">
              {{ result.metadata.slide_title }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showResults && !hasResults" class="no-results">
      <p>未找到相关结果，请尝试其他关键词</p>
    </div>
  </div>
</template>

<style scoped>
.semantic-search-container {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.search-header {
  margin-bottom: 1rem;
}

.search-header h3 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
  font-size: 1.2rem;
}

.search-hint {
  margin: 0;
  color: #64748b;
  font-size: 0.85rem;
}

.search-input-wrapper {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.search-input:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.search-btn {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.search-btn:hover:not(:disabled) {
  background: #2563eb;
}

.search-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.clear-btn {
  padding: 0.75rem 1rem;
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: #e2e8f0;
}

.spinner {
  display: inline-block;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.error-message {
  padding: 0.75rem;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.search-results {
  margin-top: 1rem;
}

.results-header {
  padding: 0.5rem 0;
  color: #64748b;
  font-size: 0.9rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1rem;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  background: #f1f5f9;
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.result-score {
  color: #10b981;
  font-weight: 600;
}

.result-meta {
  color: #64748b;
}

.result-content {
  color: #1e293b;
  line-height: 1.6;
  margin-bottom: 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-footer {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.8rem;
}

.result-type {
  padding: 0.25rem 0.5rem;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 4px;
  font-weight: 500;
}

.result-title {
  color: #64748b;
  font-style: italic;
}

.no-results {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

@media (max-width: 768px) {
  .search-input-wrapper {
    flex-direction: column;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>

