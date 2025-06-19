#!/bin/bash
# MSBot - Script de Inicio
# Inicia el bot con todas las verificaciones necesarias

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Función para verificar requisitos
check_requirements() {
    log "Verificando requisitos del sistema..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 no está instalado"
        exit 1
    fi
    
    # Verificar versión de Python
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 >= $2)}') -eq 0 ]]; then
        error "Se requiere Python 3.8 o superior. Versión actual: $PYTHON_VERSION"
        exit 1
    fi
    
    success "Python $PYTHON_VERSION encontrado"
}

# Función para verificar dependencias
check_dependencies() {
    log "Verificando dependencias de Python..."
    
    if [ ! -f "requirements.txt" ]; then
        error "Archivo requirements.txt no encontrado"
        exit 1
    fi
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        warning "Entorno virtual no encontrado, creando..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Instalar/actualizar dependencias
    log "Instalando dependencias..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    success "Dependencias instaladas correctamente"
}

# Función para verificar configuración
check_configuration() {
    log "Verificando configuración..."
    
    if [ ! -f ".env" ]; then
        error "Archivo .env no encontrado"
        echo "Copia .env.example a .env y configura las variables necesarias"
        exit 1
    fi
    
    # Verificar variables críticas
    source .env
    
    if [ -z "$MICROSOFT_APP_ID" ] || [ "$MICROSOFT_APP_ID" = "your_app_id_here" ]; then
        error "MICROSOFT_APP_ID no está configurado en .env"
        exit 1
    fi
    
    if [ -z "$MICROSOFT_APP_PASSWORD" ] || [ "$MICROSOFT_APP_PASSWORD" = "your_app_password_here" ]; then
        error "MICROSOFT_APP_PASSWORD no está configurado en .env"
        exit 1
    fi
    
    success "Configuración básica verificada"
}

# Función para verificar certificados SSL
check_ssl() {
    source .env
    
    if [ "$HTTPS_ENABLED" = "true" ]; then
        log "Verificando certificados SSL..."
        
        if [ ! -f "$SSL_CERT_PATH" ] || [ ! -f "$SSL_KEY_PATH" ]; then
            warning "Certificados SSL no encontrados"
            log "Generando certificados SSL auto-firmados..."
            python setup_ssl.py
            
            if [ $? -eq 0 ]; then
                success "Certificados SSL generados"
            else
                error "Error generando certificados SSL"
                exit 1
            fi
        else
            # Verificar validez de certificados
            if openssl x509 -checkend 86400 -noout -in "$SSL_CERT_PATH" >/dev/null 2>&1; then
                success "Certificados SSL válidos"
            else
                warning "Certificados SSL expiran pronto o han expirado"
                log "Considera renovar los certificados"
            fi
        fi
    else
        warning "HTTPS deshabilitado - no recomendado para producción"
    fi
}

# Función para verificar conectividad
check_connectivity() {
    log "Verificando conectividad de red..."
    
    # Verificar conexión a internet
    if ping -c 1 google.com &> /dev/null; then
        success "Conexión a internet OK"
    else
        warning "Sin conexión a internet - esto puede afectar la funcionalidad del bot"
    fi
    
    # Verificar puertos
    source .env
    if netstat -tln | grep -q ":$PORT "; then
        error "Puerto $PORT ya está en uso"
        log "Usa 'sudo lsof -i :$PORT' para ver qué proceso lo está usando"
        exit 1
    fi
    
    success "Puerto $PORT disponible"
}

# Función para mostrar información de inicio
show_startup_info() {
    source .env
    
    echo ""
    echo "🤖 ============================================="
    echo "   MSBot - Microsoft Teams RAG Interface"
    echo "============================================="
    echo ""
    echo "📋 Configuración:"
    echo "   - Entorno: $ENVIRONMENT"
    echo "   - Puerto: $PORT"
    echo "   - HTTPS: $HTTPS_ENABLED"
    echo "   - Log Level: $LOG_LEVEL"
    echo ""
    
    if [ "$HTTPS_ENABLED" = "true" ]; then
        echo "🌐 URLs:"
        echo "   - Local: https://localhost:$PORT"
        echo "   - API Health: https://localhost:$PORT/"
        echo "   - Bot Status: https://localhost:$PORT/api/status"
        if [ "$ENVIRONMENT" = "development" ]; then
            echo "   - API Docs: https://localhost:$PORT/docs"
        fi
    else
        echo "🌐 URLs:"
        echo "   - Local: http://localhost:$PORT"
        echo "   - API Health: http://localhost:$PORT/"
        echo "   - Bot Status: http://localhost:$PORT/api/status"
        if [ "$ENVIRONMENT" = "development" ]; then
            echo "   - API Docs: http://localhost:$PORT/docs"
        fi
    fi
    
    echo ""
    echo "📝 Para conectar con Teams:"
    echo "   1. Configura ngrok: ngrok http $PORT"
    echo "   2. Actualiza webhook en Bot Framework con la URL de ngrok"
    echo "   3. Mensaje endpoint: https://tu-ngrok-url.ngrok.io/api/messages"
    echo ""
    echo "🔍 Logs en tiempo real:"
    echo "   tail -f logs/msbot.log"
    echo ""
    echo "============================================="
    echo ""
}

# Función principal de inicio
start_bot() {
    log "Iniciando MSBot..."
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Mostrar información
    show_startup_info
    
    # Iniciar bot
    log "Ejecutando servidor..."
    python main.py
}

# Función de ayuda
show_help() {
    echo "MSBot - Script de Inicio"
    echo ""
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  start, --start, -s    Iniciar el bot (default)"
    echo "  check, --check, -c    Solo verificar requisitos"
    echo "  setup, --setup        Configuración inicial completa"
    echo "  help, --help, -h      Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                    # Inicia el bot"
    echo "  $0 check             # Solo verifica requisitos"
    echo "  $0 setup             # Configuración inicial"
    echo ""
}

# Función de configuración inicial
setup_bot() {
    log "Configuración inicial de MSBot..."
    
    # Crear archivo .env si no existe
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log "Archivo .env creado desde .env.example"
        else
            log "Creando archivo .env básico..."
            cat > .env << EOF
# Microsoft Teams Bot Configuration
MICROSOFT_APP_ID=your_app_id_here
MICROSOFT_APP_PASSWORD=your_app_password_here

# Server Configuration
HOST=0.0.0.0
PORT=3978
HTTPS_ENABLED=true
SSL_CERT_PATH=./certs/cert.pem
SSL_KEY_PATH=./certs/key.pem

# Environment
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
        fi
        
        warning "Configura las variables MICROSOFT_APP_ID y MICROSOFT_APP_PASSWORD en .env"
    fi
    
    # Crear directorio de logs
    mkdir -p logs
    
    # Ejecutar verificaciones
    check_requirements
    check_dependencies
    check_ssl
    
    success "Configuración inicial completada"
    echo ""
    echo "📝 Próximos pasos:"
    echo "1. Edita .env con tus credenciales de Teams"
    echo "2. Ejecuta: $0 start"
    echo "3. Configura ngrok para acceso externo"
}

# Script principal
main() {
    # Cambiar al directorio del script
    cd "$(dirname "$0")" || exit 1
    
    case "${1:-start}" in
        start|--start|-s)
            check_requirements
            check_dependencies
            check_configuration
            check_ssl
            check_connectivity
            start_bot
            ;;
        check|--check|-c)
            check_requirements
            check_dependencies
            check_configuration
            check_ssl
            check_connectivity
            success "Todas las verificaciones pasaron correctamente"
            ;;
        setup|--setup)
            setup_bot
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"