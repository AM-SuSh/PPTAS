import axios from 'axios'

const service = axios.create({
    baseURL: '/api/v1',
    timeout: 120000  // 增加到 120 秒，支持 AI 分析可能耗时较长
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
    uploadByUrl(url) {
        const formData = new FormData()
        formData.append('url', url)
        return service.post('/expand-ppt', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },
    mindmap(payload) {
        return service.post('/mindmap', payload)
    },
    mindmapFromSlides(payload) {
        return service.post('/mindmap/from-slides', payload)
    },
    searchKnowledge(query) {
        return service.get('/search', { params: { q: query } })
    },

    // 新增方法 - 深度分析
    analyzePage(pageId, title, content, rawPoints, docId = null) {
        return service.post('/analyze-page', {
            page_id: pageId,
            title,
            content,
            raw_points: rawPoints,
            doc_id: docId
        })
    },

    // 新增方法 - 流式深度分析（实时接收结果）
    async analyzePageStream(pageId, title, content, rawPoints, onChunk, docId = null) {
        try {
            const response = await fetch('/api/v1/analyze-page-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    page_id: pageId,
                    title,
                    content,
                    raw_points: rawPoints,
                    doc_id: docId
                })
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                
                // 保留最后一个不完整的行（可能没有 \n）
                buffer = lines.pop() || ''

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6))
                            onChunk(data)
                        } catch (e) {
                            console.error('Failed to parse chunk:', e)
                        }
                    }
                }
            }

            // 处理可能剩余的数据
            if (buffer && buffer.startsWith('data: ')) {
                try {
                    const data = JSON.parse(buffer.slice(6))
                    onChunk(data)
                } catch (e) {
                    console.error('Failed to parse final chunk:', e)
                }
            }
        } catch (error) {
            console.error('Stream analysis error:', error)
            throw error
        }
    },

    // 新增方法 - 初始化助教
    setTutorContext(pageId, title, content, keyConcepts, analysis = '') {
    return service.post('/tutor/set-context', {
        page_id: pageId,
        title: title,
        content: content,
        key_concepts: keyConcepts || [],
        analysis: analysis || ''
    })
},

    // 批量设置上下文（无需逐页翻阅）
    setTutorContextBulk(docId) {
        return service.post('/tutor/set-context-bulk', { doc_id: docId })
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

    // 获取单页历史分析
    getPageAnalysis(docId, pageId) {
        return service.get('/page-analysis', { params: { doc_id: docId, page_id: pageId } })
    },

    // 获取文档所有已保存分析
    getAllPageAnalysis(docId) {
        return service.get('/page-analysis/all', { params: { doc_id: docId } })
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
        return service.get('/health', {
            timeout: 3000  // 后端检查最多等待 3 秒
        })
    },

    // 新增方法 - 联合检查后端和 LLM 连接
    checkHealthComplete() {
        return service.get('/health/complete', {
            timeout: 8000  // 联合检查最多等待 8 秒
        })
    },

    // 新增方法 - 检查 LLM 连接（使用更短超时）
    checkLLMConnection() {
        return service.get('/health/llm', {
            timeout: 5000  // LLM 检查最多等待 5 秒
        })
    },

    // 新增方法 - 语义搜索 PPT/PDF 切片
    searchSemantic(query, topK = 5, fileName = null, fileType = null, minScore = 0.0) {
        return service.post('/search-semantic', {
            query,
            top_k: topK,
            file_name: fileName,
            file_type: fileType,
            min_score: minScore
        })
    },

    // 新增方法 - 获取向量数据库统计信息
    getVectorStoreStats() {
        return service.get('/vector-store/stats')
    },

    // 新增方法 - 获取特定文件的所有切片
    getFileSlides(fileName) {
        return service.get(`/vector-store/file/${encodeURIComponent(fileName)}`)
    },

    // 新增方法 - 删除特定文件的所有切片
    deleteFileSlides(fileName) {
        return service.delete(`/vector-store/file/${encodeURIComponent(fileName)}`)
    }
}
