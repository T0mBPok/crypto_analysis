from src.correlation.model import Correlation
from dataclasses import asdict
from src.database import get_neo4j_session
from typing import List, Optional
from neo4j.time import DateTime as Neo4jDateTime


class CorrelationDAO:
    @classmethod
    def _convert_record_to_correlation(cls, record: dict) -> Correlation:
        """Преобразует с защитой от NaN"""
        def convert_datetime(value):
            if isinstance(value, Neo4jDateTime):
                return value.to_native()
            return value
        
        def safe_float(value, default=0.0):
            """🔥 NaN/inf → 0.0"""
            if value is None or value != value:
                return default
            try:
                result = float(value)
                return result if -1.0 <= result <= 1.0 else default  
            except:
                return default
        
        return Correlation(
            symbol1=record['symbol1'],
            symbol2=record['symbol2'],
            pearson=safe_float(record['pearson']),
            spearman=safe_float(record['spearman']),      
            returns_corr=safe_float(record['returns_corr']), 
            strength=record.get('strength', 'WEAK'),
            calculated_at=convert_datetime(record.get('calculated_at')),
            data_points=record.get('data_points', 0)
        )
    
    @classmethod
    async def create_or_update(cls, correlation: Correlation) -> Correlation:
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
            # Преобразуем correlation в словарь, исключая None значения
            correlation_dict = {k: v for k, v in asdict(correlation).items() if v is not None}
            result = await session.run(query, **correlation_dict)
            record = await result.single()
            
            if record:
                return cls._convert_record_to_correlation(record)
            return None
    
    @classmethod
    async def find_by_symbol(cls, symbol: str, threshold: float = 0.0) -> List[Correlation]:
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
            
            return [cls._convert_record_to_correlation(record) for record in records]
    
    @classmethod
    async def get_all(
        cls,
        limit: Optional[int] = None,
        threshold: float = 0.0,
        strength_filter: Optional[str] = None,
        sort_by: str = "pearson"
    ) -> List[Correlation]:
        async with get_neo4j_session() as session:
            query = """
            MATCH (t1:Ticker)-[r:CORRELATED_WITH]-(t2:Ticker)
            WHERE t1.symbol < t2.symbol
            AND abs(r.pearson) >= $threshold
            """
            
            if strength_filter:
                query += f" AND r.strength = '{strength_filter.upper()}'"
            
            order_field = "abs(r.pearson)" if sort_by == "pearson" else f"r.{sort_by}"
            query += f"\nORDER BY {order_field} DESC"
            
            if limit is not None:
                query += "\nLIMIT $limit"
            
            query += """
            RETURN t1.symbol as symbol1,
                t2.symbol as symbol2,
                coalesce(r.pearson, 0.0) as pearson,
                coalesce(r.spearman, 0.0) as spearman,
                coalesce(r.returns_corr, 0.0) as returns_corr,
                coalesce(r.strength, 'WEAK') as strength,
                coalesce(r.data_points, 0) as data_points,
                r.calculated_at as calculated_at
            """
            
            params = {"threshold": threshold}
            if limit is not None:
                params["limit"] = limit
            
            result = await session.run(query, **params)
            records = await result.data()
            return [cls._convert_record_to_correlation(record) for record in records]
    
    @classmethod
    async def find_between(cls, symbol1: str, symbol2: str) -> Optional[Correlation]:
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
                return cls._convert_record_to_correlation(record)
            return None
    
    @classmethod
    async def get_strong_correlations(cls, threshold: float = 0.7) -> List[Correlation]:
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
            
            return [cls._convert_record_to_correlation(record) for record in records]
    
    @classmethod
    async def delete_between(cls, symbol1: str, symbol2: str) -> bool:
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
    
    @classmethod
    async def delete_all_for_symbol(cls, symbol: str) -> int:
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