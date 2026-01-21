"""优化后的 PPT 扩展系统 Agent 实现"""

from typing import List, Dict, Any
import json
import requests
from urllib.parse import urlparse

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, StructuredOutputParser, ResponseSchema
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from .models import (
    PageStructure,
    KnowledgeGap,
    ExpandedContent,
    CheckResult,
    KnowledgeUnit,
    GraphState,
)


# ==================== 配置管理 ====================
class LLMConfig:
    """LLM 配置"""
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def create_llm(self, temperature: float = 0.5) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            max_retries=3,
            temperature=temperature
        )


# ==================== 工具函数 ====================
def test_url_connectivity(url: str, timeout: int = 3) -> bool:
    """测试URL连通性"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False


# ==================== Step 0-A: 全局结构解析 Agent (简化版) ====================
class GlobalStructureAgent:
    """全局结构解析 Agent - 提取整体知识框架"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0)
    
    def run(self, state: GraphState) -> GraphState:
        """执行全局结构解析"""
        # 简化 prompt: 只提取关键信息
        template = """分析PPT的整体结构,提取核心知识框架。

PPT内容:
{ppt_texts}

以JSON格式输出(仅包含必要信息):
{{
  "main_topic": "主题",
  "chapters": [
    {{"title": "章节名", "pages": [1,2,3], "key_concepts": ["概念A", "概念B"]}}
  ],
  "knowledge_flow": "简述知识逻辑流程(50字内)"
}}
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        # 只传递关键文本,减少token消耗
        ppt_summary = "\n".join([
            f"P{i+1}: {text[:200]}" for i, text in enumerate(state["ppt_texts"])
        ])
        
        response = chain.invoke({"ppt_texts": ppt_summary})
        
        try:
            result = json.loads(response.content)
        except:
            result = {"main_topic": "未知", "chapters": [], "knowledge_flow": ""}
        
        state["global_outline"] = result
        return state


# ==================== Step 0-B: 知识点划分 Agent (全局视角) ====================
class KnowledgeClusteringAgent:
    """知识点划分 Agent - 从全局PPT提取知识单元"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.2)
    
    def run(self, state: GraphState) -> GraphState:
        """执行知识点聚类 - 从全局视角"""
        # 优化: 明确目标是帮助学生理解
        template = """你是学习助手,目标是帮助学生更好理解这份PPT。

全局结构:
{global_outline}

PPT完整内容:
{ppt_texts}

任务: 从整个PPT中提取需要补充说明的知识点
要求:
1. 识别学生可能不理解的核心概念
2. 找出需要背景知识的内容
3. 标注需要示例说明的抽象概念

输出JSON数组(每个知识点):
[
  {{
    "concept": "概念名称",
    "pages": [涉及页码],
    "why_difficult": "为什么学生可能不理解(20字内)",
    "补充方向": "需要补充什么(例如:原理/示例/背景)"
  }}
]

限制: 最多提取10个最关键的知识点
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "global_outline": json.dumps(state["global_outline"], ensure_ascii=False),
            "ppt_texts": "\n\n".join([f"第{i+1}页:\n{text}" for i, text in enumerate(state["ppt_texts"])])
        })
        
        try:
            concepts_data = json.loads(response.content)
            # 转换为 KnowledgeUnit 格式
            knowledge_units = []
            for i, concept in enumerate(concepts_data[:10]):  # 限制最多10个
                knowledge_units.append(KnowledgeUnit(
                    unit_id=f"unit_{i+1}",
                    title=concept.get("concept", ""),
                    pages=concept.get("pages", []),
                    core_concepts=[concept.get("concept", "")],
                    raw_texts=[state["ppt_texts"][p-1] for p in concept.get("pages", []) if 0 < p <= len(state["ppt_texts"])]
                ))
        except:
            knowledge_units = []
        
        state["knowledge_units"] = knowledge_units
        return state


# ==================== Step 1: 结构语义理解 Agent (简化) ====================
class StructureUnderstandingAgent:
    """结构语义理解 Agent - 生成学生理解笔记"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.5)
    
    def run(self, state: GraphState) -> GraphState:
        """执行结构语义理解和笔记生成"""
        # 生成学生理解笔记
        template = """根据以下内容，为学生生成结构化学习笔记(Markdown格式，300字内):

内容: {raw_text}

笔记格式:
## [页面主题]

### 核心概念
- 概念1: 简要说明
- 概念2: 简要说明

### 关键要点
- 要点1
- 要点2

### 重点理解
[简洁的理解要点]

要求:
- 突出最重要的概念
- 标注学生应该掌握的要点
- 适合快速复习
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({"raw_text": state["raw_text"][:1000]})  # 限制输入长度
        
        # 生成学习笔记
        understanding_notes = response.content
        
        # 同时提取页面结构信息
        structure_template = """提取页面的结构化信息(JSON格式):

