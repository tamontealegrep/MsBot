"""
Echo Handler - Simple Message Echo Implementation
This handler demonstrates the basic message flow and serves as a template
for future RAG system integrations
"""

from typing import Optional, Dict, Any
from botbuilder.core import TurnContext

from app.bot.handlers.base_handler import BaseHandler
from app.utils.logger import setup_logger

class EchoHandler(BaseHandler):
    """
    Echo Handler - Repeats user messages back
    
    This is the initial implementation that demonstrates:
    1. How messages flow through the system
    2. How to capture user input
    3. How to generate responses
    4. How to integrate with the modular handler system
    
    Future RAG handlers will follow this same pattern but replace
    the echo logic with RAG system queries.
    """
    
    def __init__(self):
        super().__init__(
            name="echo",
            description="Repite los mensajes del usuario (modo de prueba para entender el flujo)"
        )
        self.logger = setup_logger(__name__)
        self.message_count = 0
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """
        Handle message by echoing it back
        
        Args:
            message: User message text
            turn_context: Bot Framework turn context
            
        Returns:
            Echo response
        """
        
        if not self.enabled:
            return None
        
        try:
            # Increment message counter
            self.message_count += 1
            
            # Get user information
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name or "Usuario"
            
            # Log the interaction
            self.logger.info(f"Echo handler processing message {self.message_count} from {user_name} ({user_id})")
            
            # Pre-process the message
            processed_message = await self.pre_process(message, turn_context)
            
            # Create echo response with additional information
            echo_response = self._create_echo_response(processed_message, user_name, self.message_count)
            
            # Post-process the response
            final_response = await self.post_process(echo_response, message, turn_context)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error in echo handler: {str(e)}")
            return "Error: No pude procesar tu mensaje."
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Echo handler can handle any message
        
        Args:
            message: User message
            context: Additional context
            
        Returns:
            Always True (echo handles everything)
        """
        return True
    
    def _create_echo_response(self, message: str, user_name: str, count: int) -> str:
        """
        Create the echo response with formatting
        
        Args:
            message: Processed user message
            user_name: User's display name
            count: Message count
            
        Returns:
            Formatted echo response
        """
        
        # Basic echo response
        response = f"📝 **Modo Echo Activo**\n\n"
        response += f"👤 **Usuario:** {user_name}\n"
        response += f"💬 **Mensaje #{count}:** {message}\n\n"
        response += f"🔄 **Respuesta:** {message}\n\n"
        response += f"---\n"
        response += f"ℹ️ *Este es el modo echo para pruebas. "
        response += f"En el futuro, aquí se integrarán los sistemas RAG personalizados.*"
        
        return response
    
    async def pre_process(self, message: str, turn_context: TurnContext) -> str:
        """
        Pre-process message (clean and normalize)
        
        Args:
            message: Original message
            turn_context: Bot context
            
        Returns:
            Cleaned message
        """
        # Basic cleaning
        cleaned = message.strip()
        
        # Remove multiple spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    async def post_process(self, response: str, original_message: str, turn_context: TurnContext) -> str:
        """
        Post-process response (add metadata, formatting, etc.)
        
        Args:
            response: Generated response
            original_message: Original user message
            turn_context: Bot context
            
        Returns:
            Final processed response
        """
        
        # Add timestamp and system info
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        final_response = response + f"\n\n⏰ **Procesado:** {timestamp}"
        
        return final_response
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get handler statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "name": self.name,
            "messages_processed": self.message_count,
            "enabled": self.enabled,
            "description": self.description
        }
    
    def reset_stats(self):
        """Reset message counter"""
        self.message_count = 0
        self.logger.info("Echo handler stats reset")