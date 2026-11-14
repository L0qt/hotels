from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_hotel_key'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_ROOMS = 10 

class DatabaseManager:
    def __init__(self, db_name='hotel.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT,
                    role TEXT DEFAULT 'user', fullname TEXT, phone TEXT, email TEXT
                );
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price REAL,
                    description TEXT, images TEXT, amenities TEXT
                );
                CREATE TABLE IF NOT EXISTS menu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL,
                    description TEXT, image TEXT
                );
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER, user_id INTEGER,
                    check_in TEXT, check_out TEXT, status TEXT DEFAULT 'Забронировано', total_price REAL
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER, user_id INTEGER,
                    rating INTEGER, comment TEXT, date TEXT
                );
                CREATE TABLE IF NOT EXISTS food_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, room_id INTEGER,
                    item_name TEXT, price REAL, quantity INTEGER, status TEXT DEFAULT 'Готовится', date TEXT
                );
            """)
            
            if not cursor.execute("SELECT * FROM users WHERE username = 'admin'").fetchone():
                cursor.execute("INSERT INTO users (username, password, role, fullname) VALUES (?, ?, ?, ?)",
                               ('admin', generate_password_hash('admin'), 'admin', 'Главный Администратор'))
            
            if not cursor.execute("SELECT * FROM users WHERE username = 'user'").fetchone():
                cursor.execute("INSERT INTO users (username, password, role, fullname, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                               ('user', generate_password_hash('user'), 'user', 'Алексей Иванов', '+79261234567', 'alex@mail.ru'))
            
            if cursor.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
                cursor.execute("INSERT INTO rooms (title, price, description, images, amenities) VALUES (?, ?, ?, ?, ?)",
                               ('Стандартный номер', 3500.0, 'Уютный номер с одной большой кроватью.', '/static/placeholder.jpg', 'Wi-Fi, Кондиционер, ТВ, Мини-бар'))
                cursor.execute("INSERT INTO rooms (title, price, description, images, amenities) VALUES (?, ?, ?, ?, ?)",
                               ('Люкс с видом на море', 12000.0, 'Роскошный номер с панорамными окнами и джакузи.', '/static/placeholder.jpg', 'Wi-Fi, Джакузи, Панорамный вид, Завтрак включен'))
            
            if cursor.execute("SELECT COUNT(*) FROM menu").fetchone()[0] == 0:
                cursor.execute("INSERT INTO menu (name, price, description, image) VALUES (?, ?, ?, ?)",
                               ('Круассан с лососем', 650.0, 'Свежий круассан, сливочный сыр, лосось', '/static/placeholder.jpg'))
                cursor.execute("INSERT INTO menu (name, price, description, image) VALUES (?, ?, ?, ?)",
                               ('Стейк Рибай', 2500.0, 'Мраморная говядина, овощи гриль', '/static/placeholder.jpg'))
            
            if cursor.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0:
                cursor.executescript("""
                    INSERT INTO reviews (room_id, user_id, rating, comment, date) VALUES 
                    (1, 2, 5, 'Отличный номер, всё чисто и уютно!', '2026-10-20'),
                    (2, 1, 5, 'Вид на море просто потрясающий!', '2026-10-21');
                """)
            conn.commit()

    def save_files(self, files):
        paths = []
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1].lower()
                filename = f"{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                paths.append(f'/static/uploads/{filename}')
        return ','.join(paths)

    def get_user_by_username(self, username):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    def get_user_by_id(self, user_id):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    def create_user(self, username, password, fullname, phone, email):
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO users (username, password, role, fullname, phone, email) VALUES (?, ?, 'user', ?, ?, ?)",
                           (username, generate_password_hash(password), fullname, phone, email))
            conn.commit()
    def update_user(self, user_id, fullname, phone, email):
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE users SET fullname = ?, phone = ?, email = ? WHERE id = ?", (fullname, phone, email, user_id))
            conn.commit()
    def get_all_users(self):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM users").fetchall()
    def delete_user(self, user_id):
        with self.get_connection() as conn:
            conn.cursor().execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
    def update_user_role(self, user_id, role):
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()

    def get_all_rooms(self):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM rooms").fetchall()
    def get_room(self, room_id):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    
    # ОГРАНИЧЕНИЕ ЦЕНЫ КОМНАТЫ (МИНИМУМ 1000)
    def add_room(self, title, price, description, images, amenities):
        price = max(float(price), 1000.0)
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO rooms (title, price, description, images, amenities) VALUES (?, ?, ?, ?, ?)", (title, price, description, images, amenities))
            conn.commit()
            
    def update_room(self, room_id, title, price, description, images, amenities):
        price = max(float(price), 1000.0)
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE rooms SET title=?, price=?, description=?, images=?, amenities=? WHERE id=?", (title, price, description, images, amenities, room_id))
            conn.commit()
            
    def update_room_price_title(self, room_id, title, price):
        price = max(float(price), 1000.0)
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE rooms SET title = ?, price = ? WHERE id = ?", (title, price, room_id))
            conn.commit()

    def delete_room(self, room_id):
        with self.get_connection() as conn:
            conn.cursor().execute("DELETE FROM rooms WHERE id = ?", (room_id,))
            conn.commit()

    def get_all_menu(self):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM menu").fetchall()
    def get_menu_item(self, item_id):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM menu WHERE id = ?", (item_id,)).fetchone()
    
    # ОГРАНИЧЕНИЕ ЦЕНЫ БЛЮДА (МИНИМУМ 200)
    def add_menu_item(self, name, price, description, image):
        price = max(float(price), 200.0)
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO menu (name, price, description, image) VALUES (?, ?, ?, ?)", (name, price, description, image))
            conn.commit()
            
    def update_menu_item(self, item_id, name, price, description, image):
        price = max(float(price), 200.0)
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE menu SET name=?, price=?, description=?, image=? WHERE id=?", (name, price, description, image, item_id))
            conn.commit()
            
    def update_menu_price_name(self, item_id, name, price):
        price = max(float(price), 200.0)
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE menu SET name = ?, price = ? WHERE id = ?", (name, price, item_id))
            conn.commit()

    def delete_menu_item(self, item_id):
        with self.get_connection() as conn:
            conn.cursor().execute("DELETE FROM menu WHERE id = ?", (item_id,))
            conn.commit()

    def add_booking(self, room_id, user_id, check_in, check_out, total_price):
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO bookings (room_id, user_id, check_in, check_out, total_price) VALUES (?, ?, ?, ?, ?)", (room_id, user_id, check_in, check_out, total_price))
            conn.commit()
    def get_user_bookings(self, user_id):
        with self.get_connection() as conn:
            return conn.cursor().execute("""SELECT b.*, r.title, r.images FROM bookings b JOIN rooms r ON b.room_id = r.id WHERE b.user_id = ? ORDER BY b.id DESC""", (user_id,)).fetchall()
    def get_all_bookings(self):
        with self.get_connection() as conn:
            return conn.cursor().execute("""SELECT b.*, r.title, u.fullname as guest_name FROM bookings b JOIN rooms r ON b.room_id = r.id JOIN users u ON b.user_id = u.id ORDER BY b.id DESC""").fetchall()
    def update_booking(self, booking_id, check_in, check_out, status, total_price):
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE bookings SET check_in=?, check_out=?, status=?, total_price=? WHERE id=?", (check_in, check_out, status, total_price, booking_id))
            conn.commit()
    def delete_booking(self, booking_id):
        with self.get_connection() as conn:
            conn.cursor().execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            conn.commit()

    def add_review(self, room_id, user_id, rating, comment):
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO reviews (room_id, user_id, rating, comment, date) VALUES (?, ?, ?, ?, ?)", (room_id, user_id, rating, comment, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
    def get_room_reviews(self, room_id):
        with self.get_connection() as conn:
            return conn.cursor().execute("""SELECT r.*, u.fullname as guest_name FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.room_id = ? ORDER BY r.id DESC""", (room_id,)).fetchall()
    def get_all_reviews(self):
        with self.get_connection() as conn:
            return conn.cursor().execute("""SELECT r.*, u.fullname as guest_name, rm.title as room_title FROM reviews r JOIN users u ON r.user_id = u.id JOIN rooms rm ON r.room_id = rm.id ORDER BY r.id DESC""").fetchall()
    def delete_review(self, review_id):
        with self.get_connection() as conn:
            conn.cursor().execute("DELETE FROM reviews WHERE id = ?", (review_id,))
            conn.commit()

    def add_food_order(self, user_id, room_id, item_name, price, quantity):
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO food_orders (user_id, room_id, item_name, price, quantity, date) VALUES (?, ?, ?, ?, ?, ?)", (user_id, room_id, item_name, price, quantity, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
    def get_user_food_orders(self, user_id):
        with self.get_connection() as conn:
            return conn.cursor().execute("""SELECT f.*, r.title as room_title FROM food_orders f JOIN rooms r ON f.room_id = r.id WHERE f.user_id = ? ORDER BY f.id DESC""", (user_id,)).fetchall()
    def get_all_food_orders(self):
        with self.get_connection() as conn:
            return conn.cursor().execute("""SELECT f.*, u.fullname as guest_name, r.title as room_title FROM food_orders f JOIN users u ON f.user_id = u.id JOIN rooms r ON f.room_id = r.id ORDER BY f.id DESC""").fetchall()
    def update_food_order_status(self, order_id, status):
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE food_orders SET status = ? WHERE id = ?", (status, order_id))
            conn.commit()

db = DatabaseManager()

ACTIVE_BOOKING_STATUSES = ('Забронировано', 'Оплачено')
CHECK_IN_REMIND_DAYS = 3

def get_user_notifications(bookings):
    today = datetime.now().date()
    notifications = []
    for b in bookings:
        if b['status'] not in ACTIVE_BOOKING_STATUSES: continue
        try:
            check_in = datetime.strptime(b['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(b['check_out'], '%Y-%m-%d').date()
        except (ValueError, TypeError): continue
        room_title = b['title'] or f"№{b['room_id']}"
        days_to_in = (check_in - today).days
        days_to_out = (check_out - today).days
        if days_to_in == 0:
            notifications.append({'type': 'warning', 'icon': '🔑', 'title': 'Заезд сегодня', 'message': f'Сегодня заезд в номер «{room_title}». Возьмите документы на ресепшен.', 'booking_id': b['id']})
        elif 0 < days_to_in <= CHECK_IN_REMIND_DAYS:
            notifications.append({'type': 'info', 'icon': '📅', 'title': 'Скоро заезд', 'message': f'Напоминание: заезд в номер «{room_title}» через {days_to_in} дн. ({b["check_in"]}).', 'booking_id': b['id']})
        if days_to_out == 0 and today >= check_in:
            notifications.append({'type': 'danger', 'icon': '🚪', 'title': 'Выезд сегодня', 'message': f'Сегодня выезд из номера «{room_title}». Освободите номер до 12:00.', 'booking_id': b['id']})
        elif days_to_out > 0 and check_in <= today < check_out:
            notifications.append({'type': 'success', 'icon': '🏨', 'title': 'Вы проживаете в отеле', 'message': f'Номер «{room_title}». Выезд через {days_to_out} дн. ({b["check_out"]}).', 'booking_id': b['id']})
    return notifications

@app.context_processor
def inject_notifications():
    if session.get('role') == 'user':
        try: return {'notifications': get_user_notifications(db.get_user_bookings(session['user_id']))}
        except Exception: return {'notifications': []}
    return {'notifications': []}

@app.route('/')
def index(): return render_template('index.html', rooms=db.get_all_rooms(), reviews=db.get_all_reviews()[:3])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = db.get_user_by_username(request.form['username'])
        if user and check_password_hash(user['password'], request.form['password']):
            session.update({'user_id': user['id'], 'role': user['role'], 'fullname': user['fullname']})
            flash(f'Добро пожаловать, {user["fullname"]}!', 'success')
            return redirect(url_for('admin_dashboard' if user['role'] == 'admin' else 'index'))
        flash('Неверный логин или пароль', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if db.get_user_by_username(request.form['username']):
            flash('Пользователь уже существует', 'danger')
            return redirect(url_for('register'))
        db.create_user(request.form['username'], request.form['password'], request.form['fullname'], request.form['phone'], request.form['email'])
        flash('Регистрация успешна! Войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.get_user_by_id(session['user_id'])
    if request.method == 'POST':
        db.update_user(session['user_id'], request.form['fullname'], request.form['phone'], request.form['email'])
        session['fullname'] = request.form['fullname']
        flash('Профиль обновлен!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/room/<int:room_id>')
def room_detail(room_id):
    room = db.get_room(room_id)
    if not room: return "Номер не найден", 404
    images = room['images'].split(',') if room['images'] else []
    return render_template('room_detail.html', room=room, images=images, reviews=db.get_room_reviews(room_id))

@app.route('/book/<int:room_id>', methods=['POST'])
def book_room(room_id):
    if session.get('role') != 'user':
        flash('Войдите как гость для бронирования.', 'warning')
        return redirect(url_for('login'))
    room = db.get_room(room_id)
    check_in, check_out = request.form['check_in'], request.form['check_out']
    try: days = max((datetime.strptime(check_out, '%Y-%m-%d') - datetime.strptime(check_in, '%Y-%m-%d')).days, 1)
    except: days = 1
    db.add_booking(room_id, session['user_id'], check_in, check_out, room['price'] * days)
    flash(f'Номер "{room["title"]}" успешно забронирован!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/review/<int:room_id>', methods=['POST'])
def add_review(room_id):
    if session.get('role') != 'user':
        flash('Только гости могут оставлять отзывы.', 'warning')
        return redirect(url_for('login'))
    db.add_review(room_id, session['user_id'], int(request.form['rating']), request.form['comment'])
    flash('Спасибо за отзыв!', 'success')
    return redirect(url_for('room_detail', room_id=room_id))

@app.route('/user')
def user_dashboard():
    if session.get('role') != 'user': return "Доступ запрещен", 403
    return render_template('user_dashboard.html', bookings=db.get_user_bookings(session['user_id']), food_orders=db.get_user_food_orders(session['user_id']))

@app.route('/food')
def food_menu():
    if 'user_id' not in session:
        flash('Войдите, чтобы заказать еду.', 'warning')
        return redirect(url_for('login'))
    bookings = [b for b in db.get_user_bookings(session['user_id']) if b['status'] in ['Забронировано', 'Оплачено']]
    return render_template('food_menu.html', menu=db.get_all_menu(), bookings=bookings)

@app.route('/food/order', methods=['POST'])
def order_food():
    if session.get('role') != 'user': return "Доступ запрещен", 403
    db.add_food_order(session['user_id'], request.form['room_id'], request.form['item_name'], float(request.form['price']), int(request.form['quantity']))
    flash('Заказ принят! Ожидайте доставку.', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    bookings = db.get_all_bookings()
    return render_template('admin_dashboard.html', 
                           users=db.get_all_users(), rooms=db.get_all_rooms(), menu=db.get_all_menu(),
                           bookings=bookings, food_orders=db.get_all_food_orders(), 
                           reviews=db.get_all_reviews(), revenue=sum(float(b['total_price']) for b in bookings if b['total_price']))

@app.route('/admin/batch_edit_rooms', methods=['GET', 'POST'])
def admin_batch_edit_rooms():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if request.method == 'POST':
        selected_ids = request.form.getlist('selected_rooms')
        if not selected_ids:
            flash('Вы не выбрали ни одного номера!', 'warning')
            return redirect(url_for('admin_batch_edit_rooms'))
        for room_id in selected_ids:
            title = request.form.get(f'title_{room_id}')
            price = request.form.get(f'price_{room_id}')
            if title and price: db.update_room_price_title(room_id, title, float(price))
        flash(f'Успешно обновлено номеров: {len(selected_ids)}', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_batch_edit.html', rooms=db.get_all_rooms())

# НОВЫЙ МАРШРУТ ДЛЯ МАССОВОГО РЕДАКТИРОВАНИЯ МЕНЮ
@app.route('/admin/batch_edit_menu', methods=['GET', 'POST'])
def admin_batch_edit_menu():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if request.method == 'POST':
        selected_ids = request.form.getlist('selected_items')
        if not selected_ids:
            flash('Вы не выбрали ни одного блюда!', 'warning')
            return redirect(url_for('admin_batch_edit_menu'))
        for item_id in selected_ids:
            name = request.form.get(f'name_{item_id}')
            price = request.form.get(f'price_{item_id}')
            if name and price: db.update_menu_price_name(item_id, name, float(price))
        flash(f'Успешно обновлено блюд: {len(selected_ids)}', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_batch_edit_menu.html', menu=db.get_all_menu())

@app.route('/admin/add_room', methods=['GET', 'POST'])
def admin_add_room():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if len(db.get_all_rooms()) >= MAX_ROOMS:
        flash(f'Достигнут лимит номеров ({MAX_ROOMS})! Удалите старый номер.', 'danger')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        files = request.files.getlist('images')
        images_str = db.save_files(files)
        if not images_str: images_str = '/static/placeholder.jpg'
        db.add_room(request.form['title'], float(request.form['price']), request.form['description'], images_str, request.form['amenities'])
        flash('Номер добавлен!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_room.html')

@app.route('/admin/edit_room/<int:room_id>', methods=['GET', 'POST'])
def admin_edit_room(room_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    room = db.get_room(room_id)
    if request.method == 'POST':
        files = request.files.getlist('images')
        new_images = db.save_files(files)
        images_str = new_images if new_images else room['images']
        db.update_room(room_id, request.form['title'], float(request.form['price']), request.form['description'], images_str, request.form['amenities'])
        flash('Номер обновлен!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_edit_room.html', room=room)

@app.route('/admin/delete_room/<int:room_id>')
def admin_delete_room(room_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    db.delete_room(room_id)
    flash('Номер удален!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_menu', methods=['GET', 'POST'])
def admin_add_menu():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if request.method == 'POST':
        image_str = db.save_files([request.files.get('image')]) or '/static/placeholder.jpg'
        db.add_menu_item(request.form['name'], float(request.form['price']), request.form['description'], image_str)
        flash('Блюдо добавлено!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_menu.html')

@app.route('/admin/edit_menu/<int:item_id>', methods=['GET', 'POST'])
def admin_edit_menu(item_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    item = db.get_menu_item(item_id)
    if request.method == 'POST':
        new_image = db.save_files([request.files.get('image')])
        image_str = new_image if new_image else item['image']
        db.update_menu_item(item_id, request.form['name'], float(request.form['price']), request.form['description'], image_str)
        flash('Блюдо обновлено!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_edit_menu.html', item=item)

@app.route('/admin/delete_menu/<int:item_id>')
def admin_delete_menu(item_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    db.delete_menu_item(item_id)
    flash('Блюдо удалено!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_booking/<int:booking_id>', methods=['POST'])
def admin_edit_booking(booking_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    db.update_booking(booking_id, request.form['check_in'], request.form['check_out'], request.form['status'], float(request.form['total_price']))
    flash('Бронь обновлена!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_booking/<int:booking_id>')
def admin_delete_booking(booking_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    db.delete_booking(booking_id)
    flash('Бронь удалена!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_food/<int:order_id>', methods=['POST'])
def admin_update_food(order_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    db.update_food_order_status(order_id, request.form['status'])
    flash('Статус заказа обновлен!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_review/<int:review_id>')
def admin_delete_review(review_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    db.delete_review(review_id)
    flash('Отзыв удален!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if user_id == session['user_id']: 
        flash('Нельзя удалить самого себя!', 'danger')
        return redirect(url_for('admin_dashboard'))
    db.delete_user(user_id)
    flash('Пользователь удален!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/make_admin/<int:user_id>')
def admin_make_admin(user_id):
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    db.update_user_role(user_id, 'admin')
    flash('Пользователь повышен до Администратора!', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
