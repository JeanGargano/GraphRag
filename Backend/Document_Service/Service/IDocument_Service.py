from abc import ABC, abstractmethod
from fastapi import UploadFile
from Model.Schemas import DocumentUploadResponse


class IDocumentService(ABC):

    @abstractmethod
    async def process_document(self, file: UploadFile) -> DocumentUploadResponse:
        """
        Orquesta el flujo completo:
        1. Guarda el archivo y genera su ID
        2. Extrae el texto según el tipo
        3. Divide en chunks
        4. Envía chunks al Embedding Service
        """
        pass

    @abstractmethod
    async def save_file(self, file: UploadFile, document_id: str) -> str:
        """
        Guarda el archivo físico en el sistema de archivos.
        Retorna la ruta donde se guardó el archivo.
        """
        pass

    @abstractmethod
    async def send_chunks(self, document_id: str, filename: str, chunks: list[str]) -> None:
        """
        Envía los chunks al Embedding Service.
        Se puede usar para reintentos o para procesar documentos ya guardados.
        """
        pass