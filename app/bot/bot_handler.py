"""
MSBot Handler - Main Bot Logic
Handles Microsoft Teams activities and routes them to appropriate handlers
"""

import json
import time
from typing import Dict, Any, List
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
from app.bot.handlers.echo_handler import EchoHandler

class MSBotHandler(ActivityHandler):
    """
    Main bot handler that processes Teams activities
    Routes messages to appropriate modular handlers
    """
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Initialize Bot Framework Adapter
        self.adapter = self._create_adapter()
        
        # Initialize handler registry
        self.handler_registry = HandlerRegistry()
        
        # Register default handlers
        self._register_default_handlers()
        
        self.logger.info("MSBot initialized successfully")
    
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
        """Register default message handlers"""
        
        # Register Echo Handler as default
        echo_handler = EchoHandler()
        self.handler_registry.register_handler("echo", echo_handler, is_default=True)
        
        self.logger.info("Default handlers registered")
    
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
        Handle message activities from Teams
        Routes messages to appropriate handlers
        """
        
        start_time = time.time()
        
        try:
            user_message = turn_context.activity.text
            user_id = turn_context.activity.from_property.id
            
            self.logger.info(f"Processing message from user {user_id}: {user_message}")
            
            # Get appropriate handler (for now, always use default)
            handler = self.handler_registry.get_default_handler()
            
            if handler:
                # Process message through handler
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
    
    async def on_members_added_activity(self, members_added: List[ChannelAccount], turn_context: TurnContext):
        """Handle when members are added to the conversation"""
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_message = (
                    "¡Hola! Soy MSBot, tu interfaz para sistemas RAG. "
                    "Envíame un mensaje y te responderé. "
                    "Actualmente estoy en modo echo para pruebas."
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