import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class INERProvider(ABC):

    @abstractmethod
    async def extract(self, text: str) -> dict:
        """Retorna un diccionario con estructura {"entities": [...], "relations": [...]}."""
        ...


class SpacyNERProvider(INERProvider):

    def __init__(self, model_name: str = "es_core_news_sm"):
        try:
            import spacy
            self._nlp = spacy.load(model_name)
            logger.info("Modelo spaCy cargado: %s", model_name)
        except OSError:
            raise RuntimeError(
                f"Modelo spaCy '{model_name}' no encontrado. "
                f"Descárgalo con: python -m spacy download {model_name}"
            )
        except ImportError as exc:
            raise RuntimeError("Instala spaCy: pip install spacy") from exc

    async def extract(self, text: str) -> dict:
        doc = self._nlp(text)
        entities = []
        for ent in doc.ents:
            if ent.text.strip():
                # spaCy genérico no tiene mapeo a atributos complejos de la ontología,
                # mapeamos texto y tipo de manera básica.
                entities.append({
                    "type": ent.label_,
                    "properties": {
                        "text": ent.text.strip()
                    }
                })
        return {
            "entities": entities,
            "relations": []
        }