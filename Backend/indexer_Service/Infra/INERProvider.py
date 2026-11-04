from abc import ABC, abstractmethod
class INERProvider(ABC):

    @abstractmethod
    async def extract(self, text: str) -> dict:
        """Retorna un diccionario con estructura {"entities": [...], "relations": [...]}."""
        ...