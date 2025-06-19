#!/usr/bin/env python3
"""
MSBot - Punto de entrada alternativo
Script simple para ejecutar el bot sin configuración adicional
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Función principal del script de ejecución"""
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Verificar configuración básica
    if not os.path.exists(".env"):
        print("❌ Archivo .env no encontrado")
        print("Copia .env.example a .env y configura las variables necesarias")
        sys.exit(1)
    
    print("🤖 Iniciando MSBot...")
    
    try:
        # Ejecutar main.py directamente
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando MSBot: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 MSBot detenido por usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()