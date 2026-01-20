"""参考文献搜索服务"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from langchain_core.documents import Document

from .mcp_tools import MCPRouter


class ReferenceItem(BaseModel):
    """参考文献项"""
    title: str = Field(description="标题")
    url: str = Field(description="链接")
    source: str = Field(description="来源")
    snippet: str = Field(description="摘要/片段")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ReferenceSearchResult(BaseModel):
    """参考文献搜索结果"""
    query: str = Field(description="搜索查询")
    total_results: int = Field(description="总结果数")
    references: List[ReferenceItem] = Field(description="参考文献列表")


class ReferenceSearchService:
    """参考文献搜索服务"""
    
    def __init__(self):
        self.mcp_router = MCPRouter()
    
    def search_references(
        self,
        query: str,
        max_results: int = 10,
        preferred_sources: Optional[List[str]] = None
    ) -> ReferenceSearchResult:
        """搜索参考文献
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            preferred_sources: 优先知识源，如 ["arxiv", "wikipedia"]
        
        Returns:
            ReferenceSearchResult: 搜索结果
        """
        # 使用 MCP 路由器搜索
        docs = self.mcp_router.search(
            query,
            preferred_sources=preferred_sources or ["arxiv", "wikipedia"]
        )
        
        # 转换为参考文献项
        references = []
        for doc in docs[:max_results]:
            ref = ReferenceItem(
                title=doc.metadata.get("title", query),
                url=doc.metadata.get("url", ""),
                source=doc.metadata.get("source", "Unknown"),
                snippet=self._truncate_text(doc.page_content, 300),
                metadata=doc.metadata
            )
            references.append(ref)
        
        return ReferenceSearchResult(
            query=query,
            total_results=len(references),
            references=references
        )
    
    def search_by_concepts(
        self,
        concepts: List[str],
        max_results_per_concept: int = 3
    ) -> Dict[str, ReferenceSearchResult]:
        """按概念列表搜索参考文献
        
        Args:
            concepts: 概念列表
            max_results_per_concept: 每个概念的最大结果数
        
        Returns:
            Dict[concept -> ReferenceSearchResult]: 按概念组织的搜索结果
        """
        results = {}
        
        for concept in concepts:
            try:
                result = self.search_references(
                    concept,
                    max_results=max_results_per_concept
                )
                results[concept] = result
            except Exception as e:
                print(f"搜索概念 '{concept}' 时出错: {e}")
                results[concept] = ReferenceSearchResult(
                    query=concept,
                    total_results=0,
                    references=[]
                )
        
        return results
    
    def search_academic_papers(
        self,
        query: str,
        max_results: int = 5
    ) -> ReferenceSearchResult:
        """搜索学术论文（优先 Arxiv）"""
        return self.search_references(
            query,
            max_results=max_results,
            preferred_sources=["arxiv"]
        )
    
    def search_general_knowledge(
        self,
        query: str,
        max_results: int = 5
    ) -> ReferenceSearchResult:
        """搜索通用知识（优先 Wikipedia）"""
        return self.search_references(
            query,
            max_results=max_results,
            preferred_sources=["wikipedia", "baike"]
        )
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(" ", 1)[0] + "..."
