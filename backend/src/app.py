import os
import tempfile
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.utils.helpers import ensure_supported_ext, save_upload_to_temp, download_to_temp
from src.services.ppt_parser_service import DocumentParserService

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
