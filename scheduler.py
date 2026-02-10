"""
Scheduler para tareas automáticas
Ejecuta procesos a las 8am y 8pm
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """Programador de tareas automáticas"""
    
    def __init__(self, database):
        self.database = database
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self):
        """Inicia el scheduler con las tareas programadas"""
        if self.is_running:
            logger.warning("Scheduler ya está en ejecución")
            return
        
        # Importar aquí para evitar import circular
        from validators import ScheduledProcessor
        
        processor = ScheduledProcessor(self.database)
        
        # Tarea 1: Validación automática a las 8am
        self.scheduler.add_job(
            func=processor.proceso_automatico,
            trigger=CronTrigger(hour=8, minute=0),
            id='validacion_8am',
            name='Validación automática 8:00 AM',
            replace_existing=True
        )
        
        # Tarea 2: Validación automática a las 8pm
        self.scheduler.add_job(
            func=processor.proceso_automatico,
            trigger=CronTrigger(hour=20, minute=0),
            id='validacion_8pm',
            name='Validación automática 8:00 PM',
            replace_existing=True
        )
        
        # Tarea 3: Radicación de documentos validados (cada 2 horas)
        self.scheduler.add_job(
            func=processor.radicar_validados,
            trigger=CronTrigger(hour='*/2'),
            id='radicacion_periodica',
            name='Radicación periódica cada 2 horas',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Scheduler iniciado exitosamente")
        logger.info("Tareas programadas:")
        logger.info("  - Validación automática: 8:00 AM y 8:00 PM")
        logger.info("  - Radicación automática: Cada 2 horas")
    
    def stop(self):
        """Detiene el scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler detenido")
    
    def run_now(self, job_id):
        """Ejecuta una tarea inmediatamente"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.func()
            logger.info(f"Tarea '{job_id}' ejecutada manualmente")
            return True
        else:
            logger.error(f"Tarea '{job_id}' no encontrada")
            return False
    
    def get_jobs_status(self):
        """Obtiene el estado de todas las tareas"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs


# Instancia global del scheduler (se inicializa en app.py)
_scheduler_instance = None

def init_scheduler(database):
    """Inicializa el scheduler global"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler(database)
        _scheduler_instance.start()
    return _scheduler_instance

def get_scheduler():
    """Obtiene la instancia del scheduler"""
    return _scheduler_instance