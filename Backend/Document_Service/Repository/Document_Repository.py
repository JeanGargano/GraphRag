import logging
import os

from fastapi import UploadFile

from config import settings

logger = logging.getLogger(__name__)


class DocumentRepository:

    def __init__(self):
        os.makedirs(settings.upload_dir, exist_ok=True)

    async def save_file(self, file: UploadFile, document_id: str) -> str:
        """
        Guarda el archivo en el directorio de uploads.
        Usa document_id como prefijo para evitar colisiones de nombre.
        Retorna la ruta absoluta del archivo guardado.
        """
        filename = f"{document_id}_{file.filename}"
        file_path = os.path.join(settings.upload_dir, filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info("Archivo guardado en: %s", file_path)
        return file_path