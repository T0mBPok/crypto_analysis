from pybit.unified_trading import HTTP
from pybit.exceptions import FailedRequestError


session = HTTP()

def get_tickers(category: str, symbol: str = None, session = session):
    try:
        tickers = session.get_tickers(category=category, symbol=symbol)['result']
        return(tickers)
    except FailedRequestError as e:
        print(e)
        return None
    
def get_kline(category: str, symbol: str, interval: int = 60, days: int = 4, session=session):
    try:
        candles = session.get_kline(category=category, symbol=symbol, interval=interval, limit=min(days*24, 1000))['result']['list']
        return(candles)
    except FailedRequestError as e:
        print(e)
        return None