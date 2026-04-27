"""Конфигурация приложения"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Базовые настройки"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Пути
    BASE_DIR = Path(__file__).parent.parent
    TEMP_DIR = BASE_DIR / 'temp_downloads'
    TEMP_DIR.mkdir(exist_ok=True)
    
    # Настройки парсера
    MAX_VACANCIES = 2000
    DEFAULT_VACANCIES = 100
    REQUEST_TIMEOUT = 10
    REQUEST_DELAY = 0.2  # секунд между запросами
    PAGE_DELAY = 0.5  # секунд между страницами
    
    # Flask
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5000))
    
    # Ограничения
    MAX_PAGES = 20  # API ограничивает 20 страницами
    VACANCIES_PER_PAGE = 100
    
    # User-Agent
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


class DevelopmentConfig(Config):
    """Настройки для разработки"""
    DEBUG = True


class ProductionConfig(Config):
    """Настройки для продакшена"""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}