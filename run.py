#!/usr/bin/env python3
"""
MSBot - Punto de entrada alternativo
Script simple para ejecutar el bot sin configuración adicional
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Importar main.py como módulo
import main

if __name__ == "__main__":
    try:
        # Verificar configuración básica
        if not os.path.exists(".env"):
            print("❌ Archivo .env no encontrado")
            print("Copia .env.example a .env y configura las variables necesarias")
            sys.exit(1)
        
        # Ejecutar aplicación principal
        if hasattr(main, 'create_ssl_context'):
            # Usar la función principal de main.py
            if main.settings.https_enabled and main.create_ssl_context():
                main.logger.info(f"Starting HTTPS server on {main.settings.host}:{main.settings.port}")
                import uvicorn
                uvicorn.run(
                    "main:app",
                    host=main.settings.host,
                    port=main.settings.port,
                    ssl_keyfile=main.settings.ssl_key_path,
                    ssl_certfile=main.settings.ssl_cert_path,
                    reload=True if main.settings.environment == "development" else False
                )
            else:
                main.logger.info(f"Starting HTTP server on {main.settings.host}:{main.settings.port}")
                import uvicorn
                uvicorn.run(
                    "main:app",
                    host=main.settings.host,
                    port=main.settings.port,
                    reload=True if main.settings.environment == "development" else False
                )
        else:
            print("Error: No se pudo importar la función principal")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 MSBot detenido por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error iniciando MSBot: {e}")
        sys.exit(1)