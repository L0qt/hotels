-- ============================================================
--  Отель «Морской бриз» — база данных + тестовые данные
--  Запуск: MySQL Workbench -> открыть файл -> значок молнии (весь скрипт)
--  ВНИМАНИЕ: скрипт пересоздаёт базу hotel_db с нуля!
-- ============================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

DROP SCHEMA IF EXISTS `hotel_db`;
CREATE SCHEMA `hotel_db` DEFAULT CHARACTER SET utf8;
USE `hotel_db`;

-- ---------- Категории номеров ----------
CREATE TABLE `room_categories` (
  `idroom_categories` INT NOT NULL,
  `тип номера` VARCHAR(45) NULL,
  PRIMARY KEY (`idroom_categories`)) ENGINE = InnoDB;

-- ---------- Классы комфорта ----------
CREATE TABLE `room_classes` (
  `idroom_classes` INT NOT NULL,
  `класс комфорта` VARCHAR(45) NULL,
  `room_categories_idroom_categories` INT NOT NULL,
  PRIMARY KEY (`idroom_classes`),
  CONSTRAINT `fk_classes_categories1` FOREIGN KEY (`room_categories_idroom_categories`)
    REFERENCES `room_categories` (`idroom_categories`)) ENGINE = InnoDB;

-- ---------- Номера ----------
CREATE TABLE `rooms` (
  `idrooms` INT NOT NULL,
  `цена за сутки` DOUBLE NULL,
  `характеристика` VARCHAR(45) NULL,
  `номер комнаты` INT NULL,
  `описание` VARCHAR(45) NULL,
  `room_categories_idroom_categories` INT NOT NULL,
  `room_classes_idroom_classes` INT NOT NULL,
  PRIMARY KEY (`idrooms`),
  CONSTRAINT `fk_rooms_categories` FOREIGN KEY (`room_categories_idroom_categories`)
    REFERENCES `room_categories` (`idroom_categories`),
  CONSTRAINT `fk_rooms_classes1` FOREIGN KEY (`room_classes_idroom_classes`)
    REFERENCES `room_classes` (`idroom_classes`)) ENGINE = InnoDB;

-- ---------- Корпуса ----------
CREATE TABLE `hotels` (
  `idhotels` INT NOT NULL,
  `название` VARCHAR(45) NULL,
  `номер корпуса` INT NULL,
  PRIMARY KEY (`idhotels`)) ENGINE = InnoDB;

-- ---------- Загрузка корпусов ----------
CREATE TABLE `hotel_room_stocks` (
  `idroom_stocks` INT NOT NULL,
  `кол-во свободных мест` INT NULL,
  `hotels_idhotels` INT NOT NULL,
  PRIMARY KEY (`idroom_stocks`),
  CONSTRAINT `fk_room_stocks_hotels1` FOREIGN KEY (`hotels_idhotels`)
    REFERENCES `hotels` (`idhotels`)) ENGINE = InnoDB;

-- ---------- Гости ----------
CREATE TABLE `guests` (
  `idguests` INT NOT NULL,
  `ФИО` VARCHAR(45) NULL,
  `Номер телефона` VARCHAR(45) NULL,
  `Почта` VARCHAR(45) NULL,
  PRIMARY KEY (`idguests`)) ENGINE = InnoDB;

-- ---------- Купоны ----------
CREATE TABLE `coupons` (
  `idcoupons` INT NOT NULL,
  `информация` VARCHAR(45) NULL,
  `номер купона` VARCHAR(45) NULL,
  PRIMARY KEY (`idcoupons`)) ENGINE = InnoDB;

