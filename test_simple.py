#!/usr/bin/env python3
"""
Простой тест веб-приложения
"""

def test_web_app():
    try:
        from web_app import app, add_user, check_user
        print("Импорты работают")
        
        # Тестируем регистрацию
        test_username = "test_user_123"
        test_password = "password123"
        
        # Удаляем тестового пользователя если существует
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
            print("Регистрация работает")
            
            # Проверяем вход
            user = check_user(test_username, test_password)
            if user:
                print("Вход работает")
                print("Веб-приложение готово к работе!")
                return True
            else:
                print("Вход не работает")
                return False
        else:
            print("Регистрация не работает")
            return False
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    test_web_app()
