#!/usr/bin/env python3
"""
MSBot Auth Setup - Configuración de autenticación
Script para configurar usuarios autorizados fácilmente
"""

import os
import json
import sys
from pathlib import Path

def setup_auth():
    """Configurar autenticación básica para MSBot"""
    
    print("🔐 MSBot - Configuración de Autenticación")
    print("=" * 50)
    
    # Verificar si ya existe configuración
    config_file = Path("auth_config.json")
    if config_file.exists():
        print("⚠️  Ya existe configuración de autenticación.")
        response = input("¿Quieres sobrescribirla? (y/N): ").lower()
        if response != 'y':
            print("❌ Configuración cancelada")
            return
    
    # Obtener información del admin principal
    print("\n👑 Configuración de Administrador Principal")
    print("-" * 40)
    
    admin_id = input("User ID del administrador (de Teams): ").strip()
    if not admin_id:
        print("❌ El User ID es obligatorio")
        return
    
    admin_name = input("Nombre del administrador: ").strip()
    if not admin_name:
        admin_name = "Administrador"
    
    admin_email = input("Email del administrador: ").strip()
    if not admin_email:
        admin_email = "admin@empresa.com"
    
    # Crear configuración
    config = {
        "authorized_users": {
            admin_id: {
                "name": admin_name,
                "email": admin_email,
                "role": "admin",
                "added_date": "2024-01-01T00:00:00",
                "added_by": "setup_script"
            }
        },
        "last_updated": "2024-01-01T00:00:00"
    }
    
    # Preguntar si quiere agregar más usuarios
    print("\n👥 ¿Quieres agregar más usuarios? (opcional)")
    print("-" * 40)
    
    while True:
        response = input("¿Agregar otro usuario? (y/N): ").lower()
        if response != 'y':
            break
        
        user_id = input("User ID: ").strip()
        if not user_id:
            continue
        
        user_name = input("Nombre: ").strip()
        if not user_name:
            user_name = "Usuario"
        
        user_email = input("Email: ").strip()
        if not user_email:
            user_email = "usuario@empresa.com"
        
        print("Roles disponibles:")
        print("  admin - Acceso completo + comandos admin")
        print("  user  - Acceso a RAG y métricas")
        print("  guest - Solo modo echo")
        
        role = input("Rol (user/admin/guest) [user]: ").strip().lower()
        if role not in ['admin', 'user', 'guest']:
            role = 'user'
        
        config["authorized_users"][user_id] = {
            "name": user_name,
            "email": user_email,
            "role": role,
            "added_date": "2024-01-01T00:00:00",
            "added_by": "setup_script"
        }
        
        print(f"✅ Usuario {user_name} agregado como {role}")
    
    # Guardar configuración
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Configuración guardada en {config_file}")
        print(f"👥 Total usuarios configurados: {len(config['authorized_users'])}")
        
        # Mostrar resumen
        print("\n📋 Resumen de Usuarios:")
        for user_id, user_data in config["authorized_users"].items():
            print(f"  • {user_data['name']} ({user_data['role']}) - {user_id}")
        
        # Actualizar .env si es necesario
        update_env_file(admin_id, admin_email)
        
        print("\n🎉 ¡Configuración de autenticación completada!")
        print("🚀 Ahora puedes iniciar MSBot con: python main.py")
        
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")

def update_env_file(admin_id: str, admin_email: str):
    """Actualizar archivo .env con admin por defecto"""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado")
        return
    
    try:
        # Leer archivo .env
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Actualizar líneas
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("DEFAULT_ADMIN_USER_ID="):
                lines[i] = f"DEFAULT_ADMIN_USER_ID={admin_id}\n"
                updated = True
            elif line.startswith("DEFAULT_ADMIN_EMAIL="):
                lines[i] = f"DEFAULT_ADMIN_EMAIL={admin_email}\n"
                updated = True
        
        # Guardar archivo actualizado
        if updated:
            with open(env_file, 'w') as f:
                f.writelines(lines)
            print("✅ Archivo .env actualizado con admin por defecto")
        
    except Exception as e:
        print(f"⚠️  No se pudo actualizar .env: {e}")

def show_user_id_help():
    """Mostrar ayuda para obtener User ID de Teams"""
    
    print("\n📋 ¿Cómo obtener el User ID de Teams?")
    print("=" * 50)
    print("""
1. En Microsoft Teams, ve a un chat directo con el usuario
2. Haz clic en los 3 puntos (...) en la parte superior
3. Selecciona "Ver perfil"
4. En la URL verás algo como: 
   https://teams.microsoft.com/l/chat/0/0?users=29:1abc123def...
5. El User ID es la parte después de "users=", ejemplo: 29:1abc123def...

Alternativamente:
- Puedes configurar un admin temporal y luego usar comandos /admin
- Usa el bot en modo de prueba para obtener el ID del primer mensaje
    """)

def main():
    """Función principal"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        show_user_id_help()
        return
    
    setup_auth()

if __name__ == "__main__":
    main()