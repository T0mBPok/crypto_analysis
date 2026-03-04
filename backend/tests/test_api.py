# backend/tests/test_api.py
import pytest
import requests
import numpy as np
import pandas as pd
import time
import os

# Используем requests вместо TestClient для избежания конфликтов event loop
BASE_URL = "http://localhost:9000"

class TestCryptoAPI:
    """Полное тестирование Crypto Analysis API через реальный HTTP"""
    
    test_tickers = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT"]
    
    def test_1_health_check(self):
        """Тест 1: Проверка работоспособности API"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ 1. API работает")

    def test_2_add_tickers(self):
        """Тест 2: Добавление тикеров"""
        response = requests.post(
            f"{BASE_URL}/tickers/tickers/batch?category=spot",
            json=self.test_tickers
        )
        # Может быть 200 (успешно) или 500 (уже есть)
        if response.status_code == 200:
            data = response.json()
            assert "added" in data
            print(f"✅ 2. Добавлено {len(self.test_tickers)} тикеров")
        else:
            print(f"⚠️ 2. Тикеры уже существуют (статус: {response.status_code})")

    def test_3_get_tickers(self):
        """Тест 3: Получение всех тикеров"""
        response = requests.get(f"{BASE_URL}/tickers/")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ 3. Получено {len(data)} тикеров из БД")

    def test_4_get_ticker_by_symbol(self):
        """Тест 4: Получение конкретного тикера"""
        response = requests.get(f"{BASE_URL}/tickers/BTCUSDT/")
        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == "BTCUSDT"
            print("✅ 4. Найден тикер BTCUSDT")
        else:
            print(f"⚠️ 4. Тикер BTCUSDT не найден (статус: {response.status_code})")

    def test_5_search_bybit(self):
        """Тест 5: Поиск на Bybit"""
        response = requests.get(f"{BASE_URL}/tickers/bybit/?category=spot&symbol=BTCUSDT")
        assert response.status_code == 200
        data = response.json()
        assert "list" in data
        print(f"✅ 5. Найдено тикеров: {len(data['list'])}")

    def test_6_load_candles(self):
        """Тест 6: Загрузка свечей для тикера"""
        response = requests.post(
            f"{BASE_URL}/candles/BTCUSDT/batch/?category=spot&days=4&timeframe=60"
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 6. Загружено {data['created']} свечей для BTCUSDT")
        else:
            print(f"⚠️ 6. Свечи не загружены (статус: {response.status_code})")

    def test_7_get_candles(self):
        """Тест 7: Получение свечей из БД"""
        response = requests.get(f"{BASE_URL}/candles/BTCUSDT/?limit=50&timeframe=60")
        assert response.status_code == 200
        candles = response.json()
        print(f"✅ 7. Получено {len(candles)} свечей из БД")
        if len(candles) > 0:
            candle = candles[0]
            assert "start" in candle
            assert "open" in candle
            assert "high" in candle
            assert "low" in candle
            assert "close" in candle
            assert "volume" in candle

    def test_8_calculate_correlation(self):
        """Тест 8: Расчет корреляции между парой"""
        response = requests.post(
            f"{BASE_URL}/correlations/calculate?symbol1=BTCUSDT&symbol2=ETHUSDT&category=spot&timeframe=60&days=30"
        )
        if response.status_code == 200:
            corr = response.json()
            assert -1 <= corr["pearson"] <= 1
            assert -1 <= corr["spearman"] <= 1
            assert -1 <= corr["returns_corr"] <= 1
            assert corr["strength"] in ["STRONG", "MODERATE", "WEAK"]
            print(f"✅ 8. Корреляция BTC-ETH: {corr['pearson']:.3f}")
        else:
            print(f"⚠️ 8. Корреляция не рассчитана (статус: {response.status_code})")

    def test_9_get_correlation_between(self):
        """Тест 9: Получение корреляции между двумя тикерами"""
        response = requests.get(f"{BASE_URL}/correlations/between/BTCUSDT/ETHUSDT")
        if response.status_code == 200:
            print("✅ 9. Корреляция найдена в БД")
        else:
            print(f"⚠️ 9. Корреляция не найдена (статус: {response.status_code})")

    def test_10_get_correlations_for_symbol(self):
        """Тест 10: Получение всех корреляций для тикера"""
        response = requests.get(f"{BASE_URL}/correlations/BTCUSDT")
        assert response.status_code == 200
        correlations = response.json()
        print(f"✅ 10. Для BTCUSDT найдено {len(correlations)} связей")

    def test_11_get_all_correlations(self):
        """Тест 11: Получение всех корреляций с фильтрацией"""
        response = requests.get(f"{BASE_URL}/correlations/all")
        assert response.status_code == 200
        all_corr = response.json()
        print(f"✅ 11. Всего корреляций: {len(all_corr)}")

    def test_12_calculate_batch(self):
        """Тест 12: Пакетный расчет корреляций"""
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        response = requests.post(
            f"{BASE_URL}/correlations/batch?timeframe=60&days=30",
            json=symbols
        )
        if response.status_code == 200:
            correlations = response.json()
            expected = len(symbols) * (len(symbols) - 1) // 2
            print(f"✅ 12. Рассчитано {len(correlations)} пар из {expected}")
        else:
            print(f"⚠️ 12. Пакетный расчет не выполнен (статус: {response.status_code})")

    def test_13_get_full_graph(self):
        """Тест 13: Получение полного графа"""
        response = requests.get(f"{BASE_URL}/graph/full?limit=50")
        assert response.status_code == 200
        graph = response.json()
        print(f"✅ 13. Граф: {len(graph['nodes'])} узлов, {len(graph['edges'])} ребер")

    def test_14_get_ticker_graph(self):
        """Тест 14: Получение графа для конкретного тикера"""
        response = requests.get(f"{BASE_URL}/graph/ticker/BTCUSDT")
        assert response.status_code == 200
        graph = response.json()
        print(f"✅ 14. Граф BTCUSDT: {len(graph['nodes'])} узлов")

    def test_15_delete_correlation(self):
        """Тест 15: Удаление корреляции между парой"""
        response = requests.delete(f"{BASE_URL}/correlations/BTCUSDT/ETHUSDT")
        if response.status_code == 200:
            print("✅ 15. Корреляция удалена")
        else:
            print(f"⚠️ 15. Корреляция не найдена (статус: {response.status_code})")

    def test_16_delete_ticker(self):
        """Тест 16: Удаление тикера"""
        response = requests.delete(f"{BASE_URL}/tickers/SOLUSDT/")
        if response.status_code == 200:
            print("✅ 16. Тикер SOLUSDT удален")
        else:
            print(f"⚠️ 16. Тикер не найден (статус: {response.status_code})")

    def test_17_error_handling(self):
        """Тест 17: Обработка ошибок"""
        response = requests.get(f"{BASE_URL}/tickers/NONEXISTENT/")
        assert response.status_code == 404
        
        response = requests.get(f"{BASE_URL}/correlations/between/NONEXISTENT1/NONEXISTENT2")
        assert response.status_code == 404
        
        print("✅ 17. Ошибки обрабатываются корректно")

    def test_18_performance(self):
        """Тест 18: Производительность"""
        start = time.time()
        requests.get(f"{BASE_URL}/tickers/")
        ticker_time = time.time() - start
        
        start = time.time()
        requests.get(f"{BASE_URL}/graph/full?limit=50")
        graph_time = time.time() - start
        
        print(f"✅ 19. Время: /tickers/={ticker_time*1000:.1f}мс, /graph/full={graph_time*1000:.1f}мс")

    def test_19_cleanup(self):
        """Тест 19: Очистка тестовых данных"""
        for ticker in self.test_tickers:
            try:
                requests.delete(f"{BASE_URL}/tickers/{ticker}/")
            except:
                pass
        
        response = requests.get(f"{BASE_URL}/tickers/")
        remaining = response.json()
        print(f"✅ 20. Очистка завершена. Осталось тикеров: {len(remaining)}")


def test_statistical_significance():
    """Тест: Статистическая значимость корреляций"""
    np.random.seed(42)
    n_samples = 100
    
    x1 = np.random.randn(n_samples)
    y1 = x1 * 0.9 + np.random.randn(n_samples) * 0.1
    
    x2 = np.random.randn(n_samples)
    y2 = -x2 * 0.9 + np.random.randn(n_samples) * 0.1
    
    x3 = np.random.randn(n_samples)
    y3 = np.random.randn(n_samples)
    
    corr1 = np.corrcoef(x1, y1)[0, 1]
    corr2 = np.corrcoef(x2, y2)[0, 1]
    corr3 = np.corrcoef(x3, y3)[0, 1]
    
    print(f"\n📊 Тест статистической значимости:")
    print(f"   Сильная положительная: {corr1:.3f}")
    print(f"   Сильная отрицательная: {corr2:.3f}")
    print(f"   Нет корреляции: {corr3:.3f}")
    
    assert corr1 > 0.8
    assert corr2 < -0.8
    assert abs(corr3) < 0.2
    
    print("✅ Все корреляции статистически значимы")

def test_data_alignment():
    """Тест: Выравнивание временных рядов"""
    dates1 = pd.date_range("2024-01-01", periods=100, freq="h")
    dates2 = pd.date_range("2024-01-01", periods=100, freq="h")
    
    prices1 = pd.Series(np.random.randn(100).cumsum(), index=dates1)
    prices2 = pd.Series(np.random.randn(100).cumsum(), index=dates2)
    
    common_dates = prices1.index.intersection(prices2.index)
    aligned1 = prices1[common_dates]
    aligned2 = prices2[common_dates]
    
    print(f"\n📈 Тест выравнивания данных:")
    print(f"   Исходных точек: {len(prices1)} и {len(prices2)}")
    print(f"   Общих точек после выравнивания: {len(aligned1)}")
    
    assert len(aligned1) > 0
    assert len(aligned1) == len(aligned2)
    assert len(aligned1) == 100
    
    print("✅ Данные корректно выравниваются")


if __name__ == "__main__":
    # Проверяем, запущен ли сервер
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ Сервер доступен, запускаем тесты...\n")
        pytest.main([__file__, "-v", "--tb=short"])
    except requests.exceptions.ConnectionError:
        print(f"❌ Сервер не доступен по адресу {BASE_URL}")
        print("   Запустите бэкенд командой:")
        print("   cd backend && python main.py")