from typing import List
from fastapi import APIRouter, HTTPException, Query
from src.ticker.schemas import TickerUpdate, TickerResponse, TickerBase
from src.ticker.logic import TickerLogic


router = APIRouter(prefix="/tickers", tags=["Tickers"])

@router.post("/")
async def create_tickers_batch(tickers: dict):
    return await TickerLogic.add(tickers=tickers)

@router.get('/bybit/')
async def get_from_api(category: str, symbol: str | None = None):
    return await TickerLogic.pull_from_api(category=category, symbol=symbol)

@router.post("/tickers/batch")
async def add_tickers_batch(
    request: list[str],  # ["BTCUSDT", "ETHUSDT"]
    category: str = Query("spot")
):
    result = await TickerLogic.add_tickers_with_api(request, category)
    return result

@router.get("/", response_model=List[TickerResponse])
async def get_all_tickers():
    tickers = await TickerLogic.find_all()
    return [TickerResponse.model_validate(t) for t in tickers]

@router.get("/{symbol}/", response_model=TickerResponse)
async def get_ticker(symbol: str):
    ticker = await TickerLogic.find_by_symbol(symbol)
    
    if not ticker:
        raise HTTPException(404, f"Ticker {symbol} not found")
    
    return TickerResponse.model_validate(ticker)

@router.put("/{symbol}/", response_model=TickerResponse)
async def update_ticker(symbol: str, data: TickerUpdate):    
    # Проверяем, существует ли тикер
    existing = await TickerLogic.find_by_symbol(symbol)
    if not existing:
        raise HTTPException(404, f"Ticker {symbol} not found")
    
    # Обновляем поля из data
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, "No fields to update")
    
    # Создаем обновленный объект
    from src.ticker.model import Ticker as TickerModel
    updated_model = TickerModel(
        symbol=symbol,
        category=update_data.get('category', existing.category)
    )
    updated = await TickerLogic.create_or_update(updated_model)
    return TickerResponse.model_validate(updated)

@router.delete("/{symbol}/")
async def delete_ticker(symbol: str):
    # Проверяем, существует ли
    existing = await TickerLogic.find_by_symbol(symbol)
    if not existing:
        raise HTTPException(404, f"Ticker {symbol} not found")
    
    # Удаляем
    deleted = await TickerLogic.delete(symbol)
    
    if not deleted:
        raise HTTPException(500, "Failed to delete ticker")
    
    return {"ok": True, "symbol": symbol}