#!/usr/bin/env python3
"""
Запуск веб-приложения с отладкой
"""

import os
import sys

def main():
    print("Запуск веб-приложения keySecret...")
    print("=" * 50)
    
    # Проверяем наличие файлов
    required_files = ['web_app.py', 'templates', 'static']
    for file in required_files:
        if not os.path.exists(file):
            print(f"ОШИБКА: Файл/папка {file} не найден!")
            return
    
    print("Все файлы найдены")
    
    # Проверяем зависимости
    try:
        import flask
        import cryptography
        import bcrypt
        print("Зависимости установлены")
    except ImportError as e:
        print(f"ОШИБКА: Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r web_requirements.txt")
        return
    
    print("Веб-приложение будет доступно по адресу: http://localhost:5000")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Запускаем приложение
        from web_app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nПриложение остановлено")
    except Exception as e:
        print(f"Ошибка при запуске: {e}")

if __name__ == "__main__":
    main()
