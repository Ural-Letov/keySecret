import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from init_db import add_user, check_user
import os
def open_create_wallet_window(master_key):
    wallet_window = tk.Toplevel()
    wallet_window.title("Создать новый кошелек")
    wallet_window.geometry("400x400")
    wallet_window.configure(bg="#0e0e0e")
    wallet_window.resizable(False, False)

    # Поля ввода
    tk.Label(wallet_window, text="Название кошелька:", fg="#00bfff", bg="#0e0e0e").pack(pady=(10, 0))
    entry_name = tk.Entry(wallet_window, bg="#1c1c1c", fg="white", insertbackground="white")
    entry_name.pack(pady=5, ipady=5)

    tk.Label(wallet_window, text="Логин:", fg="#00bfff", bg="#0e0e0e").pack(pady=(10, 0))
    entry_login = tk.Entry(wallet_window, bg="#1c1c1c", fg="white", insertbackground="white")
    entry_login.pack(pady=5, ipady=5)

    tk.Label(wallet_window, text="Пароль:", fg="#00bfff", bg="#0e0e0e").pack(pady=(10, 0))
    entry_password = tk.Entry(wallet_window, bg="#1c1c1c", fg="white", insertbackground="white")
    entry_password.pack(pady=5, ipady=5)

    tk.Label(wallet_window, text="Хост:", fg="#00bfff", bg="#0e0e0e").pack(pady=(10, 0))
    entry_host = tk.Entry(wallet_window, bg="#1c1c1c", fg="white", insertbackground="white")
    entry_host.pack(pady=5, ipady=5)

    def save_wallet():
        name = entry_name.get()
        login_w = entry_login.get()
        password_w = entry_password.get()
        host = entry_host.get()

        if not all([name, login_w, password_w, host]):
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return

        from init_db import add_wallet
        success = add_wallet(name, login_w, password_w, host, master_key)
        if success:
            messagebox.showinfo("Успешно", "Кошелек добавлен!")
            wallet_window.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить кошелек.")

    tk.Button(wallet_window, text="Создать кошелек", command=save_wallet,
              bg="#00bfff", fg="black", font=("Arial", 10, "bold"), width=25, relief="flat").pack(pady=20)

def open_create_master_key_request_window(current_user):
    window = tk.Toplevel()
    window.title("Создать заявку на мастер ключ")
    window.geometry("400x150")
    window.configure(bg="#0e0e0e")
    window.resizable(False, False)

    tk.Label(window, text="Имя пользователя:", fg="#00bfff", bg="#0e0e0e").pack(pady=(20,5))
    entry_user = tk.Entry(window, bg="#1c1c1c", fg="white", relief="flat", width=30)
    entry_user.pack(pady=5, ipady=5)

    def send_request():
        to_user = entry_user.get().strip()
        if not to_user:
            messagebox.showwarning("Ошибка", "Введите имя пользователя.")
            return
        from init_db import send_master_key_request
        if send_master_key_request(current_user, to_user):
            messagebox.showinfo("Успешно", f"Заявка отправлена пользователю {to_user}")
            window.destroy()
        else:
            messagebox.showerror("Ошибка", f"Пользователь {to_user} не найден.")

    tk.Button(window, text="Отправить заявку", command=send_request,
              bg="#00bfff", fg="black", width=25, relief="flat").pack(pady=15)

