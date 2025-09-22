from fastapi import APIRouter, UploadFile, File, HTTPException
from ..storage import save_file

router = APIRouter()

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "Arquivo vazio")
    suffix = ".jpg"
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    fname = save_file(content, suffix=suffix)
    return {"filename": fname}
