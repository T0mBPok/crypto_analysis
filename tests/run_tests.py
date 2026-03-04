# /home/t0mb/projects/crypto_analysis/tests/run_tests.py
import subprocess
import sys
from datetime import datetime
import os

def run_tests():
    """Запуск всех тестов и генерация единого отчета"""
    
    # Определяем пути
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # /home/t0mb/projects/crypto_analysis
    backend_dir = os.path.join(project_root, "backend")
    backend_tests_dir = os.path.join(backend_dir, "tests")
    
    # Добавляем backend в PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = backend_dir + ':' + env.get('PYTHONPATH', '')
    
    print("=" * 70)
    print("🧪 ЗАПУСК ВСЕХ ТЕСТОВ CRYPTO ANALYSIS")
    print("=" * 70)
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Проект: {project_root}")
    print(f"Бэкенд: {backend_dir}")
    print(f"Тесты бэкенда: {backend_tests_dir}")
    print("=" * 70)
    
    # Словарь для хранения результатов
    results = {
        'module': {'passed': False, 'output': '', 'error': ''},
        'integration': {'passed': False, 'output': '', 'error': ''},
        'load': {'passed': False, 'output': '', 'error': ''}
    }
    
    report = []
    report.append("# ОТЧЕТ О ТЕСТИРОВАНИИ CRYPTO ANALYSIS\n")
    report.append(f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 1. Модульные тесты
    report.append("## 1. Модульные тесты бэкенда\n")
    print("\n📦 Запуск модульных тестов...")
    
    module_result = subprocess.run(
        ["pytest", os.path.join(backend_tests_dir, "test_api.py"), "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env
    )
    
    results['module']['passed'] = module_result.returncode == 0
    results['module']['output'] = module_result.stdout
    results['module']['error'] = module_result.stderr
    
    if results['module']['passed']:
        report.append("✅ **Все модульные тесты пройдены**\n")
    else:
        report.append("❌ **Некоторые модульные тесты не пройдены**\n")
        report.append("```\n")
        report.append(module_result.stderr)
        report.append("```\n")
    
    report.append("### Детальный вывод:\n")
    report.append("```\n")
    report.append(module_result.stdout)
    report.append("```\n")
    
    # 2. Интеграционные тесты
    report.append("## 2. Интеграционные тесты\n")
    print("\n🔄 Запуск интеграционных тестов...")
    
    integration_result = subprocess.run(
        [sys.executable, os.path.join(backend_tests_dir, "integration_test.py")],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env
    )
    
    results['integration']['passed'] = "✨ Все интеграционные тесты пройдены" in integration_result.stdout
    results['integration']['output'] = integration_result.stdout
    results['integration']['error'] = integration_result.stderr
    
    if results['integration']['passed']:
        report.append("✅ **Все интеграционные тесты пройдены**\n")
    else:
        report.append("❌ **Интеграционные тесты не пройдены**\n")
        report.append("```\n")
        report.append(integration_result.stderr)
        report.append("```\n")
    
    report.append("### Вывод интеграционных тестов:\n")
    report.append("```\n")
    report.append(integration_result.stdout)
    report.append("```\n")
    
    # 3. Нагрузочные тесты
    report.append("## 3. Нагрузочное тестирование\n")
    print("\n⚡ Запуск нагрузочных тестов...")
    
    load_result = subprocess.run(
        [sys.executable, os.path.join(backend_tests_dir, "load_test.py")],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env
    )
    
    results['load']['passed'] = "✅ Успешно" in load_result.stdout
    results['load']['output'] = load_result.stdout
    results['load']['error'] = load_result.stderr
    
    # Парсим результаты нагрузочного тестирования
    if results['load']['passed']:
        report.append("Результаты нагрузочного тестирования:\n")
        report.append("```\n")
        # Извлекаем только результаты
        lines = load_result.stdout.split('\n')
        for line in lines:
            if any(x in line for x in ['📊', '⚡', '✅', '❌', '📈', '📉']):
                report.append(line + '\n')
        report.append("```\n")
    else:
        report.append("❌ Нагрузочные тесты не выполнены\n")
        report.append("```\n")
        report.append(load_result.stderr)
        report.append("```\n")
    
    # 4. Покрытие кода
    report.append("## 4. Статистика покрытия\n")
    print("\n📊 Запуск coverage...")
    
    subprocess.run(
        ["coverage", "run", "-m", "pytest", os.path.join(backend_tests_dir, "test_api.py")],
        cwd=project_root,
        env=env
    )
    coverage_result = subprocess.run(
        ["coverage", "report"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    report.append("```\n")
    report.append(coverage_result.stdout)
    report.append("```\n")
    
    # 5. Выводы и рекомендации
    report.append("## 5. Выводы и рекомендации\n")
    
    # Анализ результатов из словаря
    if results['module']['passed'] and results['integration']['passed']:
        report.append("✅ **Система работает стабильно**\n")
        report.append("\nРекомендации:\n")
        report.append("1. Регулярно запускать тесты при изменениях\n")
        report.append("2. Добавить больше тестов для граничных случаев\n")
        report.append("3. Рассмотреть возможность автоматизации тестирования в CI/CD\n")
    else:
        report.append("⚠️ **Требуется доработка**\n")
        report.append("\nНеобходимо:\n")
        if not results['module']['passed']:
            report.append("   • Исправить модульные тесты\n")
        if not results['integration']['passed']:
            report.append("   • Исправить интеграционные тесты\n")
        if not results['load']['passed']:
            report.append("   • Проверить нагрузочное тестирование\n")
        report.append("   • Проверить логи на наличие ошибок\n")
        report.append("   • Повторить тестирование после исправлений\n")
    
    # Сохраняем отчет в папку tests
    report_path = os.path.join(current_dir, "FULL_TEST_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("".join(report))
    
    print("\n" + "=" * 70)
    print(f"📄 Полный отчет сохранен в {report_path}")
    print("=" * 70)
    
    # Выводим краткую статистику из словаря
    print("\n📊 Краткая статистика:")
    print(f"   • Модульные тесты: {'✅' if results['module']['passed'] else '❌'}")
    print(f"   • Интеграционные тесты: {'✅' if results['integration']['passed'] else '❌'}")
    print(f"   • Нагрузочные тесты: {'✅' if results['load']['passed'] else '❌'}")
    print(f"   • Отчет: {report_path}")

if __name__ == "__main__":
    # Проверяем, запущен ли бэкенд
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 9000))
    if result != 0:
        print("\n⚠️  ВНИМАНИЕ: Бэкенд не запущен на порту 9000!")
        print("   Запустите бэкенд командой:")
        print("   cd /home/t0mb/projects/crypto_analysis/backend")
        print("   python main.py")
        print("\n   Или нажмите Ctrl+C для выхода")
        input("\nНажмите Enter чтобы продолжить тесты без бэкенда...")
    
    run_tests()