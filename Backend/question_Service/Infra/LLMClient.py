import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1", model: str = "openai/gpt-oss-120b"):
        if not api_key:
            raise ValueError("API Key no configurada para el LLM")
            
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self._model = model

    async def generate_answer(self, query: str, context: str) -> str:
        """
        Genera una respuesta utilizando el LLM basado en el contexto proporcionado.
        """
        system_prompt = (
            "Eres un asistente virtual de la Universidad Autónoma de Occidente, especializado en modalidades de trabajo de grado. "
            "Responde a la pregunta del usuario utilizando ÚNICAMENTE la información proporcionada en el siguiente CONTEXTO. "
            "Si el contexto no contiene información suficiente para responder, di que no tienes la información. "
            "Responde en un tono amable, claro y en español."
        )

        user_prompt = f"CONTEXTO:\n{context}\n\nPREGUNTA:\n{query}"

        try:
            logger.info("Enviando petición a Groq (LLM)...")
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3, 
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generando respuesta con LLM: {e}")
            return f"Lo siento, ocurrió un error al intentar generar la respuesta: {str(e)}"
