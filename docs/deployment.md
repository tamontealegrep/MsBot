# Guía de Despliegue - MSBot en Servidor Local

Esta guía detalla cómo desplegar MSBot en un servidor local para producción, manteniendo la confidencialidad y control total de los datos.

## 📋 Requisitos del Servidor

### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 4GB
- **Almacenamiento**: 20GB disponibles
- **Red**: Conexión estable a internet con IP pública o túnel HTTPS

### Software Requerido
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.8 o superior
- **OpenSSL**: Para certificados SSL
- **Supervisor**: Para gestión de procesos
- **Nginx**: (Opcional) Para proxy reverso
- **Git**: Para clonar repositorio

## 🚀 Instalación en Servidor Linux

### Paso 1: Preparar el Sistema

```bash
# Actualizar sistema
sudo apt-get update && sudo apt-get upgrade -y

# Instalar dependencias del sistema
sudo apt-get install -y python3 python3-pip python3-venv git openssl supervisor nginx

# Crear usuario para el bot (recomendado)
sudo useradd -m -s /bin/bash msbot
sudo usermod -aG sudo msbot

# Cambiar a usuario msbot
sudo su - msbot
```

### Paso 2: Clonar y Configurar el Proyecto

```bash
# Clonar repositorio en directorio del usuario
git clone <tu-repositorio> /home/msbot/msbot
cd /home/msbot/msbot

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar configuración
nano .env
```

Configuración para producción:

```env
# Microsoft Teams Bot Configuration
MICROSOFT_APP_ID=tu_app_id_real
MICROSOFT_APP_PASSWORD=tu_app_password_real

# Server Configuration
HOST=0.0.0.0
PORT=3978
HTTPS_ENABLED=true
SSL_CERT_PATH=/home/msbot/msbot/certs/fullchain.pem
SSL_KEY_PATH=/home/msbot/msbot/certs/privkey.pem

# Environment
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🔐 Configuración SSL/TLS

### Opción 1: Certificados Let's Encrypt (Recomendado)

```bash
# Instalar Certbot
sudo apt-get install certbot

# Generar certificado (requiere dominio público)
sudo certbot certonly --standalone -d tu-dominio.com

