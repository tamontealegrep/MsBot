# Guía de Desarrollo de Handlers - MSBot

Esta guía explica cómo crear handlers personalizados para integrar diferentes sistemas RAG con MSBot.

## 🏗️ Arquitectura de Handlers

MSBot utiliza un sistema modular de handlers que permite:

1. **Extensibilidad**: Agregar nuevos sistemas RAG sin modificar el código base
2. **Routing Inteligente**: Dirigir mensajes al handler apropiado
3. **Configuración Dinámica**: Habilitar/deshabilitar handlers en tiempo de ejecución
4. **Aislamiento**: Cada handler maneja sus propios errores y configuración

## 🧩 Tipos de Handlers

### 1. BaseHandler
Clase base abstracta para todos los handlers.

```python
from app.bot.handlers.base_handler import BaseHandler

class MiHandler(BaseHandler):
    def __init__(self):
        super().__init__(
            name="mi_handler",
            description="Descripción de mi handler"
        )
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        # Lógica de procesamiento
        return "Respuesta del handler"
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        # Lógica para determinar si puede manejar el mensaje
        return True
```

### 2. RAGHandler
Clase especializada para sistemas RAG.

```python
from app.bot.handlers.base_handler import RAGHandler

class MiRAGHandler(RAGHandler):
    def __init__(self, rag_config: Dict[str, Any]):
        super().__init__(
            name="mi_rag",
            description="Mi sistema RAG personalizado",
            rag_config=rag_config
        )
    
    async def query_rag_system(self, query: str, context: Dict[str, Any] = None) -> str:
        # Implementar consulta al sistema RAG
        return "Respuesta del sistema RAG"
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        # Lógica específica para este RAG
        return "rag" in message.lower()
```

## 📝 Ejemplos de Handlers

### Handler OpenAI RAG

```python
import openai
from typing import List, Dict, Any
from app.bot.handlers.base_handler import RAGHandler

class OpenAIRAGHandler(RAGHandler):
    """Handler para sistema RAG con OpenAI GPT"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(
            name="openai_rag",
            description="Sistema RAG con OpenAI GPT",
            rag_config={"model": model}
        )
        self.client = openai.OpenAI(api_key=api_key)
        self.knowledge_base = []  # Cargar documentos aquí
    
    async def query_rag_system(self, query: str, context: Dict[str, Any] = None) -> str:
        try:
            # 1. Buscar documentos relevantes
            relevant_docs = self._search_documents(query)
            
            # 2. Construir contexto
            context_text = "\n".join([doc["content"] for doc in relevant_docs])
            
            # 3. Crear prompt con contexto
            prompt = f"""
            Contexto:
            {context_text}
            
            Pregunta: {query}
            
            Responde basándote únicamente en el contexto proporcionado.
            """
            
            # 4. Consultar OpenAI
            response = self.client.chat.completions.create(
                model=self.rag_config["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error en consulta RAG: {str(e)}"
    
    def _search_documents(self, query: str) -> List[Dict[str, Any]]:
        # Implementar búsqueda semántica
        # Por ahora, búsqueda simple por palabras clave
        relevant = []
        for doc in self.knowledge_base:
            if any(word.lower() in doc["content"].lower() for word in query.split()):
                relevant.append(doc)
        return relevant[:3]  # Top 3 documentos
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        # Puede manejar cualquier mensaje (handler por defecto)
        return True
    
    def load_knowledge_base(self, documents: List[Dict[str, Any]]):
        """Cargar base de conocimiento"""
        self.knowledge_base = documents
```

### Handler Elasticsearch RAG

```python
from elasticsearch import Elasticsearch
from app.bot.handlers.base_handler import RAGHandler

class ElasticsearchRAGHandler(RAGHandler):
    """Handler para sistema RAG con Elasticsearch"""
    
    def __init__(self, es_host: str, index_name: str):
        super().__init__(
            name="elasticsearch_rag",
            description="Sistema RAG con Elasticsearch",
            rag_config={"host": es_host, "index": index_name}
        )
        self.es = Elasticsearch([es_host])
        self.index_name = index_name
    
    async def query_rag_system(self, query: str, context: Dict[str, Any] = None) -> str:
        try:
            # Buscar documentos relevantes
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "content"],
                        "type": "best_fields"
                    }
                },
                "size": 5
            }
            
            result = self.es.search(index=self.index_name, body=search_body)
            
            if not result["hits"]["hits"]:
                return "No encontré información relevante para tu consulta."
            
            # Construir respuesta con documentos encontrados
            response = "Basándome en la información disponible:\n\n"
            
            for i, hit in enumerate(result["hits"]["hits"], 1):
                source = hit["_source"]
                response += f"{i}. {source.get('title', 'Sin título')}\n"
                response += f"   {source.get('content', '')[:200]}...\n\n"
            
            return response
            
        except Exception as e:
            return f"Error en búsqueda: {str(e)}"
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        # Manejar consultas que contengan palabras clave específicas
        keywords = ["buscar", "encontrar", "información", "documento"]
        return any(keyword in message.lower() for keyword in keywords)
```

