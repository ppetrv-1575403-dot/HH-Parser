#!/usr/bin/env python3
"""Точка входа в приложение"""
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from app.init import create_app

from app.config import config

if __name__ == '__main__':
    # Определяем окружение
    env = 'production' if '--prod' in sys.argv else 'development'
    
    app = create_app(env)
    cfg = config.get(env, config['default'])
    
    print("=" * 50)
    print("🚀 HH.ru Parser Web Application")
    print("=" * 50)
    print(f"🌐 Environment: {env}")
    print(f"🔧 Debug mode: {cfg.DEBUG}")
    print(f"📍 URL: http://{cfg.HOST}:{cfg.PORT}")
    print("=" * 50)
    
    app.run(
        host=cfg.HOST,
        port=cfg.PORT,
        debug=cfg.DEBUG,
        threaded=True
    )