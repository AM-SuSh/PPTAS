import axios from 'axios'

const service = axios.create({
    baseURL: '/api/v1',
    timeout: 30000  // 增加超时以支持 AI 分析
})

export const pptApi = {
    // 原有方法
    uploadAndExpand(file) {
        const formData = new FormData()
        formData.append('file', file)
        return service.post('/expand-ppt', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },
    
    searchKnowledge(query) {
        return service.get('/search', { params: { q: query } })
    },

    // 新增方法 - 深度分析
    analyzePage(pageId, title, content, rawPoints) {
        return service.post('/analyze-page', {
            page_id: pageId,
            title,
            content,
            raw_points: rawPoints
        })
    },

    // 新增方法 - 初始化助教
    setTutorContext(pageId, title, content, concepts) {
        return service.post('/tutor/set-context', {
            page_id: pageId,
            title,
            content,
            raw_points: concepts
        })
    },

    // 新增方法 - AI 对话
    chat(pageId, message) {
        return service.post('/chat', {
            page_id: pageId,
            message
        })
    },

    // 新增方法 - 获取对话历史
    getConversationHistory(pageId) {
        return service.get('/tutor/conversation', {
            params: { page_id: pageId }
        })
    },

    // 新增方法 - 搜索参考文献
    searchReferences(query, maxResults = 10, searchType = null) {
        return service.post('/search-references', {
            query,
            max_results: maxResults,
            search_type: searchType
        })
    },

    // 新增方法 - 按概念搜索参考
    searchByKeyConcepts(concepts, maxPerConcept = 3) {
        return service.post('/search-by-concepts', {
            concepts,
            max_per_concept: maxPerConcept
        })
    },

    // 新增方法 - 检查后端健康状态
    checkHealth() {
        return service.get('/health')
    },

    // 新增方法 - 检查 LLM 连接（使用更短超时）
    checkLLMConnection() {
        return service.get('/health/llm', {
            timeout: 10000  // LLM 检查最多等待 10 秒
        })
    }
}
