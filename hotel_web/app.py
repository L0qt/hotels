
# -*- coding: utf-8 -*-
"""Веб-приложение отеля на Flask."""

from functools import wraps
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from db import (Database, UserRepository, GuestRepository,
                RoomRepository, BookingRepository, ReviewRepository)

app = Flask(__name__)
app.secret_key = "hotel_morskoy_briz_2026"

# ====== ПОДКЛЮЧЕНИЕ К БАЗЕ: впишите свой пароль от MySQL ======
db = Database(host="localhost", user="root", password="1234", database="hotel_db")

users_repo = UserRepository(db)
guests_repo = GuestRepository(db)
rooms_repo = RoomRepository(db)
bookings_repo = BookingRepository(db)
reviews_repo = ReviewRepository(db)


# ---------- вспомогательные функции ----------
def current_user():
    if "user_id" not in session:
        return None
    return users_repo.get_by_id(session["user_id"])


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Сначала войдите в аккаунт.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for("login"))
        if u["role"] != "admin":
            flash("Раздел доступен только администратору.", "error")
            return redirect("/")
        return view(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_user():
    return {"user": current_user()}


# ---------- публичные страницы ----------
@app.route("/")
def index():
    cat = request.args.get("cat")
    category_id = int(cat) if cat and cat.isdigit() else None
    return render_template("index.html",
                           rooms=rooms_repo.all(category_id),
                           categories=rooms_repo.categories(),
                           cat=cat)


@app.route("/room/<int:rid>", methods=["GET", "POST"])
def room_detail(rid):
    room = rooms_repo.get(rid)
    if not room:
        flash("Номер не найден.", "error")
        return redirect("/")
    if request.method == "POST":
        u = current_user()
        if not u:
            return redirect(url_for("login"))
        try:
            date_str = request.form.get("date", "").strip()
            nights = int(request.form.get("nights", "1"))
            coupon = request.form.get("coupon", "").strip()
            datetime.strptime(date_str, "%Y-%m-%d")
            if nights < 1:
                raise ValueError("Количество суток должно быть не меньше 1")
            total = float(room["цена за сутки"] or 0) * nights
            coupon_id = 1
            if coupon:
                found = bookings_repo.find_coupon(coupon)
                coupon_id = found["idcoupons"] if found else 1
            bookings_repo.add(rid, u["guests_idguests"], date_str, nights, coupon_id, total)
            flash("Бронирование оформлено! Все ваши брони — в разделе «Мои брони».", "ok")
            return redirect(url_for("my_bookings"))
        except ValueError as e:
            flash("Проверьте дату и количество суток: " + str(e), "error")
        except Exception as e:
            flash("Не удалось оформить бронь: " + str(e), "error")
    return render_template("room.html", room=room, reviews=reviews_repo.by_room(rid))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        if not username or len(password) < 4 or not name or not phone:
            flash("Заполните все поля (пароль — минимум 4 символа).", "error")
            return render_template("register.html")
        if users_repo.get_by_username(username):
            flash("Такой логин уже занят.", "error")
            return render_template("register.html")
        guest_id = guests_repo.add(name, phone, email or None)
        users_repo.create(username, generate_password_hash(password), "user", guest_id)
        flash("Регистрация успешна! Теперь войдите.", "ok")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        u = users_repo.get_by_username(username)
        if u and check_password_hash(u["password_hash"], password):
            session["user_id"] = u["idusers"]
            flash("Добро пожаловать, " + u["username"] + "!", "ok")
            return redirect("/admin" if u["role"] == "admin" else "/")
        flash("Неверный логин или пароль.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из аккаунта.", "ok")
    return redirect("/")


@app.route("/my")
@login_required
def my_bookings():
    u = current_user()
    return render_template("my.html", rows=bookings_repo.by_guest(u["guests_idguests"]))


@app.route("/my/<int:bid>/cancel", methods=["POST"])
@login_required
def cancel_booking(bid):
    u = current_user()
    rows = bookings_repo.by_guest(u["guests_idguests"])
    if any(r["idbookings"] == bid and r["status"] == "Забронировано" for r in rows):
        bookings_repo.delete(bid)
        flash("Бронь отменена.", "ok")
    else:
        flash("Эту бронь нельзя отменить (уже оплачена или не ваша).", "error")
    return redirect(url_for("my_bookings"))


@app.route("/room/<int:rid>/review", methods=["POST"])
@login_required
def add_review(rid):
    u = current_user()
    rating = request.form.get("rating", "5")
    comment = request.form.get("comment", "").strip()[:45] or "Без комментария"
    reviews_repo.add(u["guests_idguests"], rid, rating, comment)
    flash("Спасибо за отзыв!", "ok")
    return redirect(url_for("room_detail", rid=rid))


# ---------- админ-панель ----------
@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html",
                           stats=bookings_repo.stats(),
                           recent=bookings_repo.recent())


