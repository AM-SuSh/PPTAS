import os
import tempfile
from typing import Optional
import json

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.utils.helpers import ensure_supported_ext, save_upload_to_temp, download_to_temp
from src.services.ppt_parser_service import DocumentParserService
from src.services.ppt_expansion_service import PPTExpansionService
from src.services.page_analysis_service import PageDeepAnalysisService
from src.services.ai_tutor_service import AITutorService, ChatMessage
from src.services.reference_search_service import ReferenceSearchService
from src.agents.base import LLMConfig

app = FastAPI(title="PPTAS Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 请求/响应模型 ====================
class ChatRequest(BaseModel):
    """聊天请求"""
    page_id: int
    message: str


class ChatResponse(BaseModel):
    """聊天响应"""
    page_id: int
    response: str
    timestamp: str


class PageAnalysisRequest(BaseModel):
    """页面分析请求"""
    page_id: int
    title: str
    content: str
    raw_points: Optional[list] = None


class ReferenceSearchRequest(BaseModel):
    """参考文献搜索请求"""
    query: str
    max_results: int = 10
    search_type: Optional[str] = None  # "academic" | "general" | None


# ==================== 配置加载 ====================
def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
    
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # 默认配置
    return {
        "llm": {
            "api_key": os.getenv("api_key", ""),
            "base_url": os.getenv("base_url", "https://api.openai.com/v1"),
            "model": os.getenv("model", "gpt-4")
        },
        "retrieval": {
            "preferred_sources": ["arxiv", "wikipedia"],
            "max_results": 3,
            "local_rag_priority": True
        },
        "expansion": {
            "max_revisions": 2,
            "min_gap_priority": 3,
            "temperature": 0.7
        }
    }


def get_parser_service():
    return DocumentParserService()


def get_expansion_service():
    config = load_config()
    llm_config = LLMConfig(
        api_key=config["llm"]["api_key"],
        base_url=config["llm"]["base_url"],
        model=config["llm"]["model"]
    )
    return PPTExpansionService(llm_config)


def get_page_analysis_service():
    config = load_config()
    llm_config = LLMConfig(
        api_key=config["llm"]["api_key"],
        base_url=config["llm"]["base_url"],
        model=config["llm"]["model"]
    )
    return PageDeepAnalysisService(llm_config)


def get_ai_tutor_service():
    config = load_config()
    llm_config = LLMConfig(
        api_key=config["llm"]["api_key"],
        base_url=config["llm"]["base_url"],
        model=config["llm"]["model"]
    )
    return AITutorService(llm_config)


def get_reference_search_service():
    return ReferenceSearchService()


# ==================== API 端点 ====================

@app.post("/api/v1/expand-ppt")
async def expand_ppt(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = None,
    parser: DocumentParserService = Depends(get_parser_service),
):
    """接收 PPTX/PDF 文件或 URL，返回解析后的逻辑结构。"""
    if not file and not url:
        raise HTTPException(status_code=400, detail="需要上传文件或提供 url")

    tmp_path = None
    try:
        if url:
            tmp_path, filename = download_to_temp(url)
        else:
            tmp_path, filename = await save_upload_to_temp(file)

        ext = ensure_supported_ext(filename)
        slides = parser.parse_document(tmp_path, ext)
        return {"slides": slides}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/v1/analyze-page")
async def analyze_page(
    request: PageAnalysisRequest,
    service: PageDeepAnalysisService = Depends(get_page_analysis_service),
):
    """对单个页面进行深度分析
    
    Args:
        request: 分析请求
        service: 分析服务
    
    Returns:
        页面深度分析结果
    """
    try:
        result = service.analyze_page(
            page_id=request.page_id,
            title=request.title,
            content=request.content,
            raw_points=request.raw_points
        )
        
        return {
            "success": True,
            "data": {
                "page_id": result.page_id,
                "title": result.title,
                "raw_content": result.raw_content,
                "deep_analysis": result.deep_analysis,
                "key_concepts": result.key_concepts,
                "learning_objectives": result.learning_objectives,
                "references": result.references,
                "raw_points": result.raw_points
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    service: AITutorService = Depends(get_ai_tutor_service),
):
    """AI 助教对话端点
    
    Args:
        request: 聊天请求
        service: AI 助教服务
    
    Returns:
        聊天响应
    """
    try:
        # 获取或初始化对话上下文
        response = service.chat(request.page_id, request.message)
        
        return ChatResponse(
            page_id=request.page_id,
            response=response,
            timestamp=""
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/v1/tutor/set-context")
async def set_tutor_context(
    request: PageAnalysisRequest,
    service: AITutorService = Depends(get_ai_tutor_service),
):
    """设置 AI 助教的页面上下文
    
    Args:
        request: 上下文请求
        service: AI 助教服务
    
    Returns:
        确认消息和欢迎语
    """
    try:
        # 这里需要从分析结果中获取深度分析内容
        # 为简化，暂时使用原始内容
        service.set_page_context(
            page_id=request.page_id,
            title=request.title,
            content=request.content,
            key_concepts=request.raw_points or [],
            analysis="（将由前端调用 analyze-page 获取）"
        )
        
        greeting = service.get_assistant_greeting(request.page_id)
        
        return {
            "success": True,
            "page_id": request.page_id,
            "greeting": greeting
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/v1/tutor/conversation")
async def get_conversation_history(
    page_id: int,
    service: AITutorService = Depends(get_ai_tutor_service),
):
    """获取对话历史
    
    Args:
        page_id: 页面 ID
        service: AI 助教服务
    
    Returns:
        对话历史
    """
    try:
        history = service.get_conversation_history(page_id)
        return {
            "page_id": page_id,
            "messages": history
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/v1/search-references")
async def search_references(
    request: ReferenceSearchRequest,
    service: ReferenceSearchService = Depends(get_reference_search_service),
):
    """搜索参考文献
    
    Args:
        request: 搜索请求
        service: 搜索服务
    
    Returns:
        搜索结果
    """
    try:
        if request.search_type == "academic":
            result = service.search_academic_papers(request.query, request.max_results)
        elif request.search_type == "general":
            result = service.search_general_knowledge(request.query, request.max_results)
        else:
            result = service.search_references(request.query, request.max_results)
        
        return {
            "success": True,
            "query": result.query,
            "total_results": result.total_results,
            "references": [
                {
                    "title": ref.title,
                    "url": ref.url,
                    "source": ref.source,
                    "snippet": ref.snippet
                }
                for ref in result.references
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/v1/search-by-concepts")
async def search_by_concepts(
    concepts: list,
    max_per_concept: int = 3,
    service: ReferenceSearchService = Depends(get_reference_search_service),
):
    """按概念搜索参考文献
    
    Args:
        concepts: 概念列表
        max_per_concept: 每个概念的最大结果数
        service: 搜索服务
    
    Returns:
        按概念组织的搜索结果
    """
    try:
        results = service.search_by_concepts(concepts, max_per_concept)
        
        return {
            "success": True,
            "results": {
                concept: {
                    "query": result.query,
                    "total": result.total_results,
                    "references": [
                        {
                            "title": ref.title,
                            "url": ref.url,
                            "source": ref.source,
                            "snippet": ref.snippet
                        }
                        for ref in result.references
                    ]
                }
                for concept, result in results.items()
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "0.2.0"}


@app.get("/api/v1/health/llm")
async def check_llm_connection():
    """检查 LLM 连接状态 - 快速诊断"""
    config = load_config()
    llm_config = LLMConfig(
        api_key=config["llm"]["api_key"],
        base_url=config["llm"]["base_url"],
        model=config["llm"]["model"]
    )
    
    # 检查 API Key 配置
    if not llm_config.api_key:
        return {
            "status": "error",
            "message": "API Key 未配置",
            "detail": "请检查 config.json 中的 llm.api_key 字段",
            "configured": False,
            "model": llm_config.model
        }
    
    try:
        # 创建 LLM 实例进行连接测试
        llm = llm_config.create_llm(temperature=0.5)
        
        # 发送一个极其简洁的测试消息（超快速）
        test_message = "Say OK"
        response = llm.invoke(test_message)
        
        # 检查是否得到有效响应
        if response and response.content:
            return {
                "status": "ok",
                "message": "LLM 连接正常",
                "model": llm_config.model,
                "configured": True,
                "response_preview": response.content[:50]
            }
        else:
            return {
                "status": "error",
                "message": "LLM 返回空结果",
                "detail": "服务返回内容为空，可能是配置问题",
                "model": llm_config.model,
                "configured": True
            }
    except Exception as e:
        error_msg = str(e).lower()
        
        # 根据错误类型提供更具体的诊断
        if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
            detail = "API Key 无效或已过期 - 请检查 config.json"
        elif "429" in error_msg or "rate_limit" in error_msg or "rate limit" in error_msg:
            detail = "超过 API 调用速率限制，请稍后再试"
        elif "quota" in error_msg or "exceeded" in error_msg:
            detail = "API 配额已用尽 - 请检查账户余额"
        elif "timeout" in error_msg or "timed out" in error_msg:
            detail = "请求超时 - 检查网络连接或 LLM 服务状态"
        elif "connection" in error_msg or "refused" in error_msg:
            detail = "无法连接到 LLM 服务 - 检查 base_url 配置"
        else:
            detail = str(e)
        
        return {
            "status": "error",
            "message": "LLM 连接失败",
            "detail": detail,
            "model": llm_config.model,
            "configured": True,
            "error_type": type(e).__name__
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

