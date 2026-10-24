import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

class HotelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление Отелем - MySQL Система")
        self.root.geometry("850x670")

        # Параметры соединения по умолчанию
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'hotel_db'
        }

        # Адаптация СУБД под длинные номера телефонов
        self.auto_fix_database_schema()

        # Создание контейнера вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_guests = ttk.Frame(self.notebook)
        self.tab_bookings = ttk.Frame(self.notebook)
        self.tab_config = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_guests, text="Регистрация Гостей")
        self.notebook.add(self.tab_bookings, text="Оформление Бронирования")
        self.notebook.add(self.tab_config, text="Настройки БД")

        self.create_guests_tab()
        self.create_bookings_tab()
        self.create_config_tab()

    def get_connection(self):
        """Установка соединения с базой данных MySQL"""
        return mysql.connector.connect(
            host=self.db_config['host'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database']
        )

    def auto_fix_database_schema(self):
        """Переводит поле Номер телефона из INT в VARCHAR без участия пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            alter_query = """
            ALTER TABLE `hotel_db`.`guests` 
            MODIFY COLUMN `Номер телефона` VARCHAR(45) NULL;
            """
            cursor.execute(alter_query)
            conn.commit()
            cursor.close()
            conn.close()
            print("[Система] База данных успешно проверена.")
        except Error as e:
            print(f"[Предупреждение] Первоначальная автонастройка пропущена. Ошибка: {e}")
    # --- ВКЛАДКА ГОСТЕЙ ---
    def create_guests_tab(self):
        form_frame = ttk.LabelFrame(self.tab_guests, text=" Данные нового гостя ")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="ID Гостя (int):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_guest_id = ttk.Entry(form_frame)
        self.ent_guest_id.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="ФИО гостя:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_guest_name = ttk.Entry(form_frame)
        self.ent_guest_name.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Номер телефона:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_guest_phone = ttk.Entry(form_frame)
        self.ent_guest_phone.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Эл. почта:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_guest_email = ttk.Entry(form_frame)
        self.ent_guest_email.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)

        btn_add_guest = ttk.Button(form_frame, text="Добавить гостя в базу", command=self.add_guest)
        btn_add_guest.grid(row=4, column=0, columnspan=2, pady=10)

        # Панель поиска по клиентам
        guest_search_frame = ttk.Frame(self.tab_guests)
        guest_search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(guest_search_frame, text="🔍 Быстрый поиск гостя:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        self.ent_guest_search = ttk.Entry(guest_search_frame, width=25)
        self.ent_guest_search.pack(side=tk.LEFT, padx=5)
        self.ent_guest_search.bind("<KeyRelease>", lambda event: self.refresh_guests()) 

        btn_clear_guest_search = ttk.Button(guest_search_frame, text="Сбросить", command=self.clear_guest_search)
        btn_clear_guest_search.pack(side=tk.LEFT, padx=5)

        # Таблица отображения
        table_frame = ttk.LabelFrame(self.tab_guests, text=" Список гостей в базе ")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "name", "phone", "email")
        self.guests_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.guests_tree.heading("id", text="ID")
        self.guests_tree.heading("name", text="ФИО")
        self.guests_tree.heading("phone", text="Номер телефона")
        self.guests_tree.heading("email", text="Почта")
        self.guests_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.guests_tree.yview)
        self.guests_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        action_frame = ttk.Frame(self.tab_guests)
        action_frame.pack(pady=5, fill=tk.X)
        
        btn_refresh = ttk.Button(action_frame, text="🔄 Обновить список", command=self.refresh_guests)
        btn_refresh.pack(side=tk.LEFT, padx=20)

        btn_delete_guest = ttk.Button(action_frame, text="🗑️ Удалить выбранного гостя", command=self.delete_guest)
        btn_delete_guest.pack(side=tk.RIGHT, padx=20)
    def add_guest(self):
        g_id = self.ent_guest_id.get().strip()
        name = self.ent_guest_name.get().strip()
        phone = self.ent_guest_phone.get().strip() 
        email = self.ent_guest_email.get().strip()

        if not g_id or not name or not phone:
            messagebox.showerror("Ошибка", "Заполните обязательные поля (ID, ФИО, Телефон)!")
            return

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO guests (idguests, ФИО, `Номер телефона`, Почта) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (int(g_id), name, phone, email))
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Успех", f"Гость {name} успешно добавлен!")
            self.refresh_guests()
            
            self.ent_guest_id.delete(0, tk.END)
            self.ent_guest_name.delete(0, tk.END)
            self.ent_guest_phone.delete(0, tk.END)
            self.ent_guest_email.delete(0, tk.END)
        except Error as e:
            messagebox.showerror("Ошибка SQL", f"Не удалось добавить запись:\n{e}")

    def delete_guest(self):
        selected_item = self.guests_tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите гостя в таблице для удаления!")
            return
            
        guest_data = self.guests_tree.item(selected_item)['values']
        guest_id = guest_data[0]
        guest_name = guest_data[1]
        
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить гостя {guest_name} (ID: {guest_id})?"):
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM guests WHERE idguests = %s", (int(guest_id),))
                conn.commit()
                cursor.close()
                conn.close()
                
                messagebox.showinfo("Успех", "Запись гостя удалена!")
                self.refresh_guests()
            except Error as e:
                messagebox.showerror("Ошибка SQL", f"Не удалось удалить. Убедитесь, что у гостя нет бронирований:\n\n{e}")

    def clear_guest_search(self):
        self.ent_guest_search.delete(0, tk.END)
        self.refresh_guests()

    def refresh_guests(self):
        for row in self.guests_tree.get_children():
            self.guests_tree.delete(row)
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            search_query = self.ent_guest_search.get().strip()
            if search_query:
                sql = """SELECT idguests, ФИО, `Номер телефона`, Почта FROM guests 
                         WHERE ФИО LIKE %s OR `Номер телефона` LIKE %s OR CAST(idguests AS CHAR) LIKE %s"""
                cursor.execute(sql, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
            else:
                cursor.execute("SELECT idguests, ФИО, `Номер телефона`, Почта FROM guests")
            
            for row in cursor.fetchall():
                self.guests_tree.insert("", tk.END, values=row)
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Ошибка обновления гостей: {e}")
    # --- ВКЛАДКА БРОНИРОВАНИЯ ---
    def create_bookings_tab(self):
        form_frame = ttk.LabelFrame(self.tab_bookings, text=" Новое бронирование ")
        form_frame.pack(fill=tk.X, padx=10, pady=5)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="ID Бронирования (int):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_book_id = ttk.Entry(form_frame)
        self.ent_book_id.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Дата заселения (ГГГГ-ММ-ДД):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_book_date = ttk.Entry(form_frame)
        self.ent_book_date.insert(0, "2026-10-13")
        self.ent_book_date.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Статус брони:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.cmb_book_status = ttk.Combobox(form_frame, values=["Забронировано", "Оплачено", "Выселен"], state="readonly")
        self.cmb_book_status.current(0)
        self.cmb_book_status.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Итоговая сумма:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_book_amount = ttk.Entry(form_frame)
        self.ent_book_amount.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="ID Гостя (FK):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_book_guest_id = ttk.Entry(form_frame)
        self.ent_book_guest_id.grid(row=4, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="ID Купона (FK):").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_book_coupon_id = ttk.Entry(form_frame)
        self.ent_book_coupon_id.insert(0, "1")
        self.ent_book_coupon_id.grid(row=5, column=1, padx=5, pady=5, sticky=tk.EW)

        btn_add_booking = ttk.Button(form_frame, text="Оформить бронь", command=self.add_booking)
        btn_add_booking.grid(row=6, column=0, columnspan=2, pady=5)

        # Панель живого поиска и фильтрации броней
        search_frame = ttk.LabelFrame(self.tab_bookings, text=" Поиск и Фильтры ")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5, pady=5)
        self.ent_search_query = ttk.Entry(search_frame, width=12)
        self.ent_search_query.pack(side=tk.LEFT, padx=5, pady=5)
        self.ent_search_query.bind("<KeyRelease>", lambda event: self.refresh_bookings())

        ttk.Label(search_frame, text="Статус:").pack(side=tk.LEFT, padx=5, pady=5)
        self.cmb_filter_status = ttk.Combobox(search_frame, values=["Все", "Забронировано", "Оплачено", "Выселен"], state="readonly", width=12)
        self.cmb_filter_status.current(0)
        self.cmb_filter_status.pack(side=tk.LEFT, padx=5, pady=5)
        self.cmb_filter_status.bind("<<ComboboxSelected>>", lambda event: self.refresh_bookings())

        ttk.Label(search_frame, text="Дата:").pack(side=tk.LEFT, padx=5, pady=5)
        self.ent_filter_date = ttk.Entry(search_frame, width=11)
        self.ent_filter_date.pack(side=tk.LEFT, padx=5, pady=5)
        self.ent_filter_date.bind("<KeyRelease>", lambda event: self.refresh_bookings())

        btn_clear_filters = ttk.Button(search_frame, text="❌ Сброс", command=self.clear_filters)
        btn_clear_filters.pack(side=tk.LEFT, padx=10, pady=5)

        # Статистическая сводка
        self.stats_frame = ttk.Frame(self.tab_bookings)
        self.stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_total_bookings = ttk.Label(self.stats_frame, text="Найдено: 0", font=("Arial", 10, "bold"))
        self.lbl_total_bookings.pack(side=tk.LEFT, padx=15)
        
        self.lbl_total_revenue = ttk.Label(self.stats_frame, text="Сумма: 0.00 руб.", font=("Arial", 10, "bold"))
        self.lbl_total_revenue.pack(side=tk.LEFT, padx=15)

        # Вывод таблицы на экран
        table_frame = ttk.LabelFrame(self.tab_bookings, text=" Список бронирований ")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "date", "status", "amount", "guest_id", "coupon_id")
        self.bookings_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.bookings_tree.heading("id", text="ID Брони")
        self.bookings_tree.heading("date", text="Дата заселения")
        self.bookings_tree.heading("status", text="Статус")
        self.bookings_tree.heading("amount", text="Сумма")
        self.bookings_tree.heading("guest_id", text="ID Гостя")
        self.bookings_tree.heading("coupon_id", text="ID Купона")
        
        for col in columns:
            self.bookings_tree.column(col, width=110, anchor=tk.CENTER)

        self.bookings_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.bookings_tree.yview)
        self.bookings_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        action_frame_b = ttk.Frame(self.tab_bookings)
        action_frame_b.pack(pady=5, fill=tk.X)

        btn_refresh_books = ttk.Button(action_frame_b, text="🔄 Обновить из БД", command=self.refresh_bookings)
        btn_refresh_books.pack(side=tk.LEFT, padx=20)

        btn_delete_booking = ttk.Button(action_frame_b, text="🗑️ Удалить выбранную бронь", command=self.delete_booking)
        btn_delete_booking.pack(side=tk.RIGHT, padx=20)
    def add_booking(self):
        b_id = self.ent_book_id.get().strip()
        b_date = self.ent_book_date.get().strip()
        status = self.cmb_book_status.get()
        amount = self.ent_book_amount.get().strip()
        g_id = self.ent_book_guest_id.get().strip()
        c_id = self.ent_book_coupon_id.get().strip()

        if not all([b_id, b_date, amount, g_id, c_id]):
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT idcoupons FROM coupons WHERE idcoupons = %s", (int(c_id),))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO coupons (idcoupons, информация, `номер купона`) VALUES (%s, %s, %s)", 
                               (int(c_id), "Авто-купон", "AUTO-" + str(c_id)))
                conn.commit()
            
            query = """INSERT INTO bookings (`idbookings`, `дата заселения`, `статус брони`, `итог сумма`, `guests_idguests`, `coupons_idcoupons`) 
                       VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (int(b_id), b_date, status, float(amount), int(g_id), int(c_id)))
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Успех", f"Бронирование №{b_id} успешно сохранено!")
            self.refresh_bookings()
            
            self.ent_book_id.delete(0, tk.END)
            self.ent_book_amount.delete(0, tk.END)
            self.ent_book_guest_id.delete(0, tk.END)
        except Error as e:
            messagebox.showerror("Ошибка SQL", f"Ошибка добавления брони:\n\n{e}")

    def delete_booking(self):
        selected_item = self.bookings_tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите бронь в таблице для удаления!")
            return
            
        booking_id = self.bookings_tree.item(selected_item)['values'][0]
        
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить бронирование №{booking_id}?"):
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bookings WHERE idbookings = %s", (int(booking_id),))
                conn.commit()
                cursor.close()
                conn.close()
                
                messagebox.showinfo("Успех", "Бронирование успешно удалено!")
                self.refresh_bookings()
            except Error as e:
                messagebox.showerror("Ошибка SQL", f"Не удалось удалить запись бронирования:\n\n{e}")

    def clear_filters(self):
        self.ent_search_query.delete(0, tk.END)
        self.cmb_filter_status.current(0)
        self.ent_filter_date.delete(0, tk.END)
        self.refresh_bookings()

    def refresh_bookings(self):
        for row in self.bookings_tree.get_children():
            self.bookings_tree.delete(row)
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = "SELECT `idbookings`, `дата заселения`, `статус брони`, `итог сумма`, `guests_idguests`, `coupons_idcoupons` FROM bookings WHERE 1=1"
            params = []
            
            search_val = self.ent_search_query.get().strip()
            if search_val:
                query += " AND (CAST(`idbookings` AS CHAR) LIKE %s OR CAST(`guests_idguests` AS CHAR) LIKE %s)"
                params.extend([f"%{search_val}%", f"%{search_val}%"])
                
            status_val = self.cmb_filter_status.get()
            if status_val != "Все":
                query += " AND `статус брони` = %s"
                params.append(status_val)
                
            date_val = self.ent_filter_date.get().strip()
            if date_val:
                query += " AND CAST(`дата заселения` AS CHAR) LIKE %s"
                params.append(f"%{date_val}%")
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            total_count = len(rows)
            total_money = 0.0
            
            for row in rows:
                self.bookings_tree.insert("", tk.END, values=row)
                if row[3] is not None:
                    total_money += float(row[3])
            cursor.close()
            conn.close()
            
            self.lbl_total_bookings.config(text=f"Найдено: {total_count}")
            self.lbl_total_revenue.config(text=f"Сумма: {total_money:.2f} руб.")
        except Error as e:
            print(f"Ошибка статистики: {e}")

    # --- ВКЛАДКА НАСТРОЕК БД ---
    def create_config_tab(self):
        form_frame = ttk.LabelFrame(self.tab_config, text=" Параметры соединения с сервером MySQL ")
        form_frame.pack(padx=20, pady=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Хост (Host):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.ent_host = ttk.Entry(form_frame)
        self.ent_host.insert(0, self.db_config['host'])
        self.ent_host.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)

        ttk.Label(form_frame, text="Пользователь (User):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.ent_user = ttk.Entry(form_frame)
        self.ent_user.insert(0, self.db_config['user'])
        self.ent_user.grid(row=1, column=1, padx=10, pady=10, sticky=tk.EW)

        ttk.Label(form_frame, text="Пароль (Password):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.ent_password = ttk.Entry(form_frame, show="*")
        self.ent_password.insert(0, self.db_config['password'])
        self.ent_password.grid(row=2, column=1, padx=10, pady=10, sticky=tk.EW)

        ttk.Label(form_frame, text="База данных (Schema):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.ent_database = ttk.Entry(form_frame)
        self.ent_database.insert(0, self.db_config['database'])
        self.ent_database.grid(row=3, column=1, padx=10, pady=10, sticky=tk.EW)

        btn_save_config = ttk.Button(form_frame, text="Применить настройки", command=self.save_config)
        btn_save_config.grid(row=4, column=0, columnspan=2, pady=15)

    def save_config(self):
        self.db_config['host'] = self.ent_host.get().strip()
        self.db_config['user'] = self.ent_user.get().strip()
        self.db_config['password'] = self.ent_password.get()
        self.db_config['database'] = self.ent_database.get().strip()
        try:
            self.auto_fix_database_schema()
            conn = self.get_connection()
            conn.close()
            messagebox.showinfo("Успех", "Соединение успешно установлено!")
            self.refresh_guests()
            self.refresh_bookings()
        except Error as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться:\n\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HotelApp(root)
    root.mainloop()
