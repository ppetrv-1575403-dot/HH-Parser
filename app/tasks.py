"""Управление фоновыми задачами"""
import threading
import uuid
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.config import Config
from app.models import ParsingJob, ParsingRequest
from app.parser import HHParser

# Импорт для корректной работы
import re

class TaskManager:
    """Менеджер фоновых задач парсинга"""
    
    def __init__(self):
        self._jobs: Dict[str, ParsingJob] = {}
        self._parser = HHParser()
    
    def create_job(self, request: ParsingRequest) -> str:
        """
        Создание новой задачи парсинга
        
        Args:
            request: Параметры парсинга
        
        Returns:
            ID задачи
        """
        job_id = str(uuid.uuid4())[:8]
        job = ParsingJob(job_id=job_id)
        
        self._jobs[job_id] = job
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(
            target=self._run_parsing_task,
            args=(job_id, request),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Created parsing job: {job_id}")
        return job_id
    
    def _run_parsing_task(self, job_id: str, request: ParsingRequest) -> None:
        """
        Запуск задачи парсинга в фоне
        
        Args:
            job_id: ID задачи
            request: Параметры парсинга
        """
        job = self._jobs[job_id]
        job.status = 'running'
        
        try:
            # Запускаем парсинг
            vacancies = self._parser.search_vacancies(request)
            
            if not vacancies:
                job.status = 'error'
                job.error_message = 'Вакансии не найдены'
                logger.warning(f"No vacancies found for job {job_id}")
                return
            
            job.vacancies_count = len(vacancies)
            job.progress = 100
            
            # Сохраняем результат
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = re.sub(r'[^\w\-_]', '_', request.search_text)
            filename = f"hh_{safe_filename}_{timestamp}"
            
            if request.format == 'excel':
                filepath = Config.TEMP_DIR / f"{filename}.xlsx"
                self._parser.save_to_excel(vacancies, str(filepath))
            else:
                filepath = Config.TEMP_DIR / f"{filename}.csv"
                self._parser.save_to_csv(vacancies, str(filepath))
            
            job.result_file = str(filepath)
            job.status = 'completed'
            job.completed_at = datetime.now()
            
            logger.info(f"Job {job_id} completed: {len(vacancies)} vacancies")
            
        except Exception as e:
            job.status = 'error'
            job.error_message = str(e)
            logger.error(f"Job {job_id} failed: {e}")
    
    def get_job(self, job_id: str) -> Optional[ParsingJob]:
        """
        Получение информации о задаче
        
        Args:
            job_id: ID задачи
        
        Returns:
            Объект задачи или None
        """
        return self._jobs.get(job_id)
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> None:
        """
        Очистка старых временных файлов
        
        Args:
            max_age_hours: Максимальный возраст файлов в часах
        """
        import time
        now = time.time()
        
        for job in self._jobs.values():
            if job.result_file and job.completed_at:
                file_path = Path(job.result_file)
                if file_path.exists():
                    file_age_hours = (now - job.completed_at.timestamp()) / 3600
                    if file_age_hours > max_age_hours:
                        try:
                            file_path.unlink()
                            logger.info(f"Cleaned up old file: {job.result_file}")
                        except Exception as e:
                            logger.error(f"Failed to cleanup {job.result_file}: {e}")

# Глобальный экземпляр менеджера задач
task_manager = TaskManager()
