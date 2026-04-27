"""Утилиты и вспомогательные функции"""
import re
from typing import Optional, List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests


def clean_html(text: Optional[str], max_length: int = 500) -> str:
    """
    Очистка HTML-тегов из текста
    
    Args:
        text: Исходный текст с HTML
        max_length: Максимальная длина результата
    
    Returns:
        Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем HTML-теги
    clean = re.sub(r'<[^>]+>', ' ', text)
    # Удаляем лишние пробелы и переносы
    clean = re.sub(r'\s+', ' ', clean)
    clean = clean.strip()
    
    # Обрезаем длинный текст
    if len(clean) > max_length:
        clean = clean[:max_length] + "..."
    
    return clean


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException)
)
def safe_request(url: str, params: Optional[dict] = None, timeout: int = 10) -> Optional[dict]:
    """
    Безопасный HTTP запрос с повторными попытками
    
    Args:
        url: URL запроса
        params: Параметры запроса
        timeout: Таймаут в секундах
    
    Returns:
        JSON ответ или None при ошибке
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise


def format_skills(skills: List[dict]) -> str:
    """
    Форматирование списка навыков
    
    Args:
        skills: Список навыков из API
    
    Returns:
        Строка с навыками через запятую
    """
    if not skills:
        return ""
    return ", ".join(skill.get('name', '') for skill in skills if skill.get('name'))


def get_area_id_by_name(city_name: str) -> Optional[int]:
    """
    Получение ID региона по названию города
    
    Args:
        city_name: Название города
    
    Returns:
        ID региона или None
    """
    from app.models import Region
    
    # Сначала ищем в предопределенном списке
    for region in Region.get_default_regions():
        if city_name.lower() in region.name.lower():
            return region.id
    
    # Если не нашли, делаем запрос к API
    try:
        url = "https://api.hh.ru/suggests/areas"
        response = requests.get(url, params={'text': city_name}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                return data['items'][0].get('id')
    except Exception as e:
        logger.warning(f"Failed to get area ID for {city_name}: {e}")
    
    return 113  # По умолчанию Россия