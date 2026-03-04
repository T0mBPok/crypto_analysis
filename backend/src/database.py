from neo4j import AsyncGraphDatabase
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from src.config import get_db_config


config = get_db_config()
neo4j_driver = AsyncGraphDatabase.driver(config['uri'], auth=(config['user'], config['pass']))

@asynccontextmanager
async def get_neo4j_session() -> AsyncGenerator:
    async with neo4j_driver.session() as session:
        try:
            yield session
        finally:
            await session.close()
            
async def init_neo4j_schema():
    async with get_neo4j_session() as session:
        # Уникальность символа
        await session.run(
            "CREATE CONSTRAINT ticker_symbol_unique IF NOT EXISTS "
            "FOR (t:Ticker) REQUIRE t.symbol IS UNIQUE"
        )
        
        # Индекс для быстрого поиска по символу
        await session.run(
            "CREATE INDEX ticker_symbol IF NOT EXISTS "
            "FOR (t:Ticker) ON (t.symbol)"
        )
        
        # 🔥 НОВЫЕ ИНДЕКСЫ ДЛЯ КОРРЕЛЯЦИЙ
        await session.run(
            "CREATE INDEX correlation_pearson IF NOT EXISTS "
            "FOR ()-[r:CORRELATED_WITH]-() ON (r.pearson)"
        )
        
        await session.run(
            "CREATE INDEX correlation_strength IF NOT EXISTS "
            "FOR ()-[r:CORRELATED_WITH]-() ON (r.strength)"
        )
        
        await session.run(
            "CREATE INDEX correlation_data_points IF NOT EXISTS "
            "FOR ()-[r:CORRELATED_WITH]-() ON (r.data_points)"
        )
        
        # Индекс для свечей по времени
        await session.run(
            "CREATE INDEX candle_timestamp IF NOT EXISTS "
            "FOR (c:Candle) ON (c.timestamp)"
        )
        
        print("✅ Neo4j schema initialized (все индексы созданы)")