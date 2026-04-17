import logging
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class QdrantClientManager:

    def __init__(self, host: str, port: int):
        logger.info("Conectando a Qdrant en %s:%d", host, port)
        self._client = QdrantClient(host=host, port=port)
        logger.info("Conexión con Qdrant establecida")

    @property
    def client(self) -> QdrantClient:
        return self._client

    def close(self) -> None:
        self._client.close()
        logger.info("Conexión con Qdrant cerrada")