### Handler Condicional

```python
from app.bot.handlers.base_handler import BaseHandler

class ConditionalHandler(BaseHandler):
    """Handler que responde solo a comandos específicos"""
    
    def __init__(self):
        super().__init__(
            name="commands",
            description="Handler para comandos específicos"
        )
        self.commands = {
            "help": self._help_command,
            "status": self._status_command,
            "info": self._info_command
        }
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        if not self.enabled:
            return None
        
        # Extraer comando
        parts = message.strip().lower().split()
        if not parts or not parts[0].startswith('/'):
            return None
        
        command = parts[0][1:]  # Remover '/'
        
        if command in self.commands:
            return await self.commands[command](parts[1:], turn_context)
        
        return None
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        return message.strip().startswith('/')
    
    async def _help_command(self, args: List[str], turn_context: TurnContext) -> str:
        return """
        🤖 **Comandos disponibles:**
        
        /help - Mostrar esta ayuda
        /status - Estado del bot
        /info - Información del sistema
        """
    
    async def _status_command(self, args: List[str], turn_context: TurnContext) -> str:
        return "✅ Bot funcionando correctamente"
    
    async def _info_command(self, args: List[str], turn_context: TurnContext) -> str:
        return """
        📊 **Información del sistema:**
        
        - Bot: MSBot v1.0
        - Handlers activos: 3
        - Uptime: 2h 30m
        """
```

## 🔧 Registro de Handlers

### Registro Básico

```python
# En bot_handler.py o en un módulo de inicialización
from app.bot.handlers.handler_registry import HandlerRegistry

# Crear instancia del handler
mi_handler = MiRAGHandler(config)

# Registrar handler
registry = HandlerRegistry()
registry.register_handler("mi_rag", mi_handler, is_default=False)
```

### Registro con Configuración Dinámica

```python
import os
from app.bot.handlers.openai_rag_handler import OpenAIRAGHandler

def initialize_handlers(registry: HandlerRegistry):
    """Inicializar handlers basado en configuración"""
    
    # Handler OpenAI si hay API key
    if os.getenv("OPENAI_API_KEY"):
        openai_handler = OpenAIRAGHandler(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        )
        registry.register_handler("openai", openai_handler)
    
    # Handler Elasticsearch si está configurado
    if os.getenv("ELASTICSEARCH_HOST"):
        es_handler = ElasticsearchRAGHandler(
            es_host=os.getenv("ELASTICSEARCH_HOST"),
            index_name=os.getenv("ELASTICSEARCH_INDEX", "documents")
        )
        registry.register_handler("elasticsearch", es_handler)
    
    # Handler de comandos siempre activo
    cmd_handler = ConditionalHandler()
    registry.register_handler("commands", cmd_handler)
```

## 🎯 Routing Inteligente

### Routing por Contenido

```python
class SmartRouter:
    """Router inteligente para seleccionar el mejor handler"""
    
    def __init__(self, registry: HandlerRegistry):
        self.registry = registry
    
    def get_best_handler(self, message: str, context: Dict[str, Any] = None):
        """Seleccionar el mejor handler para un mensaje"""
        
        # 1. Verificar handlers con can_handle específico
        for name in self.registry.get_handler_names():
            handler = self.registry.get_handler(name)
            if handler and handler.enabled and handler.can_handle(message, context):
                return handler
        
        # 2. Usar handler por defecto
        return self.registry.get_default_handler()
```

### Routing por Prioridad

```python
class PriorityHandler(BaseHandler):
    """Handler con sistema de prioridades"""
    
    def __init__(self, name: str, description: str, priority: int = 0):
        super().__init__(name, description)
        self.priority = priority
    
    def get_priority(self, message: str, context: Dict[str, Any] = None) -> int:
        """Calcular prioridad para un mensaje específico"""
        base_priority = self.priority
        
        # Ajustar prioridad basado en contenido
        if self.can_handle(message, context):
            base_priority += 10
        
        return base_priority
```

