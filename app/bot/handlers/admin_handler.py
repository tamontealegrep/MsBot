"""
Admin Handler - Comandos administrativos para MSBot
Permite gestionar usuarios, permisos y configuración del bot
"""

import json
from typing import Optional, Dict, Any
from botbuilder.core import TurnContext

from app.bot.handlers.base_handler import BaseHandler
from app.auth.auth_manager import AuthManager, UserRole, Permission
from app.auth.auth_middleware import AuthMiddleware
from app.utils.logger import setup_logger

class AdminHandler(BaseHandler):
    """
    Handler para comandos administrativos
    
    Comandos disponibles:
    - /admin status - Estado del sistema
    - /admin users - Listar usuarios
    - /admin add <user_id> <name> <email> <role> - Agregar usuario
    - /admin remove <user_id> - Remover usuario
    - /admin role <user_id> <new_role> - Cambiar rol
    - /admin metrics - Métricas de uso
    - /admin export - Exportar configuración
    """
    
    def __init__(self, auth_manager: AuthManager, auth_middleware: AuthMiddleware):
        super().__init__(
            name="admin",
            description="Comandos administrativos para gestión de usuarios y sistema"
        )
        self.auth_manager = auth_manager
        self.auth_middleware = auth_middleware
        self.logger = setup_logger(__name__)
        
        # Mapeo de comandos
        self.commands = {
            "status": self._cmd_status,
            "users": self._cmd_users,
            "add": self._cmd_add_user,
            "remove": self._cmd_remove_user,
            "role": self._cmd_change_role,
            "metrics": self._cmd_metrics,
            "export": self._cmd_export,
            "help": self._cmd_help
        }
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """Procesar comandos administrativos"""
        
        if not self.enabled:
            return None
        
        # Verificar autenticación y permisos de admin
        is_authorized, error_msg = await self.auth_middleware.process_message(
            turn_context, 
            Permission.ADMIN_COMMANDS
        )
        
        if not is_authorized:
            return error_msg
        
        # Parsear comando
        parts = message.strip().split()
        if len(parts) < 2 or parts[0] != "/admin":
            return None
        
        command = parts[1].lower()
        args = parts[2:] if len(parts) > 2 else []
        
        # Ejecutar comando
        if command in self.commands:
            try:
                admin_user = self.auth_middleware.get_user_info(turn_context)
                admin_name = admin_user["name"] if admin_user else "Admin"
                
                return await self.commands[command](args, turn_context, admin_name)
            except Exception as e:
                self.logger.error(f"Error executing admin command {command}: {e}")
                return f"❌ Error ejecutando comando: {str(e)}"
        else:
            return self._format_unknown_command(command)
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Verificar si puede manejar comandos admin"""
        return message.strip().startswith("/admin")
    
    async def _cmd_status(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin status"""
        
        stats = self.auth_manager.get_user_stats()
        
        response = f"""
🤖 **MSBot - Estado del Sistema**

👨‍💼 **Administrador:** {admin_name}
📊 **Estadísticas de Usuarios:**
  • Total autorizados: {stats['total_authorized_users']}
  • Sesiones activas: {stats['active_sessions']}

🎭 **Distribución por Roles:**
"""
        
        for role, count in stats['role_distribution'].items():
            response += f"  • {role.title()}: {count}\n"
        
        if stats['active_sessions'] > 0:
            response += f"\n👥 **Usuarios Activos:**\n"
            for user in stats['session_users']:
                response += f"  • {user['name']} ({user['role']})\n"
        
        response += f"\n---\n⏰ **Timestamp:** {turn_context.activity.timestamp}"
        
        return response.strip()
    
    async def _cmd_users(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin users"""
        
        if not self.auth_manager.authorized_users:
            return "📋 No hay usuarios autorizados configurados."
        
        response = f"👥 **Usuarios Autorizados ({len(self.auth_manager.authorized_users)}):**\n\n"
        
        for user_id, user_data in self.auth_manager.authorized_users.items():
            status = "🟢 Activo" if user_id in self.auth_manager.authenticated_users else "⚪ Inactivo"
            
            response += f"**{user_data['name']}**\n"
            response += f"  • ID: `{user_id}`\n"
            response += f"  • Email: {user_data['email']}\n"
            response += f"  • Rol: {user_data['role']}\n"
            response += f"  • Estado: {status}\n"
            response += f"  • Agregado: {user_data.get('added_date', 'N/A')}\n\n"
        
        return response.strip()
    
    async def _cmd_add_user(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin add <user_id> <name> <email> <role>"""
        
        if len(args) < 4:
            return """
❌ **Uso incorrecto**

**Formato:** `/admin add <user_id> <name> <email> <role>`

**Roles disponibles:** admin, user, guest

**Ejemplo:** `/admin add 29:1abc123 "Juan Pérez" juan.perez@empresa.com user`
            """.strip()
        
        user_id = args[0]
        name = args[1].strip('"')
        email = args[2]
        role_str = args[3].lower()
        
        # Validar rol
        try:
            role = UserRole(role_str)
        except ValueError:
            return f"❌ **Rol inválido:** `{role_str}`\n\n**Roles válidos:** admin, user, guest"
        
        # Verificar si ya existe
        if user_id in self.auth_manager.authorized_users:
            return f"⚠️ **Usuario ya existe:** {name} (`{user_id}`)"
        
        # Agregar usuario
        success = self.auth_manager.add_authorized_user(
            user_id=user_id,
            name=name,
            email=email,
            role=role,
            added_by=admin_name
        )
        
        if success:
            return f"""
✅ **Usuario agregado exitosamente**

👤 **Nombre:** {name}
🆔 **ID:** `{user_id}`
📧 **Email:** {email}
🎭 **Rol:** {role.value}
👨‍💼 **Agregado por:** {admin_name}
            """.strip()
        else:
            return f"❌ **Error agregando usuario:** {name}"
    
    async def _cmd_remove_user(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin remove <user_id>"""
        
        if len(args) < 1:
            return "❌ **Uso:** `/admin remove <user_id>`"
        
        user_id = args[0]
        
        # Verificar que existe
        if user_id not in self.auth_manager.authorized_users:
            return f"❌ **Usuario no encontrado:** `{user_id}`"
        
        # Obtener nombre antes de remover
        user_name = self.auth_manager.authorized_users[user_id].get("name", "Unknown")
        
        # Prevenir auto-eliminación del admin actual
        current_admin_id = turn_context.activity.from_property.id
        if user_id == current_admin_id:
            return "❌ **No puedes remover tu propia cuenta de administrador**"
        
        # Remover usuario
        success = self.auth_manager.remove_authorized_user(user_id, admin_name)
        
        if success:
            return f"""
✅ **Usuario removido exitosamente**

👤 **Nombre:** {user_name}
🆔 **ID:** `{user_id}`
👨‍💼 **Removido por:** {admin_name}
            """.strip()
        else:
            return f"❌ **Error removiendo usuario:** {user_name}"
    
    async def _cmd_change_role(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin role <user_id> <new_role>"""
        
        if len(args) < 2:
            return """
❌ **Uso:** `/admin role <user_id> <new_role>`

**Roles disponibles:** admin, user, guest, banned
            """.strip()
        
        user_id = args[0]
        role_str = args[1].lower()
        
        # Validar rol
        try:
            new_role = UserRole(role_str)
        except ValueError:
            return f"❌ **Rol inválido:** `{role_str}`\n\n**Roles válidos:** admin, user, guest, banned"
        
        # Verificar que el usuario existe
        if user_id not in self.auth_manager.authorized_users:
            return f"❌ **Usuario no encontrado:** `{user_id}`"
        
        # Obtener información del usuario
        user_data = self.auth_manager.authorized_users[user_id]
        user_name = user_data.get("name", "Unknown")
        old_role = user_data.get("role", "unknown")
        
        # Actualizar rol
        success = self.auth_manager.update_user_role(user_id, new_role, admin_name)
        
        if success:
            return f"""
✅ **Rol actualizado exitosamente**

👤 **Usuario:** {user_name}
🆔 **ID:** `{user_id}`
🎭 **Rol anterior:** {old_role}
🎭 **Rol nuevo:** {new_role.value}
👨‍💼 **Actualizado por:** {admin_name}
            """.strip()
        else:
            return f"❌ **Error actualizando rol para:** {user_name}"
    
    async def _cmd_metrics(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin metrics"""
        
        stats = self.auth_manager.get_user_stats()
        
        response = f"""
📊 **Métricas Detalladas del Sistema**

👥 **Usuarios:**
  • Total autorizados: {stats['total_authorized_users']}
  • Sesiones activas: {stats['active_sessions']}
  • Tasa de actividad: {(stats['active_sessions'] / stats['total_authorized_users'] * 100):.1f}% si stats['total_authorized_users'] > 0 else 0

🎭 **Por Roles:**
"""
        
        for role, count in stats['role_distribution'].items():
            percentage = (count / stats['total_authorized_users'] * 100) if stats['total_authorized_users'] > 0 else 0
            response += f"  • {role.title()}: {count} ({percentage:.1f}%)\n"
        
        if stats['session_users']:
            response += f"\n📈 **Actividad de Sesiones:**\n"
            for user in stats['session_users']:
                response += f"  • {user['name']}: {user['session_count']} interacciones\n"
        
        response += f"\n---\n📋 **Consultado por:** {admin_name}"
        
        return response.strip()
    
    async def _cmd_export(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin export"""
        
        try:
            export_data = self.auth_manager.export_users()
            
            # Crear resumen del export
            response = f"""
📤 **Exportación de Configuración**

📊 **Datos exportados:**
  • Total usuarios: {export_data['total_users']}
  • Fecha de exportación: {export_data['export_date']}

📋 **Configuración guardada en:** `auth_config.json`

⚠️ **Nota:** Para importar esta configuración en otro servidor, 
copia el archivo `auth_config.json` al nuevo sistema.

---
👨‍💼 **Exportado por:** {admin_name}
            """.strip()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in export command: {e}")
            return f"❌ **Error en exportación:** {str(e)}"
    
    async def _cmd_help(self, args, turn_context: TurnContext, admin_name: str) -> str:
        """Comando: /admin help"""
        
        return """
🤖 **MSBot - Comandos de Administración**

📋 **Comandos disponibles:**

`/admin status` - Estado del sistema y usuarios
`/admin users` - Listar todos los usuarios autorizados
`/admin add <user_id> <name> <email> <role>` - Agregar usuario
`/admin remove <user_id>` - Remover usuario
`/admin role <user_id> <new_role>` - Cambiar rol de usuario
`/admin metrics` - Métricas detalladas del sistema
`/admin export` - Exportar configuración de usuarios
`/admin help` - Mostrar esta ayuda

🎭 **Roles disponibles:**
• `admin` - Acceso completo (RAG + comandos admin)
• `user` - Acceso a RAG y métricas
• `guest` - Solo modo echo
• `banned` - Sin acceso

📝 **Ejemplos:**
`/admin add 29:1abc123 "Juan Pérez" juan@empresa.com user`
`/admin role 29:1abc123 admin`
`/admin remove 29:1abc123`

---
⚠️ **Nota:** Solo usuarios con rol `admin` pueden usar estos comandos.
        """.strip()
    
    def _format_unknown_command(self, command: str) -> str:
        """Formatear mensaje para comando desconocido"""
        
        return f"""
❌ **Comando desconocido:** `/admin {command}`

💡 **¿Necesitas ayuda?** Usa `/admin help` para ver todos los comandos disponibles.

📋 **Comandos principales:**
• `/admin status` - Estado del sistema
• `/admin users` - Listar usuarios  
• `/admin help` - Ayuda completa
        """.strip()