from abc import ABC, abstractmethod
from typing import Optional


class IExtractionStrategy(ABC):
    """
    Define el contrato para extraer texto de un documento.
    Cada implementación maneja un tipo de archivo específico.
    """

    @abstractmethod
    def extract_content(self, file_path: str) -> Optional[str]:
        """
        Extrae el contenido textual del archivo en file_path.
        Retorna None si la extracción falla.
        """
        pass