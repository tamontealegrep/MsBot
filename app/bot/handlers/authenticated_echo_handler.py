"""
Authenticated Echo Handler - Versión del Echo Handler con autenticación
Reemplaza al EchoHandler original agregando control de acceso
"""

from typing import Optional, Dict, Any
from botbuilder.core import TurnContext

from app.bot.handlers.base_handler import BaseHandler
from app.auth.auth_manager import Permission
from app.auth.auth_middleware import AuthMiddleware
from app.utils.logger import setup_logger

class AuthenticatedEchoHandler(BaseHandler):
    """
    Echo Handler con autenticación integrada
    
    Funcionalidades:
    - Verificación automática de permisos
    - Respuestas personalizadas por rol de usuario
    - Logging de actividad de usuarios
    - Información de usuario en respuestas
    """
    
    def __init__(self, auth_middleware: AuthMiddleware):
        super().__init__(
            name="auth_echo",
            description="Handler echo con autenticación y control de acceso"
        )
        self.auth_middleware = auth_middleware
        self.logger = setup_logger(__name__)
        self.message_count = 0
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """
        Manejar mensaje con autenticación
        
        Args:
            message: Mensaje del usuario
            turn_context: Contexto de Teams
            
        Returns:
            Respuesta personalizada con información de usuario
        """
        
        if not self.enabled:
            return None
        
        # Verificar autenticación con permiso de echo
        is_authorized, error_msg = await self.auth_middleware.process_message(
            turn_context, 
            Permission.USE_ECHO
        )
        
        if not is_authorized:
            return error_msg
        
        # Procesar mensaje para usuario autenticado
        return await self._process_authenticated_message(message, turn_context)
    
    async def _process_authenticated_message(self, message: str, turn_context: TurnContext) -> str:
        """Procesar mensaje para usuario autenticado"""
        
        try:
            # Incrementar contador
            self.message_count += 1
            
            # Obtener información del usuario autenticado
            user_info = self.auth_middleware.get_user_info(turn_context)
            
            if not user_info:
                return "❌ Error obteniendo información de usuario."
            
            # Log de actividad
            self.logger.info(
                f"Authenticated echo - User: {user_info['name']} ({user_info['role']}) "
                f"Message #{self.message_count}: {message[:50]}..."
            )
            
            # Pre-procesar mensaje
            processed_message = await self.pre_process(message, turn_context)
            
            # Crear respuesta personalizada
            echo_response = self._create_authenticated_response(
                processed_message, 
                user_info, 
                self.message_count
            )
            
            # Post-procesar respuesta
            final_response = await self.post_process(echo_response, message, turn_context)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error in authenticated echo handler: {e}")
            return "❌ Error procesando tu mensaje. Por favor intenta de nuevo."
    
    def _create_authenticated_response(self, message: str, user_info: Dict, count: int) -> str:
        """
        Crear respuesta echo personalizada con información de usuario
        
        Args:
            message: Mensaje procesado
            user_info: Información del usuario autenticado
            count: Número de mensaje
            
        Returns:
            Respuesta formateada
        """
        
        # Obtener emoji según el rol
        role_emojis = {
            "admin": "👑",
            "user": "👤", 
            "guest": "👥"
        }
        
        role_emoji = role_emojis.get(user_info.get("role", "guest"), "👤")
        
        # Crear respuesta base
        response = f"🤖 **MSBot - Modo Echo Autenticado**\n\n"
        
        # Información del usuario
        response += f"{role_emoji} **Usuario:** {user_info.get('name', 'Usuario')}\n"
        response += f"🎭 **Rol:** {user_info.get('role', 'unknown').title()}\n"
        response += f"💬 **Mensaje #{count}:** {message}\n\n"
        
        # Respuesta echo
        response += f"🔄 **Respuesta Echo:** {message}\n\n"
        
        # Información adicional según el rol
        if user_info.get("role") == "admin":
            response += "👑 **Privilegios de Admin:** Puedes usar comandos `/admin`\n"
        elif user_info.get("role") == "user":
            response += "🔐 **Acceso RAG:** Podrás usar sistemas RAG cuando estén configurados\n"
        elif user_info.get("role") == "guest":
            response += "ℹ️ **Acceso Limitado:** Solo puedes usar el modo echo\n"
        
        response += "\n---\n"
        response += "✨ *Sistema de autenticación activo - Usuario verificado*"
        
        return response
    
    async def pre_process(self, message: str, turn_context: TurnContext) -> str:
        """Pre-procesar mensaje"""
        # Limpieza básica
        cleaned = message.strip()
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    async def post_process(self, response: str, original_message: str, turn_context: TurnContext) -> str:
        """Post-procesar respuesta"""
        from datetime import datetime
        
        # Agregar timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        final_response = response + f"\n\n⏰ **Procesado:** {timestamp}"
        
        return final_response
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Determinar si puede manejar el mensaje
        Para el echo autenticado, puede manejar cualquier mensaje que no sea comando admin
        """
        # No manejar comandos admin
        if message.strip().startswith("/admin"):
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del handler"""
        return {
            "name": self.name,
            "messages_processed": self.message_count,
            "enabled": self.enabled,
            "description": self.description,
            "requires_auth": True
        }
    
    def reset_stats(self):
        """Resetear estadísticas"""
        self.message_count = 0
        self.logger.info("Authenticated echo handler stats reset")