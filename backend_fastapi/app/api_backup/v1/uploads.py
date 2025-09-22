# backend_fastapi/app/api/v1/uploads.py  
"""
Endpoints para upload de arquivos
"""
import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image
import io

from core.config import get_settings
from core.security import get_current_user
from models.user import Usuario
from schemas.checklist import PhotoUploadResponse

router = APIRouter()
settings = get_settings()

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/photo", response_model=PhotoUploadResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """Upload de foto para checklist"""
    
    # Validar tipo de arquivo
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Tipo de arquivo não permitido. Use JPEG, PNG ou WebP.")
    
    # Ler conteúdo do arquivo
    content = await file.read()
    
    # Validar tamanho
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "Arquivo muito grande. Máximo 5MB.")
    
    try:
        # Processar imagem com Pillow
        image = Image.open(io.BytesIO(content))
        
        # Redimensionar se muito grande (manter proporção)
        max_size = (1920, 1080)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Converter para RGB se necessário (para JPEG)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Gerar nome único
        file_extension = "jpg"
        filename = f"checklist_{uuid.uuid4().hex}.{file_extension}"
        filepath = os.path.join(settings.STORAGE_DIR, filename)
        
        # Salvar com compressão otimizada
        image.save(filepath, "JPEG", quality=85, optimize=True)
        
        # URL para acesso
        file_url = f"/files/{filename}"
        
        return PhotoUploadResponse(
            success=True,
            filename=filename,
            url=file_url,
            message="Foto enviada com sucesso"
        )
        
    except Exception as e:
        raise HTTPException(500, f"Erro ao processar imagem: {str(e)}")

@router.post("/multiple-photos")
async def upload_multiple_photos(
    files: List[UploadFile] = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """Upload de múltiplas fotos"""
    
    if len(files) > 10:
        raise HTTPException(400, "Máximo 10 fotos por vez")
    
    results = []
    errors = []
    
    for file in files:
        try:
            result = await upload_photo(file, current_user)
            results.append(result)
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
    
    return {
        "success": len(errors) == 0,
        "uploaded": len(results),
        "total": len(files),
        "results": results,
        "errors": errors
    }