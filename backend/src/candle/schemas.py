# src/candle/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CandleBase(BaseModel):
    """Базовая схема свечи - общие поля"""
    start: datetime = Field(..., description="Время начала свечи")
    open: float = Field(..., description="Цена открытия", ge=0)
    high: float = Field(..., description="Максимальная цена", ge=0)
    low: float = Field(..., description="Минимальная цена", ge=0)
    close: float = Field(..., description="Цена закрытия", ge=0)
    volume: float = Field(..., description="Объем торгов", ge=0)
    timeframe: int = Field(60, description="Таймфрейм (1h, 4h, 1d и т.д.)")

class CandleCreate(CandleBase):
    """Схема для создания свечи - все поля обязательные"""
    pass

class CandleUpdate(BaseModel):
    """Схема для обновления свечи - все поля опциональные"""
    open: Optional[float] = Field(None, description="Цена открытия", ge=0)
    high: Optional[float] = Field(None, description="Максимальная цена", ge=0)
    low: Optional[float] = Field(None, description="Минимальная цена", ge=0)
    close: Optional[float] = Field(None, description="Цена закрытия", ge=0)
    volume: Optional[float] = Field(None, description="Объем торгов", ge=0)
    timeframe: Optional[int] = Field(None, description="Таймфрейм")

class CandleResponse(CandleBase):
    """Схема для ответа API - добавляет служебные поля"""
    model_config = ConfigDict(from_attributes=True)
    
    # Можно добавить вычисляемые поля
    @property
    def price_change(self) -> float:
        """Изменение цены в процентах"""
        if self.open and self.open > 0:
            return ((self.close - self.open) / self.open) * 100
        return 0.0
    
    @property
    def is_bullish(self) -> bool:
        """Бычья свеча? (закрытие выше открытия)"""
        return self.close > self.open