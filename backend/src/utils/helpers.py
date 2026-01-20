import os
import tempfile
from typing import Tuple

import requests
from fastapi import UploadFile, HTTPException

SUPPORTED_EXTS = {".pptx", ".pdf"}


def ensure_supported_ext(filename: str) -> str:
    _, ext = os.path.splitext(filename.lower())
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(status_code=400, detail="仅支持 .pptx/.pdf 文件")
    return ext


def download_to_temp(url: str) -> Tuple[str, str]:
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="下载失败，状态码 %s" % resp.status_code)
    filename = url.split("/")[-1] or "remote_file"
    ext = ensure_supported_ext(filename)
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as f:
        f.write(resp.content)
    return path, filename


async def save_upload_to_temp(file: UploadFile) -> Tuple[str, str]:
    filename = file.filename
    ext = ensure_supported_ext(filename)
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as f:
        f.write(await file.read())
    return path, filename
