# GraphRAG

Desarrollo de un sistema GraphRAG (Retrieval-Augmented Generation basado en grafos)para asistir consultas sobre modalidades de trabajo de grado en la Universidad Autónoma de Occidente.

---

## Descripción General

Este sistema está basado en una arquitectura de microservicios, donde cada servicio cumple una función específica dentro del pipeline de procesamiento de documentos, generación de embeddings y recuperación de información.

El objetivo principal es permitir que un usuario consulte información relevante a partir de documentos previamente procesados, utilizando técnicas de IA y búsqueda semántica.

---

## Arquitectura del Sistema

Actualmente el sistema está compuesto por los siguientes microservicios:

### Orchestrator_Service

Es el **punto de entrada del sistema**.

**Responsabilidades:**

* Recibir las solicitudes del cliente
* Orquestar el flujo de comunicación entre microservicios
* Coordinar el procesamiento de documentos y consultas

**Puerto:** `8000`

---

### Document_Service

Encargado del procesamiento de documentos.

**Responsabilidades:**

* Recibir documentos o texto
* Dividir el contenido en chunks (fragmentos)
* Enviar los chunks al servicio de embeddings

**Comunicación:**

* Se conecta con `Embedding_Service`

**Puerto:** `8001`

---

### Embedding_Service

Encargado de la vectorización del contenido.

**Responsabilidades:**

* Generar embeddings a partir de texto
* Validar chunks según el número de tokens
* Almacenar los vectores en la base de datos vectorial

**Tecnologías:**

* FastEmbed
* Modelos de embedding `bge-small-en`

**Base de datos:**

* Qdrant

**Puerto:** `8002`

---

### Qdrant

Base de datos vectorial utilizada para almacenar embeddings.

Responsabilidades:

* Almacenamiento de vectores
* Búsqueda por similitud (ANN)

**Puerto:** `6333`

---

## Flujo del Sistema de Ingesta del Sistema

1. El usuario envía una solicitud al **Orchestrator**
2. El Orchestrator envía el documento al **Document Service**
3. El Document Service:

   * Divide el texto en chunks
   * Envía los chunks al **Embedding Service**
4. El Embedding Service:

   * Genera embeddings
   * Los almacena en **Qdrant**

---

## Cómo ejecutar el proyecto

### 1. Requisitos

* Docker
* Docker Compose

---

### 2. Levantar los servicios

Ubícate en la carpeta Backend y ejecuta

```bash
docker-compose up -d
```

---

### 3. Verificar servicios

Una vez levantado, tendrás:

| Servicio          | URL                   |
| ----------------- | --------------------- |
| Orchestrator      | http://localhost:8000 |
| Document Service  | http://localhost:8001 |
| Embedding Service | http://localhost:8002 |
| Qdrant            | http://localhost:6333 |

---

## Acceso a Qdrant

Puedes verificar que Qdrant está funcionando accediendo a:

```
http://localhost:6333
```

Respuesta esperada:

```json
{"title":"qdrant - vector search engine"}
```
Para visualizar dashboard de Qdrant:
http://localhost:6333/dashboard

---


## 🐳 Docker Compose

El sistema está completamente dockerizado y utiliza una red interna para la comunicación entre servicios.

* Los servicios se comunican usando el **nombre del contenedor**
* Ejemplo: `http://embedding_service:8002`

---

#

## Estado actual

Orquestación básica
Procesamiento de documentos
Generación de embeddings
Integración con Qdrant

Pendiente:

* Indexer Service
* Question Service
* Integración completa con LLM

---

## Autor

Jean Alfred Gargano Alomia

---
