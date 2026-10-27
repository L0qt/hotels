
# -*- coding: utf-8 -*-
"""Слой работы с базой данных: весь SQL собран здесь, в классах."""

import mysql.connector
from mysql.connector import Error


class Database:
    """Единая точка доступа к MySQL. Остальные классы пользуются её методами."""

    def __init__(self, host="localhost", user="root", password="", database="hotel_db"):
        self.config = {"host": host, "user": user, "password": password,
                       "database": database, "charset": "utf8mb4", "autocommit": True}

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def query_all(self, sql, params=()):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description] if cur.description else []
        cur.close(); conn.close()
        return [dict(zip(cols, row)) for row in rows]

    def query_one(self, sql, params=()):
        rows = self.query_all(sql, params)
        return rows[0] if rows else None

    def execute(self, sql, params=()):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        last_id = cur.lastrowid
        cur.close(); conn.close()
        return last_id

    def scalar(self, sql, params=()):
        row = self.query_one(sql, params)
        return list(row.values())[0] if row else 0


class UserRepository:
    """Регистрация и вход пользователей сайта."""

    def __init__(self, db):
        self.db = db

    def get_by_username(self, username):
        return self.db.query_one(
            "SELECT idusers, username, password_hash, role, guests_idguests "
            "FROM users WHERE username = %s", (username,))

    def get_by_id(self, uid):
        return self.db.query_one(
            "SELECT idusers, username, password_hash, role, guests_idguests "
            "FROM users WHERE idusers = %s", (uid,))

    def create(self, username, password_hash, role="user", guest_id=None):
        return self.db.execute(
            "INSERT INTO users (username, password_hash, role, guests_idguests) "
            "VALUES (%s, %s, %s, %s)", (username, password_hash, role, guest_id))

    def all(self):
        return self.db.query_all(
            "SELECT u.idusers, u.username, u.role, g.`ФИО` AS fio, g.`Почта` AS email "
            "FROM users u LEFT JOIN guests g ON g.idguests = u.guests_idguests "
            "ORDER BY u.idusers")


class GuestRepository:
    """Гости отеля (профиль создаётся автоматически при регистрации)."""

    def __init__(self, db):
        self.db = db

    def add(self, name, phone, email):
        new_id = self.db.scalar("SELECT COALESCE(MAX(idguests), 0) + 1 FROM guests")
        self.db.execute(
            "INSERT INTO guests (idguests, `ФИО`, `Номер телефона`, `Почта`) VALUES (%s, %s, %s, %s)",
            (new_id, name, phone, email))
        return new_id

    def get(self, gid):
        return self.db.query_one("SELECT * FROM guests WHERE idguests = %s", (gid,))

    def all(self, search=""):
        sql = "SELECT idguests, `ФИО` AS fio, `Номер телефона` AS phone, `Почта` AS email FROM guests"
        params = ()
        if search:
            sql += (" WHERE `ФИО` LIKE %s OR `Номер телефона` LIKE %s "
                    "OR CAST(idguests AS CHAR) LIKE %s")
            like = "%" + search + "%"
            params = (like, like, like)
        sql += " ORDER BY idguests"
        return self.db.query_all(sql, params)

    def delete(self, gid):
        self.db.execute("DELETE FROM guests WHERE idguests = %s", (gid,))


