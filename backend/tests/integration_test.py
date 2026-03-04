# tests/integration_test.py
import asyncio
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

class IntegrationTest:
    """Полный интеграционный тест системы"""
    
    def __init__(self):
        self.base_url = "http://localhost:9000"
        self.test_tickers = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT"]
        self.results = {}
    
    async def test_full_flow(self):
        """Тестирование полного цикла работы"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            
            # 1. Проверка доступности
            print("\n1️⃣ Проверка доступности API...")
            async with session.get(f"{self.base_url}/health") as resp:
                assert resp.status == 200
                print("   ✅ API доступен")
            
            # 2. Добавление тикеров
            print("\n2️⃣ Добавление тестовых тикеров...")
            async with session.post(
                f"{self.base_url}/tickers/tickers/batch?category=spot",
                json=self.test_tickers
            ) as resp:
                assert resp.status == 200
                print(f"   ✅ Добавлено {len(self.test_tickers)} тикеров")
            
            # 3. Загрузка свечей
            print("\n3️⃣ Загрузка свечей...")
            for ticker in self.test_tickers[:3]:  # Тестируем первые 3
                async with session.post(
                    f"{self.base_url}/candles/{ticker}/batch/?category=spot&days=4&timeframe=60"
                ) as resp:
                    data = await resp.json()
                    print(f"   ✅ {ticker}: {data['created']} свечей")
            
            # 4. Расчет корреляций
            print("\n4️⃣ Расчет корреляций...")
            async with session.post(
                f"{self.base_url}/correlations/batch?timeframe=60&days=30",
                json=self.test_tickers
            ) as resp:
                data = await resp.json()
                print(f"   ✅ Рассчитано {len(data)} корреляций")
            
            # 5. Получение графа
            print("\n5️⃣ Получение графа...")
            async with session.get(f"{self.base_url}/graph/full?limit=50") as resp:
                data = await resp.json()
                print(f"   ✅ Граф: {len(data['nodes'])} узлов, {len(data['edges'])} ребер")
            
            # 6. Анализ сильных связей
            print("\n6️⃣ Анализ сильных связей...")
            async with session.get(f"{self.base_url}/correlations/all?strength=STRONG") as resp:
                strong = await resp.json()
                print(f"   ✅ Найдено {len(strong)} сильных связей")
                
                # Показываем топ-5
                for i, c in enumerate(strong[:5]):
                    print(f"      {i+1}. {c['symbol1']} - {c['symbol2']}: {c['pearson']:.3f}")
            
            # 7. Статистика
            print("\n7️⃣ Статистика системы:")
            async with session.get(f"{self.base_url}/correlations/all") as resp:
                all_corr = await resp.json()
                pearson_values = [c['pearson'] for c in all_corr]
                
                print(f"   📊 Всего корреляций: {len(all_corr)}")
                print(f"   📈 Средняя корреляция: {np.mean(pearson_values):.3f}")
                print(f"   📉 Медианная корреляция: {np.median(pearson_values):.3f}")
                print(f"   📊 Стандартное отклонение: {np.std(pearson_values):.3f}")
            
            # 8. Очистка (опционально)
            print("\n8️⃣ Очистка тестовых данных...")
            for ticker in self.test_tickers:
                async with session.delete(f"{self.base_url}/tickers/{ticker}/") as resp:
                    pass
            print("   ✅ Тестовые данные удалены")
            
            print("\n✨ Все интеграционные тесты пройдены успешно!")

async def run_integration_tests():
    test = IntegrationTest()
    await test.test_full_flow()

if __name__ == "__main__":
    asyncio.run(run_integration_tests())