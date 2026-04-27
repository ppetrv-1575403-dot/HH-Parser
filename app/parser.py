"""Парсер вакансий с hh.ru"""
import time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
import pandas as pd

from app.config import Config
from app.models import Vacancy, ParsingRequest, ExperienceLevel
from app.utils import safe_request, clean_html, format_skills, get_area_id_by_name


class HHParser:
    """Парсер вакансий с hh.ru"""
    
    def __init__(self):
        self.base_url = "https://api.hh.ru"
        self.session_requests = 0
    
    def _build_search_params(
        self, 
        search_text: str, 
        area: int,
        page: int,
        per_page: int,
        experience: Optional[ExperienceLevel] = None,
        salary: Optional[int] = None
    ) -> Dict[str, Any]:
        """Формирование параметров поиска"""
        params = {
            'text': search_text,
            'area': area,
            'per_page': min(per_page, Config.VACANCIES_PER_PAGE),
            'page': page
        }
        
        if experience:
            params['experience'] = experience.value
        
        if salary:
            params['salary'] = salary
            params['only_with_salary'] = True
        
        return params
    
    def _get_vacancy_details(self, vacancy_id: str) -> Optional[Vacancy]:
        """
        Получение детальной информации о вакансии
        
        Args:
            vacancy_id: ID вакансии
        
        Returns:
            Объект Vacancy или None
        """
        try:
            data = safe_request(f"{self.base_url}/vacancies/{vacancy_id}")
            if not data:
                return None
            
            # Получаем информацию о зарплате
            salary_info = data.get('salary', {})
            salary_from = salary_info.get('from')
            salary_to = salary_info.get('to')
            salary_currency = salary_info.get('currency')
            
            # Собираем навыки
            skills = format_skills(data.get('key_skills', []))
            
            # Создаем объект вакансии
            vacancy = Vacancy(
                id=vacancy_id,
                title=data.get('name', ''),
                company=data.get('employer', {}).get('name', ''),
                city=data.get('area', {}).get('name', ''),
                salary_from=salary_from,
                salary_to=salary_to,
                salary_currency=salary_currency,
                experience=data.get('experience', {}).get('name', ''),
                schedule=data.get('schedule', {}).get('name', ''),
                employment=data.get('employment', {}).get('name', ''),
                skills=skills,
                url=data.get('alternate_url', ''),
                published_at=data.get('published_at', '')[:10] if data.get('published_at') else '',
                description=clean_html(data.get('description', ''), max_length=500)
            )
            
            return vacancy
            
        except Exception as e:
            logger.error(f"Failed to get details for vacancy {vacancy_id}: {e}")
            return None
    
    def _get_vacancies_batch(
        self, 
        params: Dict[str, Any], 
        max_vacancies: int
    ) -> List[str]:
        """
        Получение списка ID вакансий с одной страницы
        
        Args:
            params: Параметры поиска
            max_vacancies: Максимальное количество вакансий
        
        Returns:
            Список ID вакансий
        """
        try:
            data = safe_request(f"{self.base_url}/vacancies", params=params)
            if not data:
                return []
            
            # Получаем список ID вакансий
            vacancies = [item['id'] for item in data.get('items', [])]
            
            # Обновляем общее количество при первом запросе
            if 'total' not in params:
                params['total_found'] = min(data.get('found', 0), max_vacancies)
                params['pages'] = min(data.get('pages', 1), Config.MAX_PAGES)
                
                logger.info(f"Found {params['total_found']} vacancies, {params['pages']} pages")
            
            return vacancies
            
        except Exception as e:
            logger.error(f"Failed to fetch vacancies batch: {e}")
            return []
    
    def search_vacancies(self, request: ParsingRequest) -> List[Vacancy]:
        """
        Поиск вакансий по параметрам
        
        Args:
            request: Объект с параметрами поиска
        
        Returns:
            Список вакансий
        """
        logger.info(f"Starting parsing for: {request.search_text}")
        
        # Определяем ID региона
        area_id = get_area_id_by_name(request.city) if request.city else 113
        logger.info(f"Area ID: {area_id}")
        
        vacancies = []
        page = 0
        total_found = 0
        total_pages = 1
        
        # Определяем количество вакансий на страницу
        per_page = min(Config.VACANCIES_PER_PAGE, request.max_vacancies)
        
        while page < total_pages and len(vacancies) < request.max_vacancies:
            # Формируем параметры для текущей страницы
            params = self._build_search_params(
                search_text=request.search_text,
                area=area_id,
                page=page,
                per_page=per_page,
                experience=request.experience,
                salary=request.salary
            )
            
            try:
                # Получаем список ID вакансий
                data = safe_request(f"{self.base_url}/vacancies", params=params)
                if not data:
                    break
                
                # Устанавливаем общее количество при первом запросе
                if page == 0:
                    total_found = min(data.get('found', 0), request.max_vacancies)
                    total_pages = min(data.get('pages', 1), Config.MAX_PAGES)
                    logger.info(f"Will parse {total_found} vacancies from {total_pages} pages")
                
                # Получаем детали вакансий
                vacancy_ids = [item['id'] for item in data.get('items', [])]
                
                # Используем ThreadPoolExecutor для параллельного получения деталей
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_id = {
                        executor.submit(self._get_vacancy_details, v_id): v_id 
                        for v_id in vacancy_ids
                    }
                    
                    for future in as_completed(future_to_id):
                        vacancy = future.result()
                        if vacancy and len(vacancies) < request.max_vacancies:
                            vacancies.append(vacancy)
                            logger.debug(f"Added vacancy: {vacancy.title}")
                
                logger.info(f"Page {page + 1}/{total_pages} completed. Total: {len(vacancies)}")
                page += 1
                
                # Задержка между страницами
                if page < total_pages:
                    time.sleep(Config.PAGE_DELAY)
                
            except Exception as e:
                logger.error(f"Error parsing page {page}: {e}")
                break
        
        logger.info(f"Parsing completed. Found {len(vacancies)} vacancies")
        return vacancies[:request.max_vacancies]
    
    def save_to_excel(self, vacancies: List[Vacancy], filename: str) -> str:
        """
        Сохранение вакансий в Excel файл
        
        Args:
            vacancies: Список вакансий
            filename: Имя файла
        
        Returns:
            Путь к сохраненному файлу
        """
        if not vacancies:
            raise ValueError("No vacancies to save")
        
        # Конвертируем в DataFrame
        data = [v.to_dict() for v in vacancies]
        df = pd.DataFrame(data)
        
        # Сохраняем с форматированием
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Вакансии', index=False)
            
            # Настраиваем ширину колонок
            worksheet = writer.sheets['Вакансии']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Saved {len(vacancies)} vacancies to {filename}")
        return filename
    
    def save_to_csv(self, vacancies: List[Vacancy], filename: str) -> str:
        """
        Сохранение вакансий в CSV файл
        
        Args:
            vacancies: Список вакансий
            filename: Имя файла
        
        Returns:
            Путь к сохраненному файлу
        """
        if not vacancies:
            raise ValueError("No vacancies to save")
        
        data = [v.to_dict() for v in vacancies]
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        logger.info(f"Saved {len(vacancies)} vacancies to {filename}")
        return filename