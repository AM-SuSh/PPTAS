"""页面级别的深度分析服务"""

from typing import List, Dict, Any, Optional
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .mcp_tools import MCPRouter


class DeepAnalysisResult(BaseModel):
    """页面深度分析结果"""
    page_id: int = Field(description="页面 ID")
    title: str = Field(description="页面标题")
    
    # 原始内容
    raw_content: str = Field(description="原始文本内容")
    
    # 深度解析
    deep_analysis: str = Field(description="AI 深度解析内容 (Markdown)")
    key_concepts: List[str] = Field(description="关键概念列表")
    learning_objectives: List[str] = Field(description="学习目标")
    
    # 参考文献
    references: List[Dict[str, str]] = Field(description="参考文献列表")
    
    # 原始数据结构
    raw_points: List[Dict[str, Any]] = Field(default_factory=list, description="原始要点")


class PageDeepAnalysisService:
    """单页深度分析服务"""
    
    def __init__(self, llm_config):
        self.llm = llm_config.create_llm(temperature=0.5)
        self.mcp_router = MCPRouter()
        self.llm_config = llm_config
    
    def analyze_page(
        self,
        page_id: int,
        title: str,
        content: str,
        raw_points: List[Dict[str, Any]] = None
    ) -> DeepAnalysisResult:
        """分析单个页面
        
        Args:
            page_id: 页面 ID
            title: 页面标题
            content: 页面内容
            raw_points: 原始要点结构
        
        Returns:
            DeepAnalysisResult: 深度分析结果
        """
        # 1. 生成深度分析
        deep_analysis = self._generate_deep_analysis(title, content)
        
        # 2. 提取关键概念
        key_concepts = self._extract_key_concepts(title, content, deep_analysis)
        
        # 3. 提取学习目标
        learning_objectives = self._extract_learning_objectives(title, content)
        
        # 4. 搜索参考文献
        references = self._search_references(title, key_concepts)
        
        return DeepAnalysisResult(
            page_id=page_id,
            title=title,
            raw_content=content,
            deep_analysis=deep_analysis,
            key_concepts=key_concepts,
            learning_objectives=learning_objectives,
            references=references,
            raw_points=raw_points or []
        )
    
    def _generate_deep_analysis(self, title: str, content: str) -> str:
        """生成深度分析内容"""
        template = """你是一位资深的教育专家和学科讲师。请对以下 PPT 内容进行深度分析和讲解。

【页面标题】: {title}

【原始内容】:
{content}

请提供：
1. 核心概念的详细解释
2. 概念之间的关系和联系
3. 实际应用案例或示例
4. 常见误区和注意事项
5. 进阶思考和拓展方向

请用 Markdown 格式组织内容，确保结构清晰，便于理解。
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "title": title,
            "content": content
        })
        
        return response.content
    
    def _extract_key_concepts(self, title: str, content: str, analysis: str) -> List[str]:
        """提取关键概念"""
        template = """从以下内容中提取5-8个核心关键概念。

【标题】: {title}
【内容】: {content}
【分析】: {analysis}

请直接返回一个 JSON 数组，格式如下：
["概念1", "概念2", "概念3", ...]

只返回 JSON 数组，不要其他内容。
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "title": title,
            "content": content,
            "analysis": analysis
        })
        
        try:
            # 清理响应中可能存在的 markdown 代码块
            text = response.content.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            concepts = json.loads(text.strip())
            return concepts if isinstance(concepts, list) else []
        except:
            return [title]
    
    def _extract_learning_objectives(self, title: str, content: str) -> List[str]:
        """提取学习目标"""
        template = """根据以下页面内容，提取学生完成此部分学习后应该达到的3-5个学习目标。

【标题】: {title}
【内容】: {content}

学习目标应该：
- 具体可测量
- 以"能够/会...开始"
- 涵盖不同认知层次

请返回 JSON 数组格式：
["目标1", "目标2", "目标3", ...]

只返回 JSON 数组。
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "title": title,
            "content": content
        })
        
        try:
            text = response.content.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            objectives = json.loads(text.strip())
            return objectives if isinstance(objectives, list) else []
        except:
            return ["理解 " + title]
    
    def _search_references(self, title: str, concepts: List[str], max_refs: int = 5) -> List[Dict[str, str]]:
        """搜索参考文献"""
        references = []
        
        # 组合搜索查询
        search_queries = [title] + concepts[:3]
        
        for query in search_queries:
            if len(references) >= max_refs:
                break
            
            try:
                # 使用 MCP 路由器搜索
                docs = self.mcp_router.search(query, preferred_sources=["arxiv", "wikipedia"])
                
                for doc in docs[:1]:  # 每个查询最多 1 个结果
                    ref = {
                        "title": doc.metadata.get("title", query),
                        "url": doc.metadata.get("url", ""),
                        "source": doc.metadata.get("source", "Unknown"),
                        "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                    references.append(ref)
            except:
                pass
        
        return references
