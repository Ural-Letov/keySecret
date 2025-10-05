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

def test_shared_key_visibility():
    """Ключ не выдаётся при pending и доступен после accept"""
    try:
        from init_db import DB_NAME, send_master_key_request, respond_to_request, get_shared_master_keys
        from web_app import add_user, check_user
        import sqlite3

        requester = "req_user"
        owner = "own_user"
        pwd = "test123"

        # Очистим пользователей и запросы
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM master_key_requests WHERE from_user=? OR to_user=?", (requester, requester))
        cur.execute("DELETE FROM master_key_requests WHERE from_user=? OR to_user=?", (owner, owner))
        cur.execute("DELETE FROM users WHERE username IN (?, ?)", (requester, owner))
        conn.commit()
        conn.close()

        # Создадим пользователей
        assert add_user(requester, pwd)
        assert add_user(owner, pwd)
        assert check_user(requester, pwd)
        assert check_user(owner, pwd)

        # Отправим запрос
        assert send_master_key_request(requester, owner)

        # Проверим: ключ скрыт (None)
        shared = get_shared_master_keys(requester)
        assert shared and shared[0][2] == 'pending'
        assert shared[0][1] is None

        # Найдём id запроса и примем его
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id FROM master_key_requests WHERE from_user=? AND to_user=? ORDER BY id DESC LIMIT 1", (requester, owner))
        req_id = cur.fetchone()[0]
        conn.close()
        respond_to_request(req_id, True)

        # Теперь ключ должен быть видим
        shared2 = get_shared_master_keys(requester)
        assert shared2 and shared2[0][2] == 'accepted'
        assert shared2[0][1] is not None

        print("✅ Видимость общего мастер-ключа работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки видимости ключа: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование веб-приложения keySecret")
    print("=" * 50)
    
    tests = [
        ("Импорты", test_imports),
        ("База данных", test_database),
        ("Регистрация", test_registration),
        ("Видимость общего мастер-ключа", test_shared_key_visibility)
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
