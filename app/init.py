"""Инициализация Flask приложения"""
from flask import Flask
from loguru import logger
import sys
import os

from app.config import config

def create_app(config_name: str = 'default') -> Flask:
    """
    Фабрика создания Flask приложения
    
    Args:
        config_name: Имя конфигурации
    
    Returns:
        Flask приложение
    """
    # Настройка логирования
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="7 days",
        format="{time} | {level} | {name} - {message}",
        level="DEBUG"
    )
    
    # Создаем приложение
    #app = Flask(__name__, template_folder='../templates')
    project_root = os.path.dirname(__file__)
    static_path = os.path.join(project_root, '../static')
    app = Flask(__name__, template_folder = '../templates', static_folder = static_path)
    app.config.from_object(config.get(config_name, config['default']))
    
    # Регистрируем маршруты
    from app.routes import bp
    app.register_blueprint(bp)
    
    logger.info(f"Application started with {config_name} config")
    
    return app