from fastapi import HTTPException
from src.candle.dao import CandleDAO
from src.candle.model import Candle
from src.ticker.dao import TickerDAO
from src.services.bybit import get_kline


class CandleLogic(CandleDAO):
    async def pull_candles(category: str, symbol: str, days: int = 4, timeframe: int = 60):
        ticker = await TickerDAO.find_by_symbol(symbol)
        if not ticker:
            raise HTTPException(404, f"Ticker {symbol} not found")
        
        kline = get_kline(category=category, symbol=symbol, interval=timeframe, days=days)
                    
        def array_to_candle(arr):
            arr.append(timeframe)
            
            return Candle(
                start=float(arr[0]),
                open=float(arr[1]),
                high=float(arr[2]),
                low=float(arr[3]),
                close=float(arr[4]),
                volume=float(arr[5]),
                timeframe=timeframe
            )

        candles = list(map(array_to_candle, kline))
        return candles