内容: {raw_text}

{{
  "title": "页面标题",
  "main_concepts": ["核心概念1", "核心概念2"],
  "key_points": ["要点1", "要点2"]
}}

仅返回JSON，不要其他内容。
"""
        structure_prompt = ChatPromptTemplate.from_template(structure_template)
        structure_chain = structure_prompt | self.llm
        
        structure_response = structure_chain.invoke({"raw_text": state["raw_text"][:800]})
        
        try:
            structure_data = json.loads(structure_response.content)
            page_structure = {
                "page_id": state.get("current_page_id", 0),
                "title": structure_data.get("title", ""),
                "main_concepts": structure_data.get("main_concepts", []),
                "key_points": structure_data.get("key_points", []),
                "relationships": {},
                "teaching_goal": ""
            }
        except:
            page_structure = {
                "page_id": 0, 
                "title": "", 
                "main_concepts": [], 
                "key_points": [], 
                "relationships": {}, 
                "teaching_goal": ""
            }
        
        state["page_structure"] = page_structure
        state["understanding_notes"] = understanding_notes
        return state


# ==================== Step 2: 知识缺口识别 Agent (针对学生) ====================
class GapIdentificationAgent:
    """知识缺口识别 Agent - 识别学生理解障碍"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.2)
    
    def run(self, state: GraphState) -> GraphState:
        """识别知识缺口"""
        # 优化: 聚焦学生理解需求
        template = """你是教学助手,识别学生理解这段内容的障碍点。

内容: {raw_text}

识别(JSON数组,最多5个):
[
  {{
    "concept": "概念",
    "gap_type": "缺少什么(选一个: 直观解释/应用示例/背景知识/公式推导)",
    "priority": 优先级1-5
  }}
]

原则:
- 只标注真正影响理解的缺口
- 优先级高的是必须补充的
- 不要过度延伸
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({"raw_text": state["raw_text"][:800]})
        
        try:
            gaps_data = json.loads(response.content)
            knowledge_gaps = [
                KnowledgeGap(
                    concept=g.get("concept", ""),
                    gap_types=[g.get("gap_type", "")],
                    priority=g.get("priority", 3)
                ) for g in gaps_data[:5]  # 最多5个
            ]
        except:
            knowledge_gaps = []
        
        state["knowledge_gaps"] = knowledge_gaps
        return state


# ==================== Step 3: 定向知识扩展 Agent (精简) ====================
class KnowledgeExpansionAgent:
    """定向知识扩展 Agent - 生成补充说明"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.6)
    
    def run(self, state: GraphState) -> GraphState:
        """生成扩展内容"""
        expanded_contents = []
        
        # 按优先级排序,只处理前3个
        sorted_gaps = sorted(state["knowledge_gaps"], key=lambda x: x.priority, reverse=True)[:3]
        
        for gap in sorted_gaps:
            gap_type = gap.gap_types[0] if gap.gap_types else "解释"
            
            # 精简 prompt,明确要求
            template = """为学生补充说明(150字内,通俗易懂):

概念: {concept}
需要: {gap_type}
PPT原文: {raw_text}

补充说明:"""
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "concept": gap.concept,
                "gap_type": gap_type,
                "raw_text": state["raw_text"][:500]
            })
            
            expanded_contents.append(ExpandedContent(
                concept=gap.concept,
                gap_type=gap_type,
                content=response.content[:300],  # 限制长度
                sources=["AI生成"]
            ))
        
        state["expanded_content"] = expanded_contents
        return state


