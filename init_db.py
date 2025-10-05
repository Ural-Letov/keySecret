import sqlite3
import secrets
import hashlib
import base64
from cryptography.fernet import Fernet, InvalidToken
import bcrypt
import os

def _resolve_db_path() -> str:
    """Возвращает абсолютный путь к users.db, корректный и при запуске из .py, и из PyInstaller .exe.

    - В режиме PyInstaller (атрибут sys._MEIPASS) кладем БД рядом с исполняемым файлом.
    - В обычном режиме — рядом с исходниками (корень проекта).
    """
    # Определяем базовую директорию: рядом с исполняемым файлом/скриптом
    base_dir = os.path.dirname(os.path.abspath(getattr(__import__('__main__'), '__file__', __file__)))
    return os.path.join(base_dir, 'users.db')

DB_NAME = _resolve_db_path()



def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        master_key TEXT UNIQUE NOT NULL
    )
    ''')
    conn.commit()
    conn.close()


def create_wallets_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        login TEXT NOT NULL,
        password TEXT NOT NULL,
        host TEXT NOT NULL,
        mk_name TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()



def get_fernet_key(master_key: str) -> Fernet:
    digest = hashlib.sha256(master_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_data(data: str, master_key: str) -> str:
    f = get_fernet_key(master_key)
    return f.encrypt(data.encode()).decode()


def decrypt_data(token: str, master_key: str) -> str:
    f = get_fernet_key(master_key)
    return f.decrypt(token.encode()).decode()



def generate_master_key():
    return secrets.token_hex(8)


def add_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    master_key = generate_master_key()

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute(
            "INSERT INTO users (username, password, master_key) VALUES (?, ?, ?)",
            (username, hashed, master_key)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def check_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, password, master_key FROM users WHERE username=?",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[1].encode()):
        return (row[0], row[2])
    return None



def create_requests_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS master_key_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user TEXT NOT NULL,
        to_user TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
    )
    ''')
    conn.commit()
    conn.close()


def send_master_key_request(from_user, to_user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username=?", (to_user,))
    if not cursor.fetchone():
        conn.close()
        return False
    cursor.execute(
        "INSERT INTO master_key_requests (from_user, to_user, status) VALUES (?, ?, 'pending')",
        (from_user, to_user)
    )
    conn.commit()
    conn.close()
    return True


def get_received_requests(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, from_user, status FROM master_key_requests WHERE to_user=?",
        (username,)
    )
    results = cursor.fetchall()
    conn.close()
    return results


def respond_to_request(request_id, accept):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    status = 'accepted' if accept else 'rejected'
    cursor.execute(
        "UPDATE master_key_requests SET status=? WHERE id=?",
        (status, request_id)
    )
    conn.commit()
    conn.close()


def get_shared_master_keys(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT u.username, u.master_key, r.status
    FROM master_key_requests r
    JOIN users u ON r.to_user = u.username
    WHERE r.from_user = ?
    ''', (username,))
    rows = cursor.fetchall()
    conn.close()

    # Безопасность: не возвращаем значение мастер-ключа до одобрения
    sanitized = []
    for row in rows:
        to_username, master_key, status = row
        visible_key = master_key if status == 'accepted' else None
        sanitized.append((to_username, visible_key, status))
    return sanitized



def add_wallet(name, login, password, host, master_key):
    mk_name = master_key[:4]
    name_enc = encrypt_data(name, master_key)
    login_enc = encrypt_data(login, master_key)
    password_enc = encrypt_data(password, master_key)
    host_enc = encrypt_data(host, master_key)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO wallets (name, login, password, host, mk_name) VALUES (?, ?, ?, ?, ?)",
            (name_enc, login_enc, password_enc, host_enc, mk_name)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def search_wallets(name_filter: str, mk_name: str, provided_master_key: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, login, password, host FROM wallets WHERE mk_name=?",
        (mk_name,)
    )
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        wid, name_enc, login_enc, pass_enc, host_enc = r
        entry = {"id": wid, "name": None, "login": None, "password": None, "host": None, "decrypted": False}
        try:
            name_dec = decrypt_data(name_enc, provided_master_key)
            login_dec = decrypt_data(login_enc, provided_master_key)
            pass_dec = decrypt_data(pass_enc, provided_master_key)
            host_dec = decrypt_data(host_enc, provided_master_key)
            entry.update({
                "name": name_dec,
                "login": login_dec,
                "password": pass_dec,
                "host": host_dec,
                "decrypted": True
            })
        except (InvalidToken, Exception):
            entry.update({
                "name": None,
                "login": None,
                "password": None,
                "host": None,
                "decrypted": False
            })
        results.append(entry)

    if name_filter:
        nf_lower = name_filter.lower()
        filtered = []
        for e in results:
            if e["decrypted"] and nf_lower in e["name"].lower():
                filtered.append(e)
        return filtered

    return results



create_db()
create_wallets_table()
create_requests_table()