def open_received_requests_window(current_user):
    window = tk.Toplevel()
    window.title("Заявки на твой мастер ключ")
    window.geometry("500x400")
    window.configure(bg="#0e0e0e")
    window.resizable(False, False)

    from init_db import get_received_requests, respond_to_request

    frame_content = tk.Frame(window, bg="#0e0e0e")
    frame_content.pack(fill="both", expand=True)

    def refresh_requests():
        for widget in frame_content.winfo_children():
            widget.destroy()

        requests = get_received_requests(current_user)
        if not requests:
            tk.Label(frame_content, text="Нет новых заявок", fg="white", bg="#0e0e0e").pack(pady=20)
            return

        for req_id, from_user, status in requests:
            bg_color = "#ffcc00" if status == "pending" else "#121212"
            frame = tk.Frame(frame_content, bg=bg_color, padx=10, pady=6)

            tk.Label(frame, text=f"От: {from_user}", fg="#0e0e0e" if status == "pending" else "#00bfff",
                     bg=bg_color).pack(side="left")
            tk.Label(frame, text=f"Статус: {status}", fg="#0e0e0e" if status == "pending" else "white",
                     bg=bg_color).pack(side="left", padx=10)

            if status == "pending":
                def accept_func(rid=req_id):
                    respond_to_request(rid, True)
                    refresh_requests()

                def reject_func(rid=req_id):
                    respond_to_request(rid, False)
                    refresh_requests()

                tk.Button(frame, text="Согласиться", command=accept_func,
                          bg="#00bfff", fg="black", relief="flat").pack(side="right", padx=5)
                tk.Button(frame, text="Отказать", command=reject_func,
                          bg="#ff5555", fg="black", relief="flat").pack(side="right", padx=5)

            frame.pack(fill="x", pady=5, padx=10)

    refresh_requests()


def open_master_keys_window(current_user):
    window = tk.Toplevel()
    window.title("Мастер ключи")
    window.geometry("400x440")
    window.configure(bg="#0e0e0e")
    window.resizable(False, False)

    from init_db import get_shared_master_keys
    from tkinter import messagebox

    frame_content = tk.Frame(window, bg="#0e0e0e")
    frame_content.pack(fill="both", expand=True)

    def refresh_keys():
        for widget in frame_content.winfo_children():
            widget.destroy()

        keys = get_shared_master_keys(current_user)
        if not keys:
            tk.Label(frame_content, text="Нет доступных мастер-ключей", fg="white", bg="#0e0e0e").pack(pady=20)
            return

        for u_name, mk, status in keys:
            frame = tk.Frame(frame_content, bg="#121212", padx=10, pady=8)
            tk.Label(frame, text=f"Пользователь: {u_name}", fg="#00bfff", bg="#121212").grid(row=0, column=0, sticky="w")
            display_mk = mk if status == "accepted" else ("Отказано в доступе" if status == "rejected" else "Ожидает решения")
            tk.Label(frame, text=f"Мастер-ключ: {display_mk}", fg="white", bg="#121212").grid(row=1, column=0, sticky="w", pady=(4,0))

            def copy_mk(mk_val=mk, st=status):
                if st == "accepted":
                    window.clipboard_clear()
                    window.clipboard_append(mk_val)
                    messagebox.showinfo("Скопировано", "Мастер-ключ скопирован в буфер обмена.")
                elif st == "rejected":
                    messagebox.showwarning("Недоступно", "Доступ к мастер-ключу отклонён.")
                else:
                    messagebox.showinfo("Ожидание", "Заявка ещё не обработана.")

            btn = tk.Button(frame, text="Копировать мастер-ключ", command=copy_mk,
                            bg="#00bfff", fg="black", relief="flat")
            btn.grid(row=0, column=1, rowspan=2, padx=8, sticky="e")

            frame.pack(fill="x", pady=6, padx=10)

    tk.Button(window, text="Обновить", command=refresh_keys,
              bg="#00bfff", fg="black", font=("Arial", 10, "bold"), width=20, relief="flat").pack(pady=10)

    refresh_keys()



