from src.ticker.dao import TickerDAO
from src.services.bybit import get_tickers
from src.ticker.model import Ticker


class TickerLogic(TickerDAO):
    async def pull_from_api(category: str, symbol: str) -> dict:
        return get_tickers(category=category, symbol=symbol)
    
    @classmethod
    async def pull_from_api(cls, category: str, symbol: str) -> dict:
        from src.services.bybit import get_tickers
        return get_tickers(category=category, symbol=symbol)
    
    @classmethod
    async def add_tickers_with_api(cls, symbols: list[str], category: str = "spot") -> dict:
        if not symbols:
            return {'ok': False, 'message': 'Список тикеров пустой!'}
        
        # Получаем существующие
        existing_tickers = await cls.find_all()
        existing_symbols = {t.symbol for t in existing_tickers}
        
        new_tickers = []
        failed = []
        skipped = []
        
        for symbol in symbols:
            symbol = symbol.strip().upper()
            
            if not symbol or len(symbol) < 4:
                failed.append(symbol)
                continue
            
            if symbol in existing_symbols:
                skipped.append(symbol)
                continue
            
            try:
                ticker_data = await cls.pull_from_api(category, symbol)
                
                # ✅ Создаем Ticker ТОЛЬКО с полями модели
                ticker = Ticker(
                    symbol=symbol,
                    category=category
                )
                new_tickers.append(ticker)
                
            except Exception as e:
                failed.append(f"{symbol}: {str(e)[:50]}")
        
        # ✅ DAO ожидает list[Ticker]
        result = {'ok': True, 'added': 0, 'skipped': len(skipped), 'failed': len(failed)}
        
        if new_tickers:
            # ✅ Возвращает list[Ticker] или int?
            added_tickers = await cls.create_or_update(new_tickers)
            result['added'] = len(new_tickers)  # или len(added_tickers)
            result['new_symbols'] = [t.symbol for t in new_tickers]
        
        if skipped:
            result['skipped_symbols'] = skipped
        
        if failed:
            result['failed_symbols'] = failed
        
        return result
    
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