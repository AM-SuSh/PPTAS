# 数据库对比分析：pptas_cache.sqlite3 vs ppt_vector_db

## 📊 两个数据库的用途和区别

### 1. **pptas_cache.sqlite3** (PersistenceService)

**位置**: `backend/src/services/persistence_service.py`  
**存储路径**: `backend/pptas_cache.sqlite3`

#### 用途
- ✅ **文档元数据缓存**：存储文档基本信息（文件名、类型、hash等）
- ✅ **完整幻灯片数据**：存储解析后的完整slides JSON数据
- ✅ **AI分析结果缓存**：存储每页的AI分析结果（knowledge_clusters, understanding_notes等）
- ✅ **快速查询**：基于doc_id和page_id的精确查询

#### 数据结构
```sql
-- documents 表
doc_id (TEXT PRIMARY KEY)
file_name, file_type, file_hash (UNIQUE)
slides_json (TEXT)  -- 完整的slides数组JSON
created_at, updated_at

-- page_analysis 表
doc_id, page_id (PRIMARY KEY)
analysis_json (TEXT)  -- AI分析结果JSON
created_at, updated_at
```

#### 特点
- 🔍 **精确查询**：通过doc_id和page_id快速定位
- 💾 **完整数据**：存储完整的slides和分析结果
- 🚀 **快速访问**：SQLite索引，毫秒级查询
- 📦 **轻量级**：只存储结构化数据，文件小

---

### 2. **ppt_vector_db** (VectorStoreService/ChromaDB)

**位置**: `backend/src/services/vector_store_service.py`  
**存储路径**: `backend/ppt_vector_db/`

#### 用途
- ✅ **语义搜索**：基于向量相似度的语义搜索
- ✅ **文本切片存储**：存储分块后的文本内容
- ✅ **向量索引**：存储1536维向量用于相似度计算
- ✅ **跨文件搜索**：可以搜索所有已上传的文件

#### 数据结构
```
ChromaDB 内部结构：
- embeddings: 1536维向量数组
- documents: 文本切片内容
- metadatas: {file_name, file_type, page_num, slide_title, ...}
- ids: 唯一标识符
```

#### 特点
- 🔍 **语义搜索**：理解语义，不仅仅是关键词匹配
- 📊 **向量计算**：基于余弦相似度的相似度计算
- 🌐 **跨文件**：可以搜索所有文件的内容
- 💽 **体积大**：每个向量约6KB，文件较大

---

## 🔄 数据重复分析

### 重复的部分
1. **文档元数据**：两个数据库都存储了file_name, file_type, page_num等
2. **文本内容**：PersistenceService存储完整slides，VectorStore存储文本切片

### 不重复的部分
1. **PersistenceService独有**：
   - 完整的slides JSON（包含图片、格式等）
   - AI分析结果（knowledge_clusters, understanding_notes等）
   - 基于hash的文档去重

2. **VectorStore独有**：
   - 向量数据（embeddings）
   - 文本切片（chunks）
   - 语义搜索能力

---

## 💡 是否可以合并？

### ❌ **不建议完全合并**，原因：

1. **技术栈不同**：
   - SQLite：关系型数据库，适合结构化数据
   - ChromaDB：向量数据库，专门为向量搜索优化

2. **用途不同**：
   - SQLite：精确查询、数据缓存
   - ChromaDB：语义搜索、相似度计算

3. **性能考虑**：
   - SQLite：快速的结构化查询
   - ChromaDB：向量计算需要专门的索引

### ✅ **但可以优化整合**：

#### 方案1：保持分离，但共享元数据
- SQLite存储完整数据和AI分析结果
- ChromaDB存储向量和文本切片
- 通过doc_id关联两个数据库

#### 方案2：在SQLite中存储向量引用
- SQLite存储完整数据
- ChromaDB存储向量
- SQLite中存储ChromaDB的ID引用

#### 方案3：统一元数据管理
- 创建一个统一的元数据服务
- 两个数据库都从统一服务获取元数据
- 减少数据重复

---

## 🎯 推荐方案：保持分离 + 元数据同步

### 当前架构（推荐保持）
```
┌─────────────────────────────────────┐
│   pptas_cache.sqlite3              │
│   - 文档元数据                      │
│   - 完整slides数据                  │
│   - AI分析结果                      │
└─────────────────────────────────────┘
              │
              │ doc_id关联
              ▼
┌─────────────────────────────────────┐
│   ppt_vector_db (ChromaDB)          │
│   - 文本切片                        │
│   - 向量数据                        │
│   - 语义搜索                        │
└─────────────────────────────────────┘
```

### 优化建议

1. **减少元数据重复**：
   - 在ChromaDB的metadata中只存储必要的搜索字段
   - 完整元数据从SQLite获取

2. **统一doc_id管理**：
   - 确保两个数据库使用相同的doc_id
   - 通过doc_id关联数据

3. **数据同步机制**：
   - 当SQLite中删除文档时，同步删除ChromaDB中的数据
   - 当更新文档时，同步更新两个数据库

---

## 📝 代码实现位置

### PersistenceService (SQLite)
- **文件**: `backend/src/services/persistence_service.py`
- **初始化**: `backend/src/app.py:138-160`
- **使用位置**:
  - `expand_ppt`: 存储文档和slides
  - `analyze_page_stream`: 存储AI分析结果
  - `get_page_analysis`: 获取缓存的分析结果

### VectorStoreService (ChromaDB)
- **文件**: `backend/src/services/vector_store_service.py`
- **初始化**: `backend/src/app.py:163-175`
- **使用位置**:
  - `expand_ppt`: 存储文本切片和向量
  - 语义搜索功能（如果有实现）

---

## 🔧 如果要合并，需要考虑的问题

1. **SQLite + 向量扩展**：
   - SQLite可以存储向量（作为BLOB），但查询效率低
   - 需要自己实现向量相似度计算

2. **ChromaDB + 结构化数据**：
   - ChromaDB可以存储JSON，但查询不如SQLite灵活
   - 需要自己实现精确查询

3. **混合方案**：
   - 使用支持向量的数据库（如PostgreSQL + pgvector）
   - 但会增加系统复杂度

---

## ✅ 结论

**建议保持当前架构**，因为：
1. ✅ 两个数据库各司其职，性能最优
2. ✅ 技术栈成熟，维护简单
3. ✅ 可以独立扩展和优化
4. ✅ 数据重复是必要的（不同格式，不同用途）

**优化方向**：
1. 🔄 确保两个数据库的doc_id一致
2. 🔄 实现数据同步机制（删除、更新）
3. 🔄 减少不必要的元数据重复
4. 🔄 统一数据访问接口
