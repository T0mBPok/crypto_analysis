from datetime import datetime
from dataclasses import dataclass
from neo4j.time import DateTime as Neo4jDateTime

@dataclass
class Correlation:
    symbol1: str
    symbol2: str
    pearson: float
    spearman: float
    returns_corr: float
    strength: str = ""
    calculated_at: datetime = None
    data_points: int = 0
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создает модель из словаря с преобразованием Neo4j DateTime"""
        def convert_datetime(value):
            if isinstance(value, Neo4jDateTime):
                return value.to_native()
            return value
        
        return cls(
            symbol1=data.get('symbol1'),
            symbol2=data.get('symbol2'),
            pearson=data.get('pearson', 0.0),
            spearman=data.get('spearman', 0.0),
            returns_corr=data.get('returns_corr', 0.0),
            strength=data.get('strength', ''),
            calculated_at=convert_datetime(data.get('calculated_at')),
            data_points=data.get('data_points', 0)
        )