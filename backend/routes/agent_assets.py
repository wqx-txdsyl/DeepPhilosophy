"""Serve the exact generated-image namespace; never fall through to SPA HTML."""
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from routes.agent_core import AGNES_IMG_DIR

router = APIRouter()


@router.get('/agent_images/{filename}')
def generated_image(filename: str):
    if not re.fullmatch(r'[0-9a-f]{12}\.png', filename):
        raise HTTPException(status_code=404, detail='Image not found')
    path = AGNES_IMG_DIR / filename
    if not path.is_file() or path.is_symlink():
        raise HTTPException(status_code=404, detail='Image not found')
    return FileResponse(path, media_type='image/png', headers={'Cache-Control':'public, max-age=3600'})
