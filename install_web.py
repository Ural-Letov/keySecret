#!/usr/bin/env python3
"""
Скрипт для установки зависимостей веб-версии keySecret
"""

import subprocess
import sys
import os

def install_requirements():
    """Устанавливает зависимости из web_requirements.txt"""
    print("📦 Установка зависимостей для веб-версии keySecret...")
    print("=" * 60)
    
    try:
        # Проверяем наличие файла requirements
        if not os.path.exists('web_requirements.txt'):
            print("❌ Файл web_requirements.txt не найден!")
            return False
        
        # Устанавливаем зависимости
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'web_requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Зависимости успешно установлены!")
            return True
        else:
            print(f"❌ Ошибка при установке зависимостей:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Основная функция"""
    print("🔧 Установщик зависимостей keySecret Web")
    print("=" * 60)
    
    if install_requirements():
        print("\n🎉 Установка завершена!")
        print("Теперь вы можете запустить веб-приложение:")
        print("python web_app.py")
        print("или")
        print("python run_web.py")
    else:
        print("\n❌ Установка не удалась!")
        print("Попробуйте установить зависимости вручную:")
        print("pip install -r web_requirements.txt")

if __name__ == "__main__":
    main()