def open_search_wallet_window(master_key):
    search_window = tk.Toplevel()
    search_window.title("Поиск кошельков")
    search_window.geometry("700x600")
    search_window.configure(bg="#0e0e0e")
    search_window.resizable(False, False)

    tk.Label(search_window, text="Название кошелька (поиск):", fg="#00bfff", bg="#0e0e0e").pack(pady=(10,0))
    entry_name = tk.Entry(search_window, bg="#1c1c1c", fg="white", relief="flat", width=40,insertbackground="white")
    entry_name.pack(pady=5, ipady=5)

    frame_mk = tk.Frame(search_window, bg="#0e0e0e")
    frame_mk.pack(pady=(5,0))
    tk.Label(frame_mk, text="Первые 4 символа MK:", fg="#00bfff", bg="#0e0e0e").grid(row=0, column=0, padx=5)
    entry_mkname = tk.Entry(frame_mk, bg="#1c1c1c", fg="white", relief="flat", width=6,insertbackground="white")
    entry_mkname.grid(row=0, column=1, padx=5)
    entry_mkname.insert(0, master_key[:4])

    tk.Label(frame_mk, text="(Полный мастер-ключ для дешифровки):", fg="#00bfff", bg="#0e0e0e").grid(row=1, column=0, columnspan=2, pady=(6,0))
    entry_full_mk = tk.Entry(frame_mk, bg="#1c1c1c", fg="white", relief="flat", width=40,insertbackground="white")
    entry_full_mk.grid(row=2, column=0, columnspan=2, pady=5)
    entry_full_mk.insert(0, master_key)

    def add_context_menu(entry):
        menu = tk.Menu(entry, tearoff=0)
        menu.add_command(label="Копировать", command=lambda: entry.event_generate('<<Copy>>'))
        menu.add_command(label="Вставить", command=lambda: entry.event_generate('<<Paste>>'))
        menu.add_command(label="Вырезать", command=lambda: entry.event_generate('<<Cut>>'))

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        entry.bind("<Button-3>", show_menu)

    add_context_menu(entry_name)
    add_context_menu(entry_mkname)
    add_context_menu(entry_full_mk)

    canvas_frame = tk.Frame(search_window, bg="#0e0e0e")
    canvas_frame.pack(fill="both", expand=True, pady=10, padx=10)

    canvas = tk.Canvas(canvas_frame, bg="#0e0e0e", highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg="#0e0e0e")

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    from init_db import search_wallets

    def show_wallets():
        for widget in inner.winfo_children():
            widget.destroy()

        name_filter = entry_name.get().strip()
        mk4 = entry_mkname.get().strip()
        provided_mk = entry_full_mk.get().strip()

        if not mk4:
            tk.Label(inner, text="Введите первые 4 символа MK для поиска.", fg="red", bg="#0e0e0e").pack(pady=10)
            return

        wallets = search_wallets(name_filter, mk4, provided_mk)

        if not wallets:
            tk.Label(inner, text="Ничего не найдено", fg="red", bg="#0e0e0e").pack(pady=10)
            return

        for e in wallets:
            if e["decrypted"]:
                name = e["name"]
                login = e["login"]
                pwd = e["password"]
                host = e["host"]
                status = "Дешифровано"
            else:

                name = "*** (зашифровано)"
                login = "***"
                pwd = "***"
                host = "***"
                status = "Не расшифровано (неверный мастер-ключ)"

            card = tk.Frame(inner, bg="#121212", bd=0, padx=8, pady=6)
            tk.Label(card, text=f"Название: {name}", anchor="w", justify="left", fg="#00bfff", bg="#121212").pack(anchor="w")
            tk.Label(card, text=f"Логин: {login}", anchor="w", justify="left", fg="white", bg="#121212").pack(anchor="w")
            tk.Label(card, text=f"Пароль: {pwd}", anchor="w", justify="left", fg="white", bg="#121212").pack(anchor="w")
            tk.Label(card, text=f"Хост: {host}", anchor="w", justify="left", fg="white", bg="#121212").pack(anchor="w")
            tk.Label(card, text=f"Статус: {status}", anchor="w", justify="left", fg="#999999", bg="#121212").pack(anchor="w", pady=(4,0))

            if e["decrypted"]:
                def make_copy(pwd_val=e["password"]):
                    search_window.clipboard_clear()
                    search_window.clipboard_append(pwd_val)
                    messagebox.showinfo("Скопировано", "Пароль скопирован в буфер обмена.")
                tk.Button(card, text="Копировать пароль", command=make_copy, bg="#00bfff", fg="black", relief="flat").pack(pady=(6,0))

            card.pack(fill="x", pady=6)

    show_wallets()

    tk.Button(search_window, text="Обновить / Фильтровать", command=show_wallets,
              bg="#00bfff", fg="black", font=("Arial", 10, "bold"), width=25, relief="flat").pack(pady=8)


def login():
    username = entry_username.get()
    password = entry_password.get()

    user = check_user(username, password)
    if user:
        root.destroy()
        open_main_window(user[0], user[1])
    else:
        messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль.")

