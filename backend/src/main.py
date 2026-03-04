from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_swagger_ui_theme import setup_swagger_ui_theme
import uvicorn
from contextlib import asynccontextmanager

from src.config import settings
from src.database import init_neo4j_schema, neo4j_driver
from src.exceptions import TokenExpiredException, TokenNoFoundException
from src.ticker.router import router as tickers_router
from src.candle.router import router as candles_router
from src.correlation.router import router as correlations_router
from src.graph.router import router as graph_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения:
    - При старте: инициализация схемы Neo4j (индексы и constraints)
    - При остановке: закрытие соединения с Neo4j
    """
    # Startup
    print("🚀 Инициализация Crypto Analysis API...")
    print(f"📊 Подключение к Neo4j: {settings.DB_HOST}:{settings.DB_PORT}")
    await init_neo4j_schema()
    print("✅ Neo4j schema initialized")
    yield
    # Shutdown
    print("👋 Завершение работы...")
    await neo4j_driver.close()
    print("✅ Neo4j connection closed")


app = FastAPI(
    title='Crypto Analysis',
    description='API для анализа корреляций криптовалют с Neo4j',
    version='1.0.0',
    lifespan=lifespan,
    docs_url=None
)

setup_swagger_ui_theme(app, docs_path="/docs")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:5174"  
    ], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
    allow_origin_regex="http://localhost:\\d+"
)

# Подключаем роутеры
app.include_router(tickers_router)
app.include_router(candles_router)
app.include_router(correlations_router)
app.include_router(graph_router)


# Обработчики исключений
@app.exception_handler(TokenExpiredException)
async def token_expired_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(TokenNoFoundException)
async def token_no_found_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работоспособности"""
    return {
        "app": "Crypto Analysis",
        "version": "1.0.0",
        "status": "running",
        "database": {
            "type": "Neo4j",
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "name": settings.DB_NAME
        }
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем подключение к Neo4j
        await neo4j_driver.verify_connectivity()
        return {
            "status": "healthy", 
            "database": "connected",
            "app_port": settings.APP_PORT
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "database": "disconnected", 
                "error": str(e)
            }
        )


if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = settings.APP_PORT
    
    print(f"🚀 Запуск сервера на {HOST}:{PORT}")
    print(f"📚 Документация: http://{HOST}:{PORT}/docs")
    print(f"🔍 Neo4j: {settings.DB_HOST}:{settings.DB_PORT}")
    
    uvicorn.run(
        'src.main:app', 
        host=HOST, 
        port=PORT, 
        reload=True
    )