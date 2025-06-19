# MSBot - Microsoft Teams RAG Interface Bot

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Microsoft Teams](https://img.shields.io/badge/Microsoft%20Teams-Bot-purple.svg)

## 📋 Descripción

**MSBot** es un bot modular para Microsoft Teams diseñado específicamente para servir como interfaz entre usuarios y sistemas RAG (Retrieval Augmented Generation). El bot está diseñado para ejecutarse en servidores locales privados, garantizando la confidencialidad y control total de los datos.

### 🎯 Características Principales

- **🔒 Ejecución Local**: Diseñado para ejecutarse en servidores privados (no requiere Azure)
- **🧩 Arquitectura Modular**: Sistema de handlers intercambiables para diferentes sistemas RAG
- **📝 Modo Echo**: Funcionalidad inicial que repite mensajes para entender el flujo
- **🔐 HTTPS Nativo**: Soporte completo para SSL/TLS
- **📊 Logging Estructurado**: Sistema de logs JSON para monitoreo avanzado
- **🚀 FastAPI**: API moderna y rápida con documentación automática
- **🔧 Configuración Flexible**: Variables de entorno y configuración centralizada

## 🏗️ Arquitectura

```
MSBot/
├── app/
│   ├── main.py                    # Servidor FastAPI principal
│   ├── bot/
│   │   ├── bot_handler.py         # Lógica principal del bot
│   │   └── handlers/              # Sistema modular de handlers
│   │       ├── base_handler.py    # Clase base para handlers
│   │       ├── echo_handler.py    # Handler de echo (ejemplo)
│   │       └── handler_registry.py # Registro de handlers
│   ├── config/
│   │   └── settings.py            # Configuración centralizada
│   └── utils/
│       └── logger.py              # Sistema de logging
├── docs/                          # Documentación
├── certs/                         # Certificados SSL (generados)
├── requirements.txt               # Dependencias Python
└── .env                          # Variables de entorno
```

## 🚀 Instalación y Configuración

### Prerequisitos

- Python 3.8 o superior
- OpenSSL (para certificados HTTPS)
- Cuenta Microsoft 365 con permisos para crear aplicaciones

### 1. Clonar y Configurar el Proyecto

```bash
# Clonar el repositorio
git clone <repository-url>
cd msbot

# Instalar dependencias
pip install -r requirements.txt

# Generar certificados SSL para HTTPS local
python setup_ssl.py
```

### 2. Configurar Variables de Entorno

Edita el archivo `.env` con tu configuración:

```env
# Microsoft Teams Bot Configuration
MICROSOFT_APP_ID=tu_app_id_aqui
MICROSOFT_APP_PASSWORD=tu_app_password_aqui

# Server Configuration
HOST=0.0.0.0
PORT=3978
HTTPS_ENABLED=true
SSL_CERT_PATH=./certs/cert.pem
SSL_KEY_PATH=./certs/key.pem

# Environment
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 3. Registrar la Aplicación en Microsoft Teams

Ver la guía detallada en [`docs/setup_teams.md`](docs/setup_teams.md)

## 🏃‍♂️ Ejecución

### Desarrollo Local

```bash
# Ejecutar con HTTPS (recomendado)
python main.py

# El bot estará disponible en:
# https://localhost:3978
```

### Producción Local

```bash
# Configurar environment
export ENVIRONMENT=production

# Ejecutar
python main.py
```

### Usando Supervisor (Recomendado para Producción)

```bash
# Instalar supervisor
sudo apt-get install supervisor  # Ubuntu/Debian
# o
brew install supervisor  # macOS

# Copiar configuración
sudo cp configs/msbot.conf /etc/supervisor/conf.d/

# Iniciar
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start msbot
```

## 🔧 Configuración de Microsoft Teams

### 1. Registrar Aplicación en Azure AD

1. Ve a [Azure Portal](https://portal.azure.com)
2. Navega a "Azure Active Directory" > "App registrations"
3. Haz clic en "New registration"
4. Completa:
   - **Name**: MSBot
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Deja vacío por ahora

### 2. Configurar Credenciales

1. En tu aplicación, ve a "Certificates & secrets"
2. Haz clic en "New client secret"
3. Copia el **Application (client) ID** y el **Client secret**
4. Actualiza el archivo `.env` con estos valores

### 3. Crear Bot en Bot Framework

1. Ve a [Bot Framework Portal](https://dev.botframework.com)
2. Haz clic en "Create a Bot"
3. Selecciona "Register an existing bot built using Bot Builder SDK"
4. Completa:
   - **Bot name**: MSBot
   - **Bot handle**: msbot-tuorganizacion
   - **Microsoft App ID**: El ID de tu aplicación Azure AD
   - **Messaging endpoint**: `https://tu-dominio:3978/api/messages`

### 4. Configurar Canal de Teams

1. En Bot Framework Portal, ve a tu bot
2. Haz clic en "Channels"
3. Haz clic en el icono de Microsoft Teams
4. Configura y guarda

### 5. Crear Teams App Package

1. Ve a [Teams Developer Portal](https://dev.teams.microsoft.com)
2. Crea una nueva aplicación
3. Configura:
   - **App ID**: Genera un nuevo GUID
   - **Bot ID**: El App ID de tu aplicación Azure AD
   - **Messaging endpoint**: `https://tu-dominio:3978/api/messages`

## 🧩 Sistema Modular de Handlers

### Estructura de Handlers

MSBot utiliza un sistema modular de handlers que permite agregar fácilmente nuevas funcionalidades:

```python
from app.bot.handlers.base_handler import RAGHandler

class MiRAGHandler(RAGHandler):
    def __init__(self):
        super().__init__(
            name="mi_rag",
            description="Mi sistema RAG personalizado"
        )
    
    async def query_rag_system(self, query: str, context=None) -> str:
        # Implementar lógica RAG aquí
        return f"Respuesta RAG para: {query}"
    
    def can_handle(self, message: str, context=None) -> bool:
        # Lógica para determinar si este handler puede procesar el mensaje
        return "rag" in message.lower()

# Registrar el handler
bot_handler.add_handler("mi_rag", MiRAGHandler())
```

### Handler Actual: Echo

El handler actual (`EchoHandler`) demuestra el flujo completo:

1. **Captura** el mensaje del usuario
2. **Procesa** el mensaje (limpieza, normalización)
3. **Genera** una respuesta (actualmente echo)
4. **Envía** la respuesta de vuelta a Teams

### Agregar Nuevos Handlers RAG

Para agregar un nuevo sistema RAG:

1. Crea una nueva clase heredando de `RAGHandler`
2. Implementa `query_rag_system()` con tu lógica RAG
3. Implementa `can_handle()` para routing inteligente
4. Registra el handler en el sistema

Ejemplo para OpenAI RAG:

```python
class OpenAIRAGHandler(RAGHandler):
    def __init__(self, api_key: str):
        super().__init__(
            name="openai_rag",
            description="Sistema RAG con OpenAI GPT"
        )
        self.api_key = api_key
    
    async def query_rag_system(self, query: str, context=None) -> str:
        # Implementar llamada a OpenAI con contexto RAG
        # 1. Buscar documentos relevantes
        # 2. Construir prompt con contexto
        # 3. Llamar a OpenAI API
        # 4. Retornar respuesta
        pass
```

## 📊 Monitoreo y Logs

### Logs Estructurados

MSBot genera logs en formato JSON para facilitar el análisis:

```json
{
  "timestamp": "2024-03-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.bot.bot_handler",
  "message": "Processing message from user",
  "user_id": "29:1AbCdEf...",
  "activity_type": "message",
  "handler_name": "echo",
  "execution_time_ms": 150.5
}
```

### Endpoints de Monitoreo

- `GET /`: Health check básico
- `GET /api/status`: Estado del bot y handlers registrados
- `GET /docs`: Documentación API (solo desarrollo)

## 🔒 Seguridad

### HTTPS Local

MSBot incluye soporte completo para HTTPS local:

```bash
# Generar certificados auto-firmados
python setup_ssl.py

# Los certificados se guardan en ./certs/
```

### Variables de Entorno

Todas las credenciales sensibles se manejan via variables de entorno:

- `MICROSOFT_APP_ID`: ID de la aplicación Teams
- `MICROSOFT_APP_PASSWORD`: Secreto de la aplicación
- Nunca hardcodear credenciales en el código

### Firewall y Red

Para producción, configurar:

1. Firewall para permitir solo puerto 3978
2. Certificados SSL válidos (no auto-firmados)
3. Dominio público o túnel seguro para webhook

## 🐛 Solución de Problemas

### Bot No Responde

1. Verificar logs del servidor
2. Comprobar configuración de webhook en Teams
3. Validar credenciales en `.env`
4. Verificar conectividad HTTPS

### Errores de Certificado

```bash
# Regenerar certificados
rm -rf certs/
python setup_ssl.py
```

### Logs de Debug

```bash
# Cambiar nivel de log
export LOG_LEVEL=DEBUG
python main.py
```

## 🚀 Despliegue en Producción

### Requisitos

- Servidor Linux con Python 3.8+
- Dominio público con certificado SSL válido
- Firewall configurado
- Supervisor o systemd para gestión de procesos

### Pasos

1. **Configurar servidor**:
   ```bash
   # Instalar dependencias del sistema
   sudo apt-get update
   sudo apt-get install python3 python3-pip supervisor nginx
   
   # Clonar código
   git clone <repo> /opt/msbot
   cd /opt/msbot
   
   # Instalar dependencias Python
   pip3 install -r requirements.txt
   ```

2. **Configurar certificados SSL**:
   ```bash
   # Usar Let's Encrypt para certificados válidos
   sudo apt-get install certbot
   sudo certbot certonly --standalone -d tu-dominio.com
   
   # Actualizar rutas en .env
   SSL_CERT_PATH=/etc/letsencrypt/live/tu-dominio.com/fullchain.pem
   SSL_KEY_PATH=/etc/letsencrypt/live/tu-dominio.com/privkey.pem
   ```

3. **Configurar Supervisor**:
   ```bash
   # Copiar configuración
   sudo cp configs/msbot.conf /etc/supervisor/conf.d/
   
   # Actualizar rutas en la configuración
   sudo vim /etc/supervisor/conf.d/msbot.conf
   
   # Iniciar servicio
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start msbot
   ```

4. **Actualizar configuración Teams**:
   - Cambiar endpoint a `https://tu-dominio.com:3978/api/messages`
   - Verificar que el bot responde

## 🤝 Contribución

### Agregar Nuevos Handlers

1. Crea tu handler heredando de `BaseHandler` o `RAGHandler`
2. Implementa los métodos requeridos
3. Agrega tests en `tests/handlers/`
4. Documenta tu handler en `docs/handlers/`

### Reportar Issues

1. Verifica logs del sistema
2. Reproduce el error
3. Incluye configuración (sin credenciales)
4. Abre issue con detalles completos

## 📚 Documentación Adicional

- [Configuración de Teams App](docs/setup_teams.md)
- [Guía de Despliegue](docs/deployment.md)
- [Desarrollo de Handlers](docs/handlers.md)
- [API Reference](docs/api.md)

## 📞 Soporte

Para soporte técnico:
1. Revisar documentación
2. Consultar logs del sistema
3. Verificar configuración
4. Contactar al equipo de desarrollo

---

**MSBot v1.0** - Bot modular para Microsoft Teams con integración RAG