def register():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Ошибка", "Введите имя пользователя и пароль!")
        return

    success = add_user(username, password)
    if success:
        messagebox.showinfo("Успешно", "Пользователь зарегистрирован!")
    else:
        messagebox.showerror("Ошибка", "Такой пользователь уже существует.")

def open_main_window(username, master_key):
    root_main = tk.Tk()
    root_main.title("keySecret — корпоративная система")
    root_main.geometry("600x400")
    root_main.configure(bg="#0e0e0e")
    root_main.resizable(False, False)

    # Приветствие
    top_frame = tk.Frame(root_main, bg="#0e0e0e")
    top_frame.pack(fill="x", pady=10, padx=10)
    greeting = tk.Label(
        top_frame,
        text=f"Привет, {username}!",
        font=("Arial", 11, "bold"),
        fg="#00bfff",
        bg="#0e0e0e",
        anchor="e"
    )
    greeting.pack(anchor="e")

    center_frame = tk.Frame(root_main, bg="#0e0e0e")
    center_frame.pack(expand=True)

    button_style = {
        "bg": "#00bfff",
        "fg": "black",
        "font": ("Arial", 10, "bold"),
        "width": 30,
        "height": 2,
        "relief": "flat",
        "activebackground": "#0099cc",
        "activeforeground": "white"
    }

    tk.Button(center_frame, text="Поиск кошельков", **button_style,
              command=lambda: open_search_wallet_window(master_key)).pack(pady=5)
    tk.Button(center_frame, text="Создать новый кошелёк", **button_style,
              command=lambda: open_create_wallet_window(master_key)).pack(pady=5)
    tk.Button(center_frame, text="Мастер ключи", **button_style,
              command=lambda: open_master_keys_window(username)).pack(pady=5)

    tk.Button(center_frame, text="Создать заявку на мастер ключ", **button_style,
              command=lambda: open_create_master_key_request_window(username)).pack(pady=5)

    tk.Button(center_frame, text="Заявки на твой мастер ключ", **button_style,
              command=lambda: open_received_requests_window(username)).pack(pady=5)

    bottom_frame = tk.Frame(root_main, bg="#0e0e0e")
    bottom_frame.pack(side="bottom", fill="x", pady=10)
    footer = tk.Label(
        bottom_frame,
        text=f"Постоянный мастер-ключ: {master_key}",
        font=("Consolas", 10, "bold"),
        fg="#00bfff",
        bg="#0e0e0e"
    )
    footer.pack()

    root_main.mainloop()

root = tk.Tk()
root.title("keySecret — вход")
root.geometry("600x500")
root.configure(bg="#0e0e0e")
root.resizable(False, False)

if os.path.exists("logo.png"):
    img = Image.open("logo.png")
    img = img.resize((456, 160))
    logo = ImageTk.PhotoImage(img)
    logo_label = tk.Label(root, image=logo, bg="#0e0e0e")
    logo_label.image = logo
    logo_label.pack(pady=20)
else:
    tk.Label(root, text="keySecret", font=("Arial", 24, "bold"), fg="#00bfff", bg="#0e0e0e").pack(pady=30)


tk.Label(root, text="Имя пользователя:", fg="#00bfff", bg="#0e0e0e", font=("Arial", 10)).pack(pady=(10, 0))
entry_username = tk.Entry(root, bg="#1c1c1c", fg="white", insertbackground="white", relief="flat", width=30)
entry_username.pack(pady=5, ipady=5)

tk.Label(root, text="Пароль:", fg="#00bfff", bg="#0e0e0e", font=("Arial", 10)).pack(pady=(10, 0))
entry_password = tk.Entry(root, bg="#1c1c1c", fg="white", insertbackground="white", show="*", relief="flat", width=30)
entry_password.pack(pady=5, ipady=5)

tk.Button(root, text="Войти", command=login, bg="#00bfff", fg="black", font=("Arial", 10, "bold"), width=25, relief="flat").pack(pady=15)
tk.Button(root, text="Регистрация", command=register, bg="#1c1c1c", fg="#00bfff", font=("Arial", 9, "bold"), width=25, relief="flat").pack()


root.mainloop()
