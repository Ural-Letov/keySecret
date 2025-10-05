import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import threading
import json
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from logging.handlers import RotatingFileHandler

# Предполагается, что эти функции находятся в файле init_db.py
from init_db import add_user, check_user, add_wallet, search_wallets, send_master_key_request, get_received_requests, respond_to_request, get_shared_master_keys

# --- СТИЛИЗАЦИЯ И ТЕМА ---
STYLE = {
    # Основные цвета
    "bg_color": "#0f0f23",  # Темно-синий фон
    "fg_color": "#ffffff",  # Белый текст
    "accent_color": "#6366f1",  # Современный фиолетовый
    "accent_hover": "#4f46e5",  # Темнее при наведении
    "secondary_bg_color": "#1e1b4b",  # Темно-фиолетовый
    "card_bg_color": "#312e81",  # Фон карточек
    "entry_bg_color": "#374151",  # Фон полей ввода
    "entry_focus_color": "#4f46e5",  # Цвет фокуса
    "success_color": "#10b981",  # Зеленый успех
    "error_color": "#ef4444",  # Красный ошибка
    "warning_color": "#f59e0b",  # Оранжевый предупреждение
    "info_color": "#3b82f6",  # Синий информация
    
    # Шрифты - современная типографика
    "font_tiny": ("Segoe UI", 8),
    "font_small": ("Segoe UI", 9),
    "font_normal": ("Segoe UI", 10),
    "font_medium": ("Segoe UI", 11),
    "font_bold": ("Segoe UI", 12, "bold"),
    "font_semibold": ("Segoe UI", 13, "bold"),
    "font_large": ("Segoe UI", 16, "bold"),
    "font_title": ("Segoe UI", 20, "bold"),
    "font_display": ("Segoe UI", 24, "bold"),
    
    # Моноширинные шрифты для кодов и ключей
    "font_mono_small": ("Consolas", 9),
    "font_mono_normal": ("Consolas", 10),
    "font_mono_medium": ("Consolas", 11),
    "font_mono_large": ("Consolas", 12, "bold"),
    
    # Отступы и размеры
    "padding_small": 5,
    "padding": 10,
    "padding_large": 15,
    "ipadding": 8,
    "border_radius": 8,
    "button_height": 40,
    "entry_height": 35
}


