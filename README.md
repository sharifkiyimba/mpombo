# 🍽️ Mpombo Family Restaurant — Web System

**Authentic Ugandan Food · Lyantonde District, Uganda**

A complete Flask restaurant management system with:
- Full public website (homepage, menu, order, reservation, tracking)
- Admin dashboard (orders, reservations, customers, sales report)
- UGX pricing throughout
- MTN MoMo + Airtel Money + Cash payment options
- Mobile-responsive Ugandan aesthetic design

---

## 📁 Project Structure

```
mpombo/
├── app.py                        ← Main Flask application
├── .env                          ← Environment variables (DB credentials)
├── requirements.txt              ← Python dependencies
├── database.sql                  ← Full database schema + sample data
└── templates/
    ├── base.html                 ← Master layout (nav, footer, design system)
    ├── index.html                ← Homepage
    ├── menu.html                 ← Full menu with cart
    ├── order.html                ← Checkout / place order
    ├── reserve.html              ← Table reservation
    ├── track.html                ← Order tracking
    ├── reservation_status.html   ← Check reservation status
    ├── about.html                ← About the restaurant
    ├── contact.html              ← Contact page
    ├── login.html                ← Login page
    ├── register.html             ← Register page
    └── admin/
        ├── base_admin.html       ← Admin layout with sidebar
        ├── dashboard.html        ← Admin dashboard
        ├── orders.html           ← Order management
        ├── reservations.html     ← Reservation management
        ├── sales.html            ← Sales reports
        └── customers.html        ← Customer list
```

---

## ⚙️ Setup Instructions

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

> If you have issues, try:
> ```bash
> pip install Flask==2.3.3 Werkzeug==2.3.7 Flask-MySQLdb==1.0.1 python-dotenv==1.0.0
> ```
> You may also need: `sudo apt-get install libmysqlclient-dev` on Ubuntu/WSL

---

### 2. Create the MySQL Database

**Option A — Run the SQL file:**
```bash
mysql -u root -p < database.sql
```

**Option B — In MySQL shell:**
```sql
CREATE DATABASE mpombo_restaurant;
```

---

### 3. Configure Your Environment

Edit `.env` with your MySQL credentials:

```env
SECRET_KEY=mpombo-super-secret-key-2024
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=raxsun12345
MYSQL_DB=mpombo_restaurant
```

---

### 4. Run the Application

```bash
python app.py
```

---

### 5. Set Up the Database Tables

Open your browser and visit:
```
http://localhost:5000/setup-db
```

This creates all tables and the admin user automatically.

---

### 6. Access the System

| URL | Description |
|-----|-------------|
| `http://localhost:5000/` | Homepage |
| `http://localhost:5000/menu` | Full menu |
| `http://localhost:5000/order` | Place an order |
| `http://localhost:5000/reserve` | Reserve a table |
| `http://localhost:5000/track` | Track an order |
| `http://localhost:5000/login` | Staff/Admin login |
| `http://localhost:5000/dashboard` | Admin dashboard |
| `http://localhost:5000/setup-db` | Initialize DB (run once) |
| `http://localhost:5000/fix-db` | Patch old DB schema |

---

## 🔐 Admin Login

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

> ⚠️ Change this password after first login!

---

## 💳 Payment Methods Supported

| Method | Value in DB |
|--------|------------|
| MTN Mobile Money | `mtn_momo` |
| Airtel Money | `airtel_money` |
| Cash on Delivery | `cash` |
| Card Payment | `card` |

---

## 🚗 Delivery Pricing (UGX)

| Setting | Value |
|---------|-------|
| Base fee | UGX 5,000 |
| Per kilometre | UGX 1,000 |
| Max distance | 20 km |
| Free delivery on orders above | UGX 50,000 |

---

## 📋 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/place-order` | Place a new order (JSON) |
| `POST` | `/api/reserve` | Make a reservation (JSON) |
| `POST` | `/admin/update-order` | Update order status |
| `POST` | `/admin/update-reservation` | Update reservation status |

---

## 🌍 Ugandan Menu Categories

1. **Ugandan Specials** — Luwombo, Matoke, Rolex, Posho & Beans, Katogo, Groundnut Soup
2. **Grills & Meats** — Tilapia, Nyama Choma, Grilled Chicken, Beef Muchomo, Beef Steak
3. **Rice & Stews** — Rice & Chicken Stew, Beef Pilau, Beans & Rice
4. **Sides & Extras** — Chips, Chapati, Steamed Rice, Kachumbari, Posho
5. **Drinks** — Passion Juice, Pineapple Juice, Avocado Smoothie, Soda, Water, Waragi Cocktail

---

## 🛠️ Troubleshooting

**MySQL connection error:**
- Check `.env` credentials match your MySQL setup
- Make sure MySQL service is running: `sudo service mysql start`

**Table doesn't exist:**
- Visit `http://localhost:5000/setup-db` to create tables

**`total` column missing:**
- Visit `http://localhost:5000/fix-db` to patch the schema

**Flask-MySQLdb install fails:**
- Try: `sudo apt-get install python3-dev default-libmysqlclient-dev`
- Then: `pip install mysqlclient`

---

*Built for Mpombo Family Restaurant · Lyantonde District, Uganda 🇺🇬*
