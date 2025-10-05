#!/usr/bin/env python3
"""
Скрипт для запуска веб-версии keySecret
"""

import os
import sys
import subprocess

def check_dependencies():
    """Проверяет установлены ли необходимые зависимости"""
    try:
        import flask
        import cryptography
        import bcrypt
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите зависимости командой: pip install -r web_requirements.txt")
        return False

def main():
    """Основная функция запуска"""
    print("🚀 Запуск веб-версии keySecret...")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    # Проверяем наличие основного файла
    if not os.path.exists('web_app.py'):
        print("❌ Файл web_app.py не найден!")
        sys.exit(1)
    
    print("🌐 Веб-приложение будет доступно по адресу: http://localhost:5000")
    print("📝 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Запускаем Flask приложение
        from web_app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
