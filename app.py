from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import random, string, json, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mpombo-uganda-secret-2024')

# ── Database ─────────────────────────────────────────────
app.config['MYSQL_HOST']     = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER']     = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB']       = os.environ.get('MYSQL_DB', 'mpombo_restaurant')
app.config['MYSQL_PORT']     = int(os.environ.get('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ── Restaurant Config ─────────────────────────────────────
class Config:
    RESTAURANT_NAME     = 'Mpombo Family Restaurant'
    RESTAURANT_PHONE    = '+256-789-123-456'
    RESTAURANT_WHATSAPP = '256789123456'
    RESTAURANT_EMAIL    = 'info@mpombofamily.com'
    RESTAURANT_ADDRESS  = 'Opposite Petro Uganda, Lyantonde District, Uganda'
    DELIVERY_BASE_FEE   = 5000   # UGX
    DELIVERY_PER_KM     = 1000   # UGX per km
    MAX_DELIVERY_KM     = 20
    FREE_DELIVERY_MIN   = 50000  # UGX — orders above this get free delivery

# ── Full Ugandan Menu ─────────────────────────────────────
MENU = [
    {
        'id': 1, 'name': 'Ugandan Specials', 'icon': '🍌',
        'description': 'Authentic traditional dishes cooked the real Ugandan way',
        'dishes': [
            {'id': 101, 'name': 'Luwombo (Chicken)',        'price': 30000, 'prep': 35, 'badge': 'Bestseller', 'veg': False,
             'desc': 'Traditional steamed chicken wrapped in fresh banana leaves, slow-cooked with rich groundnut sauce. A Buganda royal delicacy.',
             'img': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=600&q=80'},
            {'id': 102, 'name': 'Matoke & Groundnut Sauce', 'price': 12000, 'prep': 25, 'badge': 'Vegan',      'veg': True,
             'desc': 'Steamed green bananas served with rich groundnut (enkinyagi) sauce. The backbone of Ugandan home cooking.',
             'img': 'https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=600&q=80'},
            {'id': 103, 'name': 'Rolex',                    'price': 8000,  'prep': 10, 'badge': 'Street Fave','veg': True,
             'desc': "Uganda's iconic rolled chapati with fried eggs, cabbage, tomatoes and onions. A beloved street food staple.",
             'img': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=600&q=80'},
            {'id': 104, 'name': 'Posho & Beans',            'price': 7000,  'prep': 20, 'badge': 'Vegan',      'veg': True,
             'desc': 'Stiff maize ugali with slow-cooked kidney beans in a rich tomato and onion gravy. Filling and classic.',
             'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 105, 'name': 'Katogo (Offals & Matoke)', 'price': 15000, 'prep': 30, 'badge': 'Breakfast',  'veg': False,
             'desc': 'A hearty Ugandan breakfast — matoke cooked with beef offals in tomato gravy. Rich, warming, deeply satisfying.',
             'img': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80'},
            {'id': 106, 'name': 'Groundnut Soup',           'price': 14000, 'prep': 25, 'badge': 'Vegan',      'veg': True,
             'desc': 'Creamy, warming soup made from fresh Ugandan groundnuts. Served with posho or rice of your choice.',
             'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
        ]
    },
    {
        'id': 2, 'name': 'Grills & Meats', 'icon': '🔥',
        'description': 'Fresh meats grilled over charcoal with Ugandan herbs and spices',
        'dishes': [
            {'id': 201, 'name': 'Grilled Tilapia (Whole)',  'price': 28000, 'prep': 25, 'badge': 'Lake Fresh', 'veg': False,
             'desc': 'Fresh Lake Victoria tilapia, grilled whole with lemon, garlic and local spices. Served with chips or posho.',
             'img': 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&q=80'},
            {'id': 202, 'name': 'Nyama Choma (Goat)',       'price': 35000, 'prep': 40, 'badge': 'Signature',  'veg': False,
             'desc': 'Ugandan-style roasted goat, slow-cooked over firewood for deep smoky flavour. Served with kachumbari salad.',
             'img': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80'},
            {'id': 203, 'name': 'Grilled Chicken (Half)',   'price': 25000, 'prep': 30, 'badge': None,         'veg': False,
             'desc': 'Free-range chicken marinated in local spices, grilled to a golden crisp. Juicy inside, charred outside.',
             'img': 'https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=600&q=80'},
            {'id': 204, 'name': 'Beef Muchomo (Skewers)',   'price': 18000, 'prep': 20, 'badge': 'Popular',    'veg': False,
             'desc': 'Tender beef pieces on skewers, grilled over charcoal with onions, peppers and Ugandan seasoning.',
             'img': 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=600&q=80'},
            {'id': 205, 'name': 'Beef Steak',               'price': 38000, 'prep': 25, 'badge': 'Premium',    'veg': False,
             'desc': 'Prime beef steak cooked to your preference, served with sautéed vegetables and your choice of starch.',
             'img': 'https://images.unsplash.com/photo-1546964124-0cce460f38ef?w=600&q=80'},
        ]
    },
    {
        'id': 3, 'name': 'Rice & Stews', 'icon': '🍛',
        'description': 'Comforting rice dishes and slow-cooked Ugandan stews',
        'dishes': [
            {'id': 301, 'name': 'Rice & Chicken Stew',      'price': 18000, 'prep': 20, 'badge': None,         'veg': False,
             'desc': 'Steamed white rice served with slow-cooked chicken stew in tomato, onion and pepper sauce.',
             'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 302, 'name': 'Beef Pilau',               'price': 20000, 'prep': 30, 'badge': 'Spiced',     'veg': False,
             'desc': 'Fragrant East African spiced rice cooked with tender beef, cumin, cloves, cinnamon and black pepper.',
             'img': 'https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&q=80'},
            {'id': 303, 'name': 'Beans & Rice',             'price': 9000,  'prep': 15, 'badge': 'Vegan',      'veg': True,
             'desc': 'Red kidney beans in a rich tomato sauce on a bed of fluffy steamed white rice.',
             'img': 'https://images.unsplash.com/photo-1567364816519-cbc9c4ffe1eb?w=600&q=80'},
        ]
    },
    {
        'id': 4, 'name': 'Sides & Extras', 'icon': '🍟',
        'description': 'Perfect additions to complete your meal',
        'dishes': [
            {'id': 401, 'name': 'Chips (French Fries)',     'price': 8000,  'prep': 12, 'badge': None,         'veg': True,
             'desc': 'Thick-cut golden chips fried to a crisp. Served with ketchup or chilli sauce.',
             'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 402, 'name': 'Chapati (2 pieces)',       'price': 2000,  'prep': 8,  'badge': 'Vegan',      'veg': True,
             'desc': 'Soft, layered flatbread made from wheat flour on a hot griddle. Perfect with any stew.',
             'img': 'https://images.unsplash.com/photo-1635194415227-7d2bf0a161d2?w=600&q=80'},
            {'id': 403, 'name': 'Steamed Rice',             'price': 5000,  'prep': 15, 'badge': 'Vegan',      'veg': True,
             'desc': 'Plain steamed white rice — the perfect base for any stew or sauce.',
             'img': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=600&q=80'},
            {'id': 404, 'name': 'Kachumbari Salad',         'price': 4000,  'prep': 5,  'badge': 'Vegan',      'veg': True,
             'desc': 'Fresh East African salad of diced tomatoes, red onions, coriander and chilli.',
             'img': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&q=80'},
            {'id': 405, 'name': 'Posho (Ugali)',            'price': 3000,  'prep': 10, 'badge': 'Vegan',      'veg': True,
             'desc': 'Stiff maize flour ugali — the ultimate Ugandan staple. Pairs perfectly with any stew.',
             'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
        ]
    },
    {
        'id': 5, 'name': 'Drinks', 'icon': '🥤',
        'description': 'Fresh local juices and cold beverages',
        'dishes': [
            {'id': 501, 'name': 'Fresh Passion Juice',      'price': 5000,  'prep': 5,  'badge': 'Fresh',      'veg': True,
             'desc': "Freshly squeezed passion fruit — Uganda's most beloved tropical juice. Tart, sweet, energising.",
             'img': 'https://images.unsplash.com/photo-1613478225719-9e5d4f3d8c3a?w=600&q=80'},
            {'id': 502, 'name': 'Fresh Pineapple Juice',    'price': 5000,  'prep': 5,  'badge': 'Fresh',      'veg': True,
             'desc': "Cold-pressed fresh pineapple using Uganda's sweet highland pineapples. No sugar added.",
             'img': 'https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=600&q=80'},
            {'id': 503, 'name': 'Avocado Smoothie',         'price': 7000,  'prep': 7,  'badge': 'Local Fave', 'veg': True,
             'desc': 'Creamy Ugandan avocado blended with milk and honey. Thick, nutritious, uniquely Ugandan.',
             'img': 'https://images.unsplash.com/photo-1638176066666-ffb2f013c7dd?w=600&q=80'},
            {'id': 504, 'name': 'Soda (Coke/Fanta/Sprite)', 'price': 3000, 'prep': 1,  'badge': None,         'veg': True,
             'desc': 'Chilled 500ml soft drink. Choose from Coca-Cola, Fanta Orange, or Sprite.',
             'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 505, 'name': 'Mineral Water (500ml)',    'price': 2000,  'prep': 1,  'badge': None,         'veg': True,
             'desc': 'Cold Rwenzori or Splash mineral water.',
             'img': 'https://images.unsplash.com/photo-1564419320468-6872c04a7f6e?w=600&q=80'},
            {'id': 506, 'name': 'Waragi Cocktail',          'price': 12000, 'prep': 5,  'badge': '18+',        'veg': True,
             'desc': "Uganda's favourite gin-based spirit mixed with tonic and fresh lime. Adults only.",
             'img': 'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=600&q=80'},
        ]
    },
]

ALL_ITEMS = {item['id']: item for cat in MENU for item in cat['dishes']}

# ── Jinja Globals ─────────────────────────────────────────
def fmt_ugx(amount):
    try:
        return f"UGX {int(float(amount)):,}"
    except:
        return "UGX 0"

app.jinja_env.globals['fmt_ugx'] = fmt_ugx
app.jinja_env.globals['now']     = datetime.now

# ── Decorators ────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Helpers ───────────────────────────────────────────────
def gen_order_number():
    ts  = datetime.now().strftime('%y%m%d%H%M%S')
    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f'MP-{ts}-{rnd}'

def calc_delivery_fee(distance_km, subtotal):
    if subtotal >= Config.FREE_DELIVERY_MIN:
        return 0
    if distance_km > Config.MAX_DELIVERY_KM:
        return None  # out of range
    return Config.DELIVERY_BASE_FEE + (distance_km * Config.DELIVERY_PER_KM)

def get_order_cols():
    """Return actual column names of the orders table."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("DESCRIBE orders")
        cols = [r['Field'] for r in cur.fetchall()]
        cur.close()
        return cols
    except:
        return []

def get_total_col():
    """Detect which total column the orders table uses (handles legacy schemas)."""
    cols = get_order_cols()
    if 'total_amount' in cols: return 'total_amount'
    if 'total'        in cols: return 'total'
    return None

# ═══════════════════════════════════════════════════════════
#  PUBLIC PAGES
# ═══════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html', config=Config, menu=MENU)

@app.route('/menu')
def menu():
    return render_template('menu.html', config=Config, menu=MENU)

@app.route('/about')
def about():
    return render_template('about.html', config=Config)

@app.route('/contact')
def contact():
    return render_template('contact.html', config=Config)

@app.route('/order')
def order():
    return render_template('order.html', config=Config, menu=MENU)

@app.route('/reserve')
def reserve():
    return render_template('reserve.html', config=Config)

# ── Track Order ───────────────────────────────────────────
@app.route('/track', methods=['GET', 'POST'])
def track():
    order_data = None
    order_number = ''
    if request.method == 'POST':
        order_number = request.form.get('order_number', '').strip().upper()
        if order_number:
            try:
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM orders WHERE order_number = %s", (order_number,))
                row = cur.fetchone()
                if row:
                    tc = get_total_col()
                    order_data = dict(row)
                    order_data['total_display'] = fmt_ugx(order_data.get(tc, 0) if tc else 0)
                    # If old schema, try to pull customer info from customers table
                    if not order_data.get('customer_name') and order_data.get('customer_id'):
                        try:
                            cur.execute("SELECT * FROM customers WHERE id=%s", (order_data['customer_id'],))
                            cust = cur.fetchone()
                            if cust:
                                order_data['customer_name'] = cust['name']
                                order_data['customer_phone'] = cust['phone']
                        except:
                            pass
                    # Fetch order items
                    try:
                        cur.execute("""
                            SELECT oi.*, mi.name as item_name
                            FROM order_items oi
                            LEFT JOIN menu_items mi ON oi.menu_item_id = mi.id
                            WHERE oi.order_id = %s
                        """, (row['id'],))
                        order_data['items_list'] = cur.fetchall()
                    except:
                        # Fallback: try JSON items column
                        try:
                            order_data['items_list'] = json.loads(order_data.get('items', '[]') or '[]')
                        except:
                            order_data['items_list'] = []
                    # Fetch status history
                    try:
                        cur.execute("SELECT * FROM order_tracking WHERE order_id = %s ORDER BY created_at ASC", (row['id'],))
                        order_data['tracking'] = cur.fetchall()
                    except:
                        order_data['tracking'] = []
                else:
                    flash(f'No order found with number "{order_number}". Please check and try again.', 'warning')
                cur.close()
            except Exception as e:
                flash(f'Error: {e}', 'danger')
    return render_template('track.html', config=Config, order=order_data, order_number=order_number)

# ── Reservation Status ────────────────────────────────────
@app.route('/reservation-status')
def reservation_status():
    phone = request.args.get('phone', '').strip()
    reservation = None
    if phone:
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT * FROM reservations WHERE phone = %s ORDER BY reservation_date DESC LIMIT 1",
                (phone,)
            )
            reservation = cur.fetchone()
            cur.close()
            if not reservation:
                flash('No reservation found for that phone number.', 'warning')
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('reservation_status.html', config=Config, reservation=reservation)

# ═══════════════════════════════════════════════════════════
#  AUTHENTICATION
# ═══════════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, username))
            user = cur.fetchone()
            cur.close()
            if user and check_password_hash(user['password_hash'], password):
                session['logged_in'] = True
                session['user_id']   = user['id']
                session['username']  = user['username']
                session['role']      = user['role']
                flash(f"Welcome back, {user['username']}! 👋", 'success')
                return redirect(url_for('dashboard') if user['role'] == 'admin' else url_for('index'))
            else:
                flash('Wrong username or password. Please try again.', 'danger')
        except Exception as e:
            flash(f'Login error: {e}', 'danger')
    return render_template('login.html', config=Config)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO users (username, email, phone, password_hash, role) VALUES (%s,%s,%s,%s,'customer')",
                (username, email, phone, generate_password_hash(password))
            )
            mysql.connection.commit()
            cur.close()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username or email already exists.', 'danger')
    return render_template('register.html', config=Config)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current  = request.form.get('current', '')
        new_pass = request.form.get('new_password', '')
        confirm  = request.form.get('confirm', '')

        if new_pass != confirm:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))

        if len(new_pass) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('change_password'))

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()

            if not check_password_hash(user['password_hash'], current):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('change_password'))

            new_hash = generate_password_hash(new_pass)
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, session['user_id'])
            )
            mysql.connection.commit()
            cur.close()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard') if session.get('role') == 'admin' else url_for('index'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')

    return render_template('change_password.html', config=Config)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out. Come back soon! 🍽️', 'info')
    return redirect(url_for('index'))

# ═══════════════════════════════════════════════════════════
#  ORDER API
# ═══════════════════════════════════════════════════════════

@app.route('/api/place-order', methods=['POST'])
def place_order():
    try:
        data       = request.json
        items      = data.get('items', [])
        name       = data.get('name', '').strip()
        phone      = data.get('phone', '').strip()
        email      = data.get('email', '')
        pay_method = data.get('payment_method', 'cash')
        order_type = data.get('order_type', 'delivery')
        distance   = float(data.get('distance', 0))
        address    = data.get('address', '')
        notes      = data.get('notes', '')

        if not items:
            return jsonify({'success': False, 'error': 'No items in order'}), 400
        if not name or not phone:
            return jsonify({'success': False, 'error': 'Name and phone are required'}), 400

        subtotal = sum(float(i['price']) * int(i['quantity']) for i in items)
        fee      = 0 if order_type != 'delivery' else (calc_delivery_fee(distance, subtotal) or 0)
        total    = subtotal + fee
        order_no = gen_order_number()

        cur  = mysql.connection.cursor()
        cols = get_order_cols()   # actual columns in the orders table
        tc   = get_total_col()    # 'total_amount' or 'total'

        # ── Build INSERT dynamically based on what columns exist ──────────
        fields = ['order_number', 'status']
        values = [order_no, 'pending']

        # customer identity — new schema uses customer_name/phone, old uses customer_id
        if 'customer_name' in cols:
            fields += ['customer_name', 'customer_phone']
            values += [name, phone]
        if 'customer_email' in cols:
            fields.append('customer_email'); values.append(email)

        # order type
        if 'order_type' in cols:
            fields.append('order_type'); values.append(order_type)

        # money columns
        if 'subtotal' in cols:
            fields.append('subtotal'); values.append(subtotal)
        if 'delivery_fee' in cols:
            fields.append('delivery_fee'); values.append(fee)
        if tc:
            fields.append(tc); values.append(total)

        # payment
        if 'payment_method' in cols:
            fields.append('payment_method'); values.append(pay_method)
        if 'payment_status' in cols:
            fields.append('payment_status'); values.append('pending')

        # address / notes
        if 'delivery_address' in cols:
            fields.append('delivery_address'); values.append(address)
        if 'special_instructions' in cols:
            fields.append('special_instructions'); values.append(notes)

        placeholders = ', '.join(['%s'] * len(fields))
        col_list     = ', '.join(fields)
        cur.execute(
            f"INSERT INTO orders ({col_list}) VALUES ({placeholders})",
            values
        )
        order_id = cur.lastrowid

        # ── If old schema uses customer_id, create/find a customers row ──
        if 'customer_id' in cols and 'customer_name' not in cols:
            try:
                cur.execute("SELECT id FROM customers WHERE phone=%s", (phone,))
                cust = cur.fetchone()
                if cust:
                    cust_id = cust['id']
                else:
                    cur.execute(
                        "INSERT INTO customers (name, phone, email) VALUES (%s,%s,%s)",
                        (name, phone, email)
                    )
                    cust_id = cur.lastrowid
                cur.execute("UPDATE orders SET customer_id=%s WHERE id=%s", (cust_id, order_id))
            except:
                pass  # customers table may not exist either — non-fatal

        # ── Insert order_items rows ──
        for item in items:
            item_subtotal = float(item['price']) * int(item['quantity'])
            try:
                cur.execute("""
                    INSERT INTO order_items
                      (order_id, menu_item_id, item_name, quantity, unit_price, subtotal)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (order_id, item['id'], item['name'],
                      item['quantity'], item['price'], item_subtotal))
            except:
                try:
                    # Fallback: table without item_name column
                    cur.execute("""
                        INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, subtotal)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (order_id, item['id'], item['quantity'], item['price'], item_subtotal))
                except:
                    pass

        # ── Tracking record ──
        try:
            cur.execute(
                "INSERT INTO order_tracking (order_id, status, notes) VALUES (%s,'pending','Order received')",
                (order_id,)
            )
        except:
            pass

        mysql.connection.commit()
        cur.close()

        return jsonify({
            'success':       True,
            'order_number':  order_no,
            'total':         total,
            'total_display': fmt_ugx(total)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ═══════════════════════════════════════════════════════════
#  RESERVATION API
# ═══════════════════════════════════════════════════════════

@app.route('/api/reserve', methods=['POST'])
def api_reserve():
    try:
        data = request.json
        cur  = mysql.connection.cursor()
        # Try new schema (guest_count) then fall back to old (guests)
        try:
            cur.execute("""
                INSERT INTO reservations
                  (name, phone, email, guest_count, reservation_date, reservation_time,
                   special_requests, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'pending')
            """, (data['name'], data['phone'], data.get('email',''),
                  data['guests'], data['date'], data['time'],
                  data.get('special_requests','')))
        except:
            cur.execute("""
                INSERT INTO reservations
                  (name, phone, email, guests, reservation_date, reservation_time,
                   special_requests, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'pending')
            """, (data['name'], data['phone'], data.get('email',''),
                  data['guests'], data['date'], data['time'],
                  data.get('special_requests','')))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True, 'message': 'Reservation received! We will confirm via phone.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ═══════════════════════════════════════════════════════════
#  ADMIN — DASHBOARD
# ═══════════════════════════════════════════════════════════

@app.route('/dashboard')
@admin_required
def dashboard():
    tc    = get_total_col()
    today = datetime.now().strftime('%Y-%m-%d')
    cur   = mysql.connection.cursor()

    # Today's stats
    if tc:
        cur.execute(f"""
            SELECT COUNT(*) as orders_today,
                   COALESCE(SUM({tc}),0) as revenue_today,
                   SUM(CASE WHEN status='pending'  THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status='preparing'THEN 1 ELSE 0 END) as preparing
            FROM orders WHERE DATE(created_at)=%s
        """, (today,))
    else:
        cur.execute("""
            SELECT COUNT(*) as orders_today, 0 as revenue_today,
                   SUM(CASE WHEN status='pending'  THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status='preparing'THEN 1 ELSE 0 END) as preparing
            FROM orders WHERE DATE(created_at)=%s
        """, (today,))
    stats = cur.fetchone() or {}

    # All-time
    if tc:
        cur.execute(f"SELECT COUNT(*) as total_orders, COALESCE(SUM({tc}),0) as total_revenue FROM orders")
    else:
        cur.execute("SELECT COUNT(*) as total_orders, 0 as total_revenue FROM orders")
    all_time = cur.fetchone() or {}

    # Recent orders — join customers if old schema
    order_cols = get_order_cols()
    if 'customer_name' in order_cols:
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 15")
    else:
        try:
            cur.execute("""
                SELECT o.*, c.name as customer_name, c.phone as customer_phone, c.email as customer_email
                FROM orders o LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.created_at DESC LIMIT 15
            """)
        except:
            cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 15")
    raw_orders = cur.fetchall()
    orders = []
    for row in raw_orders:
        d = dict(row)
        d['total_display'] = fmt_ugx(d.get(tc, 0) if tc else 0)
        orders.append(d)

    # Upcoming reservations
    cur.execute("""
        SELECT * FROM reservations
        WHERE reservation_date >= CURDATE() AND status='pending'
        ORDER BY reservation_date, reservation_time LIMIT 8
    """)
    reservations = cur.fetchall()

    # Customer count
    cur.execute("SELECT COUNT(*) as count FROM users WHERE role='customer'")
    customers = cur.fetchone() or {'count': 0}

    cur.close()
    return render_template('admin/dashboard.html',
        config=Config, stats=stats, all_time=all_time,
        orders=orders, reservations=reservations,
        customers=customers, today=today)

# ═══════════════════════════════════════════════════════════
#  ADMIN — ORDERS
# ═══════════════════════════════════════════════════════════

@app.route('/admin/orders')
@admin_required
def admin_orders():
    tc             = get_total_col()
    status_filter  = request.args.get('status', '')
    search         = request.args.get('q', '').strip()
    cur            = mysql.connection.cursor()

    order_cols = get_order_cols()
    has_cust_cols = "customer_name" in order_cols
    params = []
    if has_cust_cols:
        query = "SELECT * FROM orders WHERE 1=1"
        if status_filter:
            query += " AND status=%s"; params.append(status_filter)
        if search:
            query += " AND (order_number LIKE %s OR customer_name LIKE %s OR customer_phone LIKE %s)"
            s = f'%{search}%'; params += [s, s, s]
        query += " ORDER BY created_at DESC"
    else:
        query = ("SELECT o.*, c.name as customer_name, c.phone as customer_phone,"
                 " c.email as customer_email FROM orders o"
                 " LEFT JOIN customers c ON o.customer_id = c.id WHERE 1=1")
        if status_filter:
            query += " AND o.status=%s"; params.append(status_filter)
        if search:
            query += " AND (o.order_number LIKE %s OR c.name LIKE %s OR c.phone LIKE %s)"
            s = f'%{search}%'; params += [s, s, s]
        query += " ORDER BY o.created_at DESC"
    try:
        cur.execute(query, params)
    except:
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")

    orders = []
    for row in cur.fetchall():
        d = dict(row)
        d['total_display'] = fmt_ugx(d.get(tc, 0) if tc else 0)
        orders.append(d)
    cur.close()

    return render_template('admin/orders.html',
        config=Config, orders=orders,
        status_filter=status_filter, search=search)

@app.route('/admin/update-order', methods=['POST'])
@admin_required
def update_order():
    try:
        data = request.json
        cur  = mysql.connection.cursor()
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (data['status'], data['order_id']))
        # Log the status change in order_tracking
        try:
            cur.execute(
                "INSERT INTO order_tracking (order_id, status, notes) VALUES (%s,%s,%s)",
                (data['order_id'], data['status'], f"Status updated to {data['status']}")
            )
        except:
            pass
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Legacy route alias

# ═══════════════════════════════════════════════════════════
#  ADMIN — RESERVATIONS
# ═══════════════════════════════════════════════════════════

@app.route('/admin/reservations')
@admin_required
def admin_reservations():
    status_filter = request.args.get('status', '')
    cur           = mysql.connection.cursor()
    if status_filter:
        cur.execute(
            "SELECT * FROM reservations WHERE status=%s ORDER BY reservation_date DESC, reservation_time",
            (status_filter,)
        )
    else:
        cur.execute("SELECT * FROM reservations ORDER BY reservation_date DESC, reservation_time")
    reservations = cur.fetchall()
    cur.close()
    return render_template('admin/reservations.html',
        config=Config, reservations=reservations, status_filter=status_filter)

@app.route('/admin/update-reservation', methods=['POST'])
@admin_required
def update_reservation():
    try:
        data = request.json
        cur  = mysql.connection.cursor()
        cur.execute(
            "UPDATE reservations SET status=%s, table_number=%s WHERE id=%s",
            (data['status'], data.get('table_number', ''), data['reservation_id'])
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ═══════════════════════════════════════════════════════════
#  ADMIN — SALES REPORT
# ═══════════════════════════════════════════════════════════

@app.route('/admin/sales')
@admin_required
def admin_sales():
    tc        = get_total_col()
    date_from = request.args.get('from', (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to   = request.args.get('to',   datetime.now().strftime('%Y-%m-%d'))
    cur       = mysql.connection.cursor()

    if tc:
        cur.execute(f"""
            SELECT DATE(created_at) as sale_date,
                   COUNT(*) as order_count,
                   COALESCE(SUM({tc}), 0) as total_sales,
                   COALESCE(SUM(subtotal), 0) as subtotal_sales,
                   COALESCE(SUM(delivery_fee), 0) as delivery_revenue
            FROM orders
            WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY DATE(created_at)
            ORDER BY sale_date DESC
        """, (date_from, date_to))
        daily = cur.fetchall()

        cur.execute(f"""
            SELECT COUNT(*) as total_orders,
                   COALESCE(SUM({tc}), 0) as total_revenue,
                   COALESCE(AVG({tc}), 0) as avg_order,
                   COALESCE(SUM(delivery_fee), 0) as delivery_revenue
            FROM orders WHERE DATE(created_at) BETWEEN %s AND %s
        """, (date_from, date_to))
        summary = cur.fetchone()

        cur.execute(f"""
            SELECT payment_method,
                   COUNT(*) as count,
                   COALESCE(SUM({tc}), 0) as total
            FROM orders WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY payment_method
        """, (date_from, date_to))
        by_payment = cur.fetchall()

        cur.execute(f"""
            SELECT status, COUNT(*) as count
            FROM orders WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY status
        """, (date_from, date_to))
        by_status = cur.fetchall()
    else:
        daily = []; by_payment = []; by_status = []
        summary = {'total_orders':0,'total_revenue':0,'avg_order':0,'delivery_revenue':0}

    cur.close()
    return render_template('admin/sales.html',
        config=Config, daily=daily, summary=summary,
        by_payment=by_payment, by_status=by_status,
        date_from=date_from, date_to=date_to)

# ═══════════════════════════════════════════════════════════
#  ADMIN — CUSTOMERS
# ═══════════════════════════════════════════════════════════

@app.route('/admin/customers')
@admin_required
def admin_customers():
    search = request.args.get('q', '').strip()
    cur    = mysql.connection.cursor()
    if search:
        s = f'%{search}%'
        cur.execute(
            "SELECT * FROM users WHERE username LIKE %s OR email LIKE %s OR phone LIKE %s ORDER BY created_at DESC",
            (s, s, s)
        )
    else:
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    customers = cur.fetchall()
    cur.close()
    return render_template('admin/customers.html',
        config=Config, customers=customers, search=search)

# ═══════════════════════════════════════════════════════════
#  DATABASE SETUP
# ═══════════════════════════════════════════════════════════

@app.route('/setup-db')
def setup_db():
    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin','staff','customer') DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT PRIMARY KEY AUTO_INCREMENT,
                order_number VARCHAR(50) UNIQUE NOT NULL,
                customer_name VARCHAR(100) NOT NULL,
                customer_phone VARCHAR(20) NOT NULL,
                customer_email VARCHAR(100),
                order_type VARCHAR(20) DEFAULT 'delivery',
                subtotal DECIMAL(12,2) DEFAULT 0,
                delivery_fee DECIMAL(12,2) DEFAULT 0,
                total_amount DECIMAL(12,2) DEFAULT 0,
                status VARCHAR(30) DEFAULT 'pending',
                payment_method VARCHAR(50) DEFAULT 'cash',
                payment_status VARCHAR(20) DEFAULT 'pending',
                delivery_address TEXT,
                special_instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT PRIMARY KEY AUTO_INCREMENT,
                order_id INT,
                menu_item_id INT,
                item_name VARCHAR(100),
                quantity INT NOT NULL DEFAULT 1,
                unit_price DECIMAL(12,2) NOT NULL,
                subtotal DECIMAL(12,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_tracking (
                id INT PRIMARY KEY AUTO_INCREMENT,
                order_id INT,
                status VARCHAR(50) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                guest_count INT NOT NULL DEFAULT 2,
                reservation_date DATE NOT NULL,
                reservation_time TIME NOT NULL,
                special_requests TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                table_number VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create admin user if not exists
        cur.execute("SELECT id FROM users WHERE username='admin'")
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (username,email,phone,password_hash,role) VALUES (%s,%s,%s,%s,'admin')",
                ('admin','admin@mpombofamily.com','+256700000000',
                 generate_password_hash('admin123'))
            )

        mysql.connection.commit()
        cur.close()
        return (
            '<style>body{font-family:sans-serif;max-width:600px;margin:80px auto;text-align:center;line-height:1.8}</style>'
            '<h2 style="color:#1C3D2E">&#x2705; Database Setup Complete!</h2>'
            '<p><strong>Admin login:</strong> admin / admin123</p>'
            '<p style="color:#888;font-size:14px">If you have an existing database, also run '
            '<a href="/migrate-db" style="color:#C0592A">/migrate-db</a> to upgrade the schema.</p>'
            '<p><a href="/" style="color:#C0592A">&#x2190; Go to Website</a> &nbsp;|&nbsp;'
            '<a href="/dashboard" style="color:#1C3D2E">Admin Dashboard &#x2192;</a></p>'
        )
    except Exception as e:
        return f"<h2>❌ Setup Error</h2><pre>{e}</pre><p><a href='/'>← Back</a></p>"



# ═══════════════════════════════════════════════════════════
#  LEGACY ROUTE ALIASES (original app.py compatibility)
# ═══════════════════════════════════════════════════════════

@app.route('/fix-db')
@app.route('/migrate-db')
def fix_db():
    """Upgrade existing database schema — adds missing columns."""
    try:
        cur = mysql.connection.cursor()
        fixes = []

        cur.execute("DESCRIBE orders")
        cols = [r['Field'] for r in cur.fetchall()]

        migrations = [
            ('customer_name',        "ALTER TABLE orders ADD COLUMN customer_name VARCHAR(100) AFTER order_number"),
            ('customer_phone',       "ALTER TABLE orders ADD COLUMN customer_phone VARCHAR(20) AFTER customer_name"),
            ('customer_email',       "ALTER TABLE orders ADD COLUMN customer_email VARCHAR(100) AFTER customer_phone"),
            ('order_type',           "ALTER TABLE orders ADD COLUMN order_type VARCHAR(20) DEFAULT 'delivery'"),
            ('delivery_address',     "ALTER TABLE orders ADD COLUMN delivery_address TEXT"),
            ('special_instructions', "ALTER TABLE orders ADD COLUMN special_instructions TEXT"),
        ]
        for col, sql in migrations:
            if col not in cols:
                cur.execute(sql)
                fixes.append(f'+ {col}')

        # Add total_amount if neither total nor total_amount exists
        if 'total_amount' not in cols and 'total' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN total_amount DECIMAL(12,2) DEFAULT 0")
            fixes.append('+ total_amount')

        # Add item_name to order_items if missing
        try:
            cur.execute("DESCRIBE order_items")
            oi_cols = [r['Field'] for r in cur.fetchall()]
            if 'item_name' not in oi_cols:
                cur.execute("ALTER TABLE order_items ADD COLUMN item_name VARCHAR(100) AFTER menu_item_id")
                fixes.append('+ order_items.item_name')
        except:
            pass

        # Copy customer info from customers table if old schema
        if 'customer_id' in cols and 'customer_name' in [r for r in (cols + [m[0] for m in migrations if m[0] not in cols])]:
            try:
                cur.execute("""
                    UPDATE orders o
                    JOIN customers c ON o.customer_id = c.id
                    SET o.customer_name  = COALESCE(c.name, ''),
                        o.customer_phone = COALESCE(c.phone, ''),
                        o.customer_email = COALESCE(c.email, '')
                    WHERE (o.customer_name IS NULL OR o.customer_name = '')
                      AND o.customer_id IS NOT NULL
                """)
                fixes.append('Copied customer names from customers table')
            except:
                pass

        mysql.connection.commit()
        cur.close()

        msg = ', '.join(fixes) if fixes else 'Nothing to migrate — schema already up to date!'
        return (
            '<style>body{font-family:sans-serif;max-width:620px;margin:80px auto;line-height:1.8}</style>'
            '<h2 style="color:#1C3D2E">&#x2705; Migration Complete</h2>'
            f'<p><strong>Changes:</strong> {msg}</p>'
            '<p><a href="/dashboard" style="color:#C0592A">&#x2192; Admin Dashboard</a>'
            ' &nbsp;|&nbsp; <a href="/" style="color:#1C3D2E">&#x2192; Website</a></p>'
        )
    except Exception as e:
        return f'<h2>&#x274C; Migration Error</h2><pre>{e}</pre><p><a href="/">&#x2190; Back</a></p>'


# Old URL aliases so original links still work
@app.route('/make-reservation', methods=['POST'])
def make_reservation():
    return api_reserve()

@app.route('/place-order', methods=['POST'])
def place_order_legacy():
    return place_order()

@app.route('/track-order/<order_number>')
def track_order_details(order_number):
    """Legacy track URL — redirect to new track page."""
    return redirect(url_for('track') + f'?on={order_number}')

@app.route('/admin/update-order-status', methods=['POST'])
def update_order_status_legacy():
    return update_order()

@app.route('/admin/sales-report')
@admin_required
def sales_report_legacy():
    return redirect(url_for('admin_sales'))

@app.route('/track-search.html')
def track_search_legacy():
    return redirect(url_for('track'))

# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  🍽️  MPOMBO FAMILY RESTAURANT  —  LYANTONDE, UGANDA")
    print("=" * 60)
    print("  🌐  Website:      http://localhost:5000")
    print("  ⚙️   Setup DB:    http://localhost:5000/setup-db")
    print("  🔧  Migrate DB:   http://localhost:5000/migrate-db")
    print("  🔒  Admin login:  admin / admin123")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