## 🔄 Ciclo de Vida de Handlers

### Inicialización

```python
class AdvancedHandler(RAGHandler):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("advanced", "Handler avanzado", config)
        self.initialized = False
    
    async def initialize(self):
        """Inicialización asíncrona del handler"""
        if self.initialized:
            return
        
        # Configurar conexiones, cargar modelos, etc.
        await self._setup_connections()
        await self._load_models()
        
        self.initialized = True
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        if not self.initialized:
            await self.initialize()
        
        return await super().handle_message(message, turn_context)
```

### Limpieza

```python
class ResourceHandler(BaseHandler):
    def __init__(self):
        super().__init__("resource", "Handler con recursos")
        self.connection = None
    
    async def cleanup(self):
        """Limpiar recursos del handler"""
        if self.connection:
            await self.connection.close()
            self.connection = None
    
    def __del__(self):
        """Destructor para limpieza automática"""
        if hasattr(self, 'connection') and self.connection:
            # Nota: En producción, usar un método de limpieza explícito
            pass
```

## 📊 Métricas y Monitoreo

### Handler con Métricas

```python
import time
from collections import defaultdict
from app.bot.handlers.base_handler import BaseHandler

class MetricsHandler(BaseHandler):
    """Handler base con métricas incorporadas"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self.metrics = {
            "total_messages": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "avg_response_time": 0,
            "response_times": []
        }
        self.start_time = time.time()
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        start = time.time()
        self.metrics["total_messages"] += 1
        
        try:
            response = await self._process_message(message, turn_context)
            
            if response:
                self.metrics["successful_responses"] += 1
            else:
                self.metrics["failed_responses"] += 1
            
            # Calcular tiempo de respuesta
            response_time = time.time() - start
            self.metrics["response_times"].append(response_time)
            
            # Mantener solo últimas 100 mediciones
            if len(self.metrics["response_times"]) > 100:
                self.metrics["response_times"].pop(0)
            
            # Actualizar promedio
            self.metrics["avg_response_time"] = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            
            return response
            
        except Exception as e:
            self.metrics["failed_responses"] += 1
            raise
    
    async def _process_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """Implementar lógica específica del handler"""
        raise NotImplementedError
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del handler"""
        uptime = time.time() - self.start_time
        
        return {
            **self.metrics,
            "uptime_seconds": uptime,
            "messages_per_minute": self.metrics["total_messages"] / (uptime / 60) if uptime > 0 else 0,
            "success_rate": (self.metrics["successful_responses"] / self.metrics["total_messages"]) * 100 if self.metrics["total_messages"] > 0 else 0
        }
```

## 🚀 Mejores Prácticas

### 1. Manejo de Errores

```python
async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
    try:
        return await self._process_message(message, turn_context)
    except ConnectionError:
        return "Temporalmente no puedo acceder al sistema. Intenta más tarde."
    except TimeoutError:
        return "La consulta está tomando mucho tiempo. Intenta con una pregunta más específica."
    except Exception as e:
        self.logger.error(f"Error en handler {self.name}: {e}")
        return "Ocurrió un error procesando tu mensaje. Por favor intenta de nuevo."
```

### 2. Configuración Flexible

```python
from pydantic import BaseModel
from typing import Optional

class RAGConfig(BaseModel):
    api_key: str
    model: str = "default"
    max_tokens: int = 500
    temperature: float = 0.7
    timeout: int = 30

class ConfigurableRAGHandler(RAGHandler):
    def __init__(self, config: RAGConfig):
        super().__init__("configurable_rag", "Handler configurable")
        self.config = config
```

### 3. Testing

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_handler_response():
    handler = MiRAGHandler({"test": True})
    turn_context = MagicMock()
    
    response = await handler.handle_message("test message", turn_context)
    
    assert response is not None
    assert "test" in response.lower()

@pytest.mark.asyncio
async def test_handler_can_handle():
    handler = MiRAGHandler({"test": True})
    
    assert handler.can_handle("rag query")
    assert not handler.can_handle("unrelated message")
```

## 📚 Recursos Adicionales

- [Bot Framework SDK Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Microsoft Teams Bot Examples](https://github.com/microsoft/BotFramework-Samples)
- [Patterns for Bot Development](https://docs.microsoft.com/en-us/azure/bot-service/bot-builder-concept-dialog)

---

Esta guía proporciona la base para crear handlers personalizados. Cada sistema RAG tendrá sus propias particularidades, pero siguiendo estos patrones podrás integrar cualquier sistema de manera limpia y mantenible.