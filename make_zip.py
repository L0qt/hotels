import os
import zipfile

FOLDER_NAME = "grand_hotel_web"
ZIP_NAME = "grand_hotel_web.zip"

app_py = r'''
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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
                filename = secure_filename(file.filename)
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
    def add_room(self, title, price, description, images, amenities):
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO rooms (title, price, description, images, amenities) VALUES (?, ?, ?, ?, ?)", (title, price, description, images, amenities))
            conn.commit()
    def update_room(self, room_id, title, price, description, images, amenities):
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE rooms SET title=?, price=?, description=?, images=?, amenities=? WHERE id=?", (title, price, description, images, amenities, room_id))
            conn.commit()
    def delete_room(self, room_id):
        with self.get_connection() as conn:
            conn.cursor().execute("DELETE FROM rooms WHERE id = ?", (room_id,))
            conn.commit()

    def get_all_menu(self):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM menu").fetchall()
    def get_menu_item(self, item_id):
        with self.get_connection() as conn: return conn.cursor().execute("SELECT * FROM menu WHERE id = ?", (item_id,)).fetchone()
    def add_menu_item(self, name, price, description, image):
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT INTO menu (name, price, description, image) VALUES (?, ?, ?, ?)", (name, price, description, image))
            conn.commit()
    def update_menu_item(self, item_id, name, price, description, image):
        with self.get_connection() as conn:
            conn.cursor().execute("UPDATE menu SET name=?, price=?, description=?, image=? WHERE id=?", (name, price, description, image, item_id))
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

@app.route('/')
def index():
    return render_template('index.html', rooms=db.get_all_rooms(), reviews=db.get_all_reviews()[:3])

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
    try:
        days = max((datetime.strptime(check_out, '%Y-%m-%d') - datetime.strptime(check_in, '%Y-%m-%d')).days, 1)
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
'''

FAVICON = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0OCIgZmlsbD0iIzExMTExMSIgc3Ryb2tlPSIjYzhhOTdlIiBzdHJva2Utd2lkdGg9IjQiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9ImNlbnRyYWwiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJQbGF5ZmFpciBEaXNwbGF5LCBzZXJpZiIgZm9udC1zaXplPSI2MCIgZmlsbD0iI2M4YTk3ZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkc8L3RleHQ+PC9zdmc+"

