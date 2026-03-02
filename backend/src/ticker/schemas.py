from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class TickerBase(BaseModel):
    """Базовая схема тикера"""
    symbol: str | None = Field(..., description="Торговый символ", min_length=1, example="BTCUSDT")
    category: str = Field("spot", description="Категория рынка (spot/linear/inverse)")

class TickerCreate(TickerBase):
    """Схема для создания тикера"""
    pass

class TickerUpdate(BaseModel):
    """Схема для обновления тикера"""
    category: Optional[str] = Field(None, description="Категория рынка")

class TickerResponse(TickerBase):
    """Схема для ответа API"""
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def display_name(self) -> str:
        """Возвращает имя для отображения (если есть name, иначе symbol)"""
        return self.name if self.name else self.symbol