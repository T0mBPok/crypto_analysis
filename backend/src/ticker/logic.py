from src.ticker.dao import TickerDAO
from src.services.bybit import get_tickers
from src.ticker.model import Ticker


class TickerLogic(TickerDAO):
    async def pull_from_api(category: str, symbol: str) -> dict:
        return get_tickers(category=category, symbol=symbol)
    
    @classmethod
    async def add(cls, tickers: dict) -> dict:
        if not tickers:
            return {'ok': False, 'message': 'Не были выбраны тикеры для добавления!'}
        
        # Получаем все существующие тикеры из БД
        existing_tickers = await cls.find_all()
        existing_symbols = {t.symbol for t in existing_tickers}
        
        new_tickers = []
        category = tickers['category']
        for ticker_data in tickers['list']:
            symbol = ticker_data.get('symbol')
            
            # Проверяем, есть ли уже в БД
            if symbol and symbol not in existing_symbols:
                ticker = Ticker(
                    symbol=symbol,
                    category=category
                )
                new_tickers.append(ticker)
        
        # Добавляем новые тикеры в БД
        if new_tickers:
            added = await cls.create_or_update(new_tickers)
            return {'ok': True, 'message': "Выбранные тикеры были добавлены", 'added': added}
        
        return {'ok': True, "message": "Нет новых тикеров для добавления!"}