# Copiar certificados al directorio del bot
sudo mkdir -p /home/msbot/msbot/certs
sudo cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem /home/msbot/msbot/certs/
sudo cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem /home/msbot/msbot/certs/
sudo chown -R msbot:msbot /home/msbot/msbot/certs
sudo chmod 600 /home/msbot/msbot/certs/*

# Configurar renovación automática
sudo crontab -e
# Agregar línea:
# 0 12 * * * /usr/bin/certbot renew --quiet --post-hook "supervisorctl restart msbot"
```

### Opción 2: Certificados Auto-firmados (Solo para desarrollo interno)

```bash
# Como usuario msbot
cd /home/msbot/msbot
python setup_ssl.py

# Los certificados se generarán en ./certs/
```

## 🔧 Configuración de Supervisor

### Crear Archivo de Configuración

```bash
# Crear configuración de supervisor
sudo nano /etc/supervisor/conf.d/msbot.conf
```

Contenido del archivo:

```ini
[program:msbot]
command=/home/msbot/msbot/venv/bin/python /home/msbot/msbot/main.py
directory=/home/msbot/msbot
user=msbot
group=msbot
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/msbot.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PYTHONPATH="/home/msbot/msbot"

[program:msbot-monitor]
command=/home/msbot/msbot/venv/bin/python /home/msbot/msbot/scripts/health_monitor.py
directory=/home/msbot/msbot
user=msbot
group=msbot
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/msbot-monitor.log
```

### Activar y Iniciar Servicios

```bash
# Recargar configuración de supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar servicios
sudo supervisorctl start msbot
sudo supervisorctl start msbot-monitor

# Verificar estado
sudo supervisorctl status
```

## 🌐 Configuración de Red y Firewall

### Configurar Firewall

```bash
# Configurar UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 3978/tcp  # Puerto del bot
sudo ufw allow 80/tcp    # HTTP (para Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS (si usas Nginx)
sudo ufw enable

# Verificar reglas
sudo ufw status
```

### Configuración con Nginx (Proxy Reverso - Opcional)

```bash
# Crear configuración de Nginx
sudo nano /etc/nginx/sites-available/msbot
```

Contenido:

```nginx
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuraciones SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    location /api/messages {
        proxy_pass https://127.0.0.1:3978;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Configuraciones para WebSocket si es necesario
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        return 301 https://tu-sitio-principal.com;
    }
}

# Redirección HTTP a HTTPS
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/msbot /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl restart nginx
```

## 📊 Monitoreo y Logging

### Configurar Logs

```bash
# Crear directorio de logs personalizado
sudo mkdir -p /var/log/msbot
sudo chown msbot:msbot /var/log/msbot

# Configurar rotación de logs
sudo nano /etc/logrotate.d/msbot
```

Contenido de rotación:

```
/var/log/msbot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 msbot msbot
    postrotate
        supervisorctl restart msbot
    endscript
}
```

### Script de Monitoreo de Salud

```bash
# Crear script de monitoreo
nano /home/msbot/msbot/scripts/health_monitor.py
```

Contenido:

```python
#!/usr/bin/env python3
"""
Health Monitor para MSBot
Monitorea la salud del bot y envía alertas si es necesario
"""

import time
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_bot_health():
    """Verificar salud del bot"""
    try:
        response = requests.get('https://localhost:3978/', verify=False, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def send_alert(message):
    """Enviar alerta por email (configurar según necesidades)"""
    # Implementar notificaciones según tus necesidades
    logger.warning(f"ALERT: {message}")

def main():
    """Bucle principal de monitoreo"""
    consecutive_failures = 0
    
    while True:
        if check_bot_health():
            logger.info("Bot is healthy")
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            logger.warning(f"Bot health check failed ({consecutive_failures}/3)")
            
            if consecutive_failures >= 3:
                send_alert(f"MSBot is down - {consecutive_failures} consecutive failures")
                consecutive_failures = 0  # Reset para evitar spam
        
        time.sleep(60)  # Check cada minuto

if __name__ == "__main__":
    main()
```

```bash
# Hacer ejecutable
chmod +x /home/msbot/msbot/scripts/health_monitor.py
```

## 🔄 Actualización y Mantenimiento

### Script de Actualización

```bash
# Crear script de actualización
nano /home/msbot/msbot/scripts/update.sh
```

Contenido:

```bash
#!/bin/bash
# Script de actualización de MSBot

set -e

echo "Iniciando actualización de MSBot..."

# Cambiar al directorio del bot
cd /home/msbot/msbot

# Hacer backup de configuración
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Detener bot
sudo supervisorctl stop msbot

# Actualizar código
git pull origin main

# Activar entorno virtual
source venv/bin/activate

# Actualizar dependencias
pip install -r requirements.txt

# Reiniciar bot
sudo supervisorctl start msbot

# Verificar que está funcionando
sleep 10
if sudo supervisorctl status msbot | grep -q "RUNNING"; then
    echo "✅ Actualización completada exitosamente"
else
    echo "❌ Error en la actualización, revisar logs"
    sudo supervisorctl status msbot
fi
```

```bash
# Hacer ejecutable
chmod +x /home/msbot/msbot/scripts/update.sh
```

### Backup Automático

```bash
# Crear script de backup
nano /home/msbot/msbot/scripts/backup.sh
```

Contenido:

```bash
#!/bin/bash
# Script de backup de MSBot

BACKUP_DIR="/home/msbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="msbot_backup_$DATE.tar.gz"

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Crear backup
cd /home/msbot
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude=msbot/venv \
    --exclude=msbot/.git \
    --exclude=msbot/__pycache__ \
    msbot/

echo "Backup creado: $BACKUP_DIR/$BACKUP_FILE"

# Limpiar backups antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "msbot_backup_*.tar.gz" -mtime +7 -delete
```

```bash
# Hacer ejecutable
chmod +x /home/msbot/msbot/scripts/backup.sh

# Programar backup diario
crontab -e
# Agregar línea:
# 0 2 * * * /home/msbot/msbot/scripts/backup.sh
```

## 🛡️ Seguridad Adicional

### Hardening del Servidor

```bash
# Deshabilitar root SSH
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Cambiar puerto SSH (opcional)
sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config

# Reiniciar SSH
sudo systemctl restart ssh

# Instalar fail2ban
sudo apt-get install fail2ban

# Configurar fail2ban
sudo nano /etc/fail2ban/jail.local
```

Configuración de fail2ban:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
```

### Configuración de Secrets

```bash
# Asegurar archivo .env
chmod 600 /home/msbot/msbot/.env
chown msbot:msbot /home/msbot/msbot/.env

# Configurar secrets en variables de entorno del sistema (opcional)
sudo nano /etc/environment
# Agregar:
# MSBOT_APP_ID=tu_app_id
# MSBOT_APP_PASSWORD=tu_password
```

## 📋 Checklist de Despliegue

### Pre-despliegue
- [ ] Servidor configurado con requisitos mínimos
- [ ] Dominio DNS apuntando al servidor
- [ ] Certificados SSL configurados
- [ ] Firewall configurado
- [ ] Variables de entorno configuradas
- [ ] Teams App configurada en Azure/Bot Framework

### Despliegue
- [ ] Código clonado y dependencias instaladas
- [ ] Supervisor configurado y funcionando
- [ ] Bot respondiendo en health check
- [ ] SSL/TLS funcionando correctamente
- [ ] Logs siendo generados correctamente

### Post-despliegue
- [ ] Bot responde en Microsoft Teams
- [ ] Monitoreo configurado
- [ ] Backups programados
- [ ] Documentación actualizada
- [ ] Equipo entrenado en mantenimiento

## 🚨 Solución de Problemas

### Bot No Inicia

```bash
# Verificar logs
sudo supervisorctl tail -f msbot

# Verificar configuración
cd /home/msbot/msbot
source venv/bin/activate
python -c "from app.config.settings import get_settings; print(get_settings().validate_bot_config())"

# Verificar permisos
ls -la /home/msbot/msbot/.env
ls -la /home/msbot/msbot/certs/
```

### Problemas de SSL

```bash
# Verificar certificados
openssl x509 -in /home/msbot/msbot/certs/cert.pem -text -noout

# Probar conexión SSL
openssl s_client -connect localhost:3978

# Verificar fecha de expiración
openssl x509 -in /home/msbot/msbot/certs/cert.pem -noout -dates
```

### Problemas de Red

```bash
# Verificar puertos abiertos
sudo netstat -tlnp | grep 3978

# Verificar firewall
sudo ufw status

# Probar conectividad externa
curl -k https://tu-dominio.com:3978/
```

## 📞 Soporte y Mantenimiento

### Comandos Útiles

```bash
# Estado de servicios
sudo supervisorctl status

# Reiniciar bot
sudo supervisorctl restart msbot

# Ver logs en tiempo real
sudo supervisorctl tail -f msbot

# Ver uso de recursos
htop
df -h
free -h

# Verificar conexiones de red
sudo netstat -ant | grep 3978
```

### Contactos de Emergencia

- **Administrador de Sistema**: [contacto]
- **Desarrollador Principal**: [contacto] 
- **Soporte Microsoft Teams**: [portal de soporte]

---

Con esta guía deberías poder desplegar MSBot exitosamente en tu servidor local, manteniendo la seguridad y confidencialidad de tus datos mientras proporcionas una interfaz robusta para tus sistemas RAG.