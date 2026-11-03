class GraphRAGError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UnsupportedFileTypeError(GraphRAGError):
    def __init__(self, extension: str):
        super().__init__(
            f"Tipo de archivo '{extension}' no soportado.",
            status_code=415,
        )


class MissingFileExtensionError(GraphRAGError):
    def __init__(self):
        super().__init__("El archivo no tiene extensión.", status_code=400)


class EmptyDocumentError(GraphRAGError):
    def __init__(self):
        super().__init__(
            "No se pudo extraer texto del documento.",
            status_code=422,
        )


class NoValidChunksError(GraphRAGError):
    def __init__(self, message: str = "No hay chunks válidos para indexar."):
        super().__init__(message, status_code=422)


class LLMNotConfiguredError(GraphRAGError):
    def __init__(self):
        super().__init__(
            "El generador de respuestas no está configurado (falta groq_api_key).",
            status_code=503,
        )


class QuestionServiceUnavailableError(GraphRAGError):
    def __init__(self):
        super().__init__("QuestionService no está disponible.", status_code=503)
