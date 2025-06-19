#!/usr/bin/env python3
"""
MSBot Health Monitor
Monitorea la salud del bot y genera reportes de estado
"""

import time
import json
import requests
import logging
import argparse
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Estado de salud del bot"""
    timestamp: str
    is_healthy: bool
    response_time_ms: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    bot_info: Optional[Dict[str, Any]] = None

class HealthMonitor:
    """Monitor de salud para MSBot"""
    
    def __init__(self, 
                 base_url: str = "https://localhost:3978",
                 check_interval: int = 60,
                 alert_threshold: int = 3,
                 report_file: str = "health_report.json"):
        """
        Inicializar monitor de salud
        
        Args:
            base_url: URL base del bot
            check_interval: Intervalo entre checks en segundos
            alert_threshold: Número de fallos consecutivos antes de alerta
            report_file: Archivo para reportes de salud
        """
        self.base_url = base_url.rstrip('/')
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.report_file = Path(report_file)
        
        self.consecutive_failures = 0
        self.total_checks = 0
        self.total_failures = 0
        self.running = True
        
        # Histórico de estados (últimas 24 horas)
        self.health_history = []
        self.max_history = 24 * 60 // (check_interval // 60)  # Entradas por 24h
        
        # Configurar signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales para cierre limpio"""
        logger.info(f"Señal recibida ({signum}), cerrando monitor...")
        self.running = False
    
    def check_health(self) -> HealthStatus:
        """
        Verificar salud del bot
        
        Returns:
            Estado de salud
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # Verificar endpoint principal
            response = requests.get(
                f"{self.base_url}/",
                timeout=10,
                verify=False  # Para certificados auto-firmados en desarrollo
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Obtener información adicional del bot
                try:
                    status_response = requests.get(
                        f"{self.base_url}/api/status",
                        timeout=5,
                        verify=False
                    )
                    bot_info = status_response.json() if status_response.status_code == 200 else None
                except:
                    bot_info = None
                
                return HealthStatus(
                    timestamp=timestamp,
                    is_healthy=True,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    bot_info=bot_info
                )
            else:
                return HealthStatus(
                    timestamp=timestamp,
                    is_healthy=False,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                timestamp=timestamp,
                is_healthy=False,
                response_time_ms=response_time,
                error_message="Timeout"
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                timestamp=timestamp,
                is_healthy=False,
                response_time_ms=response_time,
                error_message="Connection Error"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                timestamp=timestamp,
                is_healthy=False,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def process_health_status(self, status: HealthStatus):
        """
        Procesar estado de salud y generar alertas si es necesario
        
        Args:
            status: Estado de salud
        """
        self.total_checks += 1
        
        # Agregar al histórico
        self.health_history.append(status)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        if status.is_healthy:
            if self.consecutive_failures > 0:
                logger.info(f"Bot recovered after {self.consecutive_failures} failures")
            self.consecutive_failures = 0
            logger.info(f"Bot healthy - response time: {status.response_time_ms:.1f}ms")
        else:
            self.consecutive_failures += 1
            self.total_failures += 1
            
            logger.warning(
                f"Bot unhealthy ({self.consecutive_failures}/{self.alert_threshold}) - "
                f"Error: {status.error_message}"
            )
            
            # Generar alerta si se alcanza el umbral
            if self.consecutive_failures >= self.alert_threshold:
                self._generate_alert(status)
    
    def _generate_alert(self, status: HealthStatus):
        """
        Generar alerta por bot inactivo
        
        Args:
            status: Estado de salud actual
        """
        alert_message = (
            f"🚨 ALERTA MSBot 🚨\n"
            f"El bot ha fallado {self.consecutive_failures} veces consecutivas\n"
            f"Último error: {status.error_message}\n"
            f"Timestamp: {status.timestamp}\n"
            f"URL: {self.base_url}\n"
        )
        
        logger.error(alert_message)
        
        # Aquí puedes agregar lógica para enviar alertas
        # Por ejemplo: email, Slack, webhook, etc.
        self._send_alert_notification(alert_message)
    
    def _send_alert_notification(self, message: str):
        """
        Enviar notificación de alerta
        Implementar según necesidades (email, Slack, etc.)
        
        Args:
            message: Mensaje de alerta
        """
        # Placeholder para implementación de notificaciones
        # Ejemplo: envío por email
        try:
            # import smtplib
            # from email.mime.text import MIMEText
            # ... implementar envío de email
            pass
        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generar reporte de salud
        
        Returns:
            Diccionario con reporte de salud
        """
        if not self.health_history:
            return {"error": "No hay datos de salud disponibles"}
        
        # Calcular métricas
        healthy_checks = sum(1 for h in self.health_history if h.is_healthy)
        total_in_history = len(self.health_history)
        uptime_percentage = (healthy_checks / total_in_history) * 100 if total_in_history > 0 else 0
        
        # Tiempo de respuesta promedio (solo checks exitosos)
        response_times = [h.response_time_ms for h in self.health_history if h.is_healthy]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Último estado
        last_status = self.health_history[-1]
        
        # Tiempo desde último fallo
        last_failure = None
        for status in reversed(self.health_history):
            if not status.is_healthy:
                last_failure = status.timestamp
                break
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_period_hours": self.max_history * (self.check_interval / 3600),
            "current_status": {
                "is_healthy": last_status.is_healthy,
                "last_check": last_status.timestamp,
                "response_time_ms": last_status.response_time_ms,
                "consecutive_failures": self.consecutive_failures
            },
            "statistics": {
                "total_checks": self.total_checks,
                "total_failures": self.total_failures,
                "uptime_percentage": round(uptime_percentage, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "checks_in_period": total_in_history,
                "healthy_checks_in_period": healthy_checks
            },
            "last_failure": last_failure,
            "bot_info": last_status.bot_info if last_status.is_healthy else None
        }
        
        return report
    
    def save_report(self):
        """Guardar reporte de salud en archivo"""
        try:
            report = self.generate_report()
            with open(self.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Reporte guardado en {self.report_file}")
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
    
    def print_status_summary(self):
        """Imprimir resumen de estado en consola"""
        if not self.health_history:
            print("No hay datos de salud disponibles")
            return
        
        report = self.generate_report()
        
        print("\n" + "="*50)
        print("📊 MSBot Health Monitor - Resumen")
        print("="*50)
        print(f"🕐 Último check: {report['current_status']['last_check']}")
        print(f"💚 Estado actual: {'Saludable' if report['current_status']['is_healthy'] else '❌ No saludable'}")
        print(f"⚡ Tiempo respuesta: {report['current_status']['response_time_ms']:.1f}ms")
        print(f"📈 Uptime: {report['statistics']['uptime_percentage']}%")
        print(f"🔢 Total checks: {report['statistics']['total_checks']}")
        print(f"❌ Total fallas: {report['statistics']['total_failures']}")
        
        if report['current_status']['consecutive_failures'] > 0:
            print(f"⚠️ Fallas consecutivas: {report['current_status']['consecutive_failures']}")
        
        print("="*50)
    
    def run(self):
        """Ejecutar monitor en bucle continuo"""
        logger.info(f"Iniciando health monitor para {self.base_url}")
        logger.info(f"Intervalo: {self.check_interval}s, Umbral alerta: {self.alert_threshold}")
        
        while self.running:
            try:
                # Verificar salud
                status = self.check_health()
                self.process_health_status(status)
                
                # Guardar reporte cada 10 checks
                if self.total_checks % 10 == 0:
                    self.save_report()
                
                # Mostrar resumen cada hora
                if self.total_checks % (3600 // self.check_interval) == 0:
                    self.print_status_summary()
                
                # Esperar siguiente check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor interrumpido por usuario")
                break
            except Exception as e:
                logger.error(f"Error en monitor: {e}")
                time.sleep(self.check_interval)
        
        # Guardar reporte final
        self.save_report()
        self.print_status_summary()
        logger.info("Health monitor terminado")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="MSBot Health Monitor")
    parser.add_argument("--url", default="https://localhost:3978", 
                       help="URL base del bot")
    parser.add_argument("--interval", type=int, default=60,
                       help="Intervalo entre checks en segundos")
    parser.add_argument("--threshold", type=int, default=3,
                       help="Número de fallos consecutivos para alerta")
    parser.add_argument("--report", default="health_report.json",
                       help="Archivo para reporte de salud")
    parser.add_argument("--single-check", action="store_true",
                       help="Ejecutar un solo check y salir")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(
        base_url=args.url,
        check_interval=args.interval,
        alert_threshold=args.threshold,
        report_file=args.report
    )
    
    if args.single_check:
        # Ejecutar un solo check
        status = monitor.check_health()
        print(json.dumps(asdict(status), indent=2))
        print(f"\nBot {'saludable' if status.is_healthy else 'no saludable'}")
        sys.exit(0 if status.is_healthy else 1)
    else:
        # Ejecutar monitor continuo
        monitor.run()

if __name__ == "__main__":
    main()