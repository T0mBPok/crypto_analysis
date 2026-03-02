from fastapi import HTTPException
from datetime import datetime
from typing import List, Dict
from neo4j.time import DateTime as Neo4jDateTime
from src.candle.logic import CandleLogic
from src.ticker.logic import TickerLogic
from src.correlation.dao import CorrelationDAO
from src.correlation.model import Correlation
from src.services.correlations import calculate_correlation


class CorrelationLogic(CorrelationDAO):
    
    def convert_neo4j_datetime(value):
        """Преобразует Neo4j DateTime в Python datetime"""
        if isinstance(value, Neo4jDateTime):
            return value.to_native()
        return value

    @classmethod
    async def _get_prices_for_calculation(
        cls,
        symbol: str,
        category: str,
        timeframe: int = 60,
        days: int = 30
    ) -> List[float]:
        """
        Внутренний метод для получения цен закрытия из свечей
        Использует существующие методы CandleLogic
        """
        # Пробуем получить свечи из БД через CandleLogic.find_by_symbol (унаследован от CandleDAO)
        candles = await CandleLogic.find_by_symbol(
            symbol=symbol,
            timeframe=timeframe,
            limit=days * 24
        )
        
        # Если данных мало, подгружаем через CandleLogic.pull_candles
        if len(candles) < 20:
            candles = await CandleLogic.pull_candles(
                category=category,
                symbol=symbol,
                days=days,
                timeframe=timeframe
            )
        
        # Сортируем по возрастанию (старые -> новые) для корректного расчета
        candles.sort(key=lambda x: x.start)
        
        return [c.close for c in candles]
    
    @classmethod
    async def calculate_pair_correlation(
        cls,
        symbol1: str,
        symbol2: str,
        category: str,
        timeframe: int = 60,
        days: int = 30
    ) -> Correlation:
        """
        Рассчитывает корреляцию между двумя тикерами и сохраняет в Neo4j
        """
        # Проверяем существование тикеров через TickerLogic
        ticker1 = await TickerLogic.find_by_symbol(symbol1)
        if not ticker1:
            raise HTTPException(404, f"Ticker {symbol1} not found in Neo4j")
        
        ticker2 = await TickerLogic.find_by_symbol(symbol2)
        if not ticker2:
            raise HTTPException(404, f"Ticker {symbol2} not found in Neo4j")
        
        # Получаем цены через внутренний метод
        prices1 = await cls._get_prices_for_calculation(symbol1, category, timeframe, days)
        prices2 = await cls._get_prices_for_calculation(symbol2, category, timeframe, days)
        
        if len(prices1) < 20 or len(prices2) < 20:
            raise HTTPException(
                400,
                f"Недостаточно данных: {symbol1}={len(prices1)}, {symbol2}={len(prices2)}"
            )
        
        # Выравниваем длины (берем минимальную)
        min_len = min(len(prices1), len(prices2))
        prices1 = prices1[-min_len:]  # берем последние N
        prices2 = prices2[-min_len:]
        
        # Используем готовую функцию calculate_correlation
        try:
            result = calculate_correlation(
                prices1=prices1,
                prices2=prices2
            )
            
            pearson = result['price_correlation']
            spearman = result['rank_correlation']
            returns_corr = result['returns_correlation']
            
        except Exception as e:
            raise HTTPException(500, f"Ошибка при расчете корреляции: {e}")
        
        # Определяем силу для Neo4j
        abs_pearson = abs(pearson)
        if abs_pearson > 0.7:
            strength = "STRONG"
        elif abs_pearson > 0.4:
            strength = "MODERATE"
        else:
            strength = "WEAK"
        
        # Создаем объект корреляции для Neo4j
        correlation = Correlation(
            symbol1=symbol1,
            symbol2=symbol2,
            pearson=pearson,
            spearman=spearman,
            returns_corr=returns_corr,
            strength=strength,
            calculated_at=datetime.now(),
            data_points=min_len
        )
        
        # Сохраняем в Neo4j через унаследованный метод DAO
        saved = await cls.create_or_update(correlation)
        if saved and saved.calculated_at:
            saved.calculated_at = cls.convert_neo4j_datetime(saved.calculated_at)
        
        return saved
    
    @classmethod
    async def calculate_all_pairs(
        cls,
        symbols: List[str],
        category: str = "spot",
        timeframe: int = 60,
        days: int = 30
    ) -> List[Correlation]:
        """
        Рассчитывает корреляции для всех пар из списка и сохраняет в Neo4j
        """
        results = []
        total_pairs = len(symbols) * (len(symbols) - 1) // 2
        current = 1
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]
                
                print(f"[{current}/{total_pairs}] 📊 {symbol1} - {symbol2}")
                
                try:
                    correlation = await cls.calculate_pair_correlation(
                        symbol1=symbol1,
                        symbol2=symbol2,
                        category=category,
                        timeframe=timeframe,
                        days=days
                    )
                    results.append(correlation)
                    print(f"   ✅ {correlation.pearson:.3f} ({correlation.strength}) - сохранено в Neo4j")
                    
                except Exception as e:
                    print(f"   ❌ Ошибка: {e}")
                
                current += 1
        
        return results
    
    @classmethod
    async def find_correlated_with(
        cls,
        symbol: str,
        threshold: float = 0.7,
        timeframe: int = 60,
        days: int = 30,
        recalculate: bool = False
    ) -> List[Dict]:
        """
        Находит тикеры, коррелирующие с заданным (из Neo4j или пересчитывает)
        """
        if not recalculate:
            # Пробуем найти в Neo4j через унаследованный метод DAO
            existing = await cls.find_by_symbol(symbol, threshold)
            if existing:
                return [
                    {
                        "symbol": c.symbol2 if c.symbol1 == symbol else c.symbol1,
                        "pearson": c.pearson,
                        "spearman": c.spearman,
                        "returns_corr": c.returns_corr,
                        "strength": c.strength,
                        "calculated_at": c.calculated_at,
                        "data_points": c.data_points
                    }
                    for c in existing
                ]
        
        # Если нет в Neo4j или нужен пересчет - получаем все тикеры из Neo4j через TickerLogic
        all_tickers = await TickerLogic.find_all()
        other_symbols = [t.symbol for t in all_tickers if t.symbol != symbol]
        
        results = []
        for other in other_symbols:
            try:
                corr = await cls.calculate_pair_correlation(
                    symbol1=symbol,
                    symbol2=other,
                    timeframe=timeframe,
                    days=days
                )
                if abs(corr.pearson) >= threshold:
                    results.append({
                        "symbol": other,
                        "pearson": corr.pearson,
                        "spearman": corr.spearman,
                        "returns_corr": corr.returns_corr,
                        "strength": corr.strength,
                        "calculated_at": corr.calculated_at,
                        "data_points": corr.data_points
                    })
            except Exception as e:
                print(f"Ошибка при расчете {symbol}-{other}: {e}")
        
        # Сортируем по силе
        results.sort(key=lambda x: abs(x["pearson"]), reverse=True)
        return results
    
    @classmethod
    async def get_correlation_matrix(
        cls,
        symbols: List[str],
        category: str = "spot",
        timeframe: int = 60,
        days: int = 30
    ) -> Dict:
        """
        Возвращает матрицу корреляций для списка символов (из Neo4j)
        """
        results = {}
        
        # Рассчитываем все пары и сохраняем в Neo4j
        correlations = await cls.calculate_all_pairs(
            symbols=symbols,
            category=category,
            timeframe=timeframe,
            days=days
        )
        
        # Строим матрицу
        for c in correlations:
            key = f"{c.symbol1}-{c.symbol2}"
            results[key] = {
                "pearson": c.pearson,
                "spearman": c.spearman,
                "returns_corr": c.returns_corr,
                "strength": c.strength,
                "data_points": c.data_points
            }
        
        return {
            "symbols": symbols,
            "pairs": results,
            "count": len(results),
            "database": "neo4j"
        }