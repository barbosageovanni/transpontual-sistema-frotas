import os, uuid
from typing import BinaryIO

STORAGE_DIR = os.getenv("STORAGE_DIR", "/data/uploads")
os.makedirs(STORAGE_DIR, exist_ok=True)

def save_file(file_bytes: bytes, suffix: str = ".jpg") -> str:
    name = f"{uuid.uuid4().hex}{suffix}"
    path = os.path.join(STORAGE_DIR, name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return name

def url_for(filename: str) -> str:
    # Em prod: devolver URL pública (S3/Supabase). Aqui, apenas caminho.
    return f"/files/{filename}"
