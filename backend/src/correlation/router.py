from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from src.correlation.schemas import CorrelationResponse
from src.correlation.logic import CorrelationLogic


router = APIRouter(prefix="/correlations", tags=["Correlations"])

@router.post("/calculate", response_model=CorrelationResponse)
async def calculate_correlation(
    symbol1: str,
    symbol2: str,
    category: str,
    timeframe: int = Query(60, description="Таймфрейм в минутах"),
    days: int = Query(30, description="Количество дней для расчета")
):
    try:
        correlation = await CorrelationLogic.calculate_pair_correlation(
            symbol1=symbol1,
            symbol2=symbol2,
            category=category,
            timeframe=timeframe,
            days=days
        )
        return CorrelationResponse.model_validate(correlation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ошибка при расчете корреляции: {e}")

@router.post("/all-tickers")
async def calculate_all_tickers_correlations(
    category: str = Query("spot", description="Категория (spot/futures)"),
    timeframe: int = Query(60, description="Таймфрейм в минутах"),
    days: int = Query(30, description="Количество дней"),
    max_tickers: int = Query(50, description="Макс. количество тикеров (для perf)")
):
    """
    🧠 Рассчитывает корреляции для ВСЕХ тикеров в Neo4j БД!
    
    Запускает полный анализ графа криптовалют.
    Сохраняет все пары в Neo4j как отношения CORRELATED_WITH.
    
    ⚠️  Время: N*(N-1)/2 запросов (50 тикеров = ~1225 пар)
    """
    try:
        result = await CorrelationLogic.calculate_all_tickers_correlations(
            category=category,
            timeframe=timeframe,
            days=days,
            max_tickers=max_tickers
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"Ошибка полного анализа: {e}")

@router.post("/batch", response_model=List[CorrelationResponse])
async def calculate_batch(
    symbols: List[str],
    timeframe: int = Query(60, description="Таймфрейм в минутах"),
    days: int = Query(30, description="Количество дней для расчета")
):
    """
    Рассчитывает корреляции для всех пар из списка и сохраняет в Neo4j
    """
    if len(symbols) < 2:
        raise HTTPException(400, "Нужно минимум 2 символа для расчета")
    
    try:
        correlations = await CorrelationLogic.calculate_all_pairs(
            symbols=symbols,
            category="spot",
            timeframe=timeframe,
            days=days
        )
        return [CorrelationResponse.model_validate(c) for c in correlations]
    except Exception as e:
        raise HTTPException(500, f"Ошибка при пакетном расчете: {e}")

@router.get("/all", response_model=List[CorrelationResponse])
async def get_all_correlations(
    limit: Optional[int] = Query(None),
    threshold: float = Query(0.0, ge=0, le=1),
    strength: Optional[str] = Query(None, pattern="^(STRONG|MODERATE|WEAK)$"),
    sort_by: str = Query("pearson", pattern="^(pearson|data_points|calculated_at)$")
):
    correlations = await CorrelationLogic.get_all_correlations(
        limit=limit, threshold=threshold, strength_filter=strength,
        sort_by=sort_by
    )
    return [CorrelationResponse.model_validate(c) for c in correlations]

@router.get("/{symbol}", response_model=List[CorrelationResponse])
async def get_correlations_for_symbol(
    symbol: str,
    threshold: float = Query(0.0, ge=0, le=1, description="Минимальный порог корреляции")
):
    """
    Возвращает все корреляции для указанного тикера
    """
    correlations = await CorrelationLogic.find_by_symbol(symbol, threshold)
    return [CorrelationResponse.model_validate(c) for c in correlations]


@router.get("/between/{symbol1}/{symbol2}", response_model=CorrelationResponse)
async def get_correlation_between(
    symbol1: str,
    symbol2: str
):
    """
    Возвращает корреляцию между двумя конкретными тикерами
    """
    correlation = await CorrelationLogic.find_between(symbol1, symbol2)
    if not correlation:
        raise HTTPException(404, f"Корреляция между {symbol1} и {symbol2} не найдена")
    
    return CorrelationResponse.model_validate(correlation)

@router.delete("/{symbol1}/{symbol2}")
async def delete_correlation(
    symbol1: str,
    symbol2: str
):
    """
    Удаляет корреляцию между двумя тикерами
    """
    deleted = await CorrelationLogic.delete_between(symbol1, symbol2)
    if not deleted:
        raise HTTPException(404, f"Корреляция между {symbol1} и {symbol2} не найдена")
    
    return {"ok": True, "message": f"Корреляция {symbol1}-{symbol2} удалена"}


@router.delete("/all/{symbol}")
async def delete_all_correlations_for_symbol(
    symbol: str
):
    """
    Удаляет все корреляции для указанного тикера
    """
    deleted = await CorrelationLogic.delete_all_for_symbol(symbol)
    return {
        "ok": True,
        "symbol": symbol,
        "deleted_count": deleted,
        "message": f"Удалено {deleted} корреляций для {symbol}"
    }