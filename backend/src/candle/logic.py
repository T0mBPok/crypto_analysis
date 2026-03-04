import asyncio

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
    
    @classmethod
    async def pull_all_tickers_candles(
        cls,
        category: str = "spot",
        timeframe: int = 60,
        days: int = 4,
        max_tickers: int = 50,
        semaphore_limit: int = 15
    ) -> dict:
        # 1. Все тикеры
        all_tickers = await TickerDAO.find_all(limit=max_tickers)
        symbols = [t.symbol for t in all_tickers]
        
        semaphore = asyncio.Semaphore(semaphore_limit)
        all_results = []
        
        # 🔥 ФУНКЦИЯ-ОБРАБОТЧИК (максимальная параллельность)
        async def process_ticker(symbol: str):
            async with semaphore:
                try:
                    # Твоя pull_candles
                    candles = await cls.pull_candles(category, symbol, days, timeframe)
                    
                    # Сразу сохраняем
                    created = await cls.create_batch(symbol, candles, timeframe)
                    
                    return {
                        "symbol": symbol,
                        "candles_received": len(candles),
                        "candles_created": created,
                        "success": True
                    }
                except Exception as e:
                    return {
                        "symbol": symbol,
                        "success": False,
                        "error": str(e)
                    }
        
        # 🔥 ВСЕ ТИКЕРЫ ОДНОВРЕМЕННО! (не батчи, максимальная скорость)
        all_tasks = [process_ticker(symbol) for symbol in symbols]
        all_results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # 🔥 СТАТИСТИКА
        successful = [r for r in all_results if isinstance(r, dict) and r.get("success")]
        errors = [r for r in all_results if isinstance(r, dict) and not r.get("success")]
        
        total_created = sum(r["candles_created"] for r in successful)
        total_received = sum(r["candles_received"] for r in successful)
        
        print(f"✅ {len(successful)}/{len(symbols)} тикеров | {total_created} свечей")
        
        return {
            "status": "ultra_fast_update",
            "tickers_processed": len(symbols),
            "successful": len(successful),
            "errors": len(errors),
            "total_candles_created": total_created,
            "total_candles_received": total_received,
            "params": {
                "category": category,
                "timeframe": timeframe, 
                "days": days,
                "parallelism": semaphore_limit
            }
        }