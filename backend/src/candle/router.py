from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from src.candle.schemas import CandleResponse
from src.ticker.dao import TickerDAO
from src.candle.logic import CandleLogic


router = APIRouter(prefix="/candles", tags=["Candles"])

@router.post("/batch/all", response_model=dict)
async def pull_all_tickers_candles(
    category: str = Query("spot", pattern="^(spot|linear)$"),
    timeframe: int = Query(60, ge=1, le=1440),
    days: int = Query(4, ge=1, le=30),
    max_tickers: int = Query(50, ge=10, le=100),
    semaphore_limit: int = Query(10, ge=5, le=25, description="Параллельные запросы к API")
):
    result = await CandleLogic.pull_all_tickers_candles(
        category=category,
        timeframe=timeframe,
        days=days,
        max_tickers=max_tickers,
        semaphore_limit=semaphore_limit
    )
    return result

@router.get("/{symbol}/", response_model=list[CandleResponse])
async def get_candles(
    symbol: str,
    timeframe: int= 60,
    limit: int = Query(100, ge=1, le=1000),
    start_time: datetime = Query(None),
    end_time: datetime = Query(None)
):
    ticker = await TickerDAO.find_by_symbol(symbol)
    if not ticker:
        raise HTTPException(404, f"Ticker {symbol} not found")
    
    candles = await CandleLogic.find_by_symbol(
        symbol=symbol,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
        timeframe=timeframe
    )
    
    return [CandleResponse.model_validate(c) for c in candles]

@router.get("/{symbol}/latest/")
async def get_latest_candle_time(
    symbol: str,
    timeframe: int= 60
):
    ticker = await TickerDAO.find_by_symbol(symbol)
    if not ticker:
        raise HTTPException(404, f"Ticker {symbol} not found")
    
    latest = await CandleLogic.get_latest_start(symbol, timeframe)
    
    return {"symbol": symbol, "timeframe": timeframe, "latest_timestamp": latest}

@router.post("/{symbol}/batch/", response_model=dict)
async def create_candles_batch(
    category: str,
    symbol: str,
    days: int = 4,
    timeframe: int = 60
):    
    candles = await CandleLogic.pull_candles(category=category, symbol=symbol, days=days, timeframe=timeframe)
    created = await CandleLogic.create_batch(symbol, candles, timeframe)
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "created": created,
        "total_received": len(candles),
        "skipped": len(candles) - created
    }

@router.delete("/{symbol}/")
async def delete_candles(
    symbol: str,
    timeframe: int = Query(None),
    start_time: datetime = Query(None),
    end_time: datetime = Query(None),
):
    try:
        deleted = await CandleLogic.delete_candles(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            timeframe=timeframe
        )
        
        return {
            "ok": True,
            "symbol": symbol,
            "deleted_count": deleted,
            "timeframe": timeframe,
            "start_time": start_time,
            "end_time": end_time
        }
    except ValueError as e:
        raise HTTPException(404, str(e))