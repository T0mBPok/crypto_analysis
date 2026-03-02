from src.correlation.model import Correlation
from dataclasses import asdict
from src.database import get_neo4j_session
from typing import List, Optional


class CorrelationDAO:
    async def create_or_update(correlation: Correlation) -> Correlation:
        """Создает или обновляет связь корреляции"""
        async with get_neo4j_session() as session:
            query = """
            MATCH (t1:Ticker {symbol: $symbol1})
            MATCH (t2:Ticker {symbol: $symbol2})
            MERGE (t1)-[r:CORRELATED_WITH]-(t2)
            SET r.pearson = $pearson,
                r.spearman = $spearman,
                r.returns_corr = $returns_corr,
                r.data_points = $data_points,
                r.calculated_at = datetime(),
                r.strength = CASE 
                    WHEN abs($pearson) > 0.7 THEN 'STRONG'
                    WHEN abs($pearson) > 0.4 THEN 'MODERATE'
                    ELSE 'WEAK'
                END
            RETURN t1.symbol as symbol1,
                   t2.symbol as symbol2,
                   r.pearson as pearson,
                   r.spearman as spearman,
                   r.returns_corr as returns_corr,
                   r.data_points as data_points,
                   r.calculated_at as calculated_at,
                   r.strength as strength
            """
            result = await session.run(query, **asdict(correlation))
            record = await result.single()
            
            return Correlation(
                symbol1=record['symbol1'],
                symbol2=record['symbol2'],
                pearson=record['pearson'],
                spearman=record['spearman'],
                returns_corr=record['returns_corr'],
                strength=record['strength'],
                calculated_at=record['calculated_at'],
                data_points=record['data_points']
            )
    
    async def find_by_symbol(symbol: str, threshold: float = 0.0) -> List[Correlation]:
        """Находит все корреляции для символа"""
        async with get_neo4j_session() as session:
            query = """
            MATCH (t1:Ticker {symbol: $symbol})-[r:CORRELATED_WITH]-(t2:Ticker)
            WHERE abs(r.pearson) >= $threshold
            RETURN t1.symbol as symbol1,
                   t2.symbol as symbol2,
                   r.pearson as pearson,
                   r.spearman as spearman,
                   r.returns_corr as returns_corr,
                   r.data_points as data_points,
                   r.calculated_at as calculated_at,
                   r.strength as strength
            ORDER BY abs(r.pearson) DESC
            """
            result = await session.run(query, symbol=symbol, threshold=threshold)
            records = await result.data()
            
            return [
                Correlation(
                    symbol1=record['symbol1'],
                    symbol2=record['symbol2'],
                    pearson=record['pearson'],
                    spearman=record['spearman'],
                    returns_corr=record['returns_corr'],
                    strength=record['strength'],
                    calculated_at=record['calculated_at'],
                    data_points=record['data_points']
                ) for record in records
            ]
    
    async def find_between(symbol1: str, symbol2: str) -> Optional[Correlation]:
        """Находит корреляцию между двумя символами"""
        async with get_neo4j_session() as session:
            query = """
            MATCH (t1:Ticker {symbol: $symbol1})-[r:CORRELATED_WITH]-(t2:Ticker {symbol: $symbol2})
            RETURN t1.symbol as symbol1,
                   t2.symbol as symbol2,
                   r.pearson as pearson,
                   r.spearman as spearman,
                   r.returns_corr as returns_corr,
                   r.data_points as data_points,
                   r.calculated_at as calculated_at,
                   r.strength as strength
            """
            result = await session.run(query, symbol1=symbol1, symbol2=symbol2)
            record = await result.single()
            
            if record:
                return Correlation(
                    symbol1=record['symbol1'],
                    symbol2=record['symbol2'],
                    pearson=record['pearson'],
                    spearman=record['spearman'],
                    returns_corr=record['returns_corr'],
                    strength=record['strength'],
                    calculated_at=record['calculated_at'],
                    data_points=record['data_points']
                )
            return None
    
    async def get_strong_correlations(threshold: float = 0.7) -> List[Correlation]:
        """Возвращает все сильные корреляции"""
        async with get_neo4j_session() as session:
            query = """
            MATCH (t1:Ticker)-[r:CORRELATED_WITH]-(t2:Ticker)
            WHERE abs(r.pearson) >= $threshold
              AND t1.symbol < t2.symbol
            RETURN t1.symbol as symbol1,
                   t2.symbol as symbol2,
                   r.pearson as pearson,
                   r.spearman as spearman,
                   r.returns_corr as returns_corr,
                   r.data_points as data_points,
                   r.calculated_at as calculated_at,
                   r.strength as strength
            ORDER BY abs(r.pearson) DESC
            """
            result = await session.run(query, threshold=threshold)
            records = await result.data()
            
            return [
                Correlation(
                    symbol1=record['symbol1'],
                    symbol2=record['symbol2'],
                    pearson=record['pearson'],
                    spearman=record['spearman'],
                    returns_corr=record['returns_corr'],
                    strength=record['strength'],
                    calculated_at=record['calculated_at'],
                    data_points=record['data_points']
                ) for record in records
            ]
    
    async def delete_between(symbol1: str, symbol2: str) -> bool:
        """Удаляет корреляцию между двумя символами"""
        async with get_neo4j_session() as session:
            query = """
            MATCH (t1:Ticker {symbol: $symbol1})-[r:CORRELATED_WITH]-(t2:Ticker {symbol: $symbol2})
            DELETE r
            RETURN count(r) as deleted
            """
            result = await session.run(query, symbol1=symbol1, symbol2=symbol2)
            record = await result.single()
            return record['deleted'] > 0
    
    async def delete_all_for_symbol(symbol: str) -> int:
        """Удаляет все корреляции для символа"""
        async with get_neo4j_session() as session:
            query = """
            MATCH (t:Ticker {symbol: $symbol})-[r:CORRELATED_WITH]-()
            DELETE r
            RETURN count(r) as deleted
            """
            result = await session.run(query, symbol=symbol)
            record = await result.single()
            return record['deleted']