class RoomRepository:
    """Номера отеля: каталог, цены, карточки, CRUD для админа."""

    def __init__(self, db):
        self.db = db

    def all(self, category_id=None):
        sql = ("SELECT r.*, c.`тип номера` AS cat, cl.`класс комфорта` AS cls, "
               "c.idroom_categories AS cat_id, cl.idroom_classes AS cls_id "
               "FROM rooms r "
               "JOIN room_categories c ON c.idroom_categories = r.room_categories_idroom_categories "
               "JOIN room_classes cl ON cl.idroom_classes = r.room_classes_idroom_classes")
        params = ()
        if category_id:
            sql += " WHERE r.room_categories_idroom_categories = %s"
            params = (category_id,)
        sql += " ORDER BY r.`номер комнаты`"
        return self.db.query_all(sql, params)

    def get(self, rid):
        rows = self.all()
        for r in rows:
            if r["idrooms"] == rid:
                return r
        return self.db.query_one(
            "SELECT r.*, c.`тип номера` AS cat, cl.`класс комфорта` AS cls, "
            "c.idroom_categories AS cat_id, cl.idroom_classes AS cls_id "
            "FROM rooms r JOIN room_categories c ON c.idroom_categories = r.room_categories_idroom_categories "
            "JOIN room_classes cl ON cl.idroom_classes = r.room_classes_idroom_classes "
            "WHERE r.idrooms = %s", (rid,))

    def add(self, number, cat_id, cls_id, price, features, description):
        new_id = self.db.scalar("SELECT COALESCE(MAX(idrooms), 0) + 1 FROM rooms")
        self.db.execute(
            "INSERT INTO rooms (idrooms, `цена за сутки`, `характеристика`, `номер комнаты`, "
            "`описание`, room_categories_idroom_categories, room_classes_idroom_classes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (new_id, price, features, number, description, cat_id, cls_id))
        return new_id

    def update(self, rid, number, cat_id, cls_id, price, features, description):
        self.db.execute(
            "UPDATE rooms SET `цена за сутки`=%s, `характеристика`=%s, `номер комнаты`=%s, "
            "`описание`=%s, room_categories_idroom_categories=%s, room_classes_idroom_classes=%s "
            "WHERE idrooms=%s",
            (price, features, number, description, cat_id, cls_id, rid))

    def delete(self, rid):
        self.db.execute("DELETE FROM reviews WHERE rooms_idrooms = %s", (rid,))
        self.db.execute("DELETE FROM rooms WHERE idrooms = %s", (rid,))

    def categories(self):
        return self.db.query_all("SELECT idroom_categories AS id, `тип номера` AS name FROM room_categories ORDER BY idroom_categories")

    def classes(self):
        return self.db.query_all("SELECT idroom_classes AS id, `класс комфорта` AS name FROM room_classes ORDER BY idroom_classes")


class BookingRepository:
    """Бронирования: оформление, списки, статусы, статистика."""

    def __init__(self, db):
        self.db = db

    def add(self, room_id, guest_id, date_str, nights, coupon_id, total, status="Забронировано"):
        new_id = self.db.scalar("SELECT COALESCE(MAX(idbookings), 0) + 1 FROM bookings")
        self.db.execute(
            "INSERT INTO bookings (idbookings, `дата заселения`, `статус брони`, `итог сумма`, "
            "`кол-во суток`, `rooms_idrooms`, `guests_idguests`, `coupons_idcoupons`) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (new_id, date_str, status, total, nights, room_id, guest_id, coupon_id))
        return new_id

    def all(self, status=None, date_part=None, search=""):
        sql = ("SELECT b.idbookings, b.`дата заселения` AS bdate, b.`статус брони` AS status, "
               "b.`итог сумма` AS total, b.`кол-во суток` AS nights, "
               "g.`ФИО` AS guest_name, g.`Номер телефона` AS guest_phone, "
               "r.`номер комнаты` AS room_number, r.`цена за сутки` AS price, "
               "cp.`номер купона` AS coupon "
               "FROM bookings b "
               "JOIN guests g ON g.idguests = b.guests_idguests "
               "LEFT JOIN rooms r ON r.idrooms = b.rooms_idrooms "
               "LEFT JOIN coupons cp ON cp.idcoupons = b.coupons_idcoupons WHERE 1=1")
        params = []
        if status and status != "Все":
            sql += " AND b.`статус брони` = %s"
            params.append(status)
        if date_part:
            sql += " AND CAST(b.`дата заселения` AS CHAR) LIKE %s"
            params.append("%" + date_part + "%")
        if search:
            sql += (" AND (CAST(b.idbookings AS CHAR) LIKE %s OR g.`ФИО` LIKE %s "
                    "OR CAST(b.guests_idguests AS CHAR) LIKE %s)")
            like = "%" + search + "%"
            params += [like, like, like]
        sql += " ORDER BY b.idbookings DESC"
        return self.db.query_all(sql, tuple(params))

    def by_guest(self, guest_id):
        return self.db.query_all(
            "SELECT b.idbookings, b.`дата заселения` AS bdate, b.`статус брони` AS status, "
            "b.`итог сумма` AS total, b.`кол-во суток` AS nights, "
            "r.`номер комнаты` AS room_number, r.`характеристика` AS features, r.idrooms AS room_id "
            "FROM bookings b LEFT JOIN rooms r ON r.idrooms = b.rooms_idrooms "
            "WHERE b.guests_idguests = %s ORDER BY b.idbookings DESC", (guest_id,))

    def set_status(self, bid, status):
        self.db.execute("UPDATE bookings SET `статус брони` = %s WHERE idbookings = %s", (status, bid))

    def delete(self, bid):
        self.db.execute("DELETE FROM booking_services WHERE bookings_idbookings = %s", (bid,))
        self.db.execute("DELETE FROM bookings WHERE idbookings = %s", (bid,))

    def find_coupon(self, coupon_number):
        return self.db.query_one("SELECT idcoupons FROM coupons WHERE `номер купона` = %s", (coupon_number,))

    def stats(self):
        return {
            "bookings": self.db.scalar("SELECT COUNT(*) FROM bookings"),
            "revenue": float(self.db.scalar("SELECT COALESCE(SUM(`итог сумма`), 0) FROM bookings")),
            "guests": self.db.scalar("SELECT COUNT(*) FROM guests"),
            "rooms": self.db.scalar("SELECT COUNT(*) FROM rooms"),
            "users": self.db.scalar("SELECT COUNT(*) FROM users"),
            "free_places": self.db.scalar("SELECT COALESCE(SUM(`кол-во свободных мест`), 0) FROM hotel_room_stocks"),
        }

    def recent(self, limit=8):
        rows = self.all()
        return rows[:limit]


class ReviewRepository:
    """Отзывы гостей о номерах."""

    def __init__(self, db):
        self.db = db

    def add(self, guest_id, room_id, rating, comment):
        new_id = self.db.scalar("SELECT COALESCE(MAX(idreviews), 0) + 1 FROM reviews")
        self.db.execute(
            "INSERT INTO reviews (idreviews, `оценка`, `комментарий`, guests_idguests, rooms_idrooms) "
            "VALUES (%s, %s, %s, %s, %s)", (new_id, str(rating), comment, guest_id, room_id))
        return new_id

    def by_room(self, room_id):
        return self.db.query_all(
            "SELECT rv.`оценка` AS rating, rv.`комментарий` AS comment, g.`ФИО` AS guest_name, rv.idreviews "
            "FROM reviews rv JOIN guests g ON g.idguests = rv.guests_idguests "
            "WHERE rv.rooms_idrooms = %s ORDER BY rv.idreviews DESC", (room_id,))

    def all(self):
        return self.db.query_all(
            "SELECT rv.idreviews, rv.`оценка` AS rating, rv.`комментарий` AS comment, "
            "g.`ФИО` AS guest_name, r.`номер комнаты` AS room_number "
            "FROM reviews rv JOIN guests g ON g.idguests = rv.guests_idguests "
            "JOIN rooms r ON r.idrooms = rv.rooms_idrooms ORDER BY rv.idreviews DESC")

    def delete(self, rid):
        self.db.execute("DELETE FROM reviews WHERE idreviews = %s", (rid,))
