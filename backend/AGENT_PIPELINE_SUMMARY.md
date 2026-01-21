# PPTAS Agent 流水线系统总结

## 📋 整体架构

```
PPT 输入
   ↓
[全局结构分析] → 提取整体知识框架
   ↓
[单页分析流程] (对每一页执行以下步骤)
   ├─→ [知识聚类] → 识别难以理解的概念
   ├─→ [理解笔记] → 生成学生学习笔记
   ├─→ [缺口识别] → 找出学生的理解障碍
   ├─→ [知识扩展] → 为缺口提供补充说明
   ├─→ [外部检索] → 从网络获取参考资料
   ├─→ [一致性校验] → 防止信息幻觉
   └─→ [内容整理] → 生成最终学习笔记
   ↓
最终分析结果
```

---

## 🔧 核心 Agent 详解

### **1️⃣ GlobalStructureAgent（全局结构解析）**

**作用**：分析整个 PPT 的知识框架和逻辑流程

**输入**：
- `ppt_texts`: List[str] - 所有页面的文本内容
- `global_outline`: Dict - 全局概览（初始为空）

**输出**：
```python
state["global_outline"] = {
    "main_topic": "主题",
    "chapters": [
        {"title": "章节名", "pages": [1,2,3], "key_concepts": ["概念A", "概念B"]}
    ],
    "knowledge_flow": "知识逻辑流程(50字内)"
}
```

**工作原理**：
- 浓缩 PPT 文本以减少 token 消耗
- 提取主题、章节结构和关键概念
- 描述知识之间的逻辑关系

**参数**：
- 温度: 0 (确定性输出)
- 输入限制: 每页 200 字摘要

---

### **2️⃣ PageKnowledgeClusterer（知识聚类 - 单页版本）**

**作用**：识别学生在该页内容中**可能有理解难度的概念**

**输入**：
- `raw_text`: str - 页面原始内容

**输出**：
```python
state["knowledge_clusters"] = [
    {
        "concept": "概念名称",
        "difficulty_level": 3,              # 1-5 难度级别
        "why_difficult": "为什么难理解",      # 最多 50 字
        "related_concepts": ["相关概念1"]     # 上下文相关概念
    }
]
```

**工作原理**：
- 分析内容中的抽象概念、技术术语、复杂关系
- 评估学生可能需要补充说明的部分
- 限制最多 10 个概念，避免信息过载

**参数**：
- 温度: 0.3 (有创意但相对稳定)
- 最多 10 个概念
- 难度分级: 1(简单) 到 5(很难)

---

### **3️⃣ StructureUnderstandingAgent（理解笔记生成）**

**作用**：为学生生成 Markdown 格式的**结构化学习笔记**

**输入**：
- `raw_text`: str - 页面原始内容
- `current_page_id`: int - 页面编号

**输出**：
```python
state["page_structure"] = {
    "page_id": 1,
    "title": "页面标题",
    "main_concepts": ["概念1", "概念2"],
    "key_points": ["要点1", "要点2"],
    "relationships": {},
    "teaching_goal": ""
}

state["understanding_notes"] = """
## [页面主题]

### 核心概念
- 概念1: 简要说明
- 概念2: 简要说明

### 关键要点
- 要点1
- 要点2

### 重点理解
[简洁的理解要点]
"""
```

**工作原理**：
- 两个 LLM 调用：一个生成学习笔记，一个提取结构信息
- 笔记格式适合快速复习
- 结构化提取便于后续处理

**参数**：
- 温度: 0.5 (平衡创意和准确性)
- 输入限制: 1000 字 + 800 字
- 笔记长度限制: 300 字

---

### **4️⃣ GapIdentificationAgent（知识缺口识别）**

**作用**：识别**学生理解这段内容的具体障碍点**

**输入**：
- `raw_text`: str - 页面原始内容
- `knowledge_clusters`: List - 已识别的难点

**输出**：
```python
state["knowledge_gaps"] = [
    KnowledgeGap(
        concept="需要补充的概念",
        gap_types=["直观解释"],           # 缺口类型
        priority=4                         # 优先级 1-5
    )
]
```

**缺口类型**：
- `直观解释` - 需要通俗易懂的解释
- `应用示例` - 需要实际应用场景
- `背景知识` - 需要前置知识补充
- `公式推导` - 需要数学推导过程

