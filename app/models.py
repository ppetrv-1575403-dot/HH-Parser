"""Модели данных с валидацией"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, field_validator

class ExperienceLevel(str, Enum):
    """Уровни опыта работы"""
    NO_EXPERIENCE = "noExperience"
    BETWEEN_1_AND_3 = "between1And3"
    BETWEEN_3_AND_6 = "between3And6"
    MORE_THAN_6 = "moreThan6"
    
    @classmethod
    def get_display_name(cls, value: str) -> str:
        names = {
            cls.NO_EXPERIENCE: "Нет опыта",
            cls.BETWEEN_1_AND_3: "1-3 года",
            cls.BETWEEN_3_AND_6: "3-6 лет",
            cls.MORE_THAN_6: "более 6 лет"
        }
        return names.get(value, "Любой")


class Vacancy(BaseModel):
    """Модель вакансии"""
    id: str
    title: str = Field(alias='Название')
    company: str = Field(alias='Компания')
    city: str = Field(alias='Город')
    salary_from: Optional[int] = Field(None, alias='Зарплата от')
    salary_to: Optional[int] = Field(None, alias='Зарплата до')
    salary_currency: Optional[str] = Field(None, alias='Валюта')
    experience: str = Field(alias='Опыт работы')
    schedule: str = Field(alias='График')
    employment: str = Field(alias='Тип занятости')
    skills: str = Field(alias='Ключевые навыки')
    url: str = Field(alias='URL')
    published_at: str = Field(alias='Дата публикации')
    description: str = Field(alias='Описание', max_length=500)
    
    class Config:
        populate_by_name = True
    
    @property
    def salary_display(self) -> str:
        """Форматированное отображение зарплаты"""
        if self.salary_from and self.salary_to:
            return f"{self.salary_from:,} - {self.salary_to:,} {self.salary_currency or '₽'}"
        elif self.salary_from:
            return f"от {self.salary_from:,} {self.salary_currency or '₽'}"
        elif self.salary_to:
            return f"до {self.salary_to:,} {self.salary_currency or '₽'}"
        return "не указана"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для DataFrame"""
        return {
            'Название': self.title,
            'Компания': self.company,
            'Город': self.city,
            'Зарплата от': self.salary_from,
            'Зарплата до': self.salary_to,
            'Валюта': self.salary_currency,
            'Опыт работы': self.experience,
            'График': self.schedule,
            'Тип занятости': self.employment,
            'Ключевые навыки': self.skills,
            'URL': self.url,
            'Дата публикации': self.published_at,
            'Описание': self.description
        }


class ParsingRequest(BaseModel):
    """Модель запроса на парсинг"""
    search_text: str = Field(..., min_length=1, max_length=100)
    city: Optional[str] = Field(None, max_length=50)
    max_vacancies: int = Field(100, ge=1, le=2000)
    salary: Optional[int] = Field(None, ge=0)
    experience: Optional[ExperienceLevel] = None
    format: str = Field('excel', pattern='^(excel|csv)$')
    
    @field_validator('search_text')
    @classmethod
    def validate_search_text(cls, v: str) -> str:
        return v.strip()
    
    @field_validator('max_vacancies')
    @classmethod
    def validate_max_vacancies(cls, v: int) -> int:
        return min(v, 2000)


class ParsingJob(BaseModel):
    """Модель задачи парсинга"""
    job_id: str
    status: str = 'waiting'  # waiting, running, completed, error
    progress: int = 0
    total: int = 0
    result_file: Optional[str] = None
    error_message: Optional[str] = None
    vacancies_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Region:
    """Модель региона"""
    id: int
    name: str
    
    @classmethod
    def get_default_regions(cls) -> List['Region']:
        """Список основных регионов России"""
        return [
            cls(113, "Россия"),
            cls(1, "Москва"),
            cls(2, "Санкт-Петербург"),
            cls(66, "Екатеринбург"),
            cls(54, "Новосибирск"),
            cls(88, "Казань"),
            cls(61, "Нижний Новгород"),
            cls(72, "Самара"),
            cls(64, "Челябинск"),
            cls(147, "Ростов-на-Дону"),
            cls(48, "Воронеж"),
            cls(76, "Пермь"),
            cls(16, "Волгоград"),
            cls(43, "Краснодар"),
            cls(77, "Саратов"),
            cls(55, "Тюмень"),
            cls(99, "Уфа"),
            cls(53, "Омск"),
            cls(49, "Красноярск"),
        ]