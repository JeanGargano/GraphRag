import logging
import os
from typing import Optional
from fastapi import HTTPException, UploadFile, status
from config import settings

logger = logging.getLogger(__name__)

DANGEROUS_EXTENSIONS = {
    "exe", "bat", "sh", "ps1", "cmd", "msi",
    "js", "vbs", "py", "rb", "php",
}


async def validate_file(file: UploadFile) -> bytes:
    """
    Valida el archivo entrante aplicando reglas de API Gateway:
    - Extensión permitida
    - Extensión no peligrosa
    - Tamaño máximo
    - Nombre de archivo saneado

    Retorna los bytes del archivo para evitar doble lectura en el servicio.
    """
    _validate_filename(file.filename)
    content = await _read_and_validate_size(file)
    return content


def _validate_filename(filename: Optional[str]) -> None:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no tiene nombre.",
        )

    ext = _get_extension(filename)

    if ext in DANGEROUS_EXTENSIONS:
        logger.warning("Intento de subida de archivo peligroso: %s", filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido por seguridad.",
        )

    if ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Extensión '.{ext}' no soportada. "
                f"Permitidas: {', '.join(settings.allowed_extensions_list)}"
            ),
        )


async def _read_and_validate_size(file: UploadFile) -> bytes:
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío.",
        )

    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"El archivo supera el tamaño máximo permitido "
                f"de {settings.max_file_size_mb} MB."
            ),
        )

    return content


def _get_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


from typing import Optional