# ==================== Step 4: 外部检索增强 Agent (优化策略) ====================
class RetrievalAgent:
    """外部检索增强 Agent - 智能多源检索"""
    
    def __init__(self, llm_config: LLMConfig, vector_db_path: str = "./knowledge_base"):
        self.llm = llm_config.create_llm(temperature=0)
        self.embeddings = OpenAIEmbeddings(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url
        )
        self.vector_db_path = vector_db_path
        self.vectorstore = None
        
        # 多源检索配置
        self.sources = {
            "baidu_baike": {"url": "https://baike.baidu.com", "available": False},
            "wikipedia": {"url": "https://zh.wikipedia.org", "available": False},
            "arxiv": {"url": "https://arxiv.org", "available": False},
        }
        self._test_sources()
    
    def _test_sources(self):
        """测试外部源连通性"""
        for name, config in self.sources.items():
            config["available"] = test_url_connectivity(config["url"])
    
    def initialize_vectorstore(self, documents: List[Document] = None):
        """初始化向量数据库"""
        try:
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            if documents:
                self.vectorstore.add_documents(documents)
        except:
            if documents:
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=self.vector_db_path
                )
    
    def retrieve_local(self, query: str, k: int = 2) -> List[Document]:
        """本地 RAG 检索"""
        if not self.vectorstore:
            return []
        return self.vectorstore.similarity_search(query, k=k)
    
    def retrieve_external(self, query: str) -> List[Document]:
        """外部检索 - 优先可用源"""
        docs = []
        
        # 只查询可用的源
        available_sources = [name for name, config in self.sources.items() if config["available"]]
        
        if not available_sources:
            return docs
        
        # 优先百度百科(中文友好)
        if "baidu_baike" in available_sources:
            # TODO: 实现百度百科API调用
            pass
        
        # 其次维基百科
        elif "wikipedia" in available_sources:
            # TODO: 实现维基百科API调用
            pass
        
        return docs
    
    def run(self, state: GraphState) -> GraphState:
        """执行检索增强"""
        retrieved_docs = []
        
        # 优化: 只为高优先级缺口检索
        high_priority_gaps = [g for g in state["knowledge_gaps"] if g.priority >= 4]
        
        if not high_priority_gaps:
            state["retrieved_docs"] = []
            return state
        
        # 合并查询,减少检索次数
        query = " ".join([gap.concept for gap in high_priority_gaps[:2]])
        
        # 1. 优先本地 RAG
        local_docs = self.retrieve_local(query, k=3)
        retrieved_docs.extend(local_docs)
        
        # 2. 仅当本地不足且有可用外部源时才检索
        if len(local_docs) < 2 and any(s["available"] for s in self.sources.values()):
            external_docs = self.retrieve_external(query)
            retrieved_docs.extend(external_docs)
        
        state["retrieved_docs"] = retrieved_docs[:5]  # 最多5条
        return state


# ==================== Step 5: 内容一致性校验 Agent (防幻觉) ====================
class ConsistencyCheckAgent:
    """内容一致性校验 Agent - 防止幻觉"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0)
    
    def run(self, state: GraphState) -> GraphState:
        """执行一致性校验"""
        # 优化: 明确防幻觉要求
        template = """你是事实核查员,校验补充内容的准确性。

PPT原文: {raw_text}

补充内容: {expanded_content}

参考资料: {retrieved_docs}

严格校验(JSON):
{{
  "status": "pass或revise",
  "issues": ["问题列表"],
  "suggestions": ["改进建议"]
}}

原则:
1. 禁止编造PPT未提及的概念
2. 所有陈述必须有依据(PPT或参考资料)
3. 不确定的内容标记为"推测"
4. 发现矛盾必须revise
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        expanded_text = "\n".join([
            f"{ec.concept}: {ec.content}" for ec in state["expanded_content"]
        ])
        
        retrieved_text = "\n".join([
            f"[参考{i+1}] {doc.page_content[:150]}"
            for i, doc in enumerate(state["retrieved_docs"][:3])
        ]) if state["retrieved_docs"] else "无参考资料"
        
        response = chain.invoke({
            "raw_text": state["raw_text"][:600],
            "expanded_content": expanded_text,
            "retrieved_docs": retrieved_text
        })
        
        try:
            result = json.loads(response.content)
            check_result = CheckResult(
                status=result.get("status", "pass"),
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", [])
            )
        except:
            check_result = CheckResult(status="pass", issues=[], suggestions=[])
        
        state["check_result"] = check_result
        return state


# ==================== Step 6: 内容结构化整理 Agent (精简版) ====================
class StructuredOrganizationAgent:
    """内容结构化整理 Agent - 生成学习笔记"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.5)
    
    def run(self, state: GraphState) -> GraphState:
        """整理最终笔记"""
        # 优化: 明确是学习笔记,不是完整文档
        template = """整理学习笔记(Markdown格式,300字内):

PPT原文:
{raw_text}

补充说明:
{expanded_content}

格式要求:
## [页面标题]

### 核心概念
- 概念1: 简要说明
- 概念2: 简要说明

### 补充理解
[补充内容,简洁易懂]

### 参考
[如有参考资料列出]

原则:
- 简洁,突出重点
- 不重复PPT原文
- 适合快速复习
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        expanded_text = "\n".join([
            f"**{ec.concept}**: {ec.content}" for ec in state["expanded_content"]
        ])
        
        response = chain.invoke({
            "raw_text": state["raw_text"][:500],
            "expanded_content": expanded_text or "无补充内容"
        })
        
        state["final_notes"] = response.content
        state["streaming_chunks"] = [response.content]
        return state