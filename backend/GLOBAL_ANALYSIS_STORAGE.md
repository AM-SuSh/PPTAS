# 全局分析结果存储与使用文档

## 📋 概述

全局分析是对整个PPT/PDF文档进行的综合分析，用于提取文档的整体主题、章节结构、知识逻辑流程和核心知识点单元。本文档说明全局分析结果的存储位置、数据结构、访问方式和使用示例。

---

## 💾 存储位置

### 数据库
- **数据库文件**: `backend/pptas_cache.sqlite3`
- **表名**: `documents`
- **字段名**: `global_analysis_json`
- **数据类型**: `TEXT` (存储JSON字符串)

### 数据库表结构

```sql
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,              -- 文档唯一标识符
    file_name TEXT,                        -- 文件名
    file_type TEXT,                        -- 文件类型 (pptx/pdf)
    file_hash TEXT UNIQUE,                 -- 文件哈希值 (SHA256)
    slides_json TEXT,                      -- 幻灯片数据 (JSON)
    global_analysis_json TEXT,             -- 全局分析结果 (JSON) ⭐
    created_at TEXT,                       -- 创建时间
    updated_at TEXT                        -- 更新时间
)
```

---

## 📊 数据结构

### JSON 结构

全局分析结果以JSON格式存储，结构如下：

```json
{
  "main_topic": "文档的核心主题",
  "chapters": [
    {
      "title": "章节标题",
      "pages": [1, 2, 3],
      "key_concepts": ["核心概念1", "核心概念2"]
    }
  ],
  "knowledge_flow": "知识逻辑流程的简要描述（50字内）",
  "knowledge_units": [
    {
      "unit_id": "unit_1",
      "title": "知识点名称",
      "pages": [1, 2, 3],
      "core_concepts": ["概念1", "概念2"]
    }
  ],
  "total_pages": 43
}
```

### 字段说明

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `main_topic` | `string` | 文档的核心主题 | `"机器学习基础"` |
| `chapters` | `array` | 章节列表 | 见下方章节结构 |
| `knowledge_flow` | `string` | 知识逻辑流程描述 | `"从基础概念到实际应用"` |
| `knowledge_units` | `array` | 知识点单元列表 | 见下方知识点单元结构 |
| `total_pages` | `integer` | 文档总页数 | `43` |

#### 章节结构 (`chapters`)

```json
{
  "title": "章节标题",
  "pages": [1, 2, 3],           // 该章节涉及的页码（从1开始）
  "key_concepts": ["概念1", "概念2"]  // 该章节的核心概念
}
```

#### 知识点单元结构 (`knowledge_units`)

```json
{
  "unit_id": "unit_1",          // 知识点单元唯一标识
  "title": "知识点名称",         // 知识点标题
  "pages": [1, 2, 3],           // 该知识点涉及的页码（从1开始）
  "core_concepts": ["概念1"]    // 该知识点的核心概念列表
}
```

---

## 🔧 后端访问方式

### 1. 使用 PersistenceService

#### 获取文档（包含全局分析）

```python
from src.services.persistence_service import get_persistence_service

persistence = get_persistence_service()

# 通过 doc_id 获取
doc = persistence.get_document_by_id(doc_id)
if doc and doc.get("global_analysis"):
    global_analysis = doc["global_analysis"]
    print(f"主题: {global_analysis['main_topic']}")
    print(f"知识点数量: {len(global_analysis['knowledge_units'])}")

# 通过 file_hash 获取
doc = persistence.get_document_by_hash(file_hash)
if doc and doc.get("global_analysis"):
    global_analysis = doc["global_analysis"]
```

#### 更新全局分析结果

```python
global_analysis = {
    "main_topic": "机器学习基础",
    "chapters": [...],
    "knowledge_flow": "...",
    "knowledge_units": [...],
    "total_pages": 43
}

persistence.update_global_analysis(doc_id, global_analysis)
```

### 2. 使用 API 接口

#### 获取全局分析结果

**接口**: `POST /api/v1/analyze-document-global`

