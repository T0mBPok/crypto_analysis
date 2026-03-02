from dataclasses import asdict
from src.candle.model import Candle
from datetime import datetime
from src.database import get_neo4j_session


class CandleDAO: 
    async def create(symbol: str, candle: Candle) -> Candle:
        async with get_neo4j_session() as session:
            query = """
            MATCH (t:Ticker {symbol: $symbol})
            CREATE (t)-[:HAS_CANDLE]->(c:Candle {
                start: $start,
                open: $open,
                high: $high,
                low: $low,
                close: $close,
                volume: $volume,
                timeframe: $timeframe,
                created_at: datetime()
            })
            RETURN c.start as start,
                   c.close as close,
                   c.open as open,
                   c.high as high,
                   c.low as low,
                   c.volume as volume,
                   c.timeframe as timeframe
            """
            result = await session.run(query, symbol=symbol, **asdict(candle))
            return Candle.from_dict(await result.single())
    
    async def find_by_symbol(symbol: str, limit: int = 100,  
                      start_time: datetime = None, 
                      timeframe: int = 60,
                      end_time: datetime = None) -> list[Candle]:
        # Находит свечи для тикера с фильтрацией
        async with get_neo4j_session() as session:
            query = """
            MATCH (t:Ticker {symbol: $symbol})-[:HAS_CANDLE]->(c:Candle)
            WHERE c.timeframe = $timeframe
              AND ($start_time IS NULL OR c.start >= $start_time)
              AND ($end_time IS NULL OR c.start <= $end_time)
            RETURN c.start as start,
                   c.close as close,
                   c.open as open,
                   c.high as high,
                   c.low as low,
                   c.volume as volume,
                   c.timeframe as timeframe
            ORDER BY c.start DESC
            LIMIT $limit
            """
            result = await session.run(
                query, 
                symbol=symbol,
                limit=limit,
                start_time=start_time,
                end_time=end_time,
                timeframe=timeframe
            )
            records = await result.data()
            return [Candle.from_dict(record) for record in records]
    
    async def get_latest_start(symbol: str, timeframe: int = 60) -> None | datetime:
        # Возвращает start последней свечи для определенного timeframe
        async with get_neo4j_session() as session:
            query = """
            MATCH (t:Ticker {symbol: $symbol})-[:HAS_CANDLE]->(c:Candle)
            WHERE c.timeframe = $timeframe
            RETURN max(c.start) as last_start
            """
            result = await session.run(query, symbol=symbol, timeframe=timeframe)
            return (await result.single())['last_start']
    
    @classmethod
    async def create_batch(cls, symbol: str, candles: list[Candle], timeframe: int = 60) -> int:
        # Создает несколько свечей за раз
        if not candles:
            return 0
        
        async with get_neo4j_session() as session:
            last_start = await cls.get_latest_start(symbol, timeframe)
            
            if last_start is None:
                new_candles = candles
            else:
                new_candles = [c for c in candles if c.start > last_start]
            
            if not new_candles:
                return 0
            
            # Создаем транзакцию для всех свечей
            query = """
            UNWIND $candles as candle
            MATCH (t:Ticker {symbol: $symbol})
            CREATE (t)-[:HAS_CANDLE]->(c:Candle {
                start: candle.start,
                open: candle.open,
                high: candle.high,
                low: candle.low,
                close: candle.close,
                volume: candle.volume,
                timeframe: $timeframe,
                created_at: datetime()
            })
            RETURN count(c) as created
            """
            
            candles_data = [
                {
                    'start': c.start.isoformat() if hasattr(c.start, 'isoformat') else c.start,
                    'open': c.open,
                    'high': c.high,
                    'low': c.low,
                    'close': c.close,
                    'volume': c.volume
                }
                for c in new_candles
            ]
            
            result = await session.run(query, symbol=symbol, candles=candles_data, timeframe=timeframe)
            return (await result.single())['created']
        
    @classmethod 
    async def delete_candles(
        cls,
        symbol: str, 
        start_time: None | datetime = None,
        end_time: None | datetime = None,
        timeframe: None | str = None
    ) -> int:
        
        # Проверка существования монеты
        ticker = await cls.ticker_dao.find_by_symbol(symbol)
        if ticker is None:
            error_msg = f"Тикер с символом '{symbol}' не существует в базе данных"
            raise ValueError(error_msg)
        
        # Формируем условия запроса
        where_conditions = ["c: Candle"]
        params = {'symbol': symbol}
        
        # Добавляем фильтр по символу через связь
        match_clause = "MATCH (t:Ticker {symbol: $symbol})-[r:HAS_CANDLE]->(c:Candle)"
        
        # Добавляем фильтр по timeframe если указан
        if timeframe is not None:
            where_conditions.append("c.timeframe = $timeframe")
            params['timeframe'] = timeframe
        
        # Добавляем фильтр по времени начала если указан
        if start_time is not None:
            where_conditions.append("c.start >= $start_time")
            params['start_time'] = start_time
        
        # Добавляем фильтр по времени конца если указан
        if end_time is not None:
            where_conditions.append("c.start <= $end_time")
            params['end_time'] = end_time
        
        # Формируем WHERE часть запроса
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"  # если условий нет, удаляем все
        
        # Полный запрос
        query = f"""
        {match_clause}
        WHERE {where_clause}
        DETACH DELETE c
        RETURN count(c) as deleted_count
        """
        
        # Выполняем удаление
        async with get_neo4j_session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            deleted = record['deleted_count'] if record else 0
            
            return deleted