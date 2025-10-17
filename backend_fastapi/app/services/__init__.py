# backend_fastapi/app/services/__init__.py
"""
Configuração de serviços
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

# Configurar caminho do Tesseract para Windows
if sys.platform == 'win32':
    # Caminho padrão de instalação do Tesseract no Windows
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    if os.path.exists(TESSERACT_PATH):
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            logger.info(f"Tesseract configurado: {TESSERACT_PATH}")
        except ImportError:
            logger.warning("pytesseract nao instalado")
    else:
        logger.warning(f"Tesseract nao encontrado em: {TESSERACT_PATH}")
        logger.warning("Instale o Tesseract ou configure o caminho correto")