**请求体**:
```json
{
  "doc_id": "15c4d7d6-41a6-4847-aa9d-4e653e6be79b",
  "force": false  // 可选，是否强制重新分析
}
```

**响应**:
```json
{
  "success": true,
  "doc_id": "15c4d7d6-41a6-4847-aa9d-4e653e6be79b",
  "global_analysis": {
    "main_topic": "机器学习基础",
    "chapters": [...],
    "knowledge_flow": "...",
    "knowledge_units": [...],
    "total_pages": 43
  },
  "cached": false  // 是否为缓存结果
}
```

#### 强制重新分析

```json
{
  "doc_id": "15c4d7d6-41a6-4847-aa9d-4e653e6be79b",
  "force": true  // 强制重新分析，忽略缓存
}
```

---

## 🌐 前端访问方式

### 1. 使用 API 调用

```javascript
import { pptApi } from '../api/index.js'

// 获取全局分析（如果已存在则返回缓存）
const res = await pptApi.analyzeDocumentGlobal(docId, false)
if (res.data?.success) {
  const globalAnalysis = res.data.global_analysis
  console.log('主题:', globalAnalysis.main_topic)
  console.log('知识点数量:', globalAnalysis.knowledge_units?.length || 0)
}

// 强制重新分析
const res = await pptApi.analyzeDocumentGlobal(docId, true)
```

### 2. API 方法定义

位置: `frontend/src/api/index.js`

```javascript
analyzeDocumentGlobal(docId, force = false) {
    return service.post('/analyze-document-global', {
        doc_id: docId,
        force: force
    })
}
```

---

## 📝 使用示例

### 示例1: 在页面分析中使用全局上下文

```python
# backend/src/app.py - analyze_page_stream 端点

# 获取全局分析结果
global_analysis = None
if request.doc_id:
    doc = persistence.get_document_by_id(request.doc_id)
    if doc and doc.get("global_analysis"):
        global_analysis = doc["global_analysis"]
        print(f"📚 加载全局分析结果: 主题={global_analysis.get('main_topic', '未知')}")

# 将全局上下文传递给知识聚类agent
knowledge_clusters = service.clustering_agent.run(
    request.content,
    global_context=global_analysis  # 传递全局上下文
)
```

### 示例2: 在前端显示全局分析结果

```vue
<!-- frontend/src/components/Workspace.vue -->

<template>
  <div v-if="globalAnalysisResult" class="global-analysis-info">
    <h3>文档主题: {{ globalAnalysisResult.main_topic }}</h3>
    <p>知识点数量: {{ globalAnalysisResult.knowledge_units?.length || 0 }}</p>
    <div v-for="unit in globalAnalysisResult.knowledge_units" :key="unit.unit_id">
      <h4>{{ unit.title }}</h4>
      <p>涉及页面: {{ unit.pages.join(', ') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { pptApi } from '../api/index.js'

const globalAnalysisResult = ref(null)

// 加载全局分析结果
const loadGlobalAnalysis = async (docId) => {
  const res = await pptApi.analyzeDocumentGlobal(docId)
  if (res.data?.success) {
    globalAnalysisResult.value = res.data.global_analysis
  }
}
</script>
```

### 示例3: 直接查询数据库

```python
import sqlite3
import json

# 连接数据库
conn = sqlite3.connect('backend/pptas_cache.sqlite3')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询全局分析结果
doc_id = "15c4d7d6-41a6-4847-aa9d-4e653e6be79b"
cursor.execute(
    "SELECT global_analysis_json FROM documents WHERE doc_id=?",
    (doc_id,)
)
row = cursor.fetchone()

if row and row['global_analysis_json']:
    global_analysis = json.loads(row['global_analysis_json'])
    print(f"主题: {global_analysis['main_topic']}")
    print(f"知识点数量: {len(global_analysis['knowledge_units'])}")
else:
    print("未找到全局分析结果")

conn.close()
```

---

## 🔄 数据流程

### 生成流程

1. **触发全局分析**
   - 用户上传文档后，前端调用 `analyzeDocumentGlobal(docId)`
   - 或用户点击"全局分析"按钮

