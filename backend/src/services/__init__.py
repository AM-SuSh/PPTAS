"""服务层模块"""

from .ppt_parser_service import DocumentParserService
from .ppt_expansion_service import PPTExpansionService
from .page_analysis_service import PageDeepAnalysisService
from .ai_tutor_service import AITutorService, ChatMessage
from .reference_search_service import ReferenceSearchService
from .mcp_tools import MCPRouter, WikipediaMCP, ArxivMCP, GoogleScholarMCP, BaiduBaikeMCP

__all__ = [
    "DocumentParserService",
    "PPTExpansionService",
    "PageDeepAnalysisService",
    "AITutorService",
    "ChatMessage",
    "ReferenceSearchService",
    "MCPRouter",
    "WikipediaMCP",
    "ArxivMCP",
    "GoogleScholarMCP",
    "BaiduBaikeMCP",
]
