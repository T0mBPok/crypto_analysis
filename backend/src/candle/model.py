from dataclasses import dataclass
from datetime import datetime

@dataclass
class Candle:
    start: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: int = 60
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            start=data.get('start'),
            open=float(data.get('open', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            close=float(data.get('close', 0)),
            volume=float(data.get('volume', 0)),
            timeframe=data.get('timeframe', 60)
        )