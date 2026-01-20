import os
import tempfile
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.utils.helpers import ensure_supported_ext, save_upload_to_temp, download_to_temp
from src.services.ppt_parser_service import DocumentParserService
from src.services.mindmap_service import MindmapService

app = FastAPI(title="PPTAS Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_parser_service():
    return DocumentParserService()

def get_mindmap_service():
    return MindmapService()


class MindmapRequest(BaseModel):
    title: str = Field(default="", description="Slide title")
    raw_points: Optional[List[Union[str, Dict[str, Any]]]] = Field(
        default=None,
        description="Slide points; supports plain strings or objects like {text, level}.",
    )
    max_depth: int = Field(default=4, ge=1, le=8)
    max_children_per_node: int = Field(default=20, ge=1, le=100)


class SlidePoint(BaseModel):
    text: str
    level: int = Field(default=0, ge=0)


class SlideItem(BaseModel):
    title: str
    page_num: Optional[int] = None
    raw_points: Optional[List[Union[str, Dict[str, Any], SlidePoint]]] = None


class MindmapFromSlidesRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="整体 PPT 标题，可选")
    slides: List[SlideItem]
    max_depth: int = Field(default=4, ge=1, le=8)
    max_children_per_node: int = Field(default=20, ge=1, le=100)


@app.post("/api/v1/mindmap")
async def build_mindmap(
    payload: MindmapRequest,
    svc: MindmapService = Depends(get_mindmap_service),
):
    """
    Build a mindmap tree for the frontend "思维导图" tab.
    Returns: { root: {id,label,children:[...] } }
    """
    return svc.build_mindmap(
        title=payload.title,
        raw_points=payload.raw_points,
        max_depth=payload.max_depth,
        max_children_per_node=payload.max_children_per_node,
    )


@app.post("/api/v1/mindmap/from-slides")
async def build_mindmap_from_slides(
    payload: MindmapFromSlidesRequest,
    svc: MindmapService = Depends(get_mindmap_service),
):
    """
    Build a mindmap for the entire PPT (all slides).
    Expects slides from /api/v1/expand-ppt output.
    """
    return svc.build_mindmap_for_ppt(
        slides=[s.model_dump() for s in payload.slides],
        deck_title=payload.title or "PPT Mindmap",
        max_depth=payload.max_depth,
        max_children_per_node=payload.max_children_per_node,
    )

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
