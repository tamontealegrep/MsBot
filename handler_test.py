#!/usr/bin/env python3
"""
MSBot Handler Testing Suite
Tests the functionality of the MSBot handler system
"""

import unittest
import sys
import os
import logging
import asyncio
from typing import Dict, Any, Optional

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the handler classes
from app.bot.handlers.base_handler import BaseHandler
from app.bot.handlers.echo_handler import EchoHandler
from app.bot.handlers.handler_registry import HandlerRegistry
from app.utils.logger import setup_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockTurnContext:
    """Mock TurnContext for testing handlers"""
    
    def __init__(self, user_id="test-user", user_name="Test User", text="Test message"):
        self.activity = type('obj', (object,), {
            'from_property': type('obj', (object,), {
                'id': user_id,
                'name': user_name
            }),
            'text': text,
            'recipient': type('obj', (object,), {
                'id': 'bot-id',
                'name': 'MSBot'
            })
        })
        self.sent_activities = []
        
    async def send_activity(self, activity):
        """Mock send_activity method"""
        self.sent_activities.append(activity)
        return None

class HandlerTests(unittest.TestCase):
    """Test suite for MSBot handlers"""
    
    def setUp(self):
        """Set up test environment"""
        self.logger = setup_logger(__name__)
        self.registry = HandlerRegistry()
        self.echo_handler = EchoHandler()
        
    def test_handler_registry(self):
        """Test handler registry functionality"""
        # Register handler
        self.registry.register_handler("echo", self.echo_handler, is_default=True)
        
        # Check if handler is registered
        self.assertIn("echo", self.registry.get_handler_names())
        
        # Check if default handler is set
        default_handler = self.registry.get_default_handler()
        self.assertIsNotNone(default_handler)
        self.assertEqual(default_handler.name, "echo")
        
        # Test handler enable/disable
        self.registry.disable_handler("echo")
        self.assertFalse(self.echo_handler.enabled)
        
        self.registry.enable_handler("echo")
        self.assertTrue(self.echo_handler.enabled)
        
        # Test handler unregistration
        self.registry.unregister_handler("echo")
        self.assertNotIn("echo", self.registry.get_handler_names())
        
    def test_echo_handler(self):
        """Test echo handler functionality"""
        # Create mock context
        context = MockTurnContext(text="Hello, bot!")
        
        # Test can_handle method
        self.assertTrue(self.echo_handler.can_handle("Any message"))
        
        # Test handle_message method
        response = asyncio.run(self.echo_handler.handle_message("Hello, bot!", context))
        
        # Check response
        self.assertIsNotNone(response)
        self.assertIn("Hello, bot!", response)
        self.assertIn("Modo Echo Activo", response)
        
        # Test pre_process method
        processed = asyncio.run(self.echo_handler.pre_process("  Test   message  ", context))
        self.assertEqual(processed, "Test message")
        
        # Test post_process method
        post_processed = asyncio.run(self.echo_handler.post_process("Test response", "Original", context))
        self.assertIn("Test response", post_processed)
        self.assertIn("Procesado:", post_processed)
        
        # Test stats
        stats = self.echo_handler.get_stats()
        self.assertEqual(stats["name"], "echo")
        self.assertEqual(stats["messages_processed"], 1)
        
        # Test reset stats
        self.echo_handler.reset_stats()
        self.assertEqual(self.echo_handler.message_count, 0)
        
    def test_handler_routing(self):
        """Test handler routing system"""
        # Register handlers
        self.registry.register_handler("echo", self.echo_handler, is_default=True)
        
        # Test get_best_handler
        best_handler = self.registry.get_best_handler("Hello")
        self.assertEqual(best_handler.name, "echo")
        
        # Test with disabled handler
        self.echo_handler.disable()
        best_handler = self.registry.get_best_handler("Hello")
        self.assertIsNone(best_handler)
        
        # Re-enable and test again
        self.echo_handler.enable()
        best_handler = self.registry.get_best_handler("Hello")
        self.assertEqual(best_handler.name, "echo")

def main():
    """Main function"""
    print("\n" + "="*50)
    print("MSBot Handler Test Suite")
    print("="*50 + "\n")
    
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    print("\n" + "="*50)
    print("Handler tests completed")
    print("="*50 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())