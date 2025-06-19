"""
Authentication Manager - Sistema de autenticación para MSBot
Maneja usuarios, roles y permisos de acceso
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from pathlib import Path

from app.utils.logger import setup_logger

class UserRole(Enum):
    """Roles de usuario disponibles"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    BANNED = "banned"

class Permission(Enum):
    """Permisos disponibles en el sistema"""
    USE_RAG = "use_rag"
    USE_ECHO = "use_echo"
    ADMIN_COMMANDS = "admin_commands"
    VIEW_METRICS = "view_metrics"
    MANAGE_USERS = "manage_users"

class AuthenticatedUser:
    """Representa un usuario autenticado"""
    
    def __init__(self, user_id: str, name: str, email: str, role: UserRole, permissions: Set[Permission]):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.permissions = permissions
        self.last_activity = datetime.now()
        self.session_count = 0
    
    def has_permission(self, permission: Permission) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        return permission in self.permissions
    
    def update_activity(self):
        """Actualizar timestamp de última actividad"""
        self.last_activity = datetime.now()
        self.session_count += 1
    
    def to_dict(self) -> Dict:
        """Convertir usuario a diccionario"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions],
            "last_activity": self.last_activity.isoformat(),
            "session_count": self.session_count
        }

class AuthManager:
    """
    Gestor de autenticación y autorización para MSBot
    
    Funcionalidades:
    - Gestión de usuarios y roles
    - Verificación de permisos
    - Whitelist/blacklist de usuarios
    - Configuración persistente
    """
    
    def __init__(self, config_file: str = "auth_config.json"):
        self.logger = setup_logger(__name__)
        self.config_file = Path(config_file)
        
        # Usuarios autenticados en sesión actual
        self.authenticated_users: Dict[str, AuthenticatedUser] = {}
        
        # Configuración de usuarios autorizados
        self.authorized_users: Dict[str, Dict] = {}
        
        # Roles y sus permisos por defecto
        self.role_permissions = {
            UserRole.ADMIN: {
                Permission.USE_RAG,
                Permission.USE_ECHO,
                Permission.ADMIN_COMMANDS,
                Permission.VIEW_METRICS,
                Permission.MANAGE_USERS
            },
            UserRole.USER: {
                Permission.USE_RAG,
                Permission.USE_ECHO,
                Permission.VIEW_METRICS
            },
            UserRole.GUEST: {
                Permission.USE_ECHO
            },
            UserRole.BANNED: set()
        }
        
        # Cargar configuración
        self._load_config()
        
        self.logger.info("Authentication manager initialized")
    
    def _load_config(self):
        """Cargar configuración de usuarios desde archivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.authorized_users = config_data.get("authorized_users", {})
                    self.logger.info(f"Loaded {len(self.authorized_users)} authorized users")
            else:
                # Crear configuración por defecto
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading auth config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Crear configuración por defecto"""
        import os
        
        # Admin por defecto desde variables de entorno
        default_admin = os.getenv("DEFAULT_ADMIN_USER_ID")
        default_admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@empresa.com")
        
        if default_admin:
            self.authorized_users = {
                default_admin: {
                    "name": "Administrador",
                    "email": default_admin_email,
                    "role": UserRole.ADMIN.value,
                    "added_date": datetime.now().isoformat(),
                    "added_by": "system"
                }
            }
        else:
            self.authorized_users = {}
        
        self._save_config()
        self.logger.info("Created default auth configuration")
    
    def _save_config(self):
        """Guardar configuración en archivo"""
        try:
            config_data = {
                "authorized_users": self.authorized_users,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info("Auth configuration saved")
        except Exception as e:
            self.logger.error(f"Error saving auth config: {e}")
    
    def authenticate_user(self, user_id: str, user_name: str = None, user_email: str = None) -> Optional[AuthenticatedUser]:
        """
        Autenticar usuario y crear sesión
        
        Args:
            user_id: ID único del usuario de Teams
            user_name: Nombre del usuario (opcional)
            user_email: Email del usuario (opcional)
            
        Returns:
            Usuario autenticado o None si no autorizado
        """
        
        # Verificar si el usuario está autorizado
        if user_id not in self.authorized_users:
            self.logger.warning(f"Unauthorized access attempt by user {user_id} ({user_name})")
            return None
        
        # Obtener configuración del usuario
        user_config = self.authorized_users[user_id]
        role = UserRole(user_config["role"])
        
        # Verificar si está baneado
        if role == UserRole.BANNED:
            self.logger.warning(f"Banned user attempted access: {user_id}")
            return None
        
        # Obtener permisos basados en el rol
        permissions = self.role_permissions.get(role, set())
        
        # Crear usuario autenticado
        auth_user = AuthenticatedUser(
            user_id=user_id,
            name=user_name or user_config.get("name", "Usuario"),
            email=user_email or user_config.get("email", ""),
            role=role,
            permissions=permissions
        )
        
        # Guardar en sesión
        self.authenticated_users[user_id] = auth_user
        auth_user.update_activity()
        
        self.logger.info(f"User authenticated: {user_id} ({auth_user.name}) as {role.value}")
        return auth_user
    
    def get_authenticated_user(self, user_id: str) -> Optional[AuthenticatedUser]:
        """Obtener usuario autenticado por ID"""
        return self.authenticated_users.get(user_id)
    
    def is_user_authorized(self, user_id: str, permission: Permission = None) -> bool:
        """
        Verificar si un usuario está autorizado
        
        Args:
            user_id: ID del usuario
            permission: Permiso específico a verificar (opcional)
            
        Returns:
            True si está autorizado
        """
        
        auth_user = self.get_authenticated_user(user_id)
        
        if not auth_user:
            return False
        
        if permission and not auth_user.has_permission(permission):
            return False
        
        # Actualizar actividad
        auth_user.update_activity()
        
        return True
    
    def add_authorized_user(self, user_id: str, name: str, email: str, role: UserRole, added_by: str = "admin") -> bool:
        """
        Agregar usuario autorizado
        
        Args:
            user_id: ID único del usuario
            name: Nombre del usuario
            email: Email del usuario
            role: Rol del usuario
            added_by: Quién agregó al usuario
            
        Returns:
            True si se agregó exitosamente
        """
        
        try:
            self.authorized_users[user_id] = {
                "name": name,
                "email": email,
                "role": role.value,
                "added_date": datetime.now().isoformat(),
                "added_by": added_by
            }
            
            self._save_config()
            self.logger.info(f"Added authorized user: {user_id} ({name}) as {role.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    def remove_authorized_user(self, user_id: str, removed_by: str = "admin") -> bool:
        """
        Remover usuario autorizado
        
        Args:
            user_id: ID del usuario a remover
            removed_by: Quién removió al usuario
            
        Returns:
            True si se removió exitosamente
        """
        
        try:
            if user_id in self.authorized_users:
                user_name = self.authorized_users[user_id].get("name", "Unknown")
                del self.authorized_users[user_id]
                
                # Remover de sesiones activas
                if user_id in self.authenticated_users:
                    del self.authenticated_users[user_id]
                
                self._save_config()
                self.logger.info(f"Removed user: {user_id} ({user_name}) by {removed_by}")
                return True
            else:
                self.logger.warning(f"Attempted to remove non-existent user: {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing user {user_id}: {e}")
            return False
    
    def update_user_role(self, user_id: str, new_role: UserRole, updated_by: str = "admin") -> bool:
        """
        Actualizar rol de usuario
        
        Args:
            user_id: ID del usuario
            new_role: Nuevo rol
            updated_by: Quién actualizó el rol
            
        Returns:
            True si se actualizó exitosamente
        """
        
        try:
            if user_id not in self.authorized_users:
                self.logger.error(f"Cannot update role: user {user_id} not found")
                return False
            
            old_role = self.authorized_users[user_id]["role"]
            self.authorized_users[user_id]["role"] = new_role.value
            self.authorized_users[user_id]["last_updated"] = datetime.now().isoformat()
            self.authorized_users[user_id]["updated_by"] = updated_by
            
            # Actualizar usuario en sesión si está activo
            if user_id in self.authenticated_users:
                auth_user = self.authenticated_users[user_id]
                auth_user.role = new_role
                auth_user.permissions = self.role_permissions.get(new_role, set())
            
            self._save_config()
            self.logger.info(f"Updated user {user_id} role from {old_role} to {new_role.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating user role {user_id}: {e}")
            return False
    
    def get_user_stats(self) -> Dict:
        """Obtener estadísticas de usuarios"""
        
        total_authorized = len(self.authorized_users)
        active_sessions = len(self.authenticated_users)
        
        # Contar por roles
        role_counts = {}
        for user_data in self.authorized_users.values():
            role = user_data["role"]
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            "total_authorized_users": total_authorized,
            "active_sessions": active_sessions,
            "role_distribution": role_counts,
            "session_users": [user.to_dict() for user in self.authenticated_users.values()]
        }
    
    def cleanup_inactive_sessions(self, timeout_hours: int = 24):
        """Limpiar sesiones inactivas"""
        
        cutoff_time = datetime.now() - timedelta(hours=timeout_hours)
        inactive_users = []
        
        for user_id, auth_user in self.authenticated_users.items():
            if auth_user.last_activity < cutoff_time:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            del self.authenticated_users[user_id]
            self.logger.info(f"Cleaned up inactive session for user {user_id}")
        
        return len(inactive_users)
    
    def export_users(self) -> Dict:
        """Exportar configuración de usuarios para backup"""
        return {
            "authorized_users": self.authorized_users,
            "export_date": datetime.now().isoformat(),
            "total_users": len(self.authorized_users)
        }
    
    def import_users(self, user_data: Dict, imported_by: str = "admin") -> bool:
        """Importar usuarios desde backup"""
        try:
            if "authorized_users" in user_data:
                self.authorized_users.update(user_data["authorized_users"])
                self._save_config()
                self.logger.info(f"Imported {len(user_data['authorized_users'])} users by {imported_by}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error importing users: {e}")
            return False