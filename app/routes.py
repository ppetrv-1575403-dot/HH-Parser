"""Маршруты Flask приложения"""
from flask import Blueprint, render_template, request, jsonify, send_file
from loguru import logger
from pydantic import ValidationError
from pathlib import Path

from app.models import ParsingRequest, Region
from app.tasks import task_manager

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@bp.route('/api/start_parsing', methods=['POST'])
def start_parsing():
    """
    Запуск парсинга вакансий
    
    Ожидает JSON:
    {
        "search_text": "Python разработчик",
        "city": "Москва",
        "max_vacancies": 100,
        "experience": "between1And3",
        "salary": 100000,
        "format": "excel"
    }
    """
    try:
        # Валидируем входные данные
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        parsed_request = ParsingRequest(**data)
        
        # Создаем задачу
        job_id = task_manager.create_job(parsed_request)
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Парсинг запущен'
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({
            'error': 'Invalid request data',
            'details': e.errors()
        }), 400
        
    except Exception as e:
        logger.error(f"Error starting parsing: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/job_status/<job_id>')
def job_status(job_id: str):
    """Получение статуса задачи парсинга"""
    try:
        job = task_manager.get_job(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'status': job.status,
            'progress': job.progress,
            'total': job.total,
            'vacancies_count': job.vacancies_count,
            'error_message': job.error_message,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        })
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/download/<job_id>')
def download_file(job_id: str):
    """Скачивание результата парсинга"""
    try:
        job = task_manager.get_job(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if not job.result_file:
            return jsonify({'error': 'File not ready'}), 400
        
        file_path = Path(job.result_file)
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Определяем MIME тип
        if file_path.suffix == '.xlsx':
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'text/csv'
        
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=file_path.name
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/regions')
def get_regions():
    """Получение списка регионов для автодополнения"""
    query = request.args.get('q', '').lower()
    
    regions = Region.get_default_regions()
    
    if query:
        regions = [r for r in regions if query in r.name.lower()]
    
    return jsonify([{'id': r.id, 'name': r.name} for r in regions])


@bp.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Очистка временных файлов"""
    try:
        task_manager.cleanup_old_files()
        return jsonify({'success': True, 'message': 'Cleanup completed'})
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/health')
def health_check():
    """Проверка работоспособности"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })


@bp.errorhandler(404)
def not_found(error):
    """Обработка 404 ошибки"""
    return jsonify({'error': 'Not found'}), 404


@bp.errorhandler(500)
def internal_error(error):
    """Обработка 500 ошибки"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500