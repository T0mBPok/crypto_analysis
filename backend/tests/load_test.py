# tests/load_test.py
import asyncio
import aiohttp
import time
from datetime import datetime
import pandas as pd

async def test_single_request(session, url):
    """Одиночный запрос"""
    start = time.time()
    try:
        async with session.get(url) as response:
            data = await response.json()
            return {
                'success': response.status == 200,
                'time': time.time() - start,
                'status': response.status
            }
    except:
        return {
            'success': False,
            'time': time.time() - start,
            'status': 0
        }

async def load_test_concurrent(url, num_requests=100, concurrency=10):
    """Нагрузочное тестирование"""
    print(f"\n🚀 Нагрузочное тестирование {url}")
    print(f"   Запросов: {num_requests}, одновременно: {concurrency}")
    
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_request():
            async with semaphore:
                return await test_single_request(session, url)
        
        tasks = [limited_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        # Анализ результатов
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        times = [r['time'] for r in successful]
        
        print(f"\n📊 Результаты:")
        print(f"   ✅ Успешно: {len(successful)}/{num_requests}")
        print(f"   ❌ Ошибок: {len(failed)}")
        if times:
            print(f"   ⚡ Среднее время: {sum(times)/len(times)*1000:.2f}мс")
            print(f"   📈 Мин время: {min(times)*1000:.2f}мс")
            print(f"   📉 Макс время: {max(times)*1000:.2f}мс")
            print(f"   📊 95-й перцентиль: {sorted(times)[int(len(times)*0.95)]*1000:.2f}мс")
        
        return results

async def run_all_load_tests():
    """Запуск всех нагрузочных тестов"""
    
    tests = [
        ("/tickers/", "Получение тикеров"),
        ("/correlations/all?limit=50", "Получение корреляций"),
        ("/graph/full?limit=50", "Получение графа"),
    ]
    
    results = {}
    
    for url, name in tests:
        base_url = "http://localhost:9000"
        result = await load_test_concurrent(f"{base_url}{url}", 50, 5)
        results[name] = result
        
        # Небольшая пауза между тестами
        await asyncio.sleep(1)
    
    # Сохраняем отчет
    report = ["# Отчет о нагрузочном тестировании\n"]
    report.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    for name, result in results.items():
        successful = [r for r in result if r['success']]
        times = [r['time'] for r in successful]
        
        report.append(f"## {name}\n")
        report.append(f"- Успешно: {len(successful)}/{len(result)}")
        if times:
            report.append(f"- Среднее время: {sum(times)/len(times)*1000:.2f}мс")
            report.append(f"- 95-й перцентиль: {sorted(times)[int(len(times)*0.95)]*1000:.2f}мс")
        report.append("")
    
    with open("load_test_report.md", "w") as f:
        f.write("\n".join(report))
    
    print("\n📄 Отчет сохранен в load_test_report.md")

if __name__ == "__main__":
    asyncio.run(run_all_load_tests())