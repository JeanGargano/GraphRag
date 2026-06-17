import logging
import json
from openai import AsyncOpenAI
from indexer_Service.Infra.Spacy_Client import INERProvider

logger = logging.getLogger(__name__)

class LLMNERProvider(INERProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1", model: str = "llama-3.1-8b-instant"): 
        if not api_key:
            raise ValueError("API Key no configurada para el LLM de NER")
            
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self._model = model
        
        self.ontology_labels = {
            "resolución", "modalidad", "requisitos", "procedimiento", 
            "unidadapoyo", "documentación", "programa", "facultad", "tiempo"
        }

    async def extract(self, text: str) -> dict:
        """
        Analiza el texto y extrae entidades y relaciones estructuradas de acuerdo con la ontología de UAO.
        """
        system_prompt = (
            "Eres un experto en extracción de conocimiento y modelado de grafos (GraphRAG). Tu tarea es analizar texto académico y extraer entidades y relaciones siguiendo ESTRICTAMENTE la ontología de la Universidad Autónoma de Occidente.\n\n"
            "### REGLAS DE NORMALIZACIÓN (EVITAR DUPLICADOS):\n"
            "1. Eres responsable de la 'Resolución de Entidades': Antes de crear una entidad, normaliza el texto.\n"
            "   - Aplica el principio de 'Nombre Canónico': Si encuentras variaciones (ej. 'Facultad de Ingeniería' vs 'Facultad de Ingeniería y Ciencias Básicas'), usa siempre el nombre oficial más preciso y completo.\n"
            "   - Agrupa sinónimos bajo el estándar de la ontología para evitar nodos duplicados en el grafo.\n"
            "2. Si un atributo no está explícito en el texto, usa `null`. NO inventes valores.\n"
            "3. Salida: Responde ÚNICAMENTE con un JSON estructurado con las claves \"entities\" y \"relations\".\n\n"
            "### ONTOLOGÍA (NODOS Y ATRIBUTOS):\n"
            "- Resolución: {titulo_resolucion, estado_actual, numero, fecha, nivel}\n"
            "- Modalidad: {nombre_modalidad, descripcion, num_max_estudiantes, articulo}\n"
            "- Requisitos: {tipo_requisito, plan_academico, descripcion, valor_minimo}\n"
            "- Procedimiento: {nombre_etapa, orden, plataforma_asociada}\n"
            "- UnidadApoyo: {nombre_rol, correo_contacto, tipo_actor}\n"
            "- Documentación: {nombre, identificador, tipo, url, estado}\n"
            "- Programa: {nombre_programa, planes_vigentes}\n"
            "- Facultad: {nombre_facultad}\n"
            "- Tiempo: {descripcion, fechaLimite}\n\n"
            "### ESQUEMA DE RELACIONES (CONEXIONES Y ATRIBUTOS):\n"
            "- (Procedimiento {nombre_etapa})-[:REQUIERE_APROBACION_DE {tipo_aprobacion, tiempo_respuesta, nota_requerida}]->(UnidadApoyo {nombre_rol})\n"
            "- (Resolución {titulo_resolucion})-[:SOPORTADO_EN]->(Documentación {identificador})\n"
            "- (Modalidad {nombre_modalidad})-[:TIENE_REQUISITOS {momento_exigencia, condicion_especial, es_obligatorio}]->(Requisitos {tipo_requisito})\n"
            "- (Modalidad {nombre_modalidad})-[:APLICA_A {fecha_inscripcion, estado_solicitud}]->(Resolución {titulo_resolucion})\n"
            "- (Modalidad {nombre_modalidad})-[:CONSTA_DE_ETAPA {orden_etapa}]->(Procedimiento {nombre_etapa})\n"
            "- (Requisitos {tipo_requisito})-[:ASOCIADO_A]->(Procedimiento {nombre_etapa})\n"
            "- (Procedimiento {nombre_etapa})-[:REQUIERE_DE {articulo_aplicable, tipo_documento}]->(Documentación {identificador})\n"
            "- (Procedimiento {nombre_etapa})-[:ES_PRERREQUISITO_DE {tiempo_maximo_etapa}]->(Procedimiento {nombre_etapa})\n"
            "- (Procedimiento {nombre_etapa})-[:DEBE_CUMPLIR]->(Tiempo {descripcion})\n"
            "- (Documentación {identificador})-[:DEBE_CUMPLIR]->(Resolución {titulo_resolucion})\n"
            "- (Programa {nombre_programa})-[:OFRECE {aplica_plan_estudio}]->(Modalidad {nombre_modalidad})\n"
            "- (Programa {nombre_programa})-[:TIENE_COMO_APOYO {nivel_resolucion}]->(UnidadApoyo {nombre_rol})\n"
            "- (Programa {nombre_programa})-[:SE_RIGE_POR {periodo_academico}]->(Resolución {titulo_resolucion})\n"
            "- (Facultad {nombre_facultad})-[:ADMINISTRA {resolucion_aprobacion}]->(Programa {nombre_programa})\n"
            "- (Tiempo {descripcion})-[:VINCULADO_A]->(UnidadApoyo {nombre_rol})\n\n"
            "### FORMATO JSON:\n"
            "{\n"
            "  \"entities\": [\n"
            "    { \"type\": \"Procedimiento\", \"properties\": { \"nombre_etapa\": \"...\", \"orden\": 1 } }\n"
            "  ],\n"
            "  \"relations\": [\n"
            "    {\n"
            "      \"source\": { \"type\": \"Procedimiento\", \"nombre_etapa\": \"...\" },\n"
            "      \"target\": { \"type\": \"UnidadApoyo\", \"nombre_rol\": \"...\" },\n"
            "      \"type\": \"REQUIERE_APROBACION_DE\",\n"
            "      \"properties\": { \"tipo_aprobacion\": \"...\" }\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            logger.info("Solicitando extracción de entidades y relaciones al LLM (Groq)...")
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Texto a analizar:\n{text}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_data = json.loads(response.choices[0].message.content)
            
            # Sanitizar y validar tipos de entidades
            entities = result_data.get("entities", [])
            valid_entities = []
            for item in entities:
                ent_type = item.get("type", "").strip()
                properties = item.get("properties", {})
                if ent_type.lower() in self.ontology_labels and isinstance(properties, dict):
                    item["type"] = ent_type.capitalize()
                    valid_entities.append(item)
                    
            relations = result_data.get("relations", [])
            valid_relations = []
            for rel in relations:
                source = rel.get("source")
                target = rel.get("target")
                rel_type = rel.get("type")
                if isinstance(source, dict) and isinstance(target, dict) and rel_type:
                    valid_relations.append(rel)
                    
            return {
                "entities": valid_entities,
                "relations": valid_relations
            }
            
        except Exception as e:
            logger.error(f"Error en extracción LLM NER de entidades/relaciones: {e}")
            return {"entities": [], "relations": []}
