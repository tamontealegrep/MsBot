# 🔐 Sistema de Autenticación MSBot

MSBot ahora incluye un sistema completo de autenticación y autorización que controla el acceso a las funcionalidades del bot.

## 🎯 Características del Sistema de Autenticación

### ✅ **Funcionalidades Implementadas:**
- **Control de Acceso por Usuario**: Solo usuarios autorizados pueden usar el bot
- **Sistema de Roles**: Admin, User, Guest con diferentes permisos
- **Comandos Administrativos**: Gestión de usuarios via Teams
- **Autenticación Transparente**: Verificación automática en cada mensaje
- **Configuración Persistente**: Base de datos de usuarios autorizada
- **Mensajes Personalizados**: Respuestas según rol de usuario

## 🎭 Roles y Permisos

### 👑 **Admin**
- ✅ Acceso completo a sistemas RAG
- ✅ Comandos administrativos (`/admin`)
- ✅ Gestión de usuarios
- ✅ Visualización de métricas
- ✅ Modo echo

### 👤 **User** 
- ✅ Acceso a sistemas RAG
- ✅ Visualización de métricas
- ✅ Modo echo
- ❌ Comandos administrativos

### 👥 **Guest**
- ✅ Modo echo únicamente
- ❌ Acceso a RAG
- ❌ Métricas
- ❌ Comandos admin

### 🚫 **Banned**
- ❌ Sin acceso al bot

## 🚀 Configuración Inicial

### 1. **Setup Automático (Recomendado)**

```bash
# Ejecutar configurador interactivo
python setup_auth.py

# Seguir las instrucciones para:
# - Configurar administrador principal
# - Agregar usuarios iniciales
# - Configurar roles y permisos
```

### 2. **Setup Manual**

```bash
# Editar .env con tu User ID de admin
nano .env

# Configurar:
DEFAULT_ADMIN_USER_ID=29:tu_user_id_de_teams
DEFAULT_ADMIN_EMAIL=tu_email@empresa.com
```

### 3. **Obtener tu User ID de Teams**

```bash
# Ver ayuda para obtener User ID
python setup_auth.py help
```

**Métodos para obtener User ID:**
1. **Desde Teams**: URL del perfil contiene el User ID
2. **Desde bot**: Mensaje inicial muestra el ID no autorizado
3. **Desde logs**: Revisar logs del servidor cuando alguien intenta acceder

## 💬 Comandos Administrativos

### 📋 **Comandos Disponibles**

```bash
/admin help          # Ayuda completa
/admin status        # Estado del sistema
/admin users         # Listar usuarios autorizados
/admin metrics       # Métricas detalladas
```

### 👥 **Gestión de Usuarios**

```bash
# Agregar usuario
/admin add 29:1abc123 "Juan Pérez" juan@empresa.com user

# Cambiar rol
/admin role 29:1abc123 admin

# Remover usuario
/admin remove 29:1abc123
```

### 📊 **Ejemplo de Respuesta de `/admin status`**

```
🤖 MSBot - Estado del Sistema

👨‍💼 Administrador: María García
📊 Estadísticas de Usuarios:
  • Total autorizados: 15
  • Sesiones activas: 8

🎭 Distribución por Roles:
  • Admin: 3
  • User: 10
  • Guest: 2

👥 Usuarios Activos:
  • Juan Pérez (user)
  • Ana López (admin)
  • Carlos Ruiz (user)
```

## 🔄 Flujo de Autenticación

### 📨 **Mensaje de Usuario No Autorizado**

```
🚫 Acceso No Autorizado

Lo siento, no tienes permisos para usar este bot.

Para obtener acceso, contacta a tu administrador con tu ID de usuario:
👤 Tu ID: 29:1abc123def456

📞 Soporte: Contacta al administrador del sistema
```

### ✅ **Mensaje de Usuario Autorizado (Echo)**

```
🤖 MSBot - Modo Echo Autenticado

👤 Usuario: Juan Pérez
🎭 Rol: User
💬 Mensaje #5: Hola bot

🔄 Respuesta Echo: Hola bot

🔐 Acceso RAG: Podrás usar sistemas RAG cuando estén configurados

---
✨ Sistema de autenticación activo - Usuario verificado
⏰ Procesado: 14:30:15
```