# ---------- Простой HTTP обработчик ----------
class SimpleHandler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # По умолчанию CORS не открыт. Для разработки можно указать
        # разрешенные origin через переменную окружения KS_ALLOWED_ORIGINS
        allow_origins = os.environ.get("KS_ALLOWED_ORIGINS")
        if allow_origins:
            # поддерживает несколько origin через запятую
            self.send_header("Access-Control-Allow-Origin", allow_origins)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/test":
            return self._send_json({"test":True})
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<h1>Server is running inside Tkinter app!</h1>")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def center_window(window, width, height):
    """Центрирует окно на экране."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def create_modern_button(parent, text, command, **kwargs):
    """Создает современную кнопку с hover эффектом."""
    # Устанавливаем значения по умолчанию
    default_kwargs = {
        "bg": STYLE["accent_color"],
        "fg": STYLE["fg_color"],
        "font": STYLE["font_medium"],
        "relief": "flat",
        "bd": 0,
        "height": 2,
        "cursor": "hand2"
    }
    
    # Обновляем значения по умолчанию переданными аргументами
    default_kwargs.update(kwargs)
    
    button = tk.Button(parent, text=text, command=command, **default_kwargs)
    
    def on_enter(e):
        button.config(bg=STYLE["accent_hover"])
    
    def on_leave(e):
        button.config(bg=STYLE["accent_color"])
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    
    return button


def copy_to_clipboard(root, text: str, timeout: int = 20):
    """Копирует text в clipboard приложения root и очищает через timeout секунд,
    если clipboard не был перезаписан другим приложением.
    """
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        logging.info("Copied sensitive data to clipboard (will clear in %s seconds)", timeout)

        def clear_if_unchanged():
            try:
                current = root.clipboard_get()
            except Exception:
                current = None
            if current == text:
                try:
                    root.clipboard_clear()
                    logging.info("Clipboard cleared after timeout")
                except Exception:
                    logging.exception("Failed to clear clipboard")

        # schedule clearing
        root.after(timeout * 1000, clear_if_unchanged)
    except Exception:
        logging.exception("Failed to copy to clipboard")

def create_modern_entry(parent, **kwargs):
    """Создает современное поле ввода."""
    # Устанавливаем значения по умолчанию
    default_kwargs = {
        "bg": STYLE["entry_bg_color"],
        "fg": STYLE["fg_color"],
        "insertbackground": STYLE["fg_color"],
        "relief": "flat",
        "bd": 0,
        "font": STYLE["font_normal"]
    }
    
    # Обновляем значения по умолчанию переданными аргументами
    default_kwargs.update(kwargs)
    
    entry = tk.Entry(parent, **default_kwargs)
    
    def on_focus_in(e):
        entry.config(bg=STYLE["entry_focus_color"])
    
    def on_focus_out(e):
        entry.config(bg=STYLE["entry_bg_color"])
    
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    
    return entry

def create_card_frame(parent, **kwargs):
    """Создает карточку с современным дизайном."""
    return tk.Frame(
        parent,
        bg=STYLE["card_bg_color"],
        relief="flat",
        bd=0,
        **kwargs
    )

def create_modern_label(parent, text, **kwargs):
    """Создает современную метку."""
    # Устанавливаем значения по умолчанию
    default_kwargs = {
        "fg": STYLE["fg_color"],
        "bg": parent.cget("bg"),
        "font": STYLE["font_normal"]
    }
    
    # Обновляем значения по умолчанию переданными аргументами
    default_kwargs.update(kwargs)
    
    return tk.Label(parent, text=text, **default_kwargs)

# --- КЛАССЫ ОКОН ПРИЛОЖЕНИЯ ---

class BaseWindow(tk.Toplevel):
    """Базовый класс для всех дочерних окон с общим стилем."""
    def __init__(self, title, width, height):
        super().__init__()
        self.title(title)
        self.configure(bg=STYLE["bg_color"])
        self.resizable(False, False)
        center_window(self, width, height)
        # Перехватываем закрытие окна, чтобы оно не закрывало главное приложение
        self.protocol("WM_DELETE_WINDOW", self.destroy)

class CreateWalletWindow(BaseWindow):
    """Окно для создания нового кошелька."""
    def __init__(self, master_key):
        super().__init__("Создать новый кошелек", 450, 500)
        self.master_key = master_key
        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self, bg=STYLE["bg_color"])
        title_frame.pack(fill="x", padx=STYLE["padding_large"], pady=(STYLE["padding_large"], STYLE["padding"]))
        
        create_modern_label(title_frame, "🔐 Создать новый кошелек", font=STYLE["font_title"]).pack()
        create_modern_label(title_frame, "Заполните данные для нового кошелька", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(pady=(5, 0))
        
        # Основной контент в карточке
        main_card = create_card_frame(self)
        main_card.pack(fill="both", expand=True, padx=STYLE["padding_large"], pady=STYLE["padding"])
        
        fields = [
            ("Название кошелька:", "Введите название для идентификации"),
            ("Логин:", "Имя пользователя или email"),
            ("Пароль:", "Пароль для входа"),
            ("Хост:", "Адрес сайта или приложения")
        ]
        self.entries = {}

        for i, (field, placeholder) in enumerate(fields):
            # Контейнер для поля
            field_frame = tk.Frame(main_card, bg=STYLE["card_bg_color"])
            field_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding_small"])
            
            # Метка поля
            create_modern_label(field_frame, field, font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(anchor="w")
            
            # Поле ввода
            entry = create_modern_entry(field_frame, width=45)
            entry.pack(fill="x", pady=(STYLE["padding_small"], 0), ipady=STYLE["ipadding"])
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda e, entry=entry, placeholder=placeholder: self.clear_placeholder(entry, placeholder))
            entry.bind("<FocusOut>", lambda e, entry=entry, placeholder=placeholder: self.restore_placeholder(entry, placeholder))
            
            self.entries[field] = entry
        
        # Кнопки
        button_frame = tk.Frame(main_card, bg=STYLE["card_bg_color"])
        button_frame.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding_large"], STYLE["padding"]))
        
        create_modern_button(button_frame, "✨ Создать кошелек", self.save_wallet, width=30).pack(side="left", padx=(0, STYLE["padding_small"]))
        create_modern_button(button_frame, "❌ Отмена", self.destroy, bg=STYLE["error_color"], width=15).pack(side="right")
    
    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=STYLE["fg_color"])
    
    def restore_placeholder(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=STYLE["accent_color"])

    def save_wallet(self):
        # Получаем данные, исключая placeholder'ы
        data = {}
        for key, entry in self.entries.items():
            value = entry.get()
            field_name = key.split(":")[0].lower().replace(" ", "_")
            # Проверяем, что это не placeholder
            placeholders = ["Введите название для идентификации", "Имя пользователя или email", 
                          "Пароль для входа", "Адрес сайта или приложения"]
            if value not in placeholders:
                data[field_name] = value
        
        if len(data) != 4:
            messagebox.showwarning("Ошибка", "Заполните все поля!", parent=self)
            return

        success = add_wallet(data["название_кошелька"], data["логин"], data["пароль"], data["хост"], self.master_key)
        if success:
            messagebox.showinfo("Успешно", "✅ Кошелек успешно добавлен!", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "❌ Не удалось добавить кошелек.", parent=self)

class SearchWalletWindow(BaseWindow):
    """Окно для поиска кошельков."""
    def __init__(self, master_key):
        super().__init__("Поиск кошельков", 800, 700)
        self.master_key = master_key
        self.create_widgets()
        self.show_wallets()

    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self, bg=STYLE["bg_color"])
        title_frame.pack(fill="x", padx=STYLE["padding_large"], pady=(STYLE["padding_large"], STYLE["padding"]))
        
        create_modern_label(title_frame, "🔍 Поиск кошельков", font=STYLE["font_title"]).pack()
        create_modern_label(title_frame, "Найдите и управляйте своими кошельками", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(pady=(5, 0))
        
        # Панель поиска в карточке
        search_card = create_card_frame(self)
        search_card.pack(fill="x", padx=STYLE["padding_large"], pady=STYLE["padding"])
        
        # Поле поиска по названию
        search_field_frame = tk.Frame(search_card, bg=STYLE["card_bg_color"])
        search_field_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding"])
        
        create_modern_label(search_field_frame, "🔎 Название кошелька (поиск):", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(anchor="w")
        self.entry_name = create_modern_entry(search_field_frame, width=50)
        self.entry_name.pack(fill="x", pady=(STYLE["padding_small"], 0), ipady=STYLE["ipadding"])
        self.entry_name.insert(0, "Введите название для поиска...")
        self.entry_name.bind("<FocusIn>", lambda e: self.clear_search_placeholder())
        self.entry_name.bind("<FocusOut>", lambda e: self.restore_search_placeholder())
        
        # Поле мастер-ключа
        mk_field_frame = tk.Frame(search_card, bg=STYLE["card_bg_color"])
        mk_field_frame.pack(fill="x", padx=STYLE["padding"], pady=(0, STYLE["padding"]))
        
        create_modern_label(mk_field_frame, "🔑 Полный мастер-ключ для дешифровки:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(anchor="w")
        self.entry_full_mk = create_modern_entry(mk_field_frame, width=50)
        self.entry_full_mk.pack(fill="x", pady=(STYLE["padding_small"], 0), ipady=STYLE["ipadding"])
        self.entry_full_mk.insert(0, self.master_key)

        # Кнопки управления
        button_frame = tk.Frame(search_card, bg=STYLE["card_bg_color"])
        button_frame.pack(fill="x", padx=STYLE["padding"], pady=(0, STYLE["padding"]))
        
        create_modern_button(button_frame, "🔄 Обновить / Фильтровать", self.show_wallets, width=30).pack(side="left")
        create_modern_button(button_frame, "➕ Создать новый", lambda: CreateWalletWindow(self.master_key), width=20).pack(side="right")
        
        # Результаты в отдельной карточке
        results_card = create_card_frame(self)
        results_card.pack(fill="both", expand=True, padx=STYLE["padding_large"], pady=(0, STYLE["padding_large"]))
        
        # Заголовок результатов
        results_header = tk.Frame(results_card, bg=STYLE["card_bg_color"])
        results_header.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding"])
        
        create_modern_label(results_header, "📋 Результаты поиска", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(side="left")
        
        # Область прокрутки для результатов
        canvas_frame = tk.Frame(results_card, bg=STYLE["card_bg_color"])
        canvas_frame.pack(fill="both", expand=True, padx=STYLE["padding"], pady=(0, STYLE["padding"]))
        
        canvas = tk.Canvas(canvas_frame, bg=STYLE["secondary_bg_color"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview, bg=STYLE["entry_bg_color"])
        self.inner_frame = tk.Frame(canvas, bg=STYLE["secondary_bg_color"])

        self.inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def clear_search_placeholder(self):
        if self.entry_name.get() == "Введите название для поиска...":
            self.entry_name.delete(0, tk.END)
            self.entry_name.config(fg=STYLE["fg_color"])
    
    def restore_search_placeholder(self):
        if not self.entry_name.get():
            self.entry_name.insert(0, "Введите название для поиска...")
            self.entry_name.config(fg=STYLE["accent_color"])

    def show_wallets(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        name_filter = self.entry_name.get().strip()
        if name_filter == "Введите название для поиска...":
            name_filter = ""
        provided_mk = self.entry_full_mk.get().strip()
        mk4 = provided_mk[:4] if provided_mk else ""

        if not mk4:
            error_frame = tk.Frame(self.inner_frame, bg=STYLE["secondary_bg_color"])
            error_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding"])
            create_modern_label(error_frame, "⚠️ Введите полный мастер-ключ для поиска.", fg=STYLE["error_color"], font=STYLE["font_medium"]).pack(pady=STYLE["padding"])
            return

        wallets = search_wallets(name_filter, mk4, provided_mk)

        if not wallets:
            no_results_frame = tk.Frame(self.inner_frame, bg=STYLE["secondary_bg_color"])
            no_results_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding"])
            create_modern_label(no_results_frame, "🔍 Ничего не найдено", fg=STYLE["warning_color"], font=STYLE["font_medium"]).pack(pady=STYLE["padding"])
            return

        for i, e in enumerate(wallets):
            # Создаем карточку кошелька
            wallet_card = create_card_frame(self.inner_frame)
            wallet_card.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding_small"])
            
            # Заголовок карточки
            header_frame = tk.Frame(wallet_card, bg=STYLE["card_bg_color"])
            header_frame.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding"], 0))
            
            if e["decrypted"]:
                name, login, pwd, host = e["name"], e["login"], e["password"], e["host"]
                status = "✅ Дешифровано"
                status_color = STYLE["success_color"]
                status_icon = "🔓"
            else:
                name, login, pwd, host = "*** (зашифровано)", "***", "***", "***"
                status = "❌ Не расшифровано (неверный мастер-ключ)"
                status_color = STYLE["error_color"]
                status_icon = "🔒"
            
            # Название и статус
            create_modern_label(header_frame, f"💼 {name}", font=STYLE["font_semibold"], fg=STYLE["accent_color"]).pack(side="left")
            create_modern_label(header_frame, f"{status_icon} {status}", font=STYLE["font_medium"], fg=status_color).pack(side="right")
            
            # Детали кошелька
            details_frame = tk.Frame(wallet_card, bg=STYLE["card_bg_color"])
            details_frame.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding_small"], STYLE["padding"]))
            
            # Создаем сетку для деталей
            details_frame.grid_columnconfigure(1, weight=1)
            
            # Логин
            create_modern_label(details_frame, "👤 Логин:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).grid(row=0, column=0, sticky="w", padx=(0, STYLE["padding_small"]))
            create_modern_label(details_frame, login, font=STYLE["font_medium"]).grid(row=0, column=1, sticky="w")
            
            # Пароль
            create_modern_label(details_frame, "🔑 Пароль:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).grid(row=1, column=0, sticky="w", padx=(0, STYLE["padding_small"]))
            create_modern_label(details_frame, pwd, font=STYLE["font_medium"]).grid(row=1, column=1, sticky="w")
            
            # Хост
            create_modern_label(details_frame, "🌐 Хост:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).grid(row=2, column=0, sticky="w", padx=(0, STYLE["padding_small"]))
            create_modern_label(details_frame, host, font=STYLE["font_medium"]).grid(row=2, column=1, sticky="w")
            
            # Кнопки действий
            if e["decrypted"]:
                actions_frame = tk.Frame(wallet_card, bg=STYLE["card_bg_color"])
                actions_frame.pack(fill="x", padx=STYLE["padding"], pady=(0, STYLE["padding"]))
                
                def make_copy(password=pwd):
                    copy_to_clipboard(self, password, timeout=20)
                    messagebox.showinfo("Скопировано", "📋 Пароль скопирован в буфер обмена! (будет очищен)", parent=self)
                
                create_modern_button(actions_frame, "📋 Копировать пароль", make_copy, width=20).pack(side="left", padx=(0, STYLE["padding_small"]))
                create_modern_button(actions_frame, "👁️ Показать/скрыть", lambda p=pwd, l=login, h=host: self.toggle_password_visibility(p, l, h), width=20).pack(side="left")
    
    def toggle_password_visibility(self, password, login, host):
        """Переключает видимость пароля в отдельном окне."""
        visibility_window = tk.Toplevel(self)
        visibility_window.title("Детали кошелька")
        visibility_window.configure(bg=STYLE["bg_color"])
        visibility_window.geometry("400x300")
        center_window(visibility_window, 400, 300)
        
        # Заголовок
        create_modern_label(visibility_window, "🔍 Детали кошелька", font=STYLE["font_large"]).pack(pady=STYLE["padding_large"])
        
        # Детали в карточке
        details_card = create_card_frame(visibility_window)
        details_card.pack(fill="both", expand=True, padx=STYLE["padding_large"], pady=STYLE["padding"])
        
        # Логин
        login_frame = tk.Frame(details_card, bg=STYLE["card_bg_color"])
        login_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding_small"])
        create_modern_label(login_frame, "👤 Логин:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(anchor="w")
        create_modern_label(login_frame, login, font=STYLE["font_normal"]).pack(anchor="w")
        
        # Пароль
        password_frame = tk.Frame(details_card, bg=STYLE["card_bg_color"])
        password_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding_small"])
        create_modern_label(password_frame, "🔑 Пароль:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(anchor="w")
        create_modern_label(password_frame, password, font=STYLE["font_normal"]).pack(anchor="w")
        
        # Хост
        host_frame = tk.Frame(details_card, bg=STYLE["card_bg_color"])
        host_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding_small"])
        create_modern_label(host_frame, "🌐 Хост:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(anchor="w")
        create_modern_label(host_frame, host, font=STYLE["font_normal"]).pack(anchor="w")
        
        # Кнопка закрытия
        create_modern_button(details_card, "❌ Закрыть", visibility_window.destroy, width=20).pack(pady=STYLE["padding_large"])


class MasterKeysWindow(BaseWindow):
    """Окно для управления мастер-ключами."""
    def __init__(self, username, master_key):
        super().__init__("Управление мастер-ключами", 800, 600)
        self.username = username
        self.master_key = master_key
        self.create_widgets()
        self.load_shared_keys()

    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self, bg=STYLE["bg_color"])
        title_frame.pack(fill="x", padx=STYLE["padding_large"], pady=(STYLE["padding_large"], STYLE["padding"]))
        
        create_modern_label(title_frame, "🔑 Управление мастер-ключами", font=STYLE["font_title"]).pack()
        create_modern_label(title_frame, "Просматривайте и управляйте доступом к вашим данным", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(pady=(5, 0))
        
        # Ваш мастер-ключ
        your_key_card = create_card_frame(self)
        your_key_card.pack(fill="x", padx=STYLE["padding_large"], pady=STYLE["padding"])
        
        key_header = tk.Frame(your_key_card, bg=STYLE["card_bg_color"])
        key_header.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding"], 0))
        
        create_modern_label(key_header, "🔐 Ваш мастер-ключ", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(side="left")
        
        key_display_frame = tk.Frame(your_key_card, bg=STYLE["card_bg_color"])
        key_display_frame.pack(fill="x", padx=STYLE["padding"], pady=(0, STYLE["padding"]))
        
        self.key_entry = create_modern_entry(key_display_frame, width=60, state="readonly")
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, STYLE["padding_small"]))
        self.key_entry.config(state="normal")
        self.key_entry.insert(0, self.master_key)
        self.key_entry.config(state="readonly")
        
        create_modern_button(key_display_frame, "📋 Копировать", self.copy_master_key, width=15).pack(side="right")
        
        # Общие ключи
        shared_keys_card = create_card_frame(self)
        shared_keys_card.pack(fill="both", expand=True, padx=STYLE["padding_large"], pady=(0, STYLE["padding_large"]))
        
        shared_header = tk.Frame(shared_keys_card, bg=STYLE["card_bg_color"])
        shared_header.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding"], 0))
        
        create_modern_label(shared_header, "🤝 Общие мастер-ключи", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(side="left")
        create_modern_button(shared_header, "🔄 Обновить", self.load_shared_keys, width=15).pack(side="right")
        
        # Область прокрутки для общих ключей
        canvas_frame = tk.Frame(shared_keys_card, bg=STYLE["card_bg_color"])
        canvas_frame.pack(fill="both", expand=True, padx=STYLE["padding"], pady=(0, STYLE["padding"]))
        
        canvas = tk.Canvas(canvas_frame, bg=STYLE["secondary_bg_color"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview, bg=STYLE["entry_bg_color"])
        self.inner_frame = tk.Frame(canvas, bg=STYLE["secondary_bg_color"])

        self.inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def copy_master_key(self):
        copy_to_clipboard(self, self.master_key, timeout=30)
        messagebox.showinfo("Скопировано", "📋 Мастер-ключ скопирован в буфер обмена! (будет очищен)", parent=self)

    def load_shared_keys(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        shared_keys = get_shared_master_keys(self.username)
        
        if not shared_keys:
            no_keys_frame = tk.Frame(self.inner_frame, bg=STYLE["secondary_bg_color"])
            no_keys_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding"])
            create_modern_label(no_keys_frame, "🔍 Нет общих мастер-ключей", fg=STYLE["warning_color"], font=STYLE["font_medium"]).pack(pady=STYLE["padding"])
            return
        
        for key_data in shared_keys:
            username, master_key, status = key_data
            
            key_card = create_card_frame(self.inner_frame)
            key_card.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding_small"])
            
            # Заголовок карточки
            header_frame = tk.Frame(key_card, bg=STYLE["card_bg_color"])
            header_frame.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding"], 0))
            
            create_modern_label(header_frame, f"👤 {username}", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(side="left")
            
            status_color = STYLE["success_color"] if status == "accepted" else STYLE["warning_color"]
            status_text = "✅ Принят" if status == "accepted" else "⏳ Ожидает"
            create_modern_label(header_frame, status_text, font=STYLE["font_small"], fg=status_color).pack(side="right")
            
            # Детали ключа
            details_frame = tk.Frame(key_card, bg=STYLE["card_bg_color"])
            details_frame.pack(fill="x", padx=STYLE["padding"], pady=(0, STYLE["padding"]))
            
            create_modern_label(details_frame, f"🔑 Ключ: {master_key}", font=STYLE["font_small"]).pack(anchor="w")
            
            if status == "accepted":
                def copy_key(key=master_key):
                    copy_to_clipboard(self, key, timeout=30)
                    messagebox.showinfo("Скопировано", "📋 Ключ скопирован в буфер обмена! (будет очищен)", parent=self)
                
                create_modern_button(details_frame, "📋 Копировать ключ", copy_key, width=20).pack(anchor="w", pady=(STYLE["padding_small"], 0))


class ShareKeyWindow(BaseWindow):
    """Окно для отправки запроса на общий доступ к ключу."""
    def __init__(self, username):
        super().__init__("Запросить ключ", 500, 400)
        self.username = username
        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self, bg=STYLE["bg_color"])
        title_frame.pack(fill="x", padx=STYLE["padding_large"], pady=(STYLE["padding_large"], STYLE["padding"]))
        
        create_modern_label(title_frame, "📤 Запросить ключ", font=STYLE["font_title"]).pack()
        create_modern_label(title_frame, "Отправьте запрос на доступ к мастер-ключу", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(pady=(5, 0))
        
        # Форма запроса
        form_card = create_card_frame(self)
        form_card.pack(fill="both", expand=True, padx=STYLE["padding_large"], pady=STYLE["padding"])
        
        form_content = tk.Frame(form_card, bg=STYLE["card_bg_color"])
        form_content.pack(fill="both", expand=True, padx=STYLE["padding_large"], pady=STYLE["padding_large"])
        
        # Поле имени пользователя
        user_frame = tk.Frame(form_content, bg=STYLE["card_bg_color"])
        user_frame.pack(fill="x", pady=STYLE["padding"])
        
        create_modern_label(user_frame, "👤 Имя пользователя получателя", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(anchor="w")
        self.entry_username = create_modern_entry(user_frame, width=40)
        self.entry_username.pack(fill="x", pady=(STYLE["padding_small"], 0), ipady=STYLE["ipadding"])
        self.entry_username.insert(0, "Введите имя пользователя...")
        self.entry_username.bind("<FocusIn>", lambda e: self.clear_username_placeholder())
        self.entry_username.bind("<FocusOut>", lambda e: self.restore_username_placeholder())
        
        # Информация
        info_frame = tk.Frame(form_content, bg=STYLE["card_bg_color"])
        info_frame.pack(fill="x", pady=STYLE["padding"])
        
        create_modern_label(info_frame, "ℹ️ Информация:", font=STYLE["font_medium"], fg=STYLE["info_color"]).pack(anchor="w")
        create_modern_label(info_frame, "• Пользователь получит уведомление о запросе\n• Вы сможете использовать его мастер-ключ после одобрения\n• Будьте осторожны при предоставлении доступа", 
                          font=STYLE["font_small"], fg=STYLE["fg_color"]).pack(anchor="w", pady=(STYLE["padding_small"], 0))
        
        # Кнопки
        buttons_frame = tk.Frame(form_content, bg=STYLE["card_bg_color"])
        buttons_frame.pack(fill="x", pady=(STYLE["padding_large"], 0))
        
        create_modern_button(buttons_frame, "📤 Отправить запрос", self.send_request, width=25).pack(side="left", padx=(0, STYLE["padding_small"]))
        create_modern_button(buttons_frame, "❌ Отмена", self.destroy, bg=STYLE["error_color"], width=15).pack(side="right")
    
    def clear_username_placeholder(self):
        if self.entry_username.get() == "Введите имя пользователя...":
            self.entry_username.delete(0, tk.END)
            self.entry_username.config(fg=STYLE["fg_color"])
    
    def restore_username_placeholder(self):
        if not self.entry_username.get():
            self.entry_username.insert(0, "Введите имя пользователя...")
            self.entry_username.config(fg=STYLE["accent_color"])
    
    def send_request(self):
        target_username = self.entry_username.get()
        
        if target_username == "Введите имя пользователя...":
            messagebox.showwarning("Ошибка", "⚠️ Введите имя пользователя получателя!")
            return
        
        if not target_username:
            messagebox.showwarning("Ошибка", "⚠️ Введите имя пользователя получателя!")
            return
        
        if target_username == self.username:
            messagebox.showwarning("Ошибка", "❌ Нельзя отправить запрос самому себе!")
            return
        
        success = send_master_key_request(self.username, target_username)
        if success:
            messagebox.showinfo("Успешно", f"✅ Запрос отправлен пользователю {target_username}!\nОжидайте одобрения.", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "❌ Пользователь не найден или произошла ошибка.", parent=self)


class IncomingRequestsWindow(BaseWindow):
    """Окно для просмотра и обработки входящих запросов на мастер-ключ."""
    def __init__(self, username):
        super().__init__("Входящие запросы", 700, 500)
        self.username = username
        self.create_widgets()
        self.load_requests()

    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self, bg=STYLE["bg_color"])
        title_frame.pack(fill="x", padx=STYLE["padding_large"], pady=(STYLE["padding_large"], STYLE["padding"]))
        
        create_modern_label(title_frame, "📥 Входящие запросы", font=STYLE["font_title"]).pack()
        create_modern_label(title_frame, "Просмотрите и одобрите запросы на доступ к вашему мастер-ключу", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(pady=(5, 0))
        
        # Область запросов
        requests_card = create_card_frame(self)
        requests_card.pack(fill="both", expand=True, padx=STYLE["padding_large"], pady=STYLE["padding"])
        
        requests_header = tk.Frame(requests_card, bg=STYLE["card_bg_color"])
        requests_header.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding"], 0))
        
        create_modern_label(requests_header, "📋 Список запросов", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(side="left")
        create_modern_button(requests_header, "🔄 Обновить", self.load_requests, width=15).pack(side="right")
        
        # Область прокрутки для запросов
        canvas_frame = tk.Frame(requests_card, bg=STYLE["card_bg_color"])
        canvas_frame.pack(fill="both", expand=True, padx=STYLE["padding"], pady=(0, STYLE["padding"]))
        
        canvas = tk.Canvas(canvas_frame, bg=STYLE["secondary_bg_color"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview, bg=STYLE["entry_bg_color"])
        self.inner_frame = tk.Frame(canvas, bg=STYLE["secondary_bg_color"])

        self.inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_requests(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        requests = get_received_requests(self.username)
        
        if not requests:
            no_requests_frame = tk.Frame(self.inner_frame, bg=STYLE["secondary_bg_color"])
            no_requests_frame.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding"])
            create_modern_label(no_requests_frame, "🔍 Нет входящих запросов", fg=STYLE["warning_color"], font=STYLE["font_medium"]).pack(pady=STYLE["padding"])
            return
        
        for request_data in requests:
            request_id, from_user, status = request_data
            
            request_card = create_card_frame(self.inner_frame)
            request_card.pack(fill="x", padx=STYLE["padding"], pady=STYLE["padding_small"])
            
            # Заголовок запроса
            header_frame = tk.Frame(request_card, bg=STYLE["card_bg_color"])
            header_frame.pack(fill="x", padx=STYLE["padding"], pady=(STYLE["padding"], 0))
            
            create_modern_label(header_frame, f"👤 От: {from_user}", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(side="left")
            
            status_color = STYLE["success_color"] if status == "accepted" else STYLE["warning_color"] if status == "pending" else STYLE["error_color"]
            status_text = "✅ Принят" if status == "accepted" else "⏳ Ожидает" if status == "pending" else "❌ Отклонен"
            create_modern_label(header_frame, status_text, font=STYLE["font_small"], fg=status_color).pack(side="right")
            
            # Детали запроса
            details_frame = tk.Frame(request_card, bg=STYLE["card_bg_color"])
            details_frame.pack(fill="x", padx=STYLE["padding"], pady=(0, STYLE["padding"]))
            
            create_modern_label(details_frame, f"🆔 ID запроса: {request_id}", font=STYLE["font_small"]).pack(anchor="w")
            create_modern_label(details_frame, f"📅 Статус: {status}", font=STYLE["font_small"]).pack(anchor="w")
            
            # Кнопки действий (только для ожидающих запросов)
            if status == "pending":
                actions_frame = tk.Frame(request_card, bg=STYLE["card_bg_color"])
                actions_frame.pack(fill="x", padx=STYLE["padding"], pady=(0, STYLE["padding"]))
                
                def accept_request(req_id=request_id):
                    respond_to_request(req_id, True)
                    messagebox.showinfo("Успешно", "✅ Запрос принят! Пользователь получил доступ к вашему мастер-ключу.", parent=self)
                    self.load_requests()
                
                def reject_request(req_id=request_id):
                    respond_to_request(req_id, False)
                    messagebox.showinfo("Успешно", "❌ Запрос отклонен.", parent=self)
                    self.load_requests()
                
                create_modern_button(actions_frame, "✅ Принять", accept_request, width=15).pack(side="left", padx=(0, STYLE["padding_small"]))
                create_modern_button(actions_frame, "❌ Отклонить", reject_request, bg=STYLE["error_color"], width=15).pack(side="left")


class MainApplication(tk.Toplevel):
    """Главное окно приложения после входа."""
    def __init__(self, username, master_key, login_window):
        super().__init__()
        self.username = username
        self.master_key = master_key
        self.login_window = login_window

        self.title("keySecret — Панель управления")
        self.configure(bg=STYLE["bg_color"])
        self.geometry("900x700")
        center_window(self, 900, 700)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()

    def create_widgets(self):
        # --- Верхняя панель ---
        top_frame = tk.Frame(self, bg=STYLE["secondary_bg_color"])
        top_frame.pack(fill="x", ipady=STYLE["padding_large"])
        
        # Логотип и приветствие
        welcome_frame = tk.Frame(top_frame, bg=STYLE["secondary_bg_color"])
        welcome_frame.pack(side="left", padx=STYLE["padding_large"])
        
        create_modern_label(welcome_frame, f"👋 Добро пожаловать, {self.username}!", font=STYLE["font_semibold"], fg=STYLE["accent_color"]).pack(anchor="w")
        create_modern_label(welcome_frame, "Управляйте своими паролями безопасно", font=STYLE["font_medium"], fg=STYLE["fg_color"]).pack(anchor="w")
        
        # Кнопка выхода
        create_modern_button(top_frame, "🚪 Выход", self.logout, bg=STYLE["error_color"], width=15).pack(side="right", padx=STYLE["padding_large"])

        # --- Центральная панель с кнопками ---
        center_frame = tk.Frame(self, bg=STYLE["bg_color"])
        center_frame.pack(expand=True, fill="both", padx=STYLE["padding_large"], pady=STYLE["padding_large"])
        
        # Заголовок раздела
        section_header = tk.Frame(center_frame, bg=STYLE["bg_color"])
        section_header.pack(fill="x", pady=(0, STYLE["padding_large"]))
        
        create_modern_label(section_header, "🎛️ Панель управления", font=STYLE["font_title"]).pack()
        create_modern_label(section_header, "Выберите действие для работы с кошельками", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(pady=(5, 0))
        
        # Сетка кнопок
        buttons_grid = tk.Frame(center_frame, bg=STYLE["bg_color"])
        buttons_grid.pack(expand=True)
        
        # Настройка сетки
        buttons_grid.grid_columnconfigure(0, weight=1)
        buttons_grid.grid_columnconfigure(1, weight=1)
        buttons_grid.grid_rowconfigure(0, weight=1)
        buttons_grid.grid_rowconfigure(1, weight=1)
        buttons_grid.grid_rowconfigure(2, weight=1)
        
        buttons = [
            ("🔍 Поиск кошельков", "Найдите и просмотрите\nваши сохраненные кошельки", lambda: SearchWalletWindow(self.master_key)),
            ("➕ Создать кошелек", "Добавьте новый кошелек\nв вашу коллекцию", lambda: CreateWalletWindow(self.master_key)),
            ("🔑 Мастер-ключи", "Управляйте доступом\nк вашим данным", self.show_master_keys),
            ("📤 Запросить ключ", "Отправьте запрос на\nобщий доступ к ключу", self.show_share_key),
            ("📥 Входящие запросы", "Просмотрите и одобрите\nзапросы на ваш ключ", self.show_incoming_requests),
            ("⚙️ Настройки", "Настройки приложения\nи профиля", self.show_settings),
        ]

        for i, (text, description, command) in enumerate(buttons):
            # Создаем карточку для кнопки
            button_card = create_card_frame(buttons_grid)
            button_card.grid(row=i//2, column=i%2, padx=STYLE["padding"], pady=STYLE["padding"], sticky="nsew")
            
            # Содержимое карточки
            card_content = tk.Frame(button_card, bg=STYLE["card_bg_color"])
            card_content.pack(expand=True, fill="both", padx=STYLE["padding_large"], pady=STYLE["padding_large"])
            
            # Иконка и текст кнопки
            create_modern_label(card_content, text, font=STYLE["font_semibold"], fg=STYLE["accent_color"]).pack(pady=(0, STYLE["padding_small"]))
            create_modern_label(card_content, description, font=STYLE["font_medium"], fg=STYLE["fg_color"]).pack(pady=(0, STYLE["padding"]))
            
            # Кнопка действия
            create_modern_button(card_content, "Выполнить", command, width=20).pack()

        # --- Нижняя панель ---
        bottom_frame = tk.Frame(self, bg=STYLE["secondary_bg_color"])
        bottom_frame.pack(side="bottom", fill="x", ipady=STYLE["padding"])
        
        # Информация о мастер-ключе
        mk_frame = tk.Frame(bottom_frame, bg=STYLE["secondary_bg_color"])
        mk_frame.pack()
        
        create_modern_label(mk_frame, "🔐 Ваш мастер-ключ:", font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack(side="left")
        create_modern_label(mk_frame, self.master_key, font=STYLE["font_mono_medium"], fg=STYLE["fg_color"]).pack(side="left", padx=(STYLE["padding_small"], 0))
    
    def show_master_keys(self):
        """Показывает окно управления мастер-ключами."""
        MasterKeysWindow(self.username, self.master_key)
    
    def show_share_key(self):
        """Показывает окно для обмена ключами."""
        ShareKeyWindow(self.username)
    
    def show_incoming_requests(self):
        """Показывает окно входящих запросов."""
        IncomingRequestsWindow(self.username)
    
    def show_settings(self):
        """Показывает окно настроек."""
        messagebox.showinfo("В разработке", "🔧 Настройки будут добавлены в следующей версии!")

    def on_closing(self):
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти из приложения?"):
            self.login_window.destroy()

    def logout(self):
        self.destroy()
        self.login_window.deiconify() # Показываем окно входа снова


class LoginFrame(tk.Frame):
    """Фрейм для входа и регистрации."""
    def __init__(self, master):
        super().__init__(master, bg=STYLE["bg_color"])
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        # Основной контейнер
        main_container = tk.Frame(self, bg=STYLE["bg_color"])
        main_container.pack(expand=True, fill="both")
        
        # Логотип и заголовок
        header_frame = tk.Frame(main_container, bg=STYLE["bg_color"])
        header_frame.pack(pady=(STYLE["padding_large"] * 2, STYLE["padding_large"]))
        
        try:
            img = Image.open("tlog.png").resize((250, 90))
            logo = ImageTk.PhotoImage(img)
            logo_label = tk.Label(header_frame, image=logo, bg=STYLE["bg_color"])
            logo_label.image = logo
            logo_label.pack()
        except FileNotFoundError:
            create_modern_label(header_frame, "🔐 keySecret", font=STYLE["font_display"], fg=STYLE["accent_color"]).pack()
        
        create_modern_label(header_frame, "Безопасное хранение паролей", font=STYLE["font_medium"], fg=STYLE["fg_color"]).pack(pady=(STYLE["padding_small"], 0))
        
        # Форма входа в карточке
        login_card = create_card_frame(main_container)
        login_card.pack(expand=True, fill="x", padx=STYLE["padding_large"] * 2, pady=STYLE["padding"])
        
        # Заголовок формы
        form_header = tk.Frame(login_card, bg=STYLE["card_bg_color"])
        form_header.pack(fill="x", padx=STYLE["padding_large"], pady=(STYLE["padding_large"], STYLE["padding"]))
        
        create_modern_label(form_header, "🔑 Вход в систему", font=STYLE["font_title"], fg=STYLE["accent_color"]).pack()
        create_modern_label(form_header, "Введите свои данные для входа", font=STYLE["font_medium"], fg=STYLE["fg_color"]).pack(pady=(STYLE["padding_small"], 0))

        # Поля ввода
        form_content = tk.Frame(login_card, bg=STYLE["card_bg_color"])
        form_content.pack(fill="x", padx=STYLE["padding_large"], pady=(0, STYLE["padding_large"]))
        
        # Поле имени пользователя
        username_frame = tk.Frame(form_content, bg=STYLE["card_bg_color"])
        username_frame.pack(fill="x", pady=STYLE["padding"])
        
        create_modern_label(username_frame, "👤 Имя пользователя", font=STYLE["font_semibold"], fg=STYLE["accent_color"]).pack(anchor="w")
        self.entry_username = create_modern_entry(username_frame, width=35)
        self.entry_username.pack(fill="x", pady=(STYLE["padding_small"], 0), ipady=STYLE["ipadding"])
        self.entry_username.insert(0, "Введите имя пользователя...")
        self.entry_username.bind("<FocusIn>", lambda e: self.clear_username_placeholder())
        self.entry_username.bind("<FocusOut>", lambda e: self.restore_username_placeholder())

        # Поле пароля
        password_frame = tk.Frame(form_content, bg=STYLE["card_bg_color"])
        password_frame.pack(fill="x", pady=STYLE["padding"])
        
        create_modern_label(password_frame, "🔒 Пароль", font=STYLE["font_semibold"], fg=STYLE["accent_color"]).pack(anchor="w")
        self.entry_password = create_modern_entry(password_frame, show="*", width=35)
        self.entry_password.pack(fill="x", pady=(STYLE["padding_small"], 0), ipady=STYLE["ipadding"])
        self.entry_password.insert(0, "Введите пароль...")
        self.entry_password.bind("<FocusIn>", lambda e: self.clear_password_placeholder())
        self.entry_password.bind("<FocusOut>", lambda e: self.restore_password_placeholder())
        
        # Кнопки
        buttons_frame = tk.Frame(form_content, bg=STYLE["card_bg_color"])
        buttons_frame.pack(fill="x", pady=(STYLE["padding_large"], 0))
        
        create_modern_button(buttons_frame, "🚀 Войти", self.login, width=25).pack(side="left", padx=(0, STYLE["padding_small"]))
        create_modern_button(buttons_frame, "📝 Регистрация", self.register, bg=STYLE["info_color"], width=25).pack(side="right")
        
        # Подсказка
        hint_frame = tk.Frame(main_container, bg=STYLE["bg_color"])
        hint_frame.pack(fill="x", padx=STYLE["padding_large"] * 2, pady=(0, STYLE["padding_large"]))
        
        create_modern_label(hint_frame, "💡 Нет аккаунта? Нажмите 'Регистрация' для создания нового", 
                          font=STYLE["font_medium"], fg=STYLE["accent_color"]).pack()
    
    def clear_username_placeholder(self):
        if self.entry_username.get() == "Введите имя пользователя...":
            self.entry_username.delete(0, tk.END)
            self.entry_username.config(fg=STYLE["fg_color"])
    
    def restore_username_placeholder(self):
        if not self.entry_username.get():
            self.entry_username.insert(0, "Введите имя пользователя...")
            self.entry_username.config(fg=STYLE["accent_color"])
    
    def clear_username_placeholder(self):
        if self.entry_username.get() == "Введите имя пользователя...":
            self.entry_username.delete(0, tk.END)
            self.entry_username.config(fg=STYLE["fg_color"])
    
    def restore_username_placeholder(self):
        if not self.entry_username.get():
            self.entry_username.insert(0, "Введите имя пользователя...")
            self.entry_username.config(fg=STYLE["accent_color"])
    
    def clear_password_placeholder(self):
        if self.entry_password.get() == "Введите пароль...":
            self.entry_password.delete(0, tk.END)
            self.entry_password.config(fg=STYLE["fg_color"], show="*")
    
    def restore_password_placeholder(self):
        if not self.entry_password.get():
            self.entry_password.insert(0, "Введите пароль...")
            self.entry_password.config(fg=STYLE["accent_color"], show="")
    
    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        
        # Проверяем, что это не placeholder'ы
        if username == "Введите имя пользователя..." or password == "Введите пароль...":
            messagebox.showwarning("Ошибка", "⚠️ Пожалуйста, введите имя пользователя и пароль!")
            return
        
        user = check_user(username, password)
        if user:
            messagebox.showinfo("Успешно", "✅ Добро пожаловать! Вы успешно вошли в систему.")
            self.master.withdraw() # Скрываем окно входа
            MainApplication(user[0], user[1], self.master)
        else:
            messagebox.showerror("Ошибка", "❌ Неверное имя пользователя или пароль.\nПроверьте правильность введенных данных.")

    def register(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        
        # Проверяем, что это не placeholder'ы
        if username == "Введите имя пользователя..." or password == "Введите пароль...":
            messagebox.showwarning("Ошибка", "⚠️ Пожалуйста, введите имя пользователя и пароль!")
            return
        
        if not username or not password:
            messagebox.showwarning("Ошибка", "⚠️ Введите имя пользователя и пароль!")
            return
        
        if len(password) < 6:
            messagebox.showwarning("Ошибка", "⚠️ Пароль должен содержать минимум 6 символов!")
            return
        
        if add_user(username, password):
            messagebox.showinfo("Успешно", "🎉 Пользователь успешно зарегистрирован!\nТеперь вы можете войти в систему.")
        else:
            messagebox.showerror("Ошибка", "❌ Пользователь с таким именем уже существует.\nПопробуйте другое имя пользователя.")


class App(tk.Tk):
    """Основной класс приложения."""
    def __init__(self):
        super().__init__()
        self.title("keySecret — Безопасное хранение паролей")
        self.configure(bg=STYLE["bg_color"])
        center_window(self, 600, 650)
        self.resizable(False, False)
        
        # Устанавливаем иконку приложения
        try:
            self.iconbitmap("app_icon.ico")
        except:
            pass  # Иконка не найдена, продолжаем без неё

        login_frame = LoginFrame(self)
        login_frame.pack(expand=True)
        # Настройка логирования перед запуском серверных/фоновых задач
        self.setup_logging()
        self.start_server()

    def setup_logging(self):
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "keysecret.log")

            logger = logging.getLogger()
            logger.setLevel(logging.INFO)

            fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

            fh = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
            fh.setFormatter(fmt)
            logger.addHandler(fh)

            ch = logging.StreamHandler()
            ch.setFormatter(fmt)
            logger.addHandler(ch)
        except Exception:
            # если логирование не настраивается — продолжаем, но без фейла
            pass

    def start_server(self):
        def run_server():
            server = HTTPServer(("localhost", 8080), SimpleHandler)
            logging.info("HTTP-сервер запущен на http://localhost:8080")
            server.serve_forever()

        threading.Thread(target=run_server, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()