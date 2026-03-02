from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from src.correlation.schemas import CorrelationResponse, CorrelationCreate
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
    """
    Рассчитывает корреляцию между двумя тикерами и сохраняет в Neo4j
    """
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


@router.get("/strong/all", response_model=List[CorrelationResponse])
async def get_strong_correlations(
    threshold: float = Query(0.7, ge=0, le=1, description="Порог силы корреляции")
):
    """
    Возвращает все сильные корреляции в базе
    """
    correlations = await CorrelationLogic.get_strong_correlations(threshold)
    return [CorrelationResponse.model_validate(c) for c in correlations]


@router.get("/find/with/{symbol}", response_model=List[dict])
async def find_correlated(
    symbol: str,
    threshold: float = Query(0.7, ge=0, le=1, description="Порог корреляции"),
    timeframe: int = Query(60, description="Таймфрейм в минутах"),
    days: int = Query(30, description="Количество дней для расчета"),
    recalculate: bool = Query(False, description="Пересчитать даже если есть в БД")
):
    """
    Находит тикеры, коррелирующие с заданным
    """
    try:
        results = await CorrelationLogic.find_correlated_with(
            symbol=symbol,
            threshold=threshold,
            timeframe=timeframe,
            days=days,
            recalculate=recalculate
        )
        return results
    except Exception as e:
        raise HTTPException(500, f"Ошибка при поиске корреляций: {e}")


@router.get("/matrix", response_model=dict)
async def get_correlation_matrix(
    symbols: str,
    timeframe: int = Query(60, description="Таймфрейм в минутах"),
    days: int = Query(30, description="Количество дней для расчета")
):
    """
    Возвращает матрицу корреляций для списка символов (символы через запятую)
    
    Пример: /correlations/matrix?symbols=BTCUSDT,ETHUSDT,SOLUSDT
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    if len(symbol_list) < 2:
        raise HTTPException(400, "Нужно минимум 2 символа для матрицы")
    
    try:
        matrix = await CorrelationLogic.get_correlation_matrix(
            symbols=symbol_list,
            category="spot",
            timeframe=timeframe,
            days=days
        )
        return matrix
    except Exception as e:
        raise HTTPException(500, f"Ошибка при построении матрицы: {e}")


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