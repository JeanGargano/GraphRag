import logging
from fastembed import TextEmbedding
from tokenizers import Tokenizer

logger = logging.getLogger(__name__)


class FastEmbedClient:

    def __init__(self, model_name: str, max_tokens: int):
        logger.info("Cargando modelo FastEmbed: %s", model_name)
        self._model = TextEmbedding(model_name=model_name)
        self._max_tokens = max_tokens
        self._tokenizer = Tokenizer.from_pretrained(model_name)
        self.vector_size = len(next(self._model.embed(["test"])))
        logger.info("Modelo listo | vector_size=%d", self.vector_size)

    def count_tokens(self, text: str) -> int:
        return len(self._tokenizer.encode(text).ids)

    def validate_chunks(self, chunks: list[str]) -> list[str]:
        """
        Descarta chunks que superen el límite de tokens del modelo.
        """
        valid = []
        for i, chunk in enumerate(chunks):
            token_count = self.count_tokens(chunk)
            if token_count > self._max_tokens:
                logger.warning(
                    "Chunk %d descartado: %d tokens (máx %d)",
                    i, token_count, self._max_tokens,
                )
            else:
                logger.debug("Chunk %d OK: %d tokens", i, token_count)
                valid.append(chunk)
        return valid

    def embed(self, chunks: list[str]) -> list[list[float]]:
        """
        Tokeniza internamente y genera el vector para cada chunk.
        """
        return [e.tolist() for e in self._model.embed(chunks)]