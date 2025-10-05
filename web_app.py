from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
from functools import wraps

# Единый источник данных/логики: используем функции из init_db.py,
# чтобы сайт и GUI работали с одной и той же БД и правилами
from init_db import (
    create_db,
    create_wallets_table,
    create_requests_table,
    add_user,
    check_user,
    add_wallet,
    search_wallets,
    send_master_key_request,
    get_received_requests,
    respond_to_request,
    get_shared_master_keys,
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'


# --- ДЕКОРАТОРЫ ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- МАРШРУТЫ ---

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_user(username, password)
        if user:
            session['username'] = user[0]
            session['master_key'] = user[1]
            flash('Добро пожаловать!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Отладочная информация
        print(f"Попытка регистрации: username='{username}', password_length={len(password)}")
        
        if not username:
            flash('Введите имя пользователя', 'error')
            return render_template('register.html')
        
        if not password:
            flash('Введите пароль', 'error')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('register.html')
        
        try:
            if add_user(username, password):
                flash('Пользователь успешно зарегистрирован! Теперь вы можете войти в систему.', 'success')
                print(f"Пользователь {username} успешно зарегистрирован")
                return redirect(url_for('login'))
            else:
                flash('Пользователь с таким именем уже существует', 'error')
                print(f"Пользователь {username} уже существует")
        except Exception as e:
            flash(f'Ошибка при регистрации: {str(e)}', 'error')
            print(f"Ошибка регистрации: {e}")
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'])

@app.route('/wallets')
@login_required
def wallets():
    return render_template('wallets.html', username=session['username'])

@app.route('/create_wallet', methods=['GET', 'POST'])
@login_required
def create_wallet():
    if request.method == 'POST':
        name = request.form['name']
        login = request.form['login']
        password = request.form['password']
        host = request.form['host']
        if add_wallet(name, login, password, host, session['master_key']):
            flash('Кошелек успешно добавлен!', 'success')
            return redirect(url_for('wallets'))
        else:
            flash('Ошибка при добавлении кошелька', 'error')
    return render_template('create_wallet.html')

@app.route('/search_wallets', methods=['POST'])
@login_required
def search_wallets_api():
    name_filter = request.form.get('name_filter', '')
    master_key = request.form.get('master_key', session['master_key'])
    mk_name = master_key[:4] if master_key else ''
    wallets = search_wallets(name_filter, mk_name, master_key)
    return jsonify(wallets)

@app.route('/master_keys')
@login_required
def master_keys():
    shared_keys = get_shared_master_keys(session['username'])
    return render_template('master_keys.html', 
                         username=session['username'],
                         master_key=session['master_key'],
                         shared_keys=shared_keys)

@app.route('/share_key', methods=['GET', 'POST'])
@login_required
def share_key():
    if request.method == 'POST':
        target_username = request.form['target_username']
        if target_username == session['username']:
            flash('Нельзя отправить запрос самому себе', 'error')
            return render_template('share_key.html')
        if send_master_key_request(session['username'], target_username):
            flash(f'Запрос отправлен пользователю {target_username}!', 'success')
            return redirect(url_for('master_keys'))
        else:
            flash('Пользователь не найден', 'error')
    return render_template('share_key.html')

@app.route('/incoming_requests')
@login_required
def incoming_requests():
    requests = get_received_requests(session['username'])
    return render_template('incoming_requests.html', requests=requests)

@app.route('/respond_request', methods=['POST'])
@login_required
def respond_request():
    request_id = request.form['request_id']
    accept = request.form['action'] == 'accept'
    respond_to_request(request_id, accept)
    action = 'принят' if accept else 'отклонен'
    flash(f'Запрос {action}', 'success')
    return redirect(url_for('incoming_requests'))

# --- API ENDPOINTS ---

@app.route('/api/test')
def api_test():
    return jsonify({"test": True})

@app.route('/api/wallets', methods=['GET'])
@login_required
def api_wallets():
    name_filter = request.args.get('name_filter', '')
    master_key = request.args.get('master_key', session['master_key'])
    mk_name = master_key[:4] if master_key else ''
    wallets = search_wallets(name_filter, mk_name, master_key)
    return jsonify(wallets)

@app.route('/api/wallets', methods=['POST'])
@login_required
def api_create_wallet():
    data = request.get_json()
    name = data.get('name')
    login = data.get('login')
    password = data.get('password')
    host = data.get('host')
    master_key = data.get('master_key', session['master_key'])
    
    if add_wallet(name, login, password, host, master_key):
        return jsonify({"success": True, "message": "Кошелек создан"})
    else:
        return jsonify({"success": False, "message": "Ошибка создания кошелька"}), 400

@app.route('/api/requests', methods=['POST'])
@login_required
def api_send_request():
    data = request.get_json()
    target_username = data.get('target_username')
    
    if target_username == session['username']:
        return jsonify({"success": False, "message": "Нельзя отправить запрос самому себе"}), 400
    
    if send_master_key_request(session['username'], target_username):
        return jsonify({"success": True, "message": "Запрос отправлен"})
    else:
        return jsonify({"success": False, "message": "Пользователь не найден"}), 400

@app.route('/api/requests', methods=['GET'])
@login_required
def api_get_requests():
    requests = get_received_requests(session['username'])
    return jsonify(requests)

@app.route('/api/requests/<int:request_id>', methods=['POST'])
@login_required
def api_respond_request(request_id):
    data = request.get_json()
    accept = data.get('accept', False)
    respond_to_request(request_id, accept)
    return jsonify({"success": True, "message": "Запрос обработан"})

if __name__ == '__main__':
    # Инициализация базы данных
    create_db()
    create_wallets_table()
    create_requests_table()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
