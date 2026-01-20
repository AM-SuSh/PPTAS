"""PPT 扩展系统的数据模型"""

from typing import TypedDict, List, Dict, Any, Annotated, Literal
from dataclasses import dataclass
import operator

from pydantic import BaseModel, Field


# ==================== 数据模型 ====================
class PageStructure(BaseModel):
    """页面结构解析结果"""
    page_id: int = Field(description="页面 ID")
    title: str = Field(description="页面标题")
    main_concepts: List[str] = Field(description="主要概念")
    key_points: List[str] = Field(description="关键要点")
    relationships: Dict[str, str] = Field(description="概念关系")
    teaching_goal: str = Field(description="教学目标")


class KnowledgeGap(BaseModel):
    """知识缺口"""
    concept: str = Field(description="概念名称")
    gap_types: List[str] = Field(description="缺口类型：如直观解释、公式推导等")
    priority: int = Field(description="优先级 1-5")


class ExpandedContent(BaseModel):
    """扩展内容"""
    concept: str = Field(description="概念名称")
    gap_type: str = Field(description="缺口类型")
    content: str = Field(description="扩展内容")
    sources: List[str] = Field(default_factory=list, description="来源")


class CheckResult(BaseModel):
    """一致性校验结果"""
    status: Literal["pass", "revise"] = Field(description="校验状态")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")


class KnowledgeUnit(BaseModel):
    """知识单元"""
    unit_id: str = Field(description="单元 ID")
    title: str = Field(description="单元标题")
    pages: List[int] = Field(description="涉及的页面")
    core_concepts: List[str] = Field(description="核心概念")
    raw_texts: List[str] = Field(description="原始文本")


# ==================== Graph State ====================
class GraphState(TypedDict):
    """LangGraph 状态"""
    # 全局输入
    ppt_texts: List[str]
    global_outline: Dict[str, Any]
    knowledge_units: List[KnowledgeUnit]
    
    # 当前处理单元
    current_unit_id: str
    current_page_id: int
    raw_text: str
    
    # Agent 输出
    page_structure: PageStructure
    knowledge_gaps: List[KnowledgeGap]
    expanded_content: List[ExpandedContent]
    retrieved_docs: List[Any]  # List[Document]
    check_result: CheckResult
    final_notes: str
    
    # 控制流
    revision_count: int
    max_revisions: int
    
    # 流式输出
    streaming_chunks: Annotated[List[str], operator.add]
