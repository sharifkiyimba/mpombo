-- ============================================================
--  MPOMBO FAMILY RESTAURANT — DATABASE
--  Lyantonde District, Uganda
--  Run: mysql -u root -p < database.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS mpombo_restaurant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mpombo_restaurant;

-- ── Users ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    phone         VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin','staff','customer') DEFAULT 'customer',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Orders ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id                   INT PRIMARY KEY AUTO_INCREMENT,
    order_number         VARCHAR(50) UNIQUE NOT NULL,
    customer_name        VARCHAR(100) NOT NULL,
    customer_phone       VARCHAR(20)  NOT NULL,
    customer_email       VARCHAR(100),
    order_type           ENUM('delivery','pickup','dine_in') DEFAULT 'delivery',
    subtotal             DECIMAL(12,2) NOT NULL DEFAULT 0,
    delivery_fee         DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_amount         DECIMAL(12,2) NOT NULL DEFAULT 0,
    status               ENUM('pending','confirmed','preparing','ready','delivered','cancelled') DEFAULT 'pending',
    payment_method       ENUM('cash','mtn_momo','airtel_money','card') DEFAULT 'cash',
    payment_status       ENUM('pending','paid','failed') DEFAULT 'pending',
    delivery_address     TEXT,
    special_instructions TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Order Items ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    order_id      INT NOT NULL,
    menu_item_id  INT,
    item_name     VARCHAR(100),
    quantity      INT          NOT NULL DEFAULT 1,
    unit_price    DECIMAL(12,2) NOT NULL,
    subtotal      DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- ── Order Tracking ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_tracking (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    order_id   INT NOT NULL,
    status     VARCHAR(50) NOT NULL,
    notes      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- ── Reservations ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reservations (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    name             VARCHAR(100) NOT NULL,
    phone            VARCHAR(20)  NOT NULL,
    email            VARCHAR(100),
    guest_count      INT NOT NULL DEFAULT 2,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    special_requests TEXT,
    status           ENUM('pending','confirmed','cancelled','completed') DEFAULT 'pending',
    table_number     VARCHAR(10),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Admin user (password: admin123) ──────────────────────
-- Note: This is a placeholder hash. Run /setup-db to create the real admin.
INSERT IGNORE INTO users (username, email, phone, password_hash, role) VALUES
(
  'admin',
  'admin@mpombofamily.com',
  '+256700000000',
  'pbkdf2:sha256:260000$placeholder$run_setup_db_to_fix',
  'admin'
);

-- ── Sample orders (for testing) ──────────────────────────
INSERT IGNORE INTO orders
  (order_number, customer_name, customer_phone, order_type, subtotal, delivery_fee, total_amount, status, payment_method)
VALUES
  ('MP-SAMPLE-0001','Nakato Sarah',   '+256701000001','delivery',30000,5000,35000,'delivered','mtn_momo'),
  ('MP-SAMPLE-0002','Ssekamanya Mike','+256702000002','pickup',  25000,0,   25000,'delivered','cash'),
  ('MP-SAMPLE-0003','Grace Nantongo', '+256703000003','delivery',42000,5000,47000,'preparing','airtel_money'),
  ('MP-SAMPLE-0004','David Okullo',   '+256704000004','dine_in', 56000,0,   56000,'confirmed','cash'),
  ('MP-SAMPLE-0005','Fatuma Apio',    '+256705000005','delivery',8000, 5000,13000,'pending',  'mtn_momo');

-- ── Sample reservations ───────────────────────────────────
INSERT IGNORE INTO reservations
  (name, phone, email, guest_count, reservation_date, reservation_time, special_requests, status, table_number)
VALUES
  ('Nakato Family',    '+256706000006','nakato@email.com',  6, CURDATE() + INTERVAL 1 DAY, '13:00:00','Birthday celebration — please prepare cake area','confirmed','T3'),
  ('Ssekamanya M.',    '+256707000007','',                  2, CURDATE() + INTERVAL 2 DAY, '19:00:00','','pending',NULL),
  ('Kampala Business', '+256708000008','biz@company.com',   8, CURDATE() + INTERVAL 3 DAY, '12:30:00','Business lunch — need projector space','pending',NULL),
  ('Grace & Friends',  '+256709000009','',                  4, CURDATE() + INTERVAL 5 DAY, '18:00:00','Anniversary dinner','confirmed','T7');
