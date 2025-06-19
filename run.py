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

# Importar y ejecutar main
from main import main

if __name__ == "__main__":
    try:
        # Verificar configuración básica
        if not os.path.exists(".env"):
            print("❌ Archivo .env no encontrado")
            print("Copia .env.example a .env y configura las variables necesarias")
            sys.exit(1)
        
        # Ejecutar aplicación
        main()
        
    except KeyboardInterrupt:
        print("\n👋 MSBot detenido por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error iniciando MSBot: {e}")
        sys.exit(1)