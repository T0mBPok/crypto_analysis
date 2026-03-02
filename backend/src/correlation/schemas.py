from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CorrelationBase(BaseModel):
    """Базовая схема корреляции"""
    symbol1: str = Field(..., description="Первый тикер", min_length=1)
    symbol2: str = Field(..., description="Второй тикер", min_length=1)
    pearson: float = Field(..., description="Корреляция Пирсона", ge=-1, le=1)
    spearman: float = Field(..., description="Корреляция Спирмена", ge=-1, le=1)
    returns_corr: float = Field(..., description="Корреляция доходностей", ge=-1, le=1)
    strength: str = Field("", description="Сила корреляции (STRONG/MODERATE/WEAK)")
    calculated_at: Optional[datetime] = Field(None, description="Время расчета")
    data_points: int = Field(0, description="Количество точек данных", ge=0)

class CorrelationCreate(CorrelationBase):
    """Схема для создания корреляции"""
    pass

class CorrelationUpdate(BaseModel):
    """Схема для обновления корреляции"""
    pearson: Optional[float] = Field(None, description="Корреляция Пирсона", ge=-1, le=1)
    spearman: Optional[float] = Field(None, description="Корреляция Спирмена", ge=-1, le=1)
    returns_corr: Optional[float] = Field(None, description="Корреляция доходностей", ge=-1, le=1)
    strength: Optional[str] = Field(None, description="Сила корреляции")
    data_points: Optional[int] = Field(None, description="Количество точек данных", ge=0)

class CorrelationResponse(CorrelationBase):
    """Схема для ответа API"""
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def pair(self) -> str:
        """Возвращает пару в формате symbol1-symbol2"""
        return f"{self.symbol1}-{self.symbol2}"