import axios from 'axios'

const service = axios.create({
    baseURL: '/api/v1'
})

export const pptApi = {
    uploadAndExpand(file) {
        const formData = new FormData()
        formData.append('file', file)
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
    }
}
