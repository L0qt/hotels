-- MySQL Forward Engineering для Отеля (Аналог интернет-магазина)

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema hotel_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `hotel_db` DEFAULT CHARACTER SET utf8 ;
USE `hotel_db` ;

-- -----------------------------------------------------
-- Table `hotel_db`.`room_categories` (Бывшая categories)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`room_categories` (
  `idroom_categories` INT NOT NULL,
  `тип номера` VARCHAR(45) NULL, -- Например: Люкс, Стандарт, Президентский
  PRIMARY KEY (`idroom_categories`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`room_classes` (Бывшая brands)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`room_classes` (
  `idroom_classes` INT NOT NULL,
  `класс комфорта` VARCHAR(45) NULL, -- Например: С видом на море, Семейный, Бизнес
  `room_categories_idroom_categories` INT NOT NULL,
  PRIMARY KEY (`idroom_classes`),
  INDEX `fk_classes_categories1_idx` (`room_categories_idroom_categories` ASC) VISIBLE,
  CONSTRAINT `fk_classes_categories1`
    FOREIGN KEY (`room_categories_idroom_categories`)
    REFERENCES `hotel_db`.`room_categories` (`idroom_categories`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`rooms` (Бывшая products)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`rooms` (
  `idrooms` INT NOT NULL,
  `цена за сутки` DOUBLE NULL,
  `характеристика` VARCHAR(45) NULL, -- Например: Кондиционер, Wi-Fi, 2 кровати
  `номер комнаты` INT NULL,          -- Номер на двери (например: 301)
  `описание` VARCHAR(45) NULL,
  `room_categories_idroom_categories` INT NOT NULL,
  `room_classes_idroom_classes` INT NOT NULL,
  PRIMARY KEY (`idrooms`),
  INDEX `fk_rooms_categories_idx` (`room_categories_idroom_categories` ASC) VISIBLE,
  INDEX `fk_rooms_classes1_idx` (`room_classes_idroom_classes` ASC) VISIBLE,
  CONSTRAINT `fk_rooms_categories`
    FOREIGN KEY (`room_categories_idroom_categories`)
    REFERENCES `hotel_db`.`room_categories` (`idroom_categories`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_rooms_classes1`
    FOREIGN KEY (`room_classes_idroom_classes`)
    REFERENCES `hotel_db`.`room_classes` (`idroom_classes`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`hotels` (Бывшая warehouses)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`hotels` (
  `idhotels` INT NOT NULL,
  `название` VARCHAR(45) NULL,       -- Название корпуса или филиала отеля
  `номер корпуса` INT NULL,
  PRIMARY KEY (`idhotels`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`hotel_room_stocks` (Бывшая product_warehouses)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`hotel_room_stocks` (
  `idroom_stocks` INT NOT NULL,
  `кол-во свободных мест` INT NULL,
  `hotels_idhotels` INT NOT NULL,
  PRIMARY KEY (`idroom_stocks`),
  INDEX `fk_room_stocks_hotels1_idx` (`hotels_idhotels` ASC) VISIBLE,
  CONSTRAINT `fk_room_stocks_hotels1`
    FOREIGN KEY (`hotels_idhotels`)
    REFERENCES `hotel_db`.`hotels` (`idhotels`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`guests` (Бывшая customers)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`guests` (
  `idguests` INT NOT NULL,
  `ФИО` VARCHAR(45) NULL,
  `Номер телефона` INT NULL,
  `Почта` VARCHAR(45) NULL,
  PRIMARY KEY (`idguests`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`coupons` (Бывшая coupons)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`coupons` (
  `idcoupons` INT NOT NULL,
  `информация` VARCHAR(45) NULL,
  `номер купона` VARCHAR(45) NULL,
  PRIMARY KEY (`idcoupons`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`bookings` (Бывшая orders)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`bookings` (
  `idbookings` INT NOT NULL,
  `дата заселения` DATE NULL,
  `статус брони` VARCHAR(45) NULL,   -- Например: Забронировано, Оплачено, Выселен
  `итог сумма` DOUBLE NULL,
  `guests_idguests` INT NOT NULL,
  `coupons_idcoupons` INT NOT NULL,
  PRIMARY KEY (`idbookings`),
  INDEX `fk_bookings_guests1_idx` (`guests_idguests` ASC) VISIBLE,
  INDEX `fk_bookings_coupons1_idx` (`coupons_idcoupons` ASC) VISIBLE,
  CONSTRAINT `fk_bookings_guests1`
    FOREIGN KEY (`guests_idguests`)
    REFERENCES `hotel_db`.`guests` (`idguests`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_bookings_coupons1`
    FOREIGN KEY (`coupons_idcoupons`)
    REFERENCES `hotel_db`.`coupons` (`idcoupons`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`booking_services` (Бывшая order_items)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`booking_services` (
  `idbooking_services` INT NOT NULL,
  `доп услуга` VARCHAR(45) NULL,     -- Например: Завтрак в номер, Спа, Трансфер
  `кол_во суток` INT NULL,
  `сумма` DOUBLE NULL,
  `bookings_idbookings` INT NOT NULL,
  PRIMARY KEY (`idbooking_services`),
  INDEX `fk_services_bookings1_idx` (`bookings_idbookings` ASC) VISIBLE,
  CONSTRAINT `fk_services_bookings1`
    FOREIGN KEY (`bookings_idbookings`)
    REFERENCES `hotel_db`.`bookings` (`idbookings`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`reviews` (Бывшая reviews)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`reviews` (
  `idreviews` INT NOT NULL,
  `оценка` VARCHAR(45) NULL,
  `комментарий` VARCHAR(45) NULL,
  `guests_idguests` INT NOT NULL,
  `rooms_idrooms` INT NOT NULL,
  PRIMARY KEY (`idreviews`),
  INDEX `fk_reviews_guests1_idx` (`guests_idguests` ASC) VISIBLE,
  INDEX `fk_reviews_rooms1_idx` (`rooms_idrooms` ASC) VISIBLE,
  CONSTRAINT `fk_reviews_guests1`
    FOREIGN KEY (`guests_idguests`)
    REFERENCES `hotel_db`.`guests` (`idguests`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_reviews_rooms1`
    FOREIGN KEY (`rooms_idrooms`)
    REFERENCES `hotel_db`.`rooms` (`idrooms`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`rooms_has_hotels` (Бывшая products_has_warehouses)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`rooms_has_hotels` (
  `rooms_idrooms` INT NOT NULL,
  `hotels_idhotels` INT NOT NULL,
  PRIMARY KEY (`rooms_idrooms`, `hotels_idhotels`),
  INDEX `fk_rooms_has_hotels_hotels1_idx` (`hotels_idhotels` ASC) VISIBLE,
  INDEX `fk_rooms_has_hotels_rooms1_idx` (`rooms_idrooms` ASC) VISIBLE,
  CONSTRAINT `fk_rooms_has_hotels_rooms1`
    FOREIGN KEY (`rooms_idrooms`)
    REFERENCES `hotel_db`.`rooms` (`idrooms`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_rooms_has_hotels_hotels1`
    FOREIGN KEY (`hotels_idhotels`)
    REFERENCES `hotel_db`.`hotels` (`idhotels`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `hotel_db`.`loyalty_cards` (Бывшая loyalty_cards, дописана до конца)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hotel_db`.`loyalty_cards` (
  `idloyalty_cards` INT NOT NULL,
  `бонус баланс` VARCHAR(45) NULL,
  `guests_idguests` INT NOT NULL,
  `rooms_idrooms` INT NOT NULL,
  PRIMARY KEY (`idloyalty_cards`),
  INDEX `fk_loyalty_cards_guests1_idx` (`guests_idguests` ASC) VISIBLE,
  INDEX `fk_loyalty_cards_rooms1_idx` (`rooms_idrooms` ASC) VISIBLE,
  CONSTRAINT `fk_loyalty_cards_guests1`
    FOREIGN KEY (`guests_idguests`)
    REFERENCES `hotel_db`.`guests` (`idguests`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_loyalty_cards_rooms1`
    FOREIGN KEY (`rooms_idrooms`)
    REFERENCES `hotel_db`.`rooms` (`idrooms`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