## 🛠️ Gestión de Usuarios

### ➕ **Agregar Usuarios**

```python
# Via comando admin
/admin add 29:1user123 "Usuario Nuevo" usuario@empresa.com user

# Via código (para integraciones)
auth_manager.add_authorized_user(
    user_id="29:1user123",
    name="Usuario Nuevo", 
    email="usuario@empresa.com",
    role=UserRole.USER,
    added_by="admin"
)
```

### 🔄 **Actualizar Roles**

```bash
# Promover a admin
/admin role 29:1user123 admin

# Degradar a guest  
/admin role 29:1user123 guest

# Banear usuario
/admin role 29:1user123 banned
```

### 📤 **Backup y Restauración**

```bash
# Exportar configuración
/admin export

# Los datos se guardan en auth_config.json
# Para restaurar, copia el archivo al nuevo servidor
```

## 📁 Archivos de Configuración

### **auth_config.json** - Base de datos de usuarios
```json
{
  "authorized_users": {
    "29:1admin123": {
      "name": "Administrador Principal",
      "email": "admin@empresa.com", 
      "role": "admin",
      "added_date": "2024-01-01T10:00:00",
      "added_by": "system"
    },
    "29:1user456": {
      "name": "Juan Pérez",
      "email": "juan@empresa.com",
      "role": "user", 
      "added_date": "2024-01-02T14:30:00",
      "added_by": "admin"
    }
  },
  "last_updated": "2024-01-02T14:30:00"
}
```

## 🔧 Integración con Handlers RAG

### **Handler con Autenticación**

```python
from app.bot.handlers.base_handler import RAGHandler
from app.auth.auth_manager import Permission
from app.auth.auth_middleware import AuthMiddleware

class MiRAGHandler(RAGHandler):
    def __init__(self, auth_middleware: AuthMiddleware):
        super().__init__("mi_rag", "Mi Sistema RAG")
        self.auth_middleware = auth_middleware
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> str:
        # Verificar permisos de RAG
        is_authorized, error_msg = await self.auth_middleware.process_message(
            turn_context, 
            Permission.USE_RAG
        )
        
        if not is_authorized:
            return error_msg
        
        # Procesar con RAG solo si está autorizado
        return await self.query_rag_system(message)
    
    async def query_rag_system(self, query: str) -> str:
        # Tu lógica RAG aquí
        return f"Respuesta RAG autorizada para: {query}"
```

## 📊 Métricas y Monitoreo

### **Estadísticas Disponibles**

```python
# Obtener stats de autenticación
stats = bot_handler.get_auth_stats()

# Limpiar sesiones inactivas
cleaned = bot_handler.cleanup_sessions(timeout_hours=24)
```

### **Logs de Autenticación**

```json
{
  "timestamp": "2024-01-02T14:30:00.000Z",
  "level": "INFO", 
  "logger": "app.auth.auth_middleware",
  "message": "User authorized: 29:1user123 (Juan Pérez) with role user",
  "user_id": "29:1user123",
  "user_name": "Juan Pérez",
  "role": "user",
  "component": "auth_system"
}
```

## 🚨 Solución de Problemas

### **Usuario No Puede Acceder**

1. **Verificar que está autorizado**:
   ```bash
   /admin users
   ```

2. **Verificar configuración**:
   ```bash
   # Revisar auth_config.json
   cat auth_config.json
   ```

3. **Agregar usuario**:
   ```bash
   /admin add [user_id] "Nombre" email@empresa.com user
   ```

### **Admin No Puede Usar Comandos**

1. **Verificar rol admin**:
   ```bash
   /admin users
   ```

2. **Promover a admin**:
   ```bash
   /admin role [user_id] admin
   ```

### **Reset Completo de Autenticación**

```bash
# Eliminar configuración existente
rm auth_config.json

# Reconfigurar desde cero
python setup_auth.py
```

## 🎯 Próximos Pasos

1. **Configurar usuarios autorizados** usando `python setup_auth.py`
2. **Probar autenticación** enviando mensajes al bot
3. **Configurar admins** para gestión remota
4. **Integrar con sistemas RAG** usando los patrones de autenticación
5. **Monitorear uso** con `/admin metrics`

---

🔐 **El sistema de autenticación está completamente integrado y listo para uso en producción.**