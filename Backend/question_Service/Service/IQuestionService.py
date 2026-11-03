from abc import ABC, abstractmethod

from question_Service.Model.Schemas import QuestionRequest, QuestionResponse


class IQuestionService(ABC):

    @abstractmethod
    async def ask_question(self, request: QuestionRequest) -> QuestionResponse:
        """Recuperación híbrida (vector + grafo) y generación de respuesta."""
        pass
