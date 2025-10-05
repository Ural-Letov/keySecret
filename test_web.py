#!/usr/bin/env python3
"""
Тест веб-приложения для проверки регистрации
"""

import sys
import os

def test_imports():
    """Проверяет импорты"""
    try:
        from web_app import app, add_user, check_user
        print("✅ Импорты работают")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_database():
    """Проверяет базу данных"""
    try:
        from web_app import add_user, check_user, DB_NAME
        import sqlite3
        
        # Проверяем подключение к БД
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ База данных доступна, пользователей: {count}")
        return True
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

def test_registration():
    """Тестирует регистрацию"""
    try:
        from web_app import add_user
        
        # Пробуем зарегистрировать тестового пользователя
        test_username = "test_web_user"
        test_password = "test123"
        
        # Удаляем пользователя если существует
        from web_app import DB_NAME
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (test_username,))
        conn.commit()
        conn.close()
        
        # Пробуем зарегистрировать
        result = add_user(test_username, test_password)
        
        if result:
            print("✅ Регистрация работает")
            
            # Проверяем вход
            from web_app import check_user
            user = check_user(test_username, test_password)
            if user:
                print("✅ Вход работает")
                return True
            else:
                print("❌ Вход не работает")
                return False
        else:
            print("❌ Регистрация не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование веб-приложения keySecret")
    print("=" * 50)
    
    tests = [
        ("Импорты", test_imports),
        ("База данных", test_database),
        ("Регистрация", test_registration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Тест: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ Тест '{test_name}' не прошел")
    
    print("\n" + "=" * 50)
    print(f"📊 Результат: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли! Веб-приложение готово к работе.")
        print("\n🚀 Для запуска выполните:")
        print("python web_app.py")
    else:
        print("❌ Некоторые тесты не прошли. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()