**工作原理**：
- 专门针对学生理解需求设计
- 评估缺口的优先级（4-5 表示必须补充）
- 最多 5 个缺口，避免过度分析

**参数**：
- 温度: 0.2 (确定性，聚焦实际问题)
- 最多 5 个缺口
- 优先级: 1(可选) 到 5(必须)

---

### **5️⃣ KnowledgeExpansionAgent（定向知识扩展）**

**作用**：为识别的缺口**生成精准的补充说明**

**输入**：
- `raw_text`: str - 页面原始内容
- `knowledge_gaps`: List[KnowledgeGap] - 需要补充的缺口

**输出**：
```python
state["expanded_content"] = [
    ExpandedContent(
        concept="概念名称",
        gap_type="补充类型",
        content="补充说明(150字内)",      # 通俗易懂
        sources=["AI生成"]
    )
]
```

**工作原理**：
- 按优先级排序，只处理前 3 个缺口
- 针对不同缺口类型生成不同风格的说明
- 严格控制长度（150 字内），确保简洁

**参数**：
- 温度: 0.6 (更多创意用于举例)
- 最多处理 3 个缺口
- 输出限制: 150 字 + 300 字最终长度
- 输入: 500 字内容

---

### **6️⃣ RetrievalAgent（外部检索增强）**

**作用**：从网络和本地知识库检索**权威的参考资料**

**输入**：
- `raw_text`: str - 页面内容
- `knowledge_gaps`: List - 高优先级缺口（优先级 ≥ 4）

**输出**：
```python
state["retrieved_docs"] = [
    Document(
        page_content="文档摘要",
        metadata={
            "source": "arxiv/wikipedia/local",
            "title": "文档标题",
            "url": "文档链接"
        }
    )
]
```

**检索策略**：

1. **智能源检测**：初始化时测试外部源连通性
2. **优先本地 RAG**：先从向量数据库检索
3. **外部检索**：仅当本地结果不足且源可用时查询
4. **早期退出**：所有源都不可用时立即返回

**可用检索源**：
- `arxiv` - 学术论文（最优先）
- `wikipedia` - 百科知识（中英文）
- `baidu_baike` - 百度百科（中文优先）
- 本地向量数据库

**参数**：
- 温度: 0 (确定性检索)
- 最多 5 条检索结果
- 只为高优先级缺口（priority ≥ 4）检索
- 合并查询以减少检索次数

---

### **7️⃣ ConsistencyCheckAgent（一致性校验）**

**作用**：**防止 LLM 幻觉**，确保补充内容与原文一致

**输入**：
- `raw_text`: str - 原始 PPT 内容
- `expanded_content`: List - 生成的补充说明
- `retrieved_docs`: List - 检索到的参考资料

**输出**：
```python
state["check_result"] = CheckResult(
    status="pass",                      # "pass" 或 "revise"
    issues=["问题1", "问题2"],
    suggestions=["改进建议1", "改进建议2"]
)
```

**校验规则**：

1. **禁止编造** - 不能提及 PPT 未涉及的新概念
2. **有据可查** - 所有陈述必须来自 PPT 或参考资料
3. **标记推测** - 不确定的内容标记为"推测"
4. **发现矛盾** - 与 PPT 或参考资料矛盾时标记为修正

**工作原理**：
- 比对生成的内容与原文
- 检查参考资料的支持度
- 识别并修正潜在的错误信息

**参数**：
- 温度: 0 (严格检查，无创意)
- 输入限制: PPT 600 字 + 参考 3 条

---

### **8️⃣ StructuredOrganizationAgent（最终内容整理）**

**作用**：整合所有分析结果，生成**最终学习笔记**

**输入**：
- `raw_text`: str - 页面原始内容
- `expanded_content`: List - 已校验的补充说明
- `check_result`: CheckResult - 校验结果

**输出**：
```python
state["final_notes"] = """
## [页面标题]

### 核心概念
- 概念1: 简要说明
- 概念2: 简要说明

### 补充理解
[补充内容，简洁易懂]

### 参考
[如有参考资料列出]
"""

state["streaming_chunks"] = [final_notes]
```

**笔记格式**：
- 标题明确
- 核心概念优先
- 避免重复原文
- 适合快速复习
- 严格控制长度（300 字内）