base_html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grand Hotel - Официальный сайт</title>
    <link rel="icon" href="{FAVICON}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{ --gold: #c8a97e; --dark: #111111; --light: #f8f5f0; --text: #333333; }}
        body {{ font-family: 'Montserrat', sans-serif; background-color: var(--light); color: var(--text); overflow-x: hidden; }}
        h1, h2, h3, h4, h5 {{ font-family: 'Playfair Display', serif; font-weight: 700; }}
        .navbar {{ background-color: rgba(17, 17, 17, 0.95) !important; backdrop-filter: blur(10px); transition: all 0.3s; padding: 15px 0; }}
        .navbar-brand {{ font-family: 'Playfair Display', serif; font-size: 1.8rem; color: var(--gold) !important; letter-spacing: 2px; }}
        .nav-link {{ color: rgba(255,255,255,0.8) !important; font-weight: 500; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; margin: 0 5px; }}
        .nav-link:hover, .nav-link.active {{ color: var(--gold) !important; }}
        .btn-gold {{ background-color: var(--gold); color: white; border: none; padding: 10px 25px; border-radius: 0; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; transition: all 0.3s; }}
        .btn-gold:hover {{ background-color: #b8956a; color: white; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(200, 169, 126, 0.4); }}
        .btn-outline-gold {{ border: 1px solid var(--gold); color: var(--gold); border-radius: 0; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; transition: all 0.3s; }}
        .btn-outline-gold:hover {{ background-color: var(--gold); color: white; }}
        .card {{ border: none; border-radius: 0; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: transform 0.3s, box-shadow 0.3s; background: white; }}
        .card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.1); }}
        .footer {{ background-color: var(--dark); color: rgba(255,255,255,0.7); padding: 50px 0 20px; margin-top: 60px; }}
        .text-gold {{ color: var(--gold); }}
        .form-control, .form-select {{ border-radius: 0; border: 1px solid #ddd; padding: 12px; }}
        .form-control:focus, .form-select:focus {{ box-shadow: none; border-color: var(--gold); }}
        .carousel-item img {{ height: 500px; object-fit: cover; }}
        
        /* --- ИСПРАВЛЕННЫЕ СТИЛИ ДЛЯ ЧИТАЕМОСТИ АДМИНКИ --- */
        .nav-tabs {{ border-bottom: 2px solid #c8a97e; }}
        .nav-tabs .nav-link {{ color: #111 !important; font-weight: 800; font-size: 1.05rem; border: none; margin-right: 10px; transition: all 0.2s; }}
        .nav-tabs .nav-link:hover {{ color: #c8a97e !important; }}
        .nav-tabs .nav-link.active {{ color: #c8a97e !important; border-bottom: 3px solid #c8a97e; background: transparent; }}
        .table {{ background-color: #ffffff; }}
        .table thead th {{ background-color: #111111 !important; color: #ffffff !important; font-weight: 700; border: none; }}
        .table tbody td {{ color: #222222; font-weight: 500; vertical-align: middle; }}
        .form-select, .form-control {{ color: #000000 !important; font-weight: 600; border: 2px solid #ccc; background-color: #fff; }}
        .form-select:focus, .form-control:focus {{ border-color: #c8a97e; box-shadow: none; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container">
            <a class="navbar-brand" href="{{{{ url_for('index') }}}}">GRAND HOTEL</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item"><a class="nav-link" href="{{{{ url_for('index') }}}}">Главная</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{{{ url_for('food_menu') }}}}">Ресторан</a></li>
                    {{% if session.get('role') == 'admin' %}}
                        <li class="nav-item"><a class="nav-link" href="{{{{ url_for('admin_dashboard') }}}}">Админ Панель</a></li>
                    {{% elif session.get('role') == 'user' %}}
                        <li class="nav-item"><a class="nav-link" href="{{{{ url_for('user_dashboard') }}}}">Мои Брони</a></li>
                        <li class="nav-item"><a class="nav-link" href="{{{{ url_for('profile') }}}}">Профиль</a></li>
                    {{% endif %}}
                    {{% if session.get('role') %}}
                        <li class="nav-item ms-3">
                            <span class="text-white small me-2">Привет, {{{{ session['fullname'].split()[0] }}}}!</span>
                            <a class="btn btn-outline-light btn-sm rounded-0" href="{{{{ url_for('logout') }}}}">Выйти</a>
                        </li>
                    {{% else %}}
                        <li class="nav-item ms-3"><a class="btn btn-outline-gold btn-sm" href="{{{{ url_for('login') }}}}">Войти</a></li>
                        <li class="nav-item ms-2"><a class="btn btn-gold btn-sm" href="{{{{ url_for('register') }}}}">Регистрация</a></li>
                    {{% endif %}}
                </ul>
            </div>
        </div>
    </nav>
    <div style="padding-top: 76px;">
        {{% with messages = get_flashed_messages(with_categories=true) %}}
            {{% if messages %}}{{% for category, message in messages %}}
                <div class="alert alert-{{{{ category }}}} alert-dismissible fade show m-0 rounded-0 text-center border-0">{{{{ message }}}}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>
            {{% endfor %}}{{% endif %}}
        {{% endwith %}}
        {{% block content %}}{{% endblock %}}
    </div>
    <footer class="footer">
        <div class="container text-center">
            <h4 class="text-white mb-3" style="font-family: 'Playfair Display', serif;">GRAND HOTEL</h4>
            <p>ул. Морская, д. 1, Сочи<br>+7 (800) 555-35-35</p>
            <p class="small mt-4 mb-0 text-muted">&copy; 2026 Grand Hotel. Все права защищены.</p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

index_html = '''{% extends 'base.html' %}
{% block content %}
<div class="position-relative" style="height: 85vh; background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.6)), url('/static/placeholder.jpg') center/cover;">
    <div class="container h-100 d-flex flex-column justify-content-center align-items-center text-center text-white">
        <h1 class="display-3 fw-bold mb-3" style="text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">Добро пожаловать в Рай</h1>
        <p class="lead mb-5 fs-4">Откройте для себя непревзойденную роскошь и комфорт на берегу моря.</p>
        <a href="#rooms" class="btn btn-gold btn-lg px-5 py-3">Выбрать номер</a>
    </div>
</div>
<div class="container my-5 py-5">
    <div class="row text-center">
        <div class="col-md-3 mb-4"><i class="fas fa-wifi fa-3x mb-3 text-gold"></i><h5>Бесплатный Wi-Fi</h5><p class="text-muted small">Интернет во всех зонах отеля</p></div>
        <div class="col-md-3 mb-4"><i class="fas fa-swimmer fa-3x mb-3 text-gold"></i><h5>Бассейн и Спа</h5><p class="text-muted small">Открытый бассейн с подогревом</p></div>
        <div class="col-md-3 mb-4"><i class="fas fa-utensils fa-3x mb-3 text-gold"></i><h5>Ресторан</h5><p class="text-muted small">Изысканная кухня от шеф-поваров</p></div>
        <div class="col-md-3 mb-4"><i class="fas fa-concierge-bell fa-3x mb-3 text-gold"></i><h5>Обслуживание 24/7</h5><p class="text-muted small">Консьерж и рум-сервис</p></div>
    </div>
</div>
<div id="rooms" class="container my-5">
    <h2 class="text-center mb-5 display-4">Наши Номера</h2>
    <div class="row">
        {% for room in rooms %}
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card h-100">
                <img src="{{ room.images.split(',')[0] }}" class="card-img-top" alt="{{ room.title }}" style="height: 250px; object-fit: cover;">
                <div class="card-body d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h4 class="card-title mb-0">{{ room.title }}</h4>
                        <span class="badge bg-dark fs-6 rounded-0">{{ room.price }} ₽/ночь</span>
                    </div>
                    <p class="card-text text-muted flex-grow-1 small">{{ room.description[:90] }}...</p>
                    <div class="mt-3">
                        <a href="{{ url_for('room_detail', room_id=room.id) }}" class="btn btn-outline-dark w-100 mb-2 rounded-0">Подробнее</a>
                        <a href="{{ url_for('room_detail', room_id=room.id) }}" class="btn btn-gold w-100 rounded-0">Забронировать</a>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
<div class="bg-dark text-white py-5 mt-5">
    <div class="container py-4">
        <h2 class="text-center mb-5 display-5">Отзывы наших гостей</h2>
        <div class="row">
            {% for r in reviews %}
            <div class="col-md-4 mb-4">
                <div class="card bg-transparent border border-secondary h-100 p-4 rounded-0">
                    <div class="mb-2 text-gold">{% for i in range(r.rating) %}<i class="fas fa-star"></i>{% endfor %}</div>
                    <p class="fst-italic text-light opacity-75">"{{ r.comment }}"</p>
                    <p class="fw-bold mt-auto mb-0 text-white">— {{ r.guest_name }}</p>
                    <p class="small text-muted">{{ r.room_title }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}'''

room_detail_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5">
    <div class="row">
        <div class="col-lg-8 mb-4">
            <div id="roomCarousel" class="carousel slide mb-4 shadow" data-bs-ride="carousel">
                <div class="carousel-inner">
                    {% for img in images %}
                    <div class="carousel-item {% if loop.first %}active{% endif %}">
                        <img src="{{ img }}" class="d-block w-100" style="height: 500px; object-fit: cover;" alt="Фото номера">
                    </div>
                    {% endfor %}
                </div>
                {% if images|length > 1 %}
                <button class="carousel-control-prev" type="button" data-bs-target="#roomCarousel" data-bs-slide="prev">
                    <span class="carousel-control-prev-icon" aria-hidden="true" style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 50%;"></span>
                </button>
                <button class="carousel-control-next" type="button" data-bs-target="#roomCarousel" data-bs-slide="next">
                    <span class="carousel-control-next-icon" aria-hidden="true" style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 50%;"></span>
                </button>
                {% endif %}
            </div>

            <h1 class="display-4">{{ room.title }}</h1>
            <p class="lead text-muted mt-3">{{ room.description }}</p>
            
            <h4 class="mt-5 mb-3">Удобства в номере:</h4>
            <div class="row bg-white p-4 shadow-sm mx-0">
                {% for amenity in room.amenities.split(',') %}
                <div class="col-md-4 col-6 mb-2"><i class="fas fa-check-circle me-2 text-gold"></i>{{ amenity.strip() }}</div>
                {% endfor %}
            </div>
            <h4 class="mt-5 mb-4">Отзывы гостей ({{ reviews|length }})</h4>
            {% if reviews %}
                {% for r in reviews %}
                <div class="card mb-3 rounded-0 border-0 shadow-sm p-3">
                    <div class="d-flex justify-content-between"><h6 class="fw-bold mb-1">{{ r.guest_name }}</h6><small class="text-muted">{{ r.date }}</small></div>
                    <div class="text-gold mb-2">{% for i in range(r.rating) %}<i class="fas fa-star"></i>{% endfor %}</div>
                    <p class="mb-0">{{ r.comment }}</p>
                </div>
                {% endfor %}
            {% else %}<p class="text-muted">Пока нет отзывов. Будьте первым!</p>{% endif %}
            {% if session.get('role') == 'user' %}
            <div class="card p-4 mt-4 rounded-0 border-0 shadow-sm bg-white">
                <h5>Оставить отзыв</h5>
                <form action="{{ url_for('add_review', room_id=room.id) }}" method="POST">
                    <div class="mb-3"><label class="form-label">Оценка</label>
                        <select name="rating" class="form-select" required>
                            <option value="5">5 звезд - Отлично</option><option value="4">4 звезды - Хорошо</option>
                            <option value="3">3 звезды - Нормально</option><option value="2">2 звезды - Плохо</option><option value="1">1 звезда - Ужасно</option>
                        </select>
                    </div>
                    <div class="mb-3"><label class="form-label">Комментарий</label><textarea name="comment" class="form-control" rows="3" required></textarea></div>
                    <button type="submit" class="btn btn-dark rounded-0">Отправить отзыв</button>
                </form>
            </div>
            {% endif %}
        </div>
        <div class="col-lg-4">
            <div class="card p-4 sticky-top shadow" style="top: 100px;">
                <h3 class="text-center mb-4">Бронирование</h3>
                <div class="text-center mb-4 pb-3 border-bottom"><span class="display-5 fw-bold text-gold">{{ room.price }}</span><span class="text-muted">/ночь</span></div>
                {% if session.get('role') == 'user' %}
                <form action="{{ url_for('book_room', room_id=room.id) }}" method="POST">
                    <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Дата заезда</label><input type="date" name="check_in" class="form-control" required></div>
                    <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Дата выезда</label><input type="date" name="check_out" class="form-control" required></div>
                    <button type="submit" class="btn btn-gold w-100 btn-lg rounded-0">Забронировать</button>
                </form>
                {% elif session.get('role') == 'admin' %}
                <div class="alert alert-info text-center rounded-0">Вы администратор.</div>
                {% else %}
                <div class="alert alert-warning text-center rounded-0"><i class="fas fa-lock mb-2 fa-2x text-warning"></i><br>Чтобы забронировать, <a href="{{ url_for('login') }}" class="alert-link">войдите</a> или <a href="{{ url_for('register') }}" class="alert-link">зарегистрируйтесь</a>.</div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

login_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5 py-5"><div class="row justify-content-center"><div class="col-md-5">
    <div class="card p-5 shadow-lg border-0">
        <h2 class="text-center mb-4">Вход в систему</h2>
        <form method="POST">
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Логин</label><input type="text" name="username" class="form-control" required placeholder="Введите логин"></div>
            <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Пароль</label><input type="password" name="password" class="form-control" required placeholder="Введите пароль"></div>
            <button type="submit" class="btn btn-gold w-100 btn-lg rounded-0">Войти</button>
        </form>
        <div class="mt-4 text-center"><span class="text-muted small">Нет аккаунта? <a href="{{ url_for('register') }}" class="text-gold fw-bold text-decoration-none">Зарегистрироваться</a></span></div>
    </div>
</div></div></div>
{% endblock %}'''

register_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5 py-5"><div class="row justify-content-center"><div class="col-md-6">
    <div class="card p-5 shadow-lg border-0">
        <h2 class="text-center mb-4">Создать аккаунт</h2>
        <form method="POST">
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Логин</label><input type="text" name="username" class="form-control" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Пароль</label><input type="password" name="password" class="form-control" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">ФИО</label><input type="text" name="fullname" class="form-control" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Телефон</label><input type="text" name="phone" class="form-control" required></div>
            <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Email</label><input type="email" name="email" class="form-control" required></div>
            <button type="submit" class="btn btn-gold w-100 btn-lg rounded-0">Зарегистрироваться</button>
        </form>
        <div class="mt-4 text-center"><span class="text-muted small">Уже есть аккаунт? <a href="{{ url_for('login') }}" class="text-gold fw-bold text-decoration-none">Войти</a></span></div>
    </div>
</div></div></div>
{% endblock %}'''

profile_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5 py-4"><div class="row justify-content-center"><div class="col-md-8">
    <div class="card p-5 shadow-sm border-0">
        <h2 class="mb-4">Мой Профиль</h2>
        <form method="POST">
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Логин (нельзя изменить)</label><input type="text" class="form-control bg-light" value="{{ user.username }}" disabled></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">ФИО</label><input type="text" name="fullname" class="form-control" value="{{ user.fullname }}" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Телефон</label><input type="text" name="phone" class="form-control" value="{{ user.phone }}" required></div>
            <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Email</label><input type="email" name="email" class="form-control" value="{{ user.email }}" required></div>
            <button type="submit" class="btn btn-gold px-5 rounded-0">Сохранить изменения</button>
        </form>
    </div>
</div></div></div>
{% endblock %}'''

user_dashboard_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5">
    <h1 class="mb-4 display-5">Личный Кабинет</h1>
    <ul class="nav nav-tabs mb-4" id="userTabs" role="tablist">
        <li class="nav-item"><button class="nav-link active fw-bold text-uppercase" data-bs-toggle="tab" data-bs-target="#bookings">Мои Брони</button></li>
        <li class="nav-item"><button class="nav-link fw-bold text-uppercase" data-bs-toggle="tab" data-bs-target="#food">Заказы в номер</button></li>
    </ul>
    <div class="tab-content">
        <div class="tab-pane fade show active" id="bookings">
            {% if bookings %}
                <div class="row">
                    {% for b in bookings %}
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 border-0 shadow-sm">
                            <div class="row g-0 h-100">
                                <div class="col-4"><img src="{{ b.images.split(',')[0] }}" class="img-fluid h-100" style="object-fit: cover;"></div>
                                <div class="col-8">
                                    <div class="card-body">
                                        <div class="d-flex justify-content-between align-items-start"><h5 class="card-title">{{ b.title }}</h5><span class="badge bg-dark rounded-0">{{ b.status }}</span></div>
                                        <p class="card-text small mb-1 text-muted"><i class="far fa-calendar-alt me-1"></i> Заезд: <b>{{ b.check_in }}</b></p>
                                        <p class="card-text small text-muted"><i class="far fa-calendar-check me-1"></i> Выезд: <b>{{ b.check_out }}</b></p>
                                        <h4 class="mt-3 text-gold">{{ b.total_price }} ₽</h4>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="alert alert-light text-center py-5 border"><i class="fas fa-bed fa-3x mb-3 text-muted"></i><h4>У вас пока нет бронирований</h4><a href="{{ url_for('index') }}" class="btn btn-gold mt-3 rounded-0">Выбрать номер</a></div>
            {% endif %}
        </div>
        <div class="tab-pane fade" id="food">
            {% if food_orders %}
                <div class="card border-0 shadow-sm"><div class="card-body p-0"><table class="table table-hover mb-0">
                    <thead class="table-light"><tr><th>Блюдо</th><th>Номер</th><th>Кол-во</th><th>Сумма</th><th>Статус</th><th>Дата</th></tr></thead>
                    <tbody>
                        {% for f in food_orders %}
                        <tr>
                            <td class="fw-bold">{{ f.item_name }}</td><td>{{ f.room_title }}</td><td>{{ f.quantity }}</td><td>{{ f.price * f.quantity }} ₽</td>
                            <td>{% if f.status == 'Готовится' %}<span class="badge bg-warning text-dark">Готовится</span>{% elif f.status == 'Доставлено' %}<span class="badge bg-success">Доставлено</span>{% else %}<span class="badge bg-secondary">{{ f.status }}</span>{% endif %}</td>
                            <td class="text-muted small">{{ f.date }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table></div></div>
            {% else %}
                <div class="alert alert-light text-center py-5 border"><i class="fas fa-utensils fa-3x mb-3 text-muted"></i><h4>Вы еще не заказывали еду</h4><a href="{{ url_for('food_menu') }}" class="btn btn-gold mt-3 rounded-0">Перейти в ресторан</a></div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}'''

food_menu_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5">
    <div class="text-center mb-5"><h1 class="display-4">Ресторан Отеля</h1><p class="lead text-muted">Изысканные блюда с доставкой прямо в ваш номер</p></div>
    {% if not bookings %}<div class="alert alert-warning text-center rounded-0"><i class="fas fa-info-circle me-2"></i> У вас нет активных броней. Заказы в номер доступны только постояльцам.</div>{% endif %}
    <div class="row">
        {% for item in menu %}
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card h-100 border-0 shadow-sm">
                <img src="{{ item.image }}" class="card-img-top" style="height: 220px; object-fit: cover;">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">{{ item.name }}</h5>
                    <p class="card-text text-muted small flex-grow-1">{{ item.description }}</p>
                    <h4 class="text-gold mb-3">{{ item.price }} ₽</h4>
                    {% if bookings %}
                    <form action="{{ url_for('order_food') }}" method="POST">
                        <input type="hidden" name="item_name" value="{{ item.name }}"><input type="hidden" name="price" value="{{ item.price }}">
                        <div class="mb-2">
                            <select name="room_id" class="form-select form-select-sm rounded-0" required>
                                <option value="">Выберите номер...</option>
                                {% for b in bookings %}<option value="{{ b.room_id }}">{{ b.title }} (Бронь #{{ b.id }})</option>{% endfor %}
                            </select>
                        </div>
                        <div class="input-group input-group-sm mb-3"><span class="input-group-text rounded-0">Кол-во</span><input type="number" name="quantity" class="form-control rounded-0" value="1" min="1" required></div>
                        <button type="submit" class="btn btn-gold btn-sm w-100 rounded-0">Заказать в номер</button>
                    </form>
                    {% else %}<button class="btn btn-secondary btn-sm w-100 rounded-0" disabled>Требуется бронь</button>{% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}'''

admin_dashboard_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5">
    <h1 class="mb-4 display-5">Тотальный Контроль</h1>
    <div class="row mb-4">
        <div class="col-md-3 mb-3"><div class="card p-4 bg-dark text-white border-0 shadow-sm h-100"><h6 class="text-uppercase small text-muted mb-2">Выручка</h6><h3 class="mb-0 text-gold">{{ revenue }} ₽</h3></div></div>
        <div class="col-md-3 mb-3"><div class="card p-4 border-0 shadow-sm h-100"><h6 class="text-uppercase small text-muted mb-2">Всего Броней</h6><h3 class="mb-0">{{ bookings|length }}</h3></div></div>
        <div class="col-md-3 mb-3"><div class="card p-4 border-0 shadow-sm h-100"><h6 class="text-uppercase small text-muted mb-2">Заказов Еды</h6><h3 class="mb-0">{{ food_orders|length }}</h3></div></div>
        <div class="col-md-3 mb-3"><div class="card p-4 border-0 shadow-sm h-100"><h6 class="text-uppercase small text-muted mb-2">Пользователей</h6><h3 class="mb-0">{{ users|length }}</h3></div></div>
    </div>
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Управление</h3>
        <div>
            <a href="{{ url_for('admin_add_room') }}" class="btn btn-gold rounded-0 me-2"><i class="fas fa-plus me-2"></i>Добавить номер</a>
            <a href="{{ url_for('admin_add_menu') }}" class="btn btn-outline-gold rounded-0"><i class="fas fa-utensils me-2"></i>Добавить блюдо</a>
        </div>
    </div>
    <ul class="nav nav-tabs mb-4" id="adminTabs" role="tablist">
        <li class="nav-item"><button class="nav-link active fw-bold" data-bs-toggle="tab" data-bs-target="#tab-bookings">Брони</button></li>
        <li class="nav-item"><button class="nav-link fw-bold" data-bs-toggle="tab" data-bs-target="#tab-rooms">Номера</button></li>
        <li class="nav-item"><button class="nav-link fw-bold" data-bs-toggle="tab" data-bs-target="#tab-menu">Меню</button></li>
        <li class="nav-item"><button class="nav-link fw-bold" data-bs-toggle="tab" data-bs-target="#tab-food">Заказы Еды</button></li>
        <li class="nav-item"><button class="nav-link fw-bold" data-bs-toggle="tab" data-bs-target="#tab-users">Юзеры</button></li>
        <li class="nav-item"><button class="nav-link fw-bold" data-bs-toggle="tab" data-bs-target="#tab-reviews">Отзывы</button></li>
    </ul>
    <div class="tab-content">
        <div class="tab-pane fade show active" id="tab-bookings">
            <div class="card border-0 shadow-sm"><div class="card-body p-0 table-responsive"><table class="table table-hover mb-0">
                <thead><tr><th>ID</th><th>Гость</th><th>Номер</th><th>Даты (Изменить)</th><th>Сумма (Изменить)</th><th>Статус</th><th></th></tr></thead>
                <tbody>
                    {% for b in bookings %}
                    <tr>
                        <td>#{{ b.id }}</td><td>{{ b.guest_name }}</td><td>{{ b.title }}</td>
                        <form action="{{ url_for('admin_edit_booking', booking_id=b.id) }}" method="POST">
                        <td class="small">
                            <input type="date" name="check_in" value="{{ b.check_in }}" class="form-control form-control-sm mb-1">
                            <input type="date" name="check_out" value="{{ b.check_out }}" class="form-control form-control-sm">
                        </td>
                        <td><input type="number" name="total_price" value="{{ b.total_price }}" class="form-control form-control-sm" style="width: 100px;"></td>
                        <td>
                            <select name="status" class="form-select form-select-sm rounded-0">
                                <option value="Забронировано" {% if b.status == 'Забронировано' %}selected{% endif %}>Забронировано</option>
                                <option value="Оплачено" {% if b.status == 'Оплачено' %}selected{% endif %}>Оплачено</option>
                                <option value="Выселен" {% if b.status == 'Выселен' %}selected{% endif %}>Выселен</option>
                            </select>
                        </td>
                        <td><button type="submit" class="btn btn-sm btn-success"><i class="fas fa-save"></i></button></form>
                            <a href="{{ url_for('admin_delete_booking', booking_id=b.id) }}" class="btn btn-sm btn-outline-danger mt-1" onclick="return confirm('Удалить?')"><i class="fas fa-trash"></i></a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table></div></div>
        </div>
        <div class="tab-pane fade" id="tab-rooms">
            <div class="row">
                {% for r in rooms %}
                <div class="col-md-4 mb-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <img src="{{ r.images.split(',')[0] }}" class="card-img-top" style="height: 150px; object-fit: cover;">
                        <div class="card-body">
                            <h5 class="card-title">{{ r.title }}</h5>
                            <p class="text-gold fw-bold mb-1">{{ r.price }} ₽/ночь</p>
                            <p class="small text-muted mb-3">{{ r.description[:50] }}...</p>
                            <div class="d-flex justify-content-between">
                                <a href="{{ url_for('admin_edit_room', room_id=r.id) }}" class="btn btn-sm btn-dark w-50 me-1 rounded-0"><i class="fas fa-edit"></i> Изменить</a>
                                <a href="{{ url_for('admin_delete_room', room_id=r.id) }}" class="btn btn-sm btn-outline-danger w-50 ms-1 rounded-0" onclick="return confirm('Удалить номер?')"><i class="fas fa-trash"></i> Удалить</a>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        <div class="tab-pane fade" id="tab-menu">
            <div class="row">
                {% for m in menu %}
                <div class="col-md-3 mb-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <img src="{{ m.image }}" class="card-img-top" style="height: 120px; object-fit: cover;">
                        <div class="card-body">
                            <h6 class="card-title">{{ m.name }}</h6>
                            <p class="text-gold fw-bold mb-2">{{ m.price }} ₽</p>
                            <div class="d-flex justify-content-between">
                                <a href="{{ url_for('admin_edit_menu', item_id=m.id) }}" class="btn btn-sm btn-dark w-50 me-1 rounded-0"><i class="fas fa-edit"></i></a>
                                <a href="{{ url_for('admin_delete_menu', item_id=m.id) }}" class="btn btn-sm btn-outline-danger w-50 ms-1 rounded-0" onclick="return confirm('Удалить блюдо?')"><i class="fas fa-trash"></i></a>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        <div class="tab-pane fade" id="tab-food">
            <div class="card border-0 shadow-sm"><div class="card-body p-0 table-responsive"><table class="table table-hover mb-0">
                <thead><tr><th>ID</th><th>Гость</th><th>Номер</th><th>Блюдо</th><th>Кол-во</th><th>Статус</th></tr></thead>
                <tbody>
                    {% for f in food_orders %}
                    <tr>
                        <td>#{{ f.id }}</td><td>{{ f.guest_name }}</td><td>{{ f.room_title }}</td><td class="fw-bold">{{ f.item_name }}</td><td>{{ f.quantity }}</td>
                        <td>
                            <form action="{{ url_for('admin_update_food', order_id=f.id) }}" method="POST" class="d-flex">
                                <select name="status" class="form-select form-select-sm me-1 rounded-0" style="width: 120px;">
                                    <option value="Готовится" {% if f.status == 'Готовится' %}selected{% endif %}>Готовится</option>
                                    <option value="В пути" {% if f.status == 'В пути' %}selected{% endif %}>В пути</option>
                                    <option value="Доставлено" {% if f.status == 'Доставлено' %}selected{% endif %}>Доставлено</option>
                                </select>
                                <button type="submit" class="btn btn-sm btn-dark rounded-0"><i class="fas fa-check"></i></button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table></div></div>
        </div>
        <div class="tab-pane fade" id="tab-users">
            <div class="card border-0 shadow-sm"><div class="card-body p-0 table-responsive"><table class="table table-hover mb-0">
                <thead><tr><th>ID</th><th>Логин</th><th>ФИО</th><th>Телефон</th><th>Роль</th><th>Действия</th></tr></thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td>#{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.fullname }}</td><td>{{ u.phone }}</td>
                        <td><span class="badge {% if u.role == 'admin' %}bg-danger{% else %}bg-secondary{% endif %}">{{ u.role }}</span></td>
                        <td>
                            {% if u.role != 'admin' %}<a href="{{ url_for('admin_make_admin', user_id=u.id) }}" class="btn btn-sm btn-outline-dark" title="Сделать админом"><i class="fas fa-user-shield"></i></a>{% endif %}
                            {% if u.id != session['user_id'] %}<a href="{{ url_for('admin_delete_user', user_id=u.id) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Удалить пользователя?')"><i class="fas fa-trash"></i></a>{% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table></div></div>
        </div>
        <div class="tab-pane fade" id="tab-reviews">
            <div class="card border-0 shadow-sm"><div class="card-body p-0 table-responsive"><table class="table table-hover mb-0">
                <thead><tr><th>Гость</th><th>Номер</th><th>Оценка</th><th>Комментарий</th><th>Удалить</th></tr></thead>
                <tbody>
                    {% for r in reviews %}
                    <tr>
                        <td>{{ r.guest_name }}</td><td>{{ r.room_title }}</td><td class="text-gold">{% for i in range(r.rating) %}<i class="fas fa-star"></i>{% endfor %}</td><td>{{ r.comment }}</td>
                        <td><a href="{{ url_for('admin_delete_review', review_id=r.id) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Удалить отзыв?')"><i class="fas fa-trash"></i></a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table></div></div>
        </div>
    </div>
</div>
{% endblock %}'''

admin_add_room_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5 py-4"><div class="row justify-content-center"><div class="col-md-8">
    <div class="card p-5 border-0 shadow-sm">
        <h2 class="mb-4">Добавить новый номер</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Название</label><input type="text" name="title" class="form-control" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Цена за ночь (₽)</label><input type="number" step="0.01" name="price" class="form-control" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Описание</label><textarea name="description" class="form-control" rows="4" required></textarea></div>
            <div class="mb-3">
                <label class="form-label small text-uppercase fw-bold">Фотографии (можно несколько)</label>
                <input type="file" name="images" class="form-control" accept="image/*" multiple>
                <div class="form-text">Выберите картинки с компьютера. Если не выбрать, будет заглушка.</div>
            </div>
            <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Удобства (через запятую)</label><input type="text" name="amenities" class="form-control" required></div>
            <button type="submit" class="btn btn-gold px-5 rounded-0">Сохранить номер</button>
        </form>
    </div>
</div></div></div>
{% endblock %}'''

admin_edit_room_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5 py-4"><div class="row justify-content-center"><div class="col-md-8">
    <div class="card p-5 border-0 shadow-sm">
        <h2 class="mb-4">Редактировать номер</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Название</label><input type="text" name="title" class="form-control" value="{{ room.title }}" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Цена за ночь (₽)</label><input type="number" step="0.01" name="price" class="form-control" value="{{ room.price }}" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Описание</label><textarea name="description" class="form-control" rows="4" required>{{ room.description }}</textarea></div>
            
            <div class="mb-3">
                <label class="form-label small text-uppercase fw-bold">Текущие фото:</label><br>
                {% for img in room.images.split(',') %}
                    <img src="{{ img }}" style="height: 80px; object-fit: cover; margin-right: 5px; margin-bottom: 5px;">
                {% endfor %}
            </div>

            <div class="mb-3">
                <label class="form-label small text-uppercase fw-bold">Загрузить новые фото (заменят старые)</label>
                <input type="file" name="images" class="form-control" accept="image/*" multiple>
                <div class="form-text text-danger">Внимание: если выберете файлы, старые фото удалятся из галереи!</div>
            </div>
            
            <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Удобства</label><input type="text" name="amenities" class="form-control" value="{{ room.amenities }}" required></div>
            <button type="submit" class="btn btn-gold px-5 rounded-0">Обновить номер</button>
        </form>
    </div>
</div></div></div>
{% endblock %}'''

admin_add_menu_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5 py-4"><div class="row justify-content-center"><div class="col-md-8">
    <div class="card p-5 border-0 shadow-sm">
        <h2 class="mb-4">Добавить блюдо</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Название</label><input type="text" name="name" class="form-control" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Цена (₽)</label><input type="number" step="0.01" name="price" class="form-control" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Описание</label><textarea name="description" class="form-control" rows="2" required></textarea></div>
            <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Фото</label><input type="file" name="image" class="form-control" accept="image/*" required></div>
            <button type="submit" class="btn btn-gold px-5 rounded-0">Сохранить блюдо</button>
        </form>
    </div>
</div></div></div>
{% endblock %}'''

admin_edit_menu_html = '''{% extends 'base.html' %}
{% block content %}
<div class="container my-5 py-4"><div class="row justify-content-center"><div class="col-md-8">
    <div class="card p-5 border-0 shadow-sm">
        <h2 class="mb-4">Редактировать блюдо</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Название</label><input type="text" name="name" class="form-control" value="{{ item.name }}" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Цена (₽)</label><input type="number" step="0.01" name="price" class="form-control" value="{{ item.price }}" required></div>
            <div class="mb-3"><label class="form-label small text-uppercase fw-bold">Описание</label><textarea name="description" class="form-control" rows="2" required>{{ item.description }}</textarea></div>
            <div class="mb-3">
                <label class="form-label small text-uppercase fw-bold">Текущее фото:</label><br>
                <img src="{{ item.image }}" style="height: 100px; object-fit: cover;">
            </div>
            <div class="mb-4"><label class="form-label small text-uppercase fw-bold">Новое фото (необязательно)</label><input type="file" name="image" class="form-control" accept="image/*"></div>
            <button type="submit" class="btn btn-gold px-5 rounded-0">Обновить блюдо</button>
        </form>
    </div>
</div></div></div>
{% endblock %}'''

files = {
    "requirements.txt": "Flask==3.0.0\nWerkzeug==3.0.0",
    "app.py": app_py,
    "templates/base.html": base_html,
    "templates/index.html": index_html,
    "templates/room_detail.html": room_detail_html,
    "templates/login.html": login_html,
    "templates/register.html": register_html,
    "templates/profile.html": profile_html,
    "templates/user_dashboard.html": user_dashboard_html,
    "templates/food_menu.html": food_menu_html,
    "templates/admin_dashboard.html": admin_dashboard_html,
    "templates/admin_add_room.html": admin_add_room_html,
    "templates/admin_edit_room.html": admin_edit_room_html,
    "templates/admin_add_menu.html": admin_add_menu_html,
    "templates/admin_edit_menu.html": admin_edit_menu_html
}

print("Создание файлов...")
os.makedirs(os.path.join(FOLDER_NAME, "static", "uploads"), exist_ok=True)
placeholder_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
    <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#111111;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#2a2a2a;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="800" height="600" fill="url(#grad)" />
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" font-size="40" fill="#c8a97e" font-weight="bold">GRAND HOTEL</text>
</svg>'''
with open(os.path.join(FOLDER_NAME, "static", "placeholder.jpg"), 'w', encoding='utf-8') as f:
    f.write(placeholder_svg)

os.makedirs(os.path.join(FOLDER_NAME, "templates"), exist_ok=True)

for filepath, content in files.items():
    full_path = os.path.join(FOLDER_NAME, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  -> Создан: {filepath}")

print("\nУпаковка в архив...")
with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files_in_dir in os.walk(FOLDER_NAME):
        for file in files_in_dir:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, FOLDER_NAME)
            zipf.write(file_path, arcname)

print(f"\nГОТОВО! Архив {ZIP_NAME} создан в текущей папке.")
