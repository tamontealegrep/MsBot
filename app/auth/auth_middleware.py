"""
Authentication Middleware - Middleware de autenticación para MSBot
Intercepta mensajes y verifica permisos antes de procesarlos
"""

from typing import Optional, Callable, Any
from botbuilder.core import TurnContext

from app.auth.auth_manager import AuthManager, Permission
from app.utils.logger import setup_logger

class AuthMiddleware:
    """
    Middleware de autenticación que se ejecuta antes de procesar mensajes
    
    Funcionalidades:
    - Verificación automática de usuarios
    - Control de acceso por permisos
    - Mensajes de error personalizados
    - Logging de intentos de acceso
    """
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.logger = setup_logger(__name__)
        
        # Mensajes de error personalizados
        self.error_messages = {
            "unauthorized": """
🚫 **Acceso No Autorizado**

Lo siento, no tienes permisos para usar este bot.

Para obtener acceso, contacta a tu administrador con tu ID de usuario:
👤 **Tu ID:** `{user_id}`

---
📞 **Soporte:** Contacta al administrador del sistema
            """.strip(),
            
            "insufficient_permissions": """
⚠️ **Permisos Insuficientes**

No tienes los permisos necesarios para realizar esta acción.

👤 **Tu rol actual:** {role}
🔐 **Permiso requerido:** {permission}

---
📞 Para solicitar permisos adicionales, contacta a tu administrador
            """.strip(),
            
            "banned": """
🚫 **Acceso Denegado**

Tu cuenta ha sido suspendida del uso de este bot.

---
📞 Para más información, contacta al administrador del sistema
            """.strip()
        }
    
    async def process_message(self, turn_context: TurnContext, required_permission: Permission = None) -> tuple[bool, Optional[str]]:
        """
        Procesar mensaje y verificar autenticación/autorización
        
        Args:
            turn_context: Contexto del mensaje de Teams
            required_permission: Permiso requerido para la acción (opcional)
            
        Returns:
            Tuple (is_authorized, error_message)
            - is_authorized: True si el usuario está autorizado
            - error_message: Mensaje de error si no está autorizado (None si está autorizado)
        """
        
        try:
            # Extraer información del usuario
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name
            user_email = getattr(turn_context.activity.from_property, 'email', None)
            
            self.logger.info(f"Processing auth for user {user_id} ({user_name})")
            
            # Intentar autenticar usuario
            auth_user = self.auth_manager.authenticate_user(user_id, user_name, user_email)
            
            if not auth_user:
                # Usuario no autorizado
                error_msg = self.error_messages["unauthorized"].format(user_id=user_id)
                self.logger.warning(f"Unauthorized access attempt: {user_id} ({user_name})")
                return False, error_msg
            
            # Verificar si está baneado
            if auth_user.role.value == "banned":
                error_msg = self.error_messages["banned"]
                self.logger.warning(f"Banned user attempted access: {user_id}")
                return False, error_msg
            
            # Verificar permisos específicos si se requieren
            if required_permission and not auth_user.has_permission(required_permission):
                error_msg = self.error_messages["insufficient_permissions"].format(
                    role=auth_user.role.value,
                    permission=required_permission.value
                )
                self.logger.warning(f"Insufficient permissions for {user_id}: required {required_permission.value}")
                return False, error_msg
            
            # Usuario autorizado
            self.logger.info(f"User authorized: {user_id} ({auth_user.name}) with role {auth_user.role.value}")
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error in auth middleware: {e}")
            error_msg = "Error interno de autenticación. Contacta al administrador."
            return False, error_msg
    
    def get_user_info(self, turn_context: TurnContext) -> Optional[dict]:
        """
        Obtener información del usuario autenticado
        
        Args:
            turn_context: Contexto del mensaje
            
        Returns:
            Diccionario con información del usuario o None
        """
        
        try:
            user_id = turn_context.activity.from_property.id
            auth_user = self.auth_manager.get_authenticated_user(user_id)
            
            if auth_user:
                return auth_user.to_dict()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return None
    
    def create_auth_decorator(self, required_permission: Permission = None):
        """
        Crear decorador de autenticación para handlers
        
        Args:
            required_permission: Permiso requerido
            
        Returns:
            Decorador de función
        """
        
        def decorator(handler_func: Callable):
            async def wrapper(handler_self, message: str, turn_context: TurnContext, *args, **kwargs):
                # Verificar autenticación
                is_authorized, error_msg = await self.process_message(turn_context, required_permission)
                
                if not is_authorized:
                    return error_msg
                
                # Ejecutar handler original
                return await handler_func(handler_self, message, turn_context, *args, **kwargs)
            
            return wrapper
        return decorator

class AuthenticatedHandler:
    """
    Clase base para handlers que requieren autenticación
    Extiende la funcionalidad de BaseHandler con autenticación automática
    """
    
    def __init__(self, auth_middleware: AuthMiddleware, required_permission: Permission = None):
        self.auth_middleware = auth_middleware
        self.required_permission = required_permission
        self.logger = setup_logger(__name__)
    
    async def handle_with_auth(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """
        Manejar mensaje con verificación de autenticación
        
        Args:
            message: Mensaje del usuario
            turn_context: Contexto de Teams
            
        Returns:
            Respuesta del handler o mensaje de error
        """
        
        # Verificar autenticación
        is_authorized, error_msg = await self.auth_middleware.process_message(
            turn_context, 
            self.required_permission
        )
        
        if not is_authorized:
            return error_msg
        
        # Procesar mensaje
        return await self.process_authenticated_message(message, turn_context)
    
    async def process_authenticated_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """
        Procesar mensaje para usuario autenticado
        Debe ser implementado por subclases
        
        Args:
            message: Mensaje del usuario
            turn_context: Contexto de Teams
            
        Returns:
            Respuesta del handler
        """
        raise NotImplementedError("Subclasses must implement process_authenticated_message")
    
    def get_current_user(self, turn_context: TurnContext):
        """Obtener usuario actual autenticado"""
        return self.auth_middleware.get_user_info(turn_context)