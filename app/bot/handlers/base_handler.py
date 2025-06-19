"""
Base Handler Class
Abstract base class for all message handlers in the modular system
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from botbuilder.core import TurnContext

class BaseHandler(ABC):
    """
    Abstract base class for all message handlers
    
    This class defines the interface that all handlers must implement.
    It's designed to be easily extensible for different RAG systems.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize base handler
        
        Args:
            name: Handler name/identifier
            description: Handler description
        """
        self.name = name
        self.description = description
        self.enabled = True
    
    @abstractmethod
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """
        Handle incoming message and return response
        
        Args:
            message: User message text
            turn_context: Bot Framework turn context
            
        Returns:
            Response message or None
        """
        pass
    
    @abstractmethod
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Determine if this handler can process the given message
        
        Args:
            message: User message text
            context: Additional context information
            
        Returns:
            True if handler can process the message
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get handler information
        
        Returns:
            Dictionary with handler metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "type": self.__class__.__name__
        }
    
    def enable(self):
        """Enable the handler"""
        self.enabled = True
    
    def disable(self):
        """Disable the handler"""
        self.enabled = False
    
    async def pre_process(self, message: str, turn_context: TurnContext) -> str:
        """
        Pre-process message before handling
        Can be overridden by subclasses for custom preprocessing
        
        Args:
            message: Original message
            turn_context: Bot Framework turn context
            
        Returns:
            Processed message
        """
        return message.strip()
    
    async def post_process(self, response: str, original_message: str, turn_context: TurnContext) -> str:
        """
        Post-process response before sending
        Can be overridden by subclasses for custom postprocessing
        
        Args:
            response: Handler response
            original_message: Original user message
            turn_context: Bot Framework turn context
            
        Returns:
            Processed response
        """
        return response

class RAGHandler(BaseHandler):
    """
    Extended base class specifically for RAG handlers
    Provides common functionality for RAG system integration
    """
    
    def __init__(self, name: str, description: str = "", rag_config: Dict[str, Any] = None):
        """
        Initialize RAG handler
        
        Args:
            name: Handler name
            description: Handler description
            rag_config: RAG system configuration
        """
        super().__init__(name, description)
        self.rag_config = rag_config or {}
    
    @abstractmethod
    async def query_rag_system(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Query the RAG system with user input
        
        Args:
            query: User query/message
            context: Additional context for the query
            
        Returns:
            RAG system response
        """
        pass
    
    async def handle_message(self, message: str, turn_context: TurnContext) -> Optional[str]:
        """
        Handle message through RAG system
        
        Args:
            message: User message
            turn_context: Bot Framework turn context
            
        Returns:
            RAG system response
        """
        if not self.enabled:
            return None
        
        try:
            # Pre-process message
            processed_message = await self.pre_process(message, turn_context)
            
            # Query RAG system
            rag_response = await self.query_rag_system(processed_message)
            
            # Post-process response
            final_response = await self.post_process(rag_response, message, turn_context)
            
            return final_response
            
        except Exception as e:
            return f"Error procesando consulta RAG: {str(e)}"
    
    def update_rag_config(self, config: Dict[str, Any]):
        """Update RAG system configuration"""
        self.rag_config.update(config)