**工作原理**：
- 合并原文、补充说明和参考资料
- 去重和去冗余
- 生成适合学生快速查阅的版本

**参数**：
- 温度: 0.5 (平衡)
- 输出限制: 300 字内
- 输入: 500 字内容 + 补充说明

---

## 📊 数据流转流程

```
GraphState 数据结构
{
    # 输入数据
    "ppt_texts": List[str],                    # 所有页面文本
    "raw_text": str,                           # 当前页面文本
    "current_page_id": int,                    # 当前页面号
    
    # Agent 1 输出：全局结构
    "global_outline": Dict,                    # 整体框架
    
    # Agent 2 输出：知识聚类
    "knowledge_clusters": List[Dict],          # 难点分析
    
    # Agent 3 输出：理解笔记
    "page_structure": Dict,                    # 页面结构
    "understanding_notes": str,                # 学习笔记
    
    # Agent 4 输出：缺口识别
    "knowledge_gaps": List[KnowledgeGap],      # 理解缺口
    
    # Agent 5 输出：知识扩展
    "expanded_content": List[ExpandedContent], # 补充说明
    
    # Agent 6 输出：外部检索
    "retrieved_docs": List[Document],          # 参考资料
    
    # Agent 7 输出：一致性校验
    "check_result": CheckResult,               # 校验结果
    
    # Agent 8 输出：最终整理
    "final_notes": str,                        # 最终笔记
    "streaming_chunks": List[str]              # 流式输出
}
```

---

## ⚡ 性能优化策略

### **Token 消耗优化**

1. **输入截断**
   - 全局分析: 每页 200 字摘要
   - 单页分析: 1000-1500 字限制
   - 检索查询: 800 字限制

2. **模型温度设置**
   - 结构化任务: 0 (确定性)
   - 生成任务: 0.5-0.6 (创意平衡)
   - 创意任务: 0.3-0.5 (相对保守)

3. **并行处理**
   - 知识聚类和笔记生成可并行
   - 多页面分析支持批处理

### **网络请求优化**

1. **源可用性缓存**
   - 初始化时测试一次
   - 如果所有源不可用，立即跳过检索
   - 不浪费时间在失败的查询上

2. **早期退出策略**
   - 仅为高优先级缺口检索（priority ≥ 4）
   - 本地 RAG 足够时跳过外部检索
   - 获得足够结果后停止查询

3. **结果过滤**
   - 去除占位符文档（"未找到..."）
   - 仅保留有有效 URL 的结果
   - 去重处理

---

## 🎯 适用场景

### **最佳表现**
- ✅ 技术性强的课程（算法、数据结构）
- ✅ 概念密集型内容（理论、原理）
- ✅ 需要案例说明的知识点
- ✅ 需要背景知识铺垫的话题

### **限制条件**
- ⚠️ 网络不稳定时，外部检索受限
- ⚠️ 非常规术语可能难以识别难点
- ⚠️ 极其简洁的 PPT（缺少上下文）
- ⚠️ 多语言混合内容

---

## 🚀 调用示例

```python
from src.services.page_analysis_service import PageDeepAnalysisService
from src.config import get_llm_config

# 初始化服务
llm_config = get_llm_config()
service = PageDeepAnalysisService(llm_config)

# 分析单个页面
result = service.analyze_page(
    page_id=1,
    title="机器学习基础",
    content="机器学习是通过让计算机从数据中学习...",
    raw_points=[]
)

# 获取分析结果
print(f"知识聚类: {result.knowledge_clusters}")
print(f"学习笔记: {result.understanding_notes}")
print(f"知识缺口: {result.knowledge_gaps}")
print(f"补充说明: {result.expanded_content}")
```

---

## 📈 后续改进方向

1. **模型优化**
   - 微调模型用于教育领域
   - 针对特定学科的专化版本

2. **缓存机制**
   - 缓存常见概念的补充说明
   - 缓存已检索的参考资料

3. **用户反馈**
   - 收集学生对笔记有用性的反馈
   - 根据反馈调整 Agent 参数

4. **多语言支持**
   - 扩展到其他语言
   - 跨语言参考检索

5. **实时流式输出**
   - 逐个 Agent 的结果流式返回
   - 改善用户体验

---

**最后更新**: 2026 年 1 月 21 日
**版本**: 1.0 (优化版)
