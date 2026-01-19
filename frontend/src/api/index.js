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
    searchKnowledge(query) {
        return service.get('/search', { params: { q: query } })
    }
}
