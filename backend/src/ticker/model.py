from datetime import datetime
from dataclasses import dataclass
from neo4j.time import DateTime as Neo4jDateTime

@dataclass
class Ticker:
    symbol: str
    category: str = "spot"
    created_at: datetime = None
    updated_at: datetime = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создает модель из словаря"""
        def convert_datetime(value):
            if isinstance(value, Neo4jDateTime):
                return value.to_native()
            return value
        
        return cls(
            symbol=data.get('symbol'),
            category=data.get('category', 'spot'),
            created_at=convert_datetime(data.get('created_at')),
            updated_at=convert_datetime(data.get('updated_at'))
        )