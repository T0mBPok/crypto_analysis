from datetime import datetime
from dataclasses import dataclass

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