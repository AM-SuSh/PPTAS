# AI Agent 逻辑链条改进方案

## 📋 问题描述

**原有问题**：
- 每页分析时只基于当前页面内容，没有全局上下文
- 导致知识点识别效果差，有些页面甚至获取不了知识点
- 无法理解页面在整个文档知识体系中的位置

**改进目标**：
- 先对整个文档进行全局分析，获取主题和知识点框架
- 然后基于全局分析结果，对每一页进行细粒度分析
- 提高知识点识别的准确性和完整性

---

## 🔄 新的逻辑链条

### 阶段1: 文档上传和全局分析

```
1. 用户上传PPT/PDF
   ↓
2. 解析文档，获取所有slides
   ↓
3. 存储到数据库（pptas_cache.sqlite3）
   ↓
4. 自动触发全局分析（analyze-document-global）
   ↓
5. 全局分析包括：
   - 全局结构解析（GlobalStructureAgent）
     * 提取主题（main_topic）
     * 识别章节结构（chapters）
     * 分析知识逻辑流程（knowledge_flow）
   - 全局知识点聚类（KnowledgeClusteringAgent）
     * 从整个文档提取知识点单元
     * 识别核心概念
     * 标注涉及页码
   ↓
6. 保存全局分析结果到数据库（documents.global_analysis_json）
```

### 阶段2: 页面级分析（基于全局上下文）

```
1. 用户点击"使用 AI 深度分析此页面"
   ↓
2. 加载全局分析结果（如果有）
   ↓
3. 页面级分析流程（analyze-page-stream）：
   
   步骤1: 知识聚类（PageKnowledgeClusterer）
   - 输入: 当前页面内容 + 全局分析结果
   - 输出: 基于全局知识框架识别的难点概念
   - 改进: 参考全局知识点单元，识别当前页面涉及的核心概念
   
   步骤2: 学习笔记生成（StructureUnderstandingAgent）
   - 输入: 当前页面内容 + 全局分析结果（global_outline, knowledge_units）
   - 输出: 结构化学习笔记
   - 改进: 说明当前页面在整个文档知识体系中的位置
   
   步骤3: 知识缺口识别（GapIdentificationAgent）
   - 输入: 当前页面内容 + 全局分析结果
   - 输出: 识别的知识缺口
   - 改进: 考虑概念在整个文档中的位置和关系
   
   步骤4: 知识扩展（KnowledgeExpansionAgent）
   - 输入: 知识缺口 + 全局上下文
   - 输出: 补充说明内容
   
   步骤5: 外部检索（RetrievalAgent）
   - 输入: 核心概念 + 全局主题
   - 输出: 参考资料
   ↓
4. 保存页面分析结果到数据库（page_analysis表）
```

---

## 🔧 代码实现位置

### 1. 数据库层（persistence_service.py）

**新增字段**：
- `documents.global_analysis_json`: 存储全局分析结果

**新增方法**：
- `update_global_analysis(doc_id, global_analysis)`: 更新全局分析结果
- `get_document_by_id/get_document_by_hash`: 返回时包含 `global_analysis` 字段

### 2. 全局分析接口（app.py）

**新增接口**：
- `POST /api/v1/analyze-document-global`: 对整个文档进行全局分析

**实现逻辑**：
```python
@app.post("/api/v1/analyze-document-global")
async def analyze_document_global(request: GlobalAnalysisRequest):
    # 1. 获取文档所有slides
    # 2. 提取所有页面文本
    # 3. 调用 GlobalStructureAgent 进行全局结构解析
    # 4. 调用 KnowledgeClusteringAgent 进行全局知识点聚类
    # 5. 保存全局分析结果
```

### 3. 页面分析接口改进（app.py）

**修改位置**：
- `POST /api/v1/analyze-page-stream`

**改进内容**：
```python
# 1. 加载全局分析结果
global_analysis = doc.get("global_analysis")

# 2. 传递给各个agent
knowledge_clusters = service.clustering_agent.run(
    request.content,
    global_context=global_analysis
)

# 3. 构建state时包含全局上下文
state = {
    "global_outline": global_outline,
    "knowledge_units": knowledge_units,
    ...
}
```

### 4. Agent改进

