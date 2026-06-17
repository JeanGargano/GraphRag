import os
import logging
from neo4j import Driver

logger = logging.getLogger(__name__)


ONTOLOGY_MAP = {
    "resolución": {"label": "Resolución", "key": "titulo_resolucion"},
    "modalidad": {"label": "Modalidad", "key": "nombre_modalidad"},
    "requisitos": {"label": "Requisitos", "key": "tipo_requisito"},
    "procedimiento": {"label": "Procedimiento", "key": "nombre_etapa"},
    "unidadapoyo": {"label": "UnidadApoyo", "key": "nombre_rol"},
    "documentación": {"label": "Documentación", "key": "identificador"},
    "programa": {"label": "Programa", "key": "nombre_programa"},
    "facultad": {"label": "Facultad", "key": "nombre_facultad"},
    "tiempo": {"label": "Tiempo", "key": "descripcion"},
}


class GraphRepository:

    def __init__(self, driver: Driver):
        self._driver = driver
        self._create_constraints()
        self._apply_ontology()

    def _apply_ontology(self) -> None:
        """
        Lee y ejecuta el archivo de ontología (ontology.cypher) si existe en este directorio.
        """
        ontology_path = os.path.join(os.path.dirname(__file__), "ontology.cypher")
        if not os.path.exists(ontology_path):
            logger.info("No se encontró archivo de ontología en %s, saltando.", ontology_path)
            return

        logger.info("Cargando ontología desde %s", ontology_path)
        try:
            with open(ontology_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parser básico: separar por ';' y omitir comentarios
            queries = []
            for query in content.split(";"):
                clean_lines = []
                for line in query.splitlines():
                    striped_line = line.strip()
                    if striped_line.startswith("//") or not striped_line:
                        continue
                    clean_lines.append(line)
                clean_query = "\n".join(clean_lines).strip()
                if clean_query:
                    queries.append(clean_query)

            with self._driver.session() as session:
                for q in queries:
                    session.run(q)
            logger.info("Ontología aplicada correctamente en Neo4j (%d consultas ejecutadas)", len(queries))
        except Exception as e:
            logger.error("Error al aplicar la ontología: %s", e)

    def _create_constraints(self) -> None:
        """
        Define constraints e índices al arrancar.
        Equivalente a las 'colecciones' en Qdrant.
        """
        with self._driver.session() as session:
            # Unicidad de documentos
            session.run("""
                CREATE CONSTRAINT document_id_unique IF NOT EXISTS
                FOR (d:Document) REQUIRE d.document_id IS UNIQUE
            """)
            # Unicidad de chunks
            session.run("""
                CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
                FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
            """)
            # Unicidad de los nodos de la ontología
            for name, info in ONTOLOGY_MAP.items():
                label = info["label"]
                key = info["key"]
                session.run(f"""
                    CREATE CONSTRAINT {name}_unique IF NOT EXISTS
                    FOR (n:{label}) REQUIRE n.{key} IS UNIQUE
                """)
            logger.info("Constraints e índices de Neo4j verificados")

    def upsert_document(self, document_id: str, filename: str) -> None:
        with self._driver.session() as session:
            session.run("""
                MERGE (d:Document {document_id: $document_id})
                SET d.filename = $filename
            """, document_id=document_id, filename=filename)

    def upsert_chunk(
        self,
        document_id: str,
        chunk_id: str,
        chunk_index: int,
        text: str,
    ) -> None:
        with self._driver.session() as session:
            # Crear chunk y relacionarlo con el documento
            session.run("""
                MERGE (c:Chunk {chunk_id: $chunk_id})
                SET c.text = $text,
                    c.chunk_index = $chunk_index,
                    c.document_id = $document_id
                WITH c
                MATCH (d:Document {document_id: $document_id})
                MERGE (d)-[:HAS_CHUNK]->(c)
            """, chunk_id=chunk_id, text=text,
                chunk_index=chunk_index, document_id=document_id)

    def link_consecutive_chunks(
        self,
        chunk_id_current: str,
        chunk_id_next: str,
    ) -> None:
        with self._driver.session() as session:
            session.run("""
                MATCH (a:Chunk {chunk_id: $current})
                MATCH (b:Chunk {chunk_id: $next})
                MERGE (a)-[:NEXT_CHUNK]->(b)
            """, current=chunk_id_current, next=chunk_id_next)

    def upsert_entity_and_link(
        self,
        chunk_id: str,
        entity_text: str,
        entity_label: str,
    ) -> None:
        info = ONTOLOGY_MAP.get(entity_label.lower())
        if not info:
            logger.warning("Etiqueta '%s' no pertenece a la ontología. Omitiendo.", entity_label)
            return

        label = info["label"]
        key = info["key"]

        query = f"""
            MERGE (e:{label} {{{key}: $text}})
            WITH e
            MATCH (c:Chunk {{chunk_id: $chunk_id}})
            MERGE (c)-[:MENTIONS]->(e)
        """
        with self._driver.session() as session:
            session.run(query, text=entity_text, chunk_id=chunk_id)

    def upsert_custom_entity_and_link(
        self,
        chunk_id: str,
        entity_type: str,
        properties: dict,
    ) -> None:
        """
        Inserta una entidad con múltiples propiedades de la ontología y la asocia al Chunk.
        """
        info = ONTOLOGY_MAP.get(entity_type.lower())
        if not info:
            logger.warning("Tipo de entidad '%s' no mapeado en la ontología. Omitiendo.", entity_type)
            return

        label = info["label"]
        key = info["key"]
        
        # Extraer el valor llave
        key_value = properties.get(key)
        if not key_value:
            # Fallback en caso de que use 'text' o no venga el campo clave
            key_value = properties.get("text") or properties.get("nombre") or ""
            key_value = str(key_value).strip()
            if not key_value:
                logger.warning("La propiedad clave '%s' para la etiqueta '%s' está vacía. Omitiendo.", key, label)
                return
            properties[key] = key_value

        # Construir set query de propiedades dinámicamente, omitiendo valores nulos
        set_statements = []
        params = {"key_value": key_value, "chunk_id": chunk_id}
        
        for k, v in properties.items():
            if k == key:
                continue
            # Guardamos con valores nulos como null explícito
            set_statements.append(f"e.{k} = ${k}")
            params[k] = v

        set_clause = ", ".join(set_statements)
        set_query = f"ON CREATE SET {set_clause}" if set_statements else ""
        merge_query = f"ON MATCH SET {set_clause}" if set_statements else ""

        query = f"""
            MERGE (e:{label} {{{key}: $key_value}})
            {set_query}
            {merge_query}
            WITH e
            MATCH (c:Chunk {{chunk_id: $chunk_id}})
            MERGE (c)-[:MENTIONS]->(e)
        """
        with self._driver.session() as session:
            session.run(query, **params)

    def upsert_custom_relation(
        self,
        source: dict,
        target: dict,
        rel_type: str,
        properties: dict,
    ) -> None:
        """
        Crea una relación directa entre dos nodos de la ontología basándose en sus atributos clave únicos.
        """
        source_type = source.get("type", "")
        target_type = target.get("type", "")
        
        source_info = ONTOLOGY_MAP.get(source_type.lower())
        target_info = ONTOLOGY_MAP.get(target_type.lower())
        
        if not source_info or not target_info:
            logger.warning("Relación omitida: Tipos '%s' o '%s' no mapeados en la ontología.", source_type, target_type)
            return

        source_label = source_info["label"]
        source_key = source_info["key"]
        source_value = source.get(source_key)
        
        target_label = target_info["label"]
        target_key = target_info["key"]
        target_value = target.get(target_key)
        
        # Fallback en caso de que no usen la clave exacta
        if not source_value:
            source_value = next((v for k, v in source.items() if k != "type" and v), None)
        if not target_value:
            target_value = next((v for k, v in target.items() if k != "type" and v), None)
            
        if not source_value or not target_value:
            logger.warning("Relación omitida: Faltan valores llave para %s o %s.", source_label, target_label)
            return

        source_value = str(source_value).strip()
        target_value = str(target_value).strip()

        # Agregar SET dinámico para las propiedades de la relación si existen
        set_statements = []
        params = {"source_val": source_value, "target_val": target_value}
        for k, v in properties.items():
            set_statements.append(f"r.{k} = ${k}")
            params[k] = v

        set_clause = "SET " + ", ".join(set_statements) if set_statements else ""
        
        # Validar tipo de relación seguro para evitar Cypher Injections
        allowed_rels = {
            "ADMINISTRA", "TIENE_COMO_APOYO", "OFRECE", "TIENE_REQUISITOS",
            "CONSTA_DE_ETAPA", "APLICA_A", "REQUIERE_DE", "ES_PRERREQUISITO_DE",
            "DEBE_CUMPLIR", "REQUIERE_APROBACION_DE", "SOPORTADO_EN", "VINCULADO_A"
        }
        
        clean_rel_type = rel_type.strip().upper()
        if clean_rel_type not in allowed_rels:
            logger.warning("Relación '%s' no permitida por seguridad o no pertenece a la ontología. Omitiendo.", rel_type)
            return

        final_query = f"""
            MATCH (a:{source_label} {{{source_key}: $source_val}})
            MATCH (b:{target_label} {{{target_key}: $target_val}})
            MERGE (a)-[r:{clean_rel_type}]->(b)
            {set_clause}
        """
        with self._driver.session() as session:
            session.run(final_query, **params)


    def search_chunks_by_entities(self, entities: list[str], limit: int = 15) -> list[dict]:
        """
        Realiza una búsqueda exploratoria en el grafo utilizando las etiquetas reales de la ontología:
        1. Chunks que mencionan las entidades directamente.
        2. Chunks vecinos (anterior/siguiente) para mantener el contexto.
        3. Chunks de otras entidades que co-ocurren con las buscadas.
        """
        if not entities:
            return []
            
        ontology_labels = [info["label"] for info in ONTOLOGY_MAP.values()]

        with self._driver.session() as session:
            # Esta query busca nodos de cualquiera de los tipos de la ontología, comparando sus atributos dinámicamente.
            # Luego explora el grafo a partir de los chunks que los mencionan.
            result = session.run("""
                MATCH (e)
                WHERE any(label IN labels(e) WHERE label IN $ontology_labels)
                  AND any(key IN keys(e) WHERE toLower(toStringOrNull(e[key])) IN [ent IN $entities | toLower(ent)])
                
                // Nivel 1: Chunks directos y sus vecinos inmediatos
                MATCH (e)<-[:MENTIONS]-(c:Chunk)
                OPTIONAL MATCH (c)-[:NEXT_CHUNK*0..1]-(neighbor:Chunk)
                
                // Nivel 2: Co-ocurrencia (Otras entidades de la ontología en los mismos chunks)
                OPTIONAL MATCH (neighbor)-[:MENTIONS]->(co_entity)<-[:MENTIONS]-(co_chunk:Chunk)
                WHERE any(lbl IN labels(co_entity) WHERE lbl IN $ontology_labels)
                
                WITH neighbor, co_chunk, e
                UNWIND [neighbor, co_chunk] AS result_chunk
                
                // Extraer el texto de coincidencia de forma dinámica (el primer valor de propiedad que coincida)
                WITH result_chunk, e,
                     [key IN keys(e) WHERE toLower(toStringOrNull(e[key])) IN [ent IN $entities | toLower(ent)]][0] AS matched_key
                
                RETURN DISTINCT result_chunk.chunk_id AS chunk_id, 
                       result_chunk.text AS text, 
                       result_chunk.document_id AS document_id, 
                       e[matched_key] AS matched_entity
                LIMIT $limit
            """, entities=entities, ontology_labels=ontology_labels, limit=limit)
            return [record.data() for record in result]


