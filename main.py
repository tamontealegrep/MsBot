"""
MSBot - Microsoft Teams Bot for RAG Integration
Main application entry point with HTTPS support
"""

import os
import ssl
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.config.settings import get_settings
from app.bot.bot_handler import MSBotHandler
from app.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Initialize settings and logger
settings = get_settings()
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MSBot - Teams RAG Interface",
    description="Modular Microsoft Teams Bot for RAG System Integration",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize bot handler
bot_handler = MSBotHandler()

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot_name": "MSBot",
        "version": "1.0.0",
        "environment": settings.environment
    }

@app.post("/api/messages")
async def messages(request: Request):
    """
    Main webhook endpoint for Microsoft Teams messages
    This is where Teams sends all bot interactions
    """
    try:
        # Get request body
        body = await request.body()
        
        # Get authorization header
        auth_header = request.headers.get("Authorization", "")
        
        # Process the activity through bot handler
        response = await bot_handler.process_activity(body, auth_header)
        
        return Response(
            content=response.get("body", ""),
            status_code=response.get("status", 200),
            headers=response.get("headers", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return Response(status_code=500)

@app.get("/api/status")
async def bot_status():
    """Get bot status and configuration info"""
    return {
        "bot_name": "MSBot",
        "status": "running",
        "handlers": bot_handler.get_registered_handlers(),
        "environment": settings.environment,
        "https_enabled": settings.https_enabled
    }

def create_ssl_context():
    """Create SSL context for HTTPS"""
    if not settings.https_enabled:
        return None
        
    if not os.path.exists(settings.ssl_cert_path) or not os.path.exists(settings.ssl_key_path):
        logger.warning("SSL certificates not found. Please run setup_ssl.py to generate them.")
        return None
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(settings.ssl_cert_path, settings.ssl_key_path)
    return ssl_context

if __name__ == "__main__":
    logger.info("Starting MSBot server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"HTTPS Enabled: {settings.https_enabled}")
    
    # Create SSL context if HTTPS is enabled
    ssl_context = create_ssl_context()
    
    if settings.https_enabled and ssl_context:
        logger.info(f"Starting HTTPS server on {settings.host}:{settings.port}")
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            ssl_keyfile=settings.ssl_key_path,
            ssl_certfile=settings.ssl_cert_path,
            reload=True if settings.environment == "development" else False
        )
    else:
        logger.info(f"Starting HTTP server on {settings.host}:{settings.port}")
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=True if settings.environment == "development" else False
        )