@app.route("/admin/rooms", methods=["GET", "POST"])
@admin_required
def admin_rooms():
    if request.method == "POST":
        rid = request.form.get("id", "").strip()
        number = request.form.get("number", "").strip()
        price = float(request.form.get("price", "0") or 0)
        cat_id = int(request.form.get("cat_id"))
        cls_id = int(request.form.get("cls_id"))
        features = request.form.get("features", "").strip()[:45]
        description = request.form.get("description", "").strip()[:45]
        if not number or price <= 0:
            flash("Укажите номер комнаты и положительную цену.", "error")
        elif rid:
            rooms_repo.update(int(rid), int(number), cat_id, cls_id, price, features, description)
            flash("Номер обновлён.", "ok")
        else:
            rooms_repo.add(int(number), cat_id, cls_id, price, features, description)
            flash("Номер добавлен. Картинку положите в static/img/room" + str(
                db.scalar("SELECT MAX(idrooms) FROM rooms")) + ".png", "ok")
        return redirect(url_for("admin_rooms"))
    edit_id = request.args.get("edit")
    edit_room = rooms_repo.get(int(edit_id)) if edit_id and edit_id.isdigit() else None
    return render_template("admin/rooms.html",
                           rooms=rooms_repo.all(),
                           categories=rooms_repo.categories(),
                           classes=rooms_repo.classes(),
                           edit_room=edit_room)


@app.route("/admin/rooms/<int:rid>/delete", methods=["POST"])
@admin_required
def admin_room_delete(rid):
    rooms_repo.delete(rid)
    flash("Номер удалён.", "ok")
    return redirect(url_for("admin_rooms"))


@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    status = request.args.get("status", "Все")
    date_part = request.args.get("date", "").strip()
    search = request.args.get("q", "").strip()
    rows = bookings_repo.all(status=status, date_part=date_part, search=search)
    total = sum(r["total"] or 0 for r in rows)
    return render_template("admin/bookings.html", rows=rows, status=status,
                           date_part=date_part, search=search, total=total)


@app.route("/admin/bookings/<int:bid>/status", methods=["POST"])
@admin_required
def admin_booking_status(bid):
    bookings_repo.set_status(bid, request.form.get("status", "Забронировано"))
    flash("Статус брони обновлён.", "ok")
    return redirect(url_for("admin_bookings"))


@app.route("/admin/bookings/<int:bid>/delete", methods=["POST"])
@admin_required
def admin_booking_delete(bid):
    bookings_repo.delete(bid)
    flash("Бронь удалена.", "ok")
    return redirect(url_for("admin_bookings"))


@app.route("/admin/guests")
@admin_required
def admin_guests():
    return render_template("admin/guests.html",
                           guests=guests_repo.all(request.args.get("q", "").strip()))


@app.route("/admin/guests/<int:gid>/delete", methods=["POST"])
@admin_required
def admin_guest_delete(gid):
    guests_repo.delete(gid)
    flash("Гость удалён.", "ok")
    return redirect(url_for("admin_guests"))


@app.route("/admin/reviews")
@admin_required
def admin_reviews():
    return render_template("admin/reviews.html", reviews=reviews_repo.all())


@app.route("/admin/reviews/<int:rid>/delete", methods=["POST"])
@admin_required
def admin_review_delete(rid):
    reviews_repo.delete(rid)
    flash("Отзыв удалён.", "ok")
    return redirect(url_for("admin_reviews"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