-- ---------- Брони (+ поля номера и суток для веб-бронирования) ----------
CREATE TABLE `bookings` (
  `idbookings` INT NOT NULL,
  `дата заселения` DATE NULL,
  `статус брони` VARCHAR(45) NULL,
  `итог сумма` DOUBLE NULL,
  `кол-во суток` INT NULL,
  `guests_idguests` INT NOT NULL,
  `coupons_idcoupons` INT NOT NULL,
  `rooms_idrooms` INT NULL,
  PRIMARY KEY (`idbookings`),
  CONSTRAINT `fk_bookings_guests1` FOREIGN KEY (`guests_idguests`)
    REFERENCES `guests` (`idguests`),
  CONSTRAINT `fk_bookings_coupons1` FOREIGN KEY (`coupons_idcoupons`)
    REFERENCES `coupons` (`idcoupons`),
  CONSTRAINT `fk_bookings_rooms1` FOREIGN KEY (`rooms_idrooms`)
    REFERENCES `rooms` (`idrooms`)) ENGINE = InnoDB;

-- ---------- Доп. услуги ----------
CREATE TABLE `booking_services` (
  `idbooking_services` INT NOT NULL,
  `доп услуга` VARCHAR(45) NULL,
  `кол_во суток` INT NULL,
  `сумма` DOUBLE NULL,
  `bookings_idbookings` INT NOT NULL,
  PRIMARY KEY (`idbooking_services`),
  CONSTRAINT `fk_services_bookings1` FOREIGN KEY (`bookings_idbookings`)
    REFERENCES `bookings` (`idbookings`)) ENGINE = InnoDB;

-- ---------- Отзывы ----------
CREATE TABLE `reviews` (
  `idreviews` INT NOT NULL,
  `оценка` VARCHAR(45) NULL,
  `комментарий` VARCHAR(45) NULL,
  `guests_idguests` INT NOT NULL,
  `rooms_idrooms` INT NOT NULL,
  PRIMARY KEY (`idreviews`),
  CONSTRAINT `fk_reviews_guests1` FOREIGN KEY (`guests_idguests`)
    REFERENCES `guests` (`idguests`),
  CONSTRAINT `fk_reviews_rooms1` FOREIGN KEY (`rooms_idrooms`)
    REFERENCES `rooms` (`idrooms`)) ENGINE = InnoDB;

-- ---------- Программа лояльности ----------
CREATE TABLE `loyalty_cards` (
  `idloyalty_cards` INT NOT NULL,
  `бонус баланс` VARCHAR(45) NULL,
  `guests_idguests` INT NOT NULL,
  `rooms_idrooms` INT NOT NULL,
  PRIMARY KEY (`idloyalty_cards`),
  CONSTRAINT `fk_loyalty_cards_guests1` FOREIGN KEY (`guests_idguests`)
    REFERENCES `guests` (`idguests`),
  CONSTRAINT `fk_loyalty_cards_rooms1` FOREIGN KEY (`rooms_idrooms`)
    REFERENCES `rooms` (`idrooms`)) ENGINE = InnoDB;

-- ---------- Пользователи сайта ----------
CREATE TABLE `users` (
  `idusers` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(45) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'user',
  `guests_idguests` INT NULL,
  PRIMARY KEY (`idusers`),
  UNIQUE KEY `uq_username` (`username`),
  CONSTRAINT `fk_users_guests` FOREIGN KEY (`guests_idguests`)
    REFERENCES `guests` (`idguests`)) ENGINE = InnoDB;

-- ============================================================
--  ТЕСТОВЫЕ ДАННЫЕ (наполнение базы)
-- ============================================================

INSERT INTO room_categories VALUES
 (1, 'Стандарт'), (2, 'Люкс'), (3, 'Президентский'), (4, 'Семейный');

INSERT INTO room_classes VALUES
 (1, 'Эконом',            1),
 (2, 'Бизнес',            1),
 (3, 'С видом на море',   2),
 (4, 'Бизнес',            2),
 (5, 'Премиум',           3),
 (6, 'Семейный комфорт',  4);

