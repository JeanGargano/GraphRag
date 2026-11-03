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

    def split_into_chunks(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """
        Parte el texto en ventanas de tokens. Cada chunk tiene como máximo
        min(chunk_size, max_tokens) tokens.
        """
        window = min(chunk_size, self._max_tokens)
        token_overlap = min(overlap, window - 1) if window > 1 else 0
        ids = self._tokenizer.encode(text).ids
        if not ids:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(ids):
            end = min(start + window, len(ids))
            piece = self._tokenizer.decode(ids[start:end]).strip()
            if piece:
                chunks.append(piece)
            if end >= len(ids):
                break
            start += window - token_overlap
        return chunks

    def embed(self, chunks: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self._model.embed(chunks)]
