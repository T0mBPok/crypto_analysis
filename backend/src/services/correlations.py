import numpy as np
from scipy import stats

def calculate_correlation(prices1: list, prices2: list):
    if prices1 == None or prices2 == None:
        raise Exception("Ошибка подлкючения к API")
    
    # 1 Пирсон
    pearson = np.corrcoef(prices1, prices2)[0, 1]
    
    # 2 Спирмен (проверка на нелинейность)
    spearman = stats.spearmanr(prices1, prices2)[0]
    
    # 3 Корреляция доходностей
    returns1 = np.diff(prices1) / prices1[:-1]
    returns2 = np.diff(prices2) / prices2[:-1]
    returns_corr = np.corrcoef(returns1, returns2)[0, 1]
    
    return {
        'price_correlation': pearson,
        'rank_correlation': spearman,
        'returns_correlation': returns_corr
    }
    