INSERT INTO rooms (`idrooms`, `цена за сутки`, `характеристика`, `номер комнаты`, `описание`, `room_categories_idroom_categories`, `room_classes_idroom_classes`) VALUES
 (1, 2900,  'Wi-Fi, кондиционер, 1 кровать',     101, 'Уютный номер для одного',      1, 1),
 (2, 3100,  'Wi-Fi, кондиционер, 2 кровати',     102, 'Комфорт для двоих',            1, 1),
 (3, 3900,  'Рабочее место, Wi-Fi, мини-бар',    103, 'Номер для деловых гостей',     1, 2),
 (4, 6500,  'Джакузи, панорамное окно, Wi-Fi',   201, 'Романтика с видом на море',    2, 3),
 (5, 7000,  'Кофемашина, диван, big-TV',         202, 'Просторный люкс бизнес-класса',2, 4),
 (6, 6800,  'Джакузи, балкон, Wi-Fi',            203, 'Солнечный люкс с балконом',    2, 3),
 (7, 12000, '3 комнаты, дворецкий, SPA',         301, 'Лучший номер отеля',           3, 5),
 (8, 5500,  '2 спальни, детская зона, кухня',    401, 'Идеален для семьи с детьми',   4, 6);

INSERT INTO hotels VALUES
 (1, 'Корпус «Морской»', 1),
 (2, 'Корпус «Горный»',  2),
 (3, 'Корпус «Лесной»',  3);

INSERT INTO hotel_room_stocks VALUES
 (1, 25, 1), (2, 18, 2), (3, 12, 3);

INSERT INTO guests VALUES
 (1, 'Смирнов Алексей Петрович',    '+7 900 111-22-33', 'smirnov@mail.ru'),
 (2, 'Иванова Мария Сергеевна',     '+7 901 222-33-44', 'ivanova@mail.ru'),
 (3, 'Петров Дмитрий Олегович',     '+7 902 333-44-55', 'petrov@mail.ru'),
 (4, 'Кузнецова Анна Викторовна',   '+7 903 444-55-66', 'kuznetsova@mail.ru');

INSERT INTO coupons VALUES
 (1, 'Без скидки',            'NO-DISCOUNT'),
 (2, 'Скидка 10% новосёлам',  'WELCOME10'),
 (3, 'Скидка 15% летняя',     'SUMMER15');

INSERT INTO bookings (`idbookings`, `дата заселения`, `статус брони`, `итог сумма`, `кол-во суток`, `guests_idguests`, `coupons_idcoupons`, `rooms_idrooms`) VALUES
 (1, '2026-11-01', 'Оплачено',      19500, 5, 1, 1, 4),
 (2, '2026-11-03', 'Забронировано',  7800, 2, 2, 2, 3),
 (3, '2026-11-05', 'Оплачено',      36000, 3, 3, 1, 7),
 (4, '2026-10-20', 'Выселен',        5500, 1, 4, 1, 8),
 (5, '2026-12-01', 'Забронировано', 11600, 4, 1, 3, 1);

INSERT INTO booking_services VALUES
 (1, 'Завтрак в номер', 5, 2500, 1),
 (2, 'Трансфер',        1, 1500, 1),
 (3, 'Спа',             3, 9000, 3),
 (4, 'Завтрак в номер', 2, 1000, 2);

INSERT INTO reviews VALUES
 (1, '5', 'Номер супер, вид завораживает!',      1, 4),
 (2, '4', 'Уютно, но хотелось большой экран.',   2, 3),
 (3, '5', 'Как в дворце! Спасибо персоналу.',    3, 7),
 (4, '3', 'Для семьи норм, но шумновато.',       4, 8);

INSERT INTO rooms_has_hotels VALUES
 (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 2), (7, 3), (8, 3);

INSERT INTO loyalty_cards VALUES
 (1, '1500 бонусов', 1, 4),
 (2, '300 бонусов',  2, 3),
 (3, '4200 бонусов', 3, 7),
 (4, '100 бонусов',  4, 8);

INSERT INTO users (`username`, `password_hash`, `role`, `guests_idguests`) VALUES
 ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', NULL),
 ('user',  'e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446', 'user',  1);

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