2. **执行分析**
   - 后端 `analyze_document_global` 端点接收请求
   - 调用 `GlobalStructureAgent` 提取整体结构
   - 调用 `KnowledgeClusteringAgent` 提取知识点单元

3. **保存结果**
   - 调用 `persistence.update_global_analysis(doc_id, global_analysis)`
   - 将结果序列化为JSON并存储到 `global_analysis_json` 字段

### 使用流程

1. **页面分析时加载全局上下文**
   - `analyze_page_stream` 端点获取全局分析结果
   - 将 `global_analysis` 传递给各个AI Agent
   - Agent使用全局上下文进行更准确的页面分析

2. **前端显示**
   - `Workspace.vue` 在 `preloadCachedAnalyses` 中加载全局分析结果
   - 显示在全局分析按钮栏中

---

## ⚠️ 注意事项

1. **数据格式**: `global_analysis_json` 字段存储的是JSON字符串，需要使用 `json.loads()` 解析

2. **空值处理**: 如果文档还没有进行全局分析，`global_analysis_json` 可能为 `NULL`，需要检查：
   ```python
   if doc and doc.get("global_analysis"):
       # 使用全局分析结果
   ```

3. **强制重新分析**: 使用 `force=true` 参数可以强制重新分析，忽略缓存结果

4. **数据一致性**: 全局分析结果与文档的 `doc_id` 绑定，删除文档时会级联删除相关数据

5. **性能考虑**: 全局分析可能耗时较长，建议：
   - 首次分析后缓存结果
   - 仅在必要时强制重新分析
   - 使用异步方式调用API

---

## 📚 相关文件

- **后端服务**: `backend/src/services/persistence_service.py`
- **API端点**: `backend/src/app.py` (第442行 `analyze_document_global`)
- **前端API**: `frontend/src/api/index.js`
- **前端组件**: `frontend/src/components/Workspace.vue`
- **AI Agent**: `backend/src/agents/base.py` (GlobalStructureAgent, KnowledgeClusteringAgent)

---

## 🔍 调试技巧

### 查看数据库中的全局分析结果

```bash
# 使用 SQLite 命令行工具
sqlite3 backend/pptas_cache.sqlite3

# 查看所有文档的全局分析
SELECT doc_id, file_name, 
       CASE 
         WHEN global_analysis_json IS NULL THEN 'NULL'
         ELSE '有数据'
       END as has_analysis
FROM documents;

# 查看特定文档的全局分析（格式化JSON）
SELECT json_extract(global_analysis_json, '$.main_topic') as main_topic,
       json_array_length(global_analysis_json, '$.knowledge_units') as knowledge_count
FROM documents
WHERE doc_id = '15c4d7d6-41a6-4847-aa9d-4e653e6be79b';
```

### Python 调试脚本

```python
# debug_global_analysis.py
import sqlite3
import json
from backend.src.services.persistence_service import get_persistence_service

persistence = get_persistence_service()

# 获取所有文档
conn = persistence._connect()
cursor = conn.execute("SELECT doc_id, file_name, global_analysis_json FROM documents")
rows = cursor.fetchall()

for row in rows:
    doc_id = row['doc_id']
    file_name = row['file_name']
    global_analysis_json = row['global_analysis_json']
    
    if global_analysis_json:
        global_analysis = json.loads(global_analysis_json)
        print(f"\n文档: {file_name} ({doc_id})")
        print(f"  主题: {global_analysis.get('main_topic', '未知')}")
        print(f"  知识点数量: {len(global_analysis.get('knowledge_units', []))}")
    else:
        print(f"\n文档: {file_name} ({doc_id}) - 未进行全局分析")

conn.close()
```

---

## 📅 更新日志

- **2024-12-XX**: 初始版本，添加全局分析功能
- **2024-12-XX**: 添加强制重新分析功能 (`force` 参数)
- **2024-12-XX**: 改进全局分析Agent，增强主题和知识点提取能力

---

## 📞 联系方式

如有问题或建议，请查看项目文档或联系开发团队。
