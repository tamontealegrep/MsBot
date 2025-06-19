"""
MSBot Handler - Main Bot Logic with Authentication
Handles Microsoft Teams activities and routes them to appropriate handlers
Now includes authentication and authorization
"""

import json
import time
from typing import Dict, Any, List, Optional
from aiohttp import web
from botbuilder.core import (
    TurnContext, 
    ActivityHandler, 
    MessageFactory,
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings
)
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount

from app.config.settings import get_settings
from app.utils.logger import setup_logger, log_teams_activity, log_handler_execution
from app.bot.handlers.handler_registry import HandlerRegistry
from app.bot.handlers.authenticated_echo_handler import AuthenticatedEchoHandler
from app.bot.handlers.admin_handler import AdminHandler
from app.auth.auth_manager import AuthManager
from app.auth.auth_middleware import AuthMiddleware

class MSBotHandler(ActivityHandler):
    """
    Main bot handler that processes Teams activities with authentication
    Routes messages to appropriate modular handlers after auth verification
    """
    
    def __init__(self, auth_manager: AuthManager = None, auth_middleware: AuthMiddleware = None):
        super().__init__()
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Initialize authentication components
        self.auth_manager = auth_manager or AuthManager()
        self.auth_middleware = auth_middleware or AuthMiddleware(self.auth_manager)
        
        # Initialize Bot Framework Adapter
        self.adapter = self._create_adapter()
        
        # Initialize handler registry
        self.handler_registry = HandlerRegistry()
        
        # Register default handlers with authentication
        self._register_default_handlers()
        
        self.logger.info("MSBot initialized successfully with authentication")
    
    def _create_adapter(self) -> BotFrameworkAdapter:
        """Create and configure Bot Framework Adapter"""
        
        # Bot Framework Adapter Settings
        settings = BotFrameworkAdapterSettings(
            app_id=self.settings.microsoft_app_id,
            app_password=self.settings.microsoft_app_password
        )
        
        # Create adapter
        adapter = BotFrameworkAdapter(settings)
        
        # Error handler
        async def on_error(context: TurnContext, error: Exception):
            self.logger.error(f"Bot error: {str(error)}")
            await context.send_activity(
                MessageFactory.text("Lo siento, ocurrió un error procesando tu mensaje.")
            )
        
        adapter.on_turn_error = on_error
        
        return adapter
    
    def _register_default_handlers(self):
        """Register default message handlers with authentication"""
        
        # Register Authenticated Echo Handler as default
        auth_echo_handler = AuthenticatedEchoHandler(self.auth_middleware)
        self.handler_registry.register_handler("auth_echo", auth_echo_handler, is_default=True)
        
        # Register Admin Handler
        admin_handler = AdminHandler(self.auth_manager, self.auth_middleware)
        self.handler_registry.register_handler("admin", admin_handler)
        
        self.logger.info("Authentication-enabled handlers registered")
    
    async def process_activity(self, body: bytes, auth_header: str) -> Dict[str, Any]:
        """
        Process incoming activity from Teams
        
        Args:
            body: Request body from Teams
            auth_header: Authorization header
            
        Returns:
            Response dictionary with status, body, and headers
        """
        
        try:
            # Parse activity from request body
            activity_data = json.loads(body.decode('utf-8'))
            activity = Activity().deserialize(activity_data)
            
            log_teams_activity(
                self.logger, 
                activity.type, 
                user_id=activity.from_property.id if activity.from_property else None,
                message=activity.text if hasattr(activity, 'text') else None
            )
            
            # Create response
            response = web.Response(status=200)
            
            # Process activity through adapter
            await self.adapter.process_activity(activity, auth_header, self.on_message_activity)
            
            return {
                "status": 200,
                "body": "",
                "headers": {"Content-Type": "application/json"}
            }
            
        except Exception as e:
            self.logger.error(f"Error processing activity: {str(e)}")
            return {
                "status": 500,
                "body": json.dumps({"error": "Internal server error"}),
                "headers": {"Content-Type": "application/json"}
            }
    
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle message activities from Teams with authentication
        Routes messages to appropriate handlers after auth check
        """
        
        start_time = time.time()
        
        try:
            user_message = turn_context.activity.text
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name
            
            self.logger.info(f"Processing message from user {user_id} ({user_name}): {user_message}")
            
            # Get appropriate handler based on message content
            handler = self._route_message_to_handler(user_message, turn_context)
            
            if handler:
                # Process message through handler (auth is handled by each handler)
                response = await handler.handle_message(user_message, turn_context)
                
                # Send response back to Teams
                if response:
                    await turn_context.send_activity(MessageFactory.text(response))
                
                # Log successful execution
                execution_time = time.time() - start_time
                log_handler_execution(
                    self.logger, 
                    handler.__class__.__name__, 
                    execution_time, 
                    True
                )
            else:
                # No handler available
                await turn_context.send_activity(
                    MessageFactory.text("Lo siento, no hay handlers disponibles para procesar tu mensaje.")
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error in message handling: {str(e)}")
            
            log_handler_execution(
                self.logger, 
                "unknown", 
                execution_time, 
                False
            )
            
            await turn_context.send_activity(
                MessageFactory.text("Ocurrió un error procesando tu mensaje. Por favor intenta de nuevo.")
            )
    
    def _route_message_to_handler(self, message: str, turn_context: TurnContext) -> Optional[Any]:
        """
        Route message to appropriate handler based on content
        
        Args:
            message: User message
            turn_context: Teams context
            
        Returns:
            Handler instance or None
        """
        
        # Check for admin commands first
        if message.strip().startswith("/admin"):
            admin_handler = self.handler_registry.get_handler("admin")
            if admin_handler and admin_handler.can_handle(message):
                return admin_handler
        
        # Use authenticated echo handler for other messages
        auth_echo_handler = self.handler_registry.get_handler("auth_echo")
        if auth_echo_handler and auth_echo_handler.can_handle(message):
            return auth_echo_handler
        
        # Fallback to default handler
        return self.handler_registry.get_default_handler()
    
    async def on_members_added_activity(self, members_added: List[ChannelAccount], turn_context: TurnContext):
        """Handle when members are added to the conversation"""
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_message = (
                    "¡Hola! Soy MSBot, tu interfaz autenticada para sistemas RAG.\n\n"
                    "🔐 **Sistema de Autenticación Activo**\n"
                    "Solo usuarios autorizados pueden usar este bot.\n\n"
                    "💬 Envíame un mensaje para verificar tu acceso.\n"
                    "👑 Los administradores pueden usar comandos `/admin help`"
                )
                await turn_context.send_activity(MessageFactory.text(welcome_message))
                
                log_teams_activity(
                    self.logger, 
                    "member_added", 
                    user_id=member.id
                )
    
    def get_registered_handlers(self) -> List[str]:
        """Get list of registered handler names"""
        return self.handler_registry.get_handler_names()
    
    def add_handler(self, name: str, handler, is_default: bool = False):
        """Add a new handler to the registry"""
        self.handler_registry.register_handler(name, handler, is_default)
        self.logger.info(f"Handler '{name}' registered successfully")
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        return self.auth_manager.get_user_stats()
    
    def cleanup_sessions(self, timeout_hours: int = 24) -> int:
        """Cleanup inactive authentication sessions"""
        return self.auth_manager.cleanup_inactive_sessions(timeout_hours)