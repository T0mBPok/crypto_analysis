from src.ticker.model import Ticker
from dataclasses import asdict
from src.database import get_neo4j_session

class TickerDAO:    
    async def create_or_update(tickers: Ticker) -> list[Ticker]:
        async with get_neo4j_session() as session:
            query = """
            UNWIND $tickers as ticker_data
            MERGE (t:Ticker {symbol: ticker_data.symbol})
            ON CREATE SET 
                t.category = ticker_data.category,
                t.created_at = datetime(),
                t.updated_at = datetime()
            ON MATCH SET
                t.updated_at = datetime()
            RETURN t.symbol as symbol, 
                t.category as category,
                t.created_at as created_at,
                t.updated_at as updated_at
            """
            
            # Преобразуем список тикеров в список словарей
            tickers_data = [asdict(ticker) for ticker in tickers]
            result = await session.run(query, tickers=tickers_data)
            records = await result.data()
            
            return [Ticker.from_dict(record) for record in records]
    
    async def find_by_symbol(symbol: str) -> None | Ticker:
        async with get_neo4j_session() as session:
            query = """
            MATCH (t:Ticker {symbol: $symbol})
            RETURN t.symbol as symbol,
                   t.category as category,
                   t.created_at as created_at,
                   t.updated_at as updated_at
            """
            result = await session.run(query, symbol=symbol)
            record = await result.single()
            return Ticker.from_dict(record) if record else None
    
    async def find_all(limit: None | int = None) -> list[Ticker]:
        async with get_neo4j_session() as session:
            query = """
            MATCH (t:Ticker)
            RETURN t.symbol as symbol,
                t.category as category,
                t.created_at as created_at,
                t.updated_at as updated_at
            ORDER BY t.symbol
            """
            
            # Добавляем LIMIT только если limit задан
            if limit is not None:
                query += "\nLIMIT $limit"
                result = await session.run(query, limit=limit)
            else:
                result = await session.run(query)
                
            records = await result.data()
            return [Ticker.from_dict(record) for record in records]

    
    @classmethod
    async def delete(cls, symbol: str) -> bool:
        """Удаляет тикер и все связанные свечи"""
        async with get_neo4j_session() as session:
            query = """
            MATCH (t:Ticker {symbol: $symbol})
            DETACH DELETE t
            RETURN count(t) as deleted
            """
            result = await session.run(query, symbol=symbol)
            record = await result.single()
            # Исправление: сначала получаем значение, потом сравниваем
            deleted_count = record['deleted'] if record else 0
            return deleted_count > 0