#### PageKnowledgeClusterer (page_analysis_service.py)
- **修改**: `run()` 方法接收 `global_context` 参数
- **改进**: 有全局上下文时，使用增强的prompt，参考全局知识点单元

#### StructureUnderstandingAgent (agents/base.py)
- **修改**: `run()` 方法检查 `state["global_outline"]` 和 `state["knowledge_units"]`
- **改进**: 有全局上下文时，说明当前页面在整个文档知识体系中的位置

#### GapIdentificationAgent (agents/base.py)
- **修改**: `run()` 方法检查全局上下文
- **改进**: 有全局上下文时，考虑概念在整个文档中的位置和关系

### 5. 前端改进

**新增API**（api/index.js）：
```javascript
analyzeDocumentGlobal(docId) {
    return service.post('/analyze-document-global', {
        doc_id: docId
    })
}
```

**自动调用**（Workspace.vue）：
- 在 `preloadCachedAnalyses()` 中，先调用全局分析接口
- 然后再加载页面分析结果

---

## 📊 数据流

### 全局分析数据流

```
文档上传
  ↓
解析slides
  ↓
存储到数据库（documents表）
  ↓
提取所有页面文本
  ↓
GlobalStructureAgent → global_outline
  ↓
KnowledgeClusteringAgent → knowledge_units
  ↓
保存到 documents.global_analysis_json
```

### 页面分析数据流

```
用户点击分析
  ↓
加载全局分析结果（documents.global_analysis_json）
  ↓
构建state（包含global_outline和knowledge_units）
  ↓
PageKnowledgeClusterer（使用全局上下文）
  ↓
StructureUnderstandingAgent（使用全局上下文）
  ↓
GapIdentificationAgent（使用全局上下文）
  ↓
其他agents...
  ↓
保存到 page_analysis表
```

---

## ✅ 改进效果

### 改进前
- ❌ 每页分析只基于当前页面
- ❌ 无法理解页面在整体知识体系中的位置
- ❌ 知识点识别不准确，有些页面识别不到知识点

### 改进后
- ✅ 先进行全局分析，建立知识框架
- ✅ 页面分析时参考全局知识框架
- ✅ 能理解页面在整个文档中的位置
- ✅ 知识点识别更准确，能识别更多知识点
- ✅ 知识缺口识别更精准，考虑前置知识

---

## 🚀 使用流程

1. **文档上传**：
   - 用户上传PPT/PDF
   - 系统自动解析并存储

2. **自动全局分析**：
   - 前端在 `preloadCachedAnalyses` 中自动调用全局分析
   - 如果已有全局分析，直接使用缓存

3. **页面分析**：
   - 用户点击"使用 AI 深度分析此页面"
   - 系统加载全局分析结果
   - 基于全局上下文进行页面级分析
   - 显示更准确的知识点和分析结果

---

## 📝 注意事项

1. **全局分析是异步的**：
   - 前端在后台调用，不阻塞UI
   - 如果全局分析未完成，页面分析仍可进行（但效果较差）

2. **缓存机制**：
   - 全局分析结果会缓存到数据库
   - 如果文档已存在，直接使用缓存的全局分析结果

3. **向后兼容**：
   - 如果没有全局分析结果，页面分析仍可进行
   - 各个agent会检查是否有全局上下文，没有时使用原始逻辑

4. **性能考虑**：
   - 全局分析可能耗时较长（取决于文档页数）
   - 建议在后台异步执行，不阻塞用户操作

---

## 🔍 调试和监控

### 后端日志
- `📊 开始全局分析，文档 {doc_id}，共 {页数} 页`
- `✅ 全局结构解析完成: {主题}`
- `✅ 全局知识点聚类完成: {数量} 个知识点单元`
- `📚 加载全局分析结果: 主题={主题}, 知识点单元={数量}`

### 前端日志
- `🌐 开始全局文档分析...`
- `✅ 全局分析完成: {主题, 知识点单元数量}`
- `♻️  全局分析已存在，直接使用`

---

## 📚 相关文件

- `backend/src/services/persistence_service.py`: 数据库操作
- `backend/src/app.py`: API接口
- `backend/src/services/page_analysis_service.py`: 页面分析服务
- `backend/src/agents/base.py`: Agent实现
- `frontend/src/api/index.js`: 前端API
- `frontend/src/components/Workspace.vue`: 前端逻辑
