"""PPT 扩展系统的各个 Agent 实现"""

from typing import List, Dict, Any
import json

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


# ==================== Step 0-A: 全局结构解析 Agent ====================
class GlobalStructureAgent:
    """全局结构解析 Agent"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0)
        self.parser = self._create_parser()
        self.chain = self._create_chain()
    
    def _create_parser(self):
        response_schemas = [
            ResponseSchema(name="chapters", description="章节列表，每个章节包含 title 和 page_range"),
            ResponseSchema(name="hierarchy", description="章节层级关系"),
            ResponseSchema(name="main_flow", description="整体知识流程")
        ]
        return StructuredOutputParser.from_response_schemas(response_schemas)
    
    def _create_chain(self):
        template = """你是一位教育内容分析专家。请分析这份 PPT 的全局结构。

PPT 内容：
{ppt_texts}

请提取：
1. 章节划分（章节标题、页码范围）
2. 章节层级关系
3. 整体知识流程

{format_instructions}
"""
        prompt = PromptTemplate(
            template=template,
            input_variables=["ppt_texts"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        return prompt | self.llm | self.parser
    
    def run(self, state: GraphState) -> GraphState:
        """执行全局结构解析"""
        ppt_texts = "\n\n".join([f"Page {i+1}: {text}" for i, text in enumerate(state["ppt_texts"])])
        result = self.chain.invoke({"ppt_texts": ppt_texts})
        state["global_outline"] = result
        return state


# ==================== Step 0-B: 知识点划分 Agent ====================
class KnowledgeClusteringAgent:
    """知识点划分 Agent - 跨页语义聚合"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.3)
        self.embeddings = OpenAIEmbeddings(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url
        )
    
    def run(self, state: GraphState) -> GraphState:
        """执行知识点聚类"""
        template = """基于全局结构，将 PPT 划分为独立的知识单元。

全局结构：
{global_outline}

PPT 内容：
{ppt_texts}

要求：
1. 识别跨页的完整知识点
2. 每个单元应包含完整的教学闭环
3. 标注每个单元的核心概念

输出格式（JSON 数组）：
[
  {{
    "unit_id": "unit_1",
    "title": "单元标题",
    "pages": [1, 2, 3],
    "core_concepts": ["概念A", "概念B"],
    "raw_texts": ["页面1文本", "页面2文本"]
  }}
]
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "global_outline": state["global_outline"],
            "ppt_texts": "\n\n".join(state["ppt_texts"])
        })
        
        # 解析为 KnowledgeUnit 列表
        try:
            units_data = json.loads(response.content)
            knowledge_units = [KnowledgeUnit(**unit) for unit in units_data]
        except:
            knowledge_units = []
        
        state["knowledge_units"] = knowledge_units
        return state


# ==================== Step 1: 结构语义理解 Agent ====================
class StructureUnderstandingAgent:
    """结构语义理解 Agent"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=PageStructure)
    
    def run(self, state: GraphState) -> GraphState:
        """执行结构语义理解"""
        template = """你是一位教学内容分析专家。请深度理解这段 PPT 内容的结构和语义。

原始文本：
{raw_text}

请提取：
1. 页面标题和主要概念
2. 关键要点
3. 概念间的关系
4. 推测的教学目标

{format_instructions}
"""
        prompt = PromptTemplate(
            template=template,
            input_variables=["raw_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        chain = prompt | self.llm | self.parser
        page_structure = chain.invoke({"raw_text": state["raw_text"]})
        
        state["page_structure"] = page_structure
        return state


# ==================== Step 2: 知识缺口识别 Agent ====================
class GapIdentificationAgent:
    """知识缺口识别 Agent"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.2)
        self.parser = PydanticOutputParser(pydantic_object=List[KnowledgeGap])
    
    def run(self, state: GraphState) -> GraphState:
        """识别知识缺口"""
        template = """你是一位教育诊断专家。请识别这段教学内容中的知识缺口。

页面结构：
{page_structure}

原始文本：
{raw_text}

请识别：
1. 哪些概念缺少直观解释
2. 哪些公式缺少推导过程
3. 哪些背景知识未提及
4. 哪些应用场景未说明

为每个缺口标注优先级（1-5，5最高）

{format_instructions}
"""
        prompt = PromptTemplate(
            template=template,
            input_variables=["page_structure", "raw_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        chain = prompt | self.llm | self.parser
        knowledge_gaps = chain.invoke({
            "page_structure": state["page_structure"].model_dump(),
            "raw_text": state["raw_text"]
        })
        
        state["knowledge_gaps"] = knowledge_gaps
        return state


# ==================== Step 3: 定向知识扩展 Agent ====================
class KnowledgeExpansionAgent:
    """定向知识扩展 Agent"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.7)
    
    def run(self, state: GraphState) -> GraphState:
        """生成扩展内容"""
        expanded_contents = []
        
        # 按优先级排序
        sorted_gaps = sorted(state["knowledge_gaps"], key=lambda x: x.priority, reverse=True)
        
        for gap in sorted_gaps:
            for gap_type in gap.gap_types:
                template = """你是一位教学内容创作专家。请为以下知识缺口生成扩展内容。

概念：{concept}
缺口类型：{gap_type}
原始上下文：{raw_text}

要求：
1. 内容准确、易懂
2. 适合学生自学
3. 与原 PPT 风格一致
4. 控制在 200-300 字

扩展内容：
"""
                prompt = PromptTemplate(
                    template=template,
                    input_variables=["concept", "gap_type", "raw_text"]
                )
                
                chain = prompt | self.llm
                response = chain.invoke({
                    "concept": gap.concept,
                    "gap_type": gap_type,
                    "raw_text": state["raw_text"]
                })
                
                expanded_contents.append(ExpandedContent(
                    concept=gap.concept,
                    gap_type=gap_type,
                    content=response.content,
                    sources=["LLM生成"]
                ))
        
        state["expanded_content"] = expanded_contents
        return state


# ==================== Step 4: 外部检索增强 Agent ====================
class RetrievalAgent:
    """外部检索增强 Agent - RAG + MCP"""
    
    def __init__(self, llm_config: LLMConfig, vector_db_path: str = "./knowledge_base"):
        self.llm = llm_config.create_llm(temperature=0)
        self.embeddings = OpenAIEmbeddings(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url
        )
        self.vector_db_path = vector_db_path
        self.vectorstore = None
    
    def initialize_vectorstore(self, documents: List[Document] = None):
        """初始化或加载向量数据库"""
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
    
    def retrieve_local(self, query: str, k: int = 3) -> List[Document]:
        """本地 RAG 检索"""
        if not self.vectorstore:
            return []
        return self.vectorstore.similarity_search(query, k=k)
    
    def retrieve_external(self, query: str) -> List[Document]:
        """外部 MCP 工具检索（示例：维基百科、Arxiv）"""
        # TODO: 集成 MCP 工具
        return []
    
    def run(self, state: GraphState) -> GraphState:
        """执行检索增强"""
        retrieved_docs = []
        
        # 为每个知识缺口检索相关内容
        for gap in state["knowledge_gaps"]:
            query = f"{gap.concept} {' '.join(gap.gap_types)}"
            
            # 1. 本地 RAG 检索
            local_docs = self.retrieve_local(query)
            retrieved_docs.extend(local_docs)
            
            # 2. 外部 MCP 检索（如果本地检索不足）
            if len(local_docs) < 2:
                external_docs = self.retrieve_external(query)
                retrieved_docs.extend(external_docs)
        
        state["retrieved_docs"] = retrieved_docs
        return state


# ==================== Step 5: 内容一致性校验 Agent ====================
class ConsistencyCheckAgent:
    """内容一致性校验 Agent"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=CheckResult)
    
    def run(self, state: GraphState) -> GraphState:
        """执行一致性校验"""
        template = """你是一位教学质量审核专家。请校验扩展内容的一致性。

原始 PPT 内容：
{raw_text}

扩展内容：
{expanded_content}

检索到的参考资料：
{retrieved_docs}

校验维度：
1. 是否引入 PPT 未出现的核心概念
2. 是否偏离本页教学目标
3. 是否存在事实错误
4. 是否与检索资料冲突

{format_instructions}
"""
        prompt = PromptTemplate(
            template=template,
            input_variables=["raw_text", "expanded_content", "retrieved_docs"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        expanded_text = "\n\n".join([
            f"{ec.concept} - {ec.gap_type}:\n{ec.content}"
            for ec in state["expanded_content"]
        ])
        
        retrieved_text = "\n\n".join([
            f"来源 {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(state["retrieved_docs"][:5])
        ])
        
        chain = prompt | self.llm | self.parser
        check_result = chain.invoke({
            "raw_text": state["raw_text"],
            "expanded_content": expanded_text,
            "retrieved_docs": retrieved_text
        })
        
        state["check_result"] = check_result
        return state


# ==================== Step 6: 内容结构化整理 Agent ====================
class StructuredOrganizationAgent:
    """内容结构化整理 Agent"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.5)
    
    def run(self, state: GraphState) -> GraphState:
        """整理最终笔记"""
        template = """你是一位学习笔记整理专家。请将扩展内容整理为结构化的学习笔记。

原始 PPT 内容：
{raw_text}

扩展内容：
{expanded_content}

参考资料：
{retrieved_docs}

整理要求：
1. 采用 Markdown 格式
2. 清晰的标题层级
3. 重点内容加粗
4. 包含：核心概念、详细解释、示例、参考资料
5. 适合学生复习使用

学习笔记：
"""
        prompt = PromptTemplate(
            template=template,
            input_variables=["raw_text", "expanded_content", "retrieved_docs"]
        )
        
        expanded_text = "\n\n".join([
            f"### {ec.concept} - {ec.gap_type}\n{ec.content}"
            for ec in state["expanded_content"]
        ])
        
        retrieved_text = "\n\n".join([
            f"**参考 {i+1}**:\n{doc.page_content[:200]}..."
            for i, doc in enumerate(state["retrieved_docs"][:3])
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "raw_text": state["raw_text"],
            "expanded_content": expanded_text,
            "retrieved_docs": retrieved_text
        })
        
        state["final_notes"] = response.content
        state["streaming_chunks"] = [response.content]
        return state
