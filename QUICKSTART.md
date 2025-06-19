# 🚀 MSBot - Quick Start Guide

¡Bienvenido a MSBot! Esta guía te ayudará a tener tu bot funcionando en menos de 10 minutos.

## ⚡ Inicio Rápido (5 minutos)

### 1. Configurar Variables de Entorno

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar con tus credenciales
nano .env
```

**Configurar estas variables críticas:**
```env
MICROSOFT_APP_ID=tu_app_id_de_azure
MICROSOFT_APP_PASSWORD=tu_password_de_azure
```

### 2. Instalar y Ejecutar

```bash
# Opción 1: Script automático (recomendado)
./scripts/start.sh

# Opción 2: Manual
pip install -r requirements.txt
python setup_ssl.py
python main.py
```

### 3. Verificar Funcionamiento

```bash
# Verificar que el bot responde
curl -k https://localhost:3978/

# Debería retornar:
# {"status":"healthy","bot_name":"MSBot","version":"1.0.0"}
```

¡Listo! Tu bot está funcionando localmente.

## 🌐 Conectar con Microsoft Teams

### Paso 1: Configurar Túnel (Desarrollo)

```bash
# Instalar ngrok (https://ngrok.com/download)
ngrok http 3978

# Usar la URL HTTPS que ngrok proporciona
# Ejemplo: https://abc123def.ngrok.io
```

### Paso 2: Registrar Bot en Teams

1. **Azure Portal** → **App registrations** → **New registration**
   - Nombre: MSBot
   - Guardar Application ID y crear Client Secret

2. **Bot Framework Portal** → **Create a Bot**
   - App ID: [Tu Application ID]
   - Password: [Tu Client Secret]  
   - Messaging endpoint: `https://tu-ngrok-url.ngrok.io/api/messages`

3. **Teams Developer Portal** → **New app**
   - Configurar bot con tu Application ID
   - Descargar package y subir a Teams

📖 **Guía completa:** [docs/setup_teams.md](docs/setup_teams.md)

## 🔧 Comandos Útiles

```bash
# Iniciar bot
./scripts/start.sh

# Solo verificar configuración
./scripts/start.sh check

# Configuración inicial
./scripts/start.sh setup

# Ver estado del bot
curl -k https://localhost:3978/api/status

# Monitor de salud
python scripts/health_monitor.py --single-check

# Ver logs en tiempo real
tail -f bot.log
```

## 🧩 Agregar Tu Primer Handler RAG

### 1. Crear Handler Personalizado

```python
# handlers/mi_rag_handler.py
from app.bot.handlers.base_handler import RAGHandler

class MiRAGHandler(RAGHandler):
    def __init__(self):
        super().__init__(
            name="mi_rag",
            description="Mi sistema RAG personalizado"
        )
    
    async def query_rag_system(self, query: str, context=None) -> str:
        # Aquí va tu lógica RAG
        return f"Respuesta RAG para: {query}"
    
    def can_handle(self, message: str, context=None) -> bool:
        return "rag" in message.lower()
```

### 2. Registrar Handler

```python
# En bot_handler.py, método _register_default_handlers()
mi_rag = MiRAGHandler()
self.handler_registry.register_handler("mi_rag", mi_rag)
```

### 3. Probar Handler

Envía un mensaje con "rag" en Teams y verás tu handler en acción.

## 📝 Ejemplos de Handlers

### Handler OpenAI

```python
import openai
from app.bot.handlers.base_handler import RAGHandler

class OpenAIRAGHandler(RAGHandler):
    def __init__(self, api_key: str):
        super().__init__("openai_rag", "OpenAI RAG Handler")
        self.client = openai.OpenAI(api_key=api_key)
    
    async def query_rag_system(self, query: str, context=None) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query}]
        )
        return response.choices[0].message.content
```

### Handler de Base de Datos

```python
import sqlite3
from app.bot.handlers.base_handler import RAGHandler

class DatabaseRAGHandler(RAGHandler):
    def __init__(self, db_path: str):
        super().__init__("database_rag", "Database RAG Handler")
        self.db_path = db_path
    
    async def query_rag_system(self, query: str, context=None) -> str:
        conn = sqlite3.connect(self.db_path)
        # Implementar búsqueda en base de datos
        # Retornar resultados formateados
        conn.close()
        return "Resultados de la base de datos..."
```

## 🔍 Solución de Problemas Rápida

### Bot No Inicia

```bash
# Verificar dependencias
pip install -r requirements.txt

# Verificar configuración
python -c "from app.config.settings import get_settings; print(get_settings().validate_bot_config())"

# Ver logs de error
tail -20 bot.log
```

### Teams No Se Conecta

```bash
# Verificar que el bot responde
curl -k https://localhost:3978/

# Verificar ngrok funciona
curl https://tu-ngrok-url.ngrok.io/

# Verificar endpoint en Bot Framework
# Debe ser: https://tu-ngrok-url.ngrok.io/api/messages
```

### Errores de SSL

```bash
# Regenerar certificados
rm -rf certs/
python setup_ssl.py
```

## 📚 Arquitectura Rápida

```
Usuario en Teams 
    ↓
Microsoft Teams Service
    ↓
Bot Framework (valida autenticación)
    ↓
Webhook → https://tu-servidor/api/messages
    ↓
MSBot (main.py)
    ↓
BotHandler (procesa mensaje)
    ↓
HandlerRegistry (selecciona handler apropiado)
    ↓
EchoHandler / TuRAGHandler (procesa y responde)
    ↓
Respuesta → Teams → Usuario
```

## 🎯 Próximos Pasos

1. **Integrar tu sistema RAG** siguiendo los ejemplos
2. **Configurar producción** con certificados SSL reales
3. **Monitoreo avanzado** con logs estructurados
4. **Despliegue** en tu servidor local

## 📖 Documentación Completa

- [README.md](README.md) - Documentación completa
- [docs/setup_teams.md](docs/setup_teams.md) - Configuración Teams
- [docs/deployment.md](docs/deployment.md) - Despliegue producción
- [docs/handlers.md](docs/handlers.md) - Desarrollo handlers

## 🆘 Soporte

¿Problemas? Revisa:
1. Los logs: `tail -f bot.log`
2. La configuración: `./scripts/start.sh check`
3. La conectividad: `curl -k https://localhost:3978/`
4. La documentación completa en `/docs/`

---

¡MSBot está listo para ser tu interfaz RAG para Microsoft Teams! 🚀