import asyncio
import logging
import os

from Config import settings

logger = logging.getLogger(__name__)


class DocumentRepository:

    def __init__(self):
        os.makedirs(settings.upload_dir, exist_ok=True)

    async def save_file(self, filename: str, file_content: bytes, document_id: str) -> str:
        stored_filename = f"{document_id}_{filename}"
        file_path = os.path.join(settings.upload_dir, stored_filename)

        def _write() -> str:
            with open(file_path, "wb") as f:
                f.write(file_content)
            return file_path

        saved = await asyncio.to_thread(_write)
        logger.info("Archivo guardado en: %s", saved)
        return saved
