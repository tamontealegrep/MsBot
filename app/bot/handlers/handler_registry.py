"""
Handler Registry - Modular Handler Management System
Manages registration, discovery, and routing of message handlers
"""

from typing import Dict, List, Optional, Any
from app.bot.handlers.base_handler import BaseHandler
from app.utils.logger import setup_logger

class HandlerRegistry:
    """
    Registry for managing message handlers
    
    This class provides a centralized system for:
    1. Registering new handlers (RAG systems, custom handlers, etc.)
    2. Routing messages to appropriate handlers
    3. Managing handler lifecycle and configuration
    4. Enabling/disabling handlers dynamically
    """
    
    def __init__(self):
        self.handlers: Dict[str, BaseHandler] = {}
        self.default_handler: Optional[str] = None
        self.logger = setup_logger(__name__)
        
        self.logger.info("Handler registry initialized")
    
    def register_handler(self, name: str, handler: BaseHandler, is_default: bool = False):
        """
        Register a new message handler
        
        Args:
            name: Unique handler name/identifier
            handler: Handler instance
            is_default: Whether this should be the default handler
        """
        
        if not isinstance(handler, BaseHandler):
            raise ValueError(f"Handler must inherit from BaseHandler")
        
        if name in self.handlers:
            self.logger.warning(f"Handler '{name}' already exists, replacing...")
        
        self.handlers[name] = handler
        
        if is_default or not self.default_handler:
            self.default_handler = name
            self.logger.info(f"Set '{name}' as default handler")
        
        self.logger.info(f"Registered handler: {name} ({handler.__class__.__name__})")
    
    def unregister_handler(self, name: str) -> bool:
        """
        Unregister a handler
        
        Args:
            name: Handler name to remove
            
        Returns:
            True if handler was removed, False if not found
        """
        
        if name not in self.handlers:
            self.logger.warning(f"Handler '{name}' not found for removal")
            return False
        
        del self.handlers[name]
        
        # If this was the default handler, clear default
        if self.default_handler == name:
            self.default_handler = None
            # Set first available handler as default
            if self.handlers:
                self.default_handler = next(iter(self.handlers))
                self.logger.info(f"New default handler: {self.default_handler}")
        
        self.logger.info(f"Unregistered handler: {name}")
        return True
    
    def get_handler(self, name: str) -> Optional[BaseHandler]:
        """
        Get handler by name
        
        Args:
            name: Handler name
            
        Returns:
            Handler instance or None if not found
        """
        return self.handlers.get(name)
    
    def get_default_handler(self) -> Optional[BaseHandler]:
        """
        Get the default handler
        
        Returns:
            Default handler instance or None
        """
        if self.default_handler:
            return self.handlers.get(self.default_handler)
        return None
    
    def get_best_handler(self, message: str, context: Dict[str, Any] = None) -> Optional[BaseHandler]:
        """
        Get the best handler for a given message
        
        This method will be enhanced in the future to support:
        - Intent detection
        - RAG system routing based on message content
        - Context-aware handler selection
        
        Args:
            message: User message
            context: Additional context
            
        Returns:
            Best matching handler or default handler
        """
        
        # Future enhancement: Add sophisticated routing logic here
        # For now, check if any handler specifically can handle the message
        for handler in self.handlers.values():
            if handler.enabled and handler.can_handle(message, context):
                return handler
        
        # Fallback to default handler
        return self.get_default_handler()
    
    def set_default_handler(self, name: str) -> bool:
        """
        Set default handler
        
        Args:
            name: Handler name to set as default
            
        Returns:
            True if successful, False if handler not found
        """
        
        if name not in self.handlers:
            self.logger.error(f"Cannot set default: handler '{name}' not found")
            return False
        
        self.default_handler = name
        self.logger.info(f"Default handler changed to: {name}")
        return True
    
    def enable_handler(self, name: str) -> bool:
        """
        Enable a handler
        
        Args:
            name: Handler name
            
        Returns:
            True if successful
        """
        
        handler = self.get_handler(name)
        if handler:
            handler.enable()
            self.logger.info(f"Handler '{name}' enabled")
            return True
        return False
    
    def disable_handler(self, name: str) -> bool:
        """
        Disable a handler
        
        Args:
            name: Handler name
            
        Returns:
            True if successful
        """
        
        handler = self.get_handler(name)
        if handler:
            handler.disable()
            self.logger.info(f"Handler '{name}' disabled")
            return True
        return False
    
    def get_handler_names(self) -> List[str]:
        """
        Get list of registered handler names
        
        Returns:
            List of handler names
        """
        return list(self.handlers.keys())
    
    def get_handler_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered handlers
        
        Returns:
            List of handler information dictionaries
        """
        
        info_list = []
        for name, handler in self.handlers.items():
            handler_info = handler.get_info()
            handler_info["is_default"] = (name == self.default_handler)
            info_list.append(handler_info)
        
        return info_list
    
    def get_enabled_handlers(self) -> List[str]:
        """
        Get list of enabled handler names
        
        Returns:
            List of enabled handler names
        """
        return [name for name, handler in self.handlers.items() if handler.enabled]
    
    def get_disabled_handlers(self) -> List[str]:
        """
        Get list of disabled handler names
        
        Returns:
            List of disabled handler names
        """
        return [name for name, handler in self.handlers.items() if not handler.enabled]
    
    def clear_all_handlers(self):
        """Clear all registered handlers"""
        self.handlers.clear()
        self.default_handler = None
        self.logger.info("All handlers cleared from registry")