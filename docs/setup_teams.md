# Configuración de Microsoft Teams App - Guía Completa

Esta guía te llevará paso a paso para configurar MSBot en Microsoft Teams desde cero.

## 📋 Prerequisitos

- Cuenta Microsoft 365 con permisos de administrador
- Acceso a Azure Portal
- Bot desplegado y ejecutándose en servidor local
- Dominio público o túnel HTTPS (ngrok recomendado para desarrollo)

## 🔧 Paso 1: Registrar Aplicación en Azure AD

### 1.1 Crear Aplicación

1. **Acceder a Azure Portal**:
   - Ve a [https://portal.azure.com](https://portal.azure.com)
   - Inicia sesión con tu cuenta Microsoft 365

2. **Navegar a Azure Active Directory**:
   - En el menú lateral, selecciona "Azure Active Directory"
   - Si no lo ves, busca "Azure Active Directory" en la barra de búsqueda

3. **Registrar Nueva Aplicación**:
   - Haz clic en "App registrations" en el menú lateral
   - Haz clic en "New registration"

4. **Completar Formulario de Registro**:
   ```
   Name: MSBot
   Supported account types: Accounts in this organizational directory only (Single tenant)
   Redirect URI: (Deja vacío por ahora)
   ```

5. **Crear Aplicación**:
   - Haz clic en "Register"
   - **GUARDA** el "Application (client) ID" - lo necesitarás más tarde

### 1.2 Crear Secreto de Cliente

1. **Ir a Certificates & Secrets**:
   - En tu aplicación recién creada, haz clic en "Certificates & secrets"

2. **Crear Nuevo Secreto**:
   - Haz clic en "New client secret"
   - Descripción: "MSBot Client Secret"
   - Expires: 24 months (recomendado)
   - Haz clic en "Add"

3. **Guardar Secreto**:
   - **COPIA INMEDIATAMENTE** el valor del secreto
   - No podrás verlo de nuevo después de salir de la página
   - Guárdalo junto con el Application ID

### 1.3 Configurar Permisos API

1. **Ir a API Permissions**:
   - Haz clic en "API permissions"

2. **Agregar Permisos**:
   - Haz clic en "Add a permission"
   - Selecciona "Microsoft Graph"
   - Selecciona "Application permissions"
   - Busca y agrega estos permisos:
     - `User.Read.All`
     - `Directory.Read.All` (opcional, para información de usuario extendida)

3. **Conceder Consentimiento**:
   - Haz clic en "Grant admin consent for [Tu Organización]"
   - Confirma haciendo clic en "Yes"

## 🤖 Paso 2: Registrar Bot en Bot Framework

### 2.1 Acceder a Bot Framework Portal

1. **Ir a Bot Framework Portal**:
   - Ve a [https://dev.botframework.com](https://dev.botframework.com)
   - Inicia sesión con la misma cuenta Microsoft 365

2. **Crear Nuevo Bot**:
   - Haz clic en "Create a Bot"
   - Selecciona "Register an existing bot built using Bot Builder SDK"

### 2.2 Configurar Bot

1. **Información Básica**:
   ```
   Display name: MSBot
   Bot handle: msbot-[tu-organizacion] (debe ser único)
   Description: Bot modular para integración con sistemas RAG
   ```

2. **Configuración**:
   ```
   Microsoft App ID: [El Application ID del Paso 1.1]
   Microsoft App Password: [El secreto del Paso 1.2]
   ```

3. **Messaging Endpoint**:
   - Para desarrollo local con ngrok: `https://tu-url-ngrok.ngrok.io/api/messages`
   - Para producción: `https://tu-dominio.com:3978/api/messages`

4. **Crear Bot**:
   - Haz clic en "Register"

### 2.3 Configurar Canal de Teams

1. **Ir a Channels**:
   - En tu bot recién creado, haz clic en "Channels"

2. **Agregar Canal de Teams**:
   - Haz clic en el icono de Microsoft Teams
   - Haz clic en "Save" (no necesitas cambiar nada)
   - El canal se activará automáticamente

## 📱 Paso 3: Crear Teams App Package

### 3.1 Acceder a Teams Developer Portal

1. **Ir a Developer Portal**:
   - Ve a [https://dev.teams.microsoft.com](https://dev.teams.microsoft.com)
   - Inicia sesión con tu cuenta Microsoft 365

2. **Crear Nueva App**:
   - Haz clic en "Apps"
   - Haz clic en "New app"
   - Ingresa un nombre: "MSBot"

### 3.2 Configurar Información Básica

1. **Basic Information**:
   ```
   Full name: MSBot
   Short name: MSBot
   Application (client) ID: [Generar nuevo GUID o usar uno existente]
   Package Name: com.tuorganizacion.msbot
   Version: 1.0.0
   Short description: Bot para integración RAG
   Long description: Bot modular diseñado para servir como interfaz entre usuarios y sistemas RAG (Retrieval Augmented Generation)
   Developer name: Tu Organización
   Website: https://tu-sitio.com (opcional)
   Privacy policy: https://tu-sitio.com/privacy (opcional)
   Terms of use: https://tu-sitio.com/terms (opcional)
   ```

2. **Branding**:
   - Agrega iconos (opcional):
     - Color icon: 192x192 px
     - Outline icon: 32x32 px

### 3.3 Configurar Bot

1. **Ir a App Features**:
   - Haz clic en "App features"
   - Haz clic en "Bot"

2. **Configurar Bot**:
   ```
   Existing bot ID: [El Application ID de tu Azure AD App]
   Scope: Personal, Team, Group Chat
   ```

3. **Commands** (opcional):
   - Agregar comandos que tu bot puede manejar:
   ```
   Command: help
   Description: Muestra ayuda del bot
   
   Command: status
   Description: Muestra estado del bot
   ```

### 3.4 Configurar Permisos

1. **Single Sign-On** (opcional):
   - Si planeas usar SSO, configura aquí
   - Para MSBot básico, no es necesario

2. **Permissions**:
   - Device permissions: Ninguno necesario para funcionalidad básica

## 🚀 Paso 4: Configurar Variables de Entorno

Actualiza tu archivo `.env` con los valores obtenidos:

```env
# Microsoft Teams Bot Configuration
MICROSOFT_APP_ID=tu_application_id_de_azure_ad
MICROSOFT_APP_PASSWORD=tu_client_secret_de_azure_ad

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

## 🌐 Paso 5: Configurar Acceso Externo (Desarrollo Local)

### 5.1 Instalar ngrok

1. **Descargar ngrok**:
   - Ve a [https://ngrok.com/download](https://ngrok.com/download)
   - Descarga la versión para tu sistema operativo
   - Extrae y coloca el ejecutable en tu PATH

2. **Crear Cuenta** (opcional pero recomendado):
   - Registrate en [https://ngrok.com](https://ngrok.com)
   - Obtén tu authtoken
   - Ejecuta: `ngrok authtoken tu-authtoken`

### 5.2 Iniciar Túnel

```bash
# Iniciar ngrok apuntando al puerto del bot
ngrok http 3978

# Ngrok mostrará URLs como:
# Forwarding https://abc123def.ngrok.io -> http://localhost:3978
```

### 5.3 Actualizar Endpoints

1. **Bot Framework Portal**:
   - Ve a tu bot en [https://dev.botframework.com](https://dev.botframework.com)
   - Actualiza "Messaging endpoint" con: `https://tu-url-ngrok.ngrok.io/api/messages`

2. **Teams Developer Portal**:
   - Si configuraste webhooks adicionales, actualízalos también

## 📥 Paso 6: Instalar y Probar la App

### 6.1 Descargar App Package

1. **En Teams Developer Portal**:
   - Ve a tu app "MSBot"
   - Haz clic en "Publish" → "Download app package"
   - Se descargará un archivo .zip

### 6.2 Subir a Teams

#### Método 1: Upload Personal

1. **Abrir Microsoft Teams**:
   - Ve a la sección "Apps"
   - Haz clic en "Upload a custom app"
   - Selecciona "Upload for me or my teams"
   - Selecciona el archivo .zip descargado

#### Método 2: Admin Center (Para toda la organización)

1. **Teams Admin Center**:
   - Ve a [https://admin.teams.microsoft.com](https://admin.teams.microsoft.com)
   - Ve a "Teams apps" → "Manage apps"
   - Haz clic en "Upload new app"
   - Sube el archivo .zip
   - Configura políticas de uso según necesites

### 6.3 Probar el Bot

1. **Iniciar Conversación**:
   - En Teams, busca "MSBot"
   - Haz clic en el bot e inicia conversación
   - Envía un mensaje de prueba

2. **Verificar Funcionamiento**:
   - El bot debería responder con un echo del mensaje
   - Verifica los logs del servidor para confirmar recepción

## 🔍 Solución de Problemas

### Bot No Aparece en Teams

1. **Verificar App Package**:
   - Asegúrate que el .zip contiene manifest.json válido
   - Verifica permisos de subida de apps personalizadas

2. **Verificar Permisos**:
   - Admin debe permitir apps personalizadas
   - Usuario debe tener permisos para instalar apps

### Bot No Responde

1. **Verificar Endpoint**:
   - Confirma que la URL de messaging endpoint es correcta
   - Verifica que el servidor está ejecutándose

2. **Verificar Credenciales**:
   - App ID y Password deben coincidir exactamente
   - Verifica que no hay espacios extra o caracteres especiales

3. **Verificar Logs**:
   ```bash
   # Ver logs del bot
   tail -f logs/msbot.log
   
   # Ver logs de ngrok
   # Ve a http://localhost:4040 para interfaz web de ngrok
   ```

### Errores de Autenticación

1. **Verificar Token**:
   - El token de Teams debe ser validado correctamente
   - Verifica configuración de Bot Framework Adapter

2. **Verificar Permisos Azure AD**:
   - Confirma que los permisos fueron concedidos
   - Verifica que la aplicación está en el tenant correcto

## 📚 Recursos Adicionales

- [Microsoft Teams Bot Documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots)
- [Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams Developer Portal](https://dev.teams.microsoft.com)
- [Azure Bot Service](https://azure.microsoft.com/en-us/services/bot-service/)

## 🆘 Soporte

Si encuentras problemas:

1. Verifica cada paso de esta guía
2. Revisa los logs del bot y ngrok
3. Confirma que todas las URLs y credenciales son correctas
4. Consulta la documentación oficial de Microsoft Teams

---

Esta guía debería permitirte configurar MSBot completamente en Microsoft Teams. Una vez funcionando el modo echo, podrás proceder a integrar tus sistemas RAG personalizados.