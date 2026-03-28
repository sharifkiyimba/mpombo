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
app.config['MYSQL_HOST']        = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER']        = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD']    = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB']          = os.environ.get('MYSQL_DB', 'mpombo_restaurant')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ── Restaurant Config ─────────────────────────────────────
class Config:
    RESTAURANT_NAME     = 'Mpombo Family Restaurant'
    RESTAURANT_PHONE    = '0704 691474 / 0706 139563 / 0772 902641'
    RESTAURANT_WHATSAPP = '256704691474'
    RESTAURANT_EMAIL    = 'info@mpombofamily.com'
    RESTAURANT_ADDRESS  = 'Located in Lyantonde, Uganda'
    DELIVERY_BASE_FEE   = 5000   # UGX
    DELIVERY_PER_KM     = 1000   # UGX per km
    MAX_DELIVERY_KM     = 20
    FREE_DELIVERY_MIN   = 50000  # UGX — orders above this get free delivery

# ── Site Settings (loaded from DB, falls back to Config) ─────
def get_menu_images():
    """Load all custom menu images from DB. Returns dict {item_id: url}."""
    images = {}
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT item_id, image_url FROM menu_images")
        for row in cur.fetchall():
            if row['image_url']:
                images[row['item_id']] = row['image_url']
        cur.close()
    except:
        pass
    return images

def get_settings():
    """Load site settings from DB. Falls back to Config defaults."""
    defaults = {
        'restaurant_name':    Config.RESTAURANT_NAME,
        'restaurant_phone':   Config.RESTAURANT_PHONE,
        'restaurant_whatsapp':Config.RESTAURANT_WHATSAPP,
        'restaurant_email':   Config.RESTAURANT_EMAIL,
        'restaurant_address': Config.RESTAURANT_ADDRESS,
        'delivery_base_fee':  str(Config.DELIVERY_BASE_FEE),
        'delivery_per_km':    str(Config.DELIVERY_PER_KM),
        'max_delivery_km':    str(Config.MAX_DELIVERY_KM),
        'free_delivery_min':  str(Config.FREE_DELIVERY_MIN),
        'hours_mon_fri':      '7:00am – 10:00pm',
        'hours_saturday':     '7:00am – 11:00pm',
        'hours_sunday':       '8:00am – 9:00pm',
        'hours_delivery':     'Until 9:00pm daily',
    }
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT setting_key, setting_value FROM site_settings")
        rows = cur.fetchall()
        cur.close()
        for row in rows:
            defaults[row['setting_key']] = row['setting_value']
    except:
        pass
    # Expose numeric delivery values
    try:
        defaults['delivery_base_fee_int'] = int(defaults['delivery_base_fee'])
        defaults['delivery_per_km_int']   = int(defaults['delivery_per_km'])
        defaults['max_delivery_km_int']   = int(defaults['max_delivery_km'])
        defaults['free_delivery_min_int'] = int(defaults['free_delivery_min'])
    except:
        defaults['delivery_base_fee_int'] = Config.DELIVERY_BASE_FEE
        defaults['delivery_per_km_int']   = Config.DELIVERY_PER_KM
        defaults['max_delivery_km_int']   = Config.MAX_DELIVERY_KM
        defaults['free_delivery_min_int'] = Config.FREE_DELIVERY_MIN
    return defaults

def save_setting(key, value):
    """Upsert a single setting into site_settings table."""
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO site_settings (setting_key, setting_value)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE setting_value = %s
    """, (key, value, value))
    mysql.connection.commit()
    cur.close()

# ── Full Ugandan Menu ─────────────────────────────────────
MENU = [
    {
        'id': 1, 'name': 'Breakfast & Snacks', 'icon': '🍳',
        'description': 'Start your day right with our hearty Ugandan breakfast',
        'dishes': [
            {'id': 101, 'name': 'Katogo Beef',           'price': 5000, 'prep': 15, 'badge': 'Breakfast', 'veg': False, 'desc': 'Matooke cooked with beef in rich tomato gravy. A classic Ugandan breakfast.',            'img': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80'},
            {'id': 102, 'name': 'Katogo Offals',         'price': 5000, 'prep': 15, 'badge': 'Breakfast', 'veg': False, 'desc': 'Matooke cooked with offals in rich tomato gravy. Warming and filling.',                  'img': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80'},
            {'id': 103, 'name': 'Katogo Liver',          'price': 5000, 'prep': 15, 'badge': 'Breakfast', 'veg': False, 'desc': 'Matooke cooked with tender liver in tomato sauce. Rich in iron and flavour.',            'img': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80'},
            {'id': 104, 'name': 'Katogo Beans',          'price': 4000, 'prep': 15, 'badge': 'Vegan',     'veg': True,  'desc': 'Matooke cooked with beans. A simple satisfying vegetarian breakfast.',                  'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 105, 'name': 'Katogo Cowpeas',        'price': 4000, 'prep': 15, 'badge': 'Vegan',     'veg': True,  'desc': 'Matooke cooked with cowpeas. Nutritious and filling.',                                   'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 106, 'name': 'Katogo Gnuts',          'price': 4000, 'prep': 15, 'badge': 'Vegan',     'veg': True,  'desc': 'Matooke cooked with groundnuts. Creamy and deeply satisfying.',                         'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
            {'id': 107, 'name': 'Katogo Mix',            'price': 7000, 'prep': 20, 'badge': 'Popular',   'veg': False, 'desc': 'Matooke cooked with a mix of meat and vegetables. Best of everything!',                  'img': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80'},
            {'id': 108, 'name': 'Rolex (1 Chapati + 2 Eggs)', 'price': 3000, 'prep': 10, 'badge': 'Street Fave', 'veg': True, 'desc': 'Uganda iconic street food — chapati rolled with fried eggs, cabbage and tomatoes.', 'img': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=600&q=80'},
            {'id': 109, 'name': 'Chapati',               'price': 1000, 'prep': 8,  'badge': None,        'veg': True,  'desc': 'Soft layered flatbread. Perfect with tea or any stew.',                                  'img': 'https://images.unsplash.com/photo-1635194415227-7d2bf0a161d2?w=600&q=80'},
            {'id': 110, 'name': 'Chapati + Soup',        'price': 1500, 'prep': 10, 'badge': None,        'veg': False, 'desc': 'Soft chapati served with a warm bowl of soup.',                                          'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
            {'id': 111, 'name': 'Chaps',                 'price': 3000, 'prep': 10, 'badge': None,        'veg': True,  'desc': 'Crispy fried chapati pieces. A popular snack.',                                          'img': 'https://images.unsplash.com/photo-1635194415227-7d2bf0a161d2?w=600&q=80'},
            {'id': 112, 'name': 'Samosa Beef',           'price': 1000, 'prep': 5,  'badge': None,        'veg': False, 'desc': 'Crispy pastry filled with spiced minced beef. Great snack any time.',                    'img': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80'},
            {'id': 113, 'name': 'Samosa Rice',           'price': 1000, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Crispy pastry filled with spiced rice. Light and tasty.',                                'img': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80'},
            {'id': 114, 'name': 'A Pair of Samosas',     'price': 2000, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Two samosas — great for a quick snack.',                                                 'img': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80'},
            {'id': 115, 'name': 'A Pair of Sausage',     'price': 3000, 'prep': 8,  'badge': None,        'veg': False, 'desc': 'Two grilled sausages. Perfect for breakfast or a snack.',                                'img': 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=600&q=80'},
            {'id': 116, 'name': 'Boiled Egg',            'price': 500,  'prep': 5,  'badge': None,        'veg': True,  'desc': 'A perfectly boiled egg. Simple and nutritious.',                                         'img': 'https://images.unsplash.com/photo-1482049016688-2d3e1b311543?w=600&q=80'},
            {'id': 117, 'name': 'Fried Egg (1)',         'price': 1000, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'One fresh egg fried to your liking.',                                                    'img': 'https://images.unsplash.com/photo-1482049016688-2d3e1b311543?w=600&q=80'},
            {'id': 118, 'name': 'French Toast',          'price': 4000, 'prep': 8,  'badge': None,        'veg': True,  'desc': 'Golden bread dipped in egg and fried. Sweet and satisfying.',                            'img': 'https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=600&q=80'},
            {'id': 119, 'name': 'Toast Bread',           'price': 1000, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Crispy toasted bread. Great with tea or coffee.',                                        'img': 'https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=600&q=80'},
            {'id': 120, 'name': 'Halfcake',              'price': 1000, 'prep': 3,  'badge': None,        'veg': True,  'desc': 'A sweet Ugandan baked halfcake. Perfect with tea.',                                      'img': 'https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=600&q=80'},
            {'id': 121, 'name': 'Doughnut',              'price': 1000, 'prep': 3,  'badge': None,        'veg': True,  'desc': 'Soft sweet Ugandan mandazi-style doughnut.',                                             'img': 'https://images.unsplash.com/photo-1551024601-bec78aea704b?w=600&q=80'},
            {'id': 122, 'name': 'Sweet Banana',          'price': 500,  'prep': 1,  'badge': 'Vegan',     'veg': True,  'desc': 'Fresh sweet banana. A natural energy boost.',                                            'img': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=600&q=80'},
            {'id': 123, 'name': 'African Tea',           'price': 2500, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Freshly brewed African tea with milk and sugar.',                                        'img': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&q=80'},
            {'id': 124, 'name': 'African Tea + Nescafe', 'price': 3500, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'African tea blended with Nescafe for a rich creamy taste.',                              'img': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&q=80'},
            {'id': 125, 'name': 'African Tea + Honey',   'price': 3500, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Sweetened African tea with pure honey. Soothing and delicious.',                         'img': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&q=80'},
            {'id': 126, 'name': 'Black Tea',             'price': 1000, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Plain black tea served hot.',                                                            'img': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&q=80'},
            {'id': 127, 'name': 'Black Tea + Nescafe',   'price': 3000, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Black tea with Nescafe instant coffee mixed in.',                                        'img': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&q=80'},
            {'id': 128, 'name': 'Black Tea + Honey',     'price': 3500, 'prep': 5,  'badge': None,        'veg': True,  'desc': 'Black tea sweetened with natural honey.',                                                'img': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&q=80'},
            {'id': 129, 'name': 'Dawah Tea',             'price': 5000, 'prep': 8,  'badge': 'Special',   'veg': True,  'desc': 'Our special spiced Dawah tea blend. Unique and warming.',                                'img': 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&q=80'},
        ]
    },
    {
        'id': 2, 'name': 'Lunch & Supper', 'icon': '🍲',
        'description': 'Hearty traditional Ugandan lunch and supper dishes',
        'dishes': [
            {'id': 201, 'name': 'Chicken Luwombo',                 'price': 13000, 'prep': 35, 'badge': 'Bestseller', 'veg': False, 'desc': 'Chicken steamed in fresh banana leaves with rich groundnut sauce. A Buganda royal delicacy.',    'img': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=600&q=80'},
            {'id': 202, 'name': 'Beef Luwombo',                    'price': 10000, 'prep': 35, 'badge': None,         'veg': False, 'desc': 'Tender beef steamed in banana leaves with groundnut sauce. Rich and aromatic.',                   'img': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=600&q=80'},
            {'id': 203, 'name': 'Goat Luwombo',                    'price': 13000, 'prep': 35, 'badge': None,         'veg': False, 'desc': 'Goat meat steamed in banana leaves with groundnut sauce. A traditional favourite.',              'img': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=600&q=80'},
            {'id': 204, 'name': 'Gnuts/Fish Luwombo',              'price': 11000, 'prep': 35, 'badge': None,         'veg': False, 'desc': 'Fish with groundnuts steamed in banana leaves. Light yet deeply flavourful.',                     'img': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=600&q=80'},
            {'id': 205, 'name': 'Gnuts/Beef Luwombo',              'price': 11000, 'prep': 35, 'badge': None,         'veg': False, 'desc': 'Beef and groundnuts steamed together in banana leaves. Hearty and filling.',                      'img': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=600&q=80'},
            {'id': 206, 'name': 'Chicken',                         'price': 12000, 'prep': 30, 'badge': None,         'veg': False, 'desc': 'Tender chicken in a rich tomato and onion stew. Served with your choice of starch.',             'img': 'https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=600&q=80'},
            {'id': 207, 'name': 'Smoked Fish',                     'price': 13000, 'prep': 20, 'badge': 'Local Fave', 'veg': False, 'desc': 'Traditional Ugandan smoked fish full of deep smoky flavour.',                                    'img': 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&q=80'},
            {'id': 208, 'name': 'Fresh Fish',                      'price': 13000, 'prep': 25, 'badge': 'Lake Fresh', 'veg': False, 'desc': 'Fresh Lake Victoria fish cooked in tomato and onion gravy.',                                     'img': 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&q=80'},
            {'id': 209, 'name': 'Beef',                            'price': 9000,  'prep': 20, 'badge': None,         'veg': False, 'desc': 'Tender beef cooked in a rich Ugandan stew. Served with starch of choice.',                       'img': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80'},
            {'id': 210, 'name': 'Cowpeas + Beef',                  'price': 12000, 'prep': 25, 'badge': None,         'veg': False, 'desc': 'Cowpeas cooked with beef in a rich tomato sauce. Nutritious and filling.',                       'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 211, 'name': 'Beans + Beef',                    'price': 12000, 'prep': 25, 'badge': None,         'veg': False, 'desc': 'Kidney beans cooked with tender beef. A satisfying Ugandan classic.',                           'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 212, 'name': 'Beans + Gnuts',                   'price': 10000, 'prep': 25, 'badge': 'Vegan',      'veg': True,  'desc': 'Beans cooked with groundnuts. Creamy protein-rich and delicious.',                               'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
            {'id': 213, 'name': 'Beef in Gnuts',                   'price': 12000, 'prep': 25, 'badge': None,         'veg': False, 'desc': 'Tender beef cooked in a creamy groundnut sauce. Rich and warming.',                              'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
            {'id': 214, 'name': 'Plain Gnuts',                     'price': 6000,  'prep': 15, 'badge': 'Vegan',      'veg': True,  'desc': 'Pure groundnut sauce. Simple creamy and deeply Ugandan.',                                        'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
            {'id': 215, 'name': 'Beans',                           'price': 6000,  'prep': 15, 'badge': 'Vegan',      'veg': True,  'desc': 'Slow-cooked kidney beans in tomato and onion sauce. A staple of Uganda.',                        'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 216, 'name': 'Basimati Pilao',                  'price': 11000, 'prep': 30, 'badge': 'Spiced',     'veg': False, 'desc': 'Fragrant basmati pilau rice with beef cumin cloves and East African spices.',                    'img': 'https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&q=80'},
            {'id': 217, 'name': 'Kikomando Beans',                 'price': 6000,  'prep': 10, 'badge': None,         'veg': True,  'desc': 'Fried chapati pieces mixed with beans. A popular budget-friendly dish.',                        'img': 'https://images.unsplash.com/photo-1635194415227-7d2bf0a161d2?w=600&q=80'},
            {'id': 218, 'name': 'Kikomando Beef',                  'price': 8000,  'prep': 12, 'badge': None,         'veg': False, 'desc': 'Fried chapati pieces mixed with beef stew. Filling and tasty.',                                  'img': 'https://images.unsplash.com/photo-1635194415227-7d2bf0a161d2?w=600&q=80'},
            {'id': 219, 'name': 'Soup (Beef/Goat/Fish/Chicken)',   'price': 5000,  'prep': 10, 'badge': None,         'veg': False, 'desc': 'Rich meat soup — choose from beef goat fish or chicken. Warm and nourishing.',                   'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
            {'id': 220, 'name': 'Side Dish',                       'price': 1000,  'prep': 5,  'badge': None,         'veg': True,  'desc': 'A small side portion — posho rice matoke or chapati.',                                           'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
        ]
    },
    {
        'id': 3, 'name': 'Fast Foods', 'icon': '🍟',
        'description': 'Quick and delicious fast food options',
        'dishes': [
            {'id': 301, 'name': 'Chips Plain',                     'price': 5000,  'prep': 12, 'badge': None,        'veg': True,  'desc': 'Crispy golden chips plain and simple.',                                                           'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 302, 'name': 'Chips Eggs',                      'price': 6000,  'prep': 12, 'badge': None,        'veg': True,  'desc': 'Golden chips served with fried eggs. A filling combo.',                                           'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 303, 'name': 'Chips Beef',                      'price': 10000, 'prep': 15, 'badge': 'Popular',   'veg': False, 'desc': 'Crispy chips served with tender beef stew.',                                                       'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 304, 'name': 'Chips Liver',                     'price': 10000, 'prep': 15, 'badge': None,        'veg': False, 'desc': 'Crispy chips served with fried liver.',                                                           'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 305, 'name': 'Chips Chicken',                   'price': 12000, 'prep': 15, 'badge': None,        'veg': False, 'desc': 'Crispy chips with tender chicken. A favourite combo.',                                            'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 306, 'name': 'Chips Goat Stew',                 'price': 14000, 'prep': 15, 'badge': None,        'veg': False, 'desc': 'Crispy chips with rich goat stew.',                                                               'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 307, 'name': 'Chips Gravy',                     'price': 7000,  'prep': 12, 'badge': None,        'veg': True,  'desc': 'Golden chips smothered in rich gravy sauce.',                                                     'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 308, 'name': 'Chips Fish',                      'price': 21000, 'prep': 20, 'badge': 'Premium',   'veg': False, 'desc': 'Crispy chips with fresh fried fish. The ultimate combo.',                                         'img': 'https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600&q=80'},
            {'id': 309, 'name': 'Half Rice + Half Plain Chips',    'price': 11000, 'prep': 15, 'badge': None,        'veg': True,  'desc': 'Half steamed rice half crispy chips.',                                                            'img': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=600&q=80'},
            {'id': 310, 'name': 'Half Rice + Half Chips Chicken',  'price': 17000, 'prep': 20, 'badge': 'Popular',   'veg': False, 'desc': 'Half rice half chips served with chicken.',                                                        'img': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=600&q=80'},
            {'id': 311, 'name': 'Half Rice + Half Chips Liver',    'price': 15000, 'prep': 20, 'badge': None,        'veg': False, 'desc': 'Half rice half chips served with fried liver.',                                                    'img': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=600&q=80'},
            {'id': 312, 'name': 'Half Rice + Half Chips Beef',     'price': 15000, 'prep': 20, 'badge': None,        'veg': False, 'desc': 'Half rice half chips served with beef stew.',                                                      'img': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=600&q=80'},
            {'id': 313, 'name': 'Half Rice + Half Chips Goatmeat', 'price': 15000, 'prep': 20, 'badge': None,        'veg': False, 'desc': 'Half rice half chips served with goat meat.',                                                      'img': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=600&q=80'},
            {'id': 314, 'name': 'Half Rice + Half Chips Eggs',     'price': 12000, 'prep': 15, 'badge': None,        'veg': True,  'desc': 'Half rice half chips served with fried eggs.',                                                     'img': 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=600&q=80'},
            {'id': 315, 'name': 'Fried Chicken',                   'price': 12000, 'prep': 20, 'badge': 'Crispy',    'veg': False, 'desc': 'Golden fried chicken crispy outside and juicy inside.',                                           'img': 'https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=600&q=80'},
            {'id': 316, 'name': 'Molokoni',                        'price': 9000,  'prep': 20, 'badge': None,        'veg': False, 'desc': 'Traditional Ugandan tripe stew. Rich and deeply flavoured.',                                      'img': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80'},
            {'id': 317, 'name': 'Liver Plain',                     'price': 10000, 'prep': 15, 'badge': None,        'veg': False, 'desc': 'Pan-fried liver with onions and peppers.',                                                        'img': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80'},
            {'id': 318, 'name': 'Chicken Pilao',                   'price': 15000, 'prep': 30, 'badge': 'Spiced',    'veg': False, 'desc': 'Fragrant pilau rice cooked with tender chicken and East African spices.',                         'img': 'https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&q=80'},
            {'id': 319, 'name': 'Pilao + Goatmeat',               'price': 15000, 'prep': 30, 'badge': None,        'veg': False, 'desc': 'Fragrant pilau rice with rich goat meat.',                                                        'img': 'https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&q=80'},
            {'id': 320, 'name': 'Fried Beef',                      'price': 10000, 'prep': 15, 'badge': None,        'veg': False, 'desc': 'Tender beef stir-fried with onions peppers and spices.',                                         'img': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80'},
            {'id': 321, 'name': 'Food Only',                       'price': 5000,  'prep': 10, 'badge': None,        'veg': True,  'desc': 'Plain starch only — posho rice or matoke. No accompaniment.',                                    'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 322, 'name': 'Karo Only',                       'price': 6000,  'prep': 10, 'badge': None,        'veg': True,  'desc': 'Plain karo (cassava/starch). A filling staple.',                                                  'img': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&q=80'},
            {'id': 323, 'name': 'Kikomando',                       'price': 4000,  'prep': 10, 'badge': None,        'veg': True,  'desc': 'Fried chapati pieces. Quick tasty and filling.',                                                  'img': 'https://images.unsplash.com/photo-1635194415227-7d2bf0a161d2?w=600&q=80'},
            {'id': 324, 'name': 'Kikomando (Liver/Beef/Offals)',   'price': 5000,  'prep': 12, 'badge': None,        'veg': False, 'desc': 'Fried chapati pieces with liver beef or offals.',                                                 'img': 'https://images.unsplash.com/photo-1635194415227-7d2bf0a161d2?w=600&q=80'},
            {'id': 325, 'name': 'Fruits',                          'price': 2000,  'prep': 5,  'badge': 'Fresh',     'veg': True,  'desc': 'Fresh seasonal fruits. Light healthy and refreshing.',                                            'img': 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=600&q=80'},
        ]
    },
    {
        'id': 4, 'name': 'Drinks', 'icon': '🥤',
        'description': 'Refreshing drinks and beverages',
        'dishes': [
            {'id': 401, 'name': 'Passion Juice Small (300ml)', 'price': 2000, 'prep': 3, 'badge': 'Fresh', 'veg': True, 'desc': 'Fresh passion fruit juice 300ml. Tart sweet and energising.', 'img': 'https://images.unsplash.com/photo-1613478225719-9e5d4f3d8c3a?w=600&q=80'},
            {'id': 402, 'name': 'Passion Juice Big (500ml)',   'price': 3000, 'prep': 3, 'badge': 'Fresh', 'veg': True, 'desc': 'Fresh passion fruit juice 500ml. More of Uganda favourite juice.', 'img': 'https://images.unsplash.com/photo-1613478225719-9e5d4f3d8c3a?w=600&q=80'},
            {'id': 403, 'name': 'Cocktail Small (300ml)',      'price': 3000, 'prep': 5, 'badge': None,    'veg': True, 'desc': 'Mixed fruit cocktail drink 300ml. Refreshing and fruity.', 'img': 'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=600&q=80'},
            {'id': 404, 'name': 'Cocktail Big (500ml)',        'price': 4000, 'prep': 5, 'badge': None,    'veg': True, 'desc': 'Mixed fruit cocktail drink 500ml. A big refreshing treat.', 'img': 'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=600&q=80'},
            {'id': 405, 'name': 'Mineral Water Small (500ml)','price': 1000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Cold Rwenzori or Splash mineral water 500ml.', 'img': 'https://images.unsplash.com/photo-1564419320468-6872c04a7f6e?w=600&q=80'},
            {'id': 406, 'name': 'Mineral Water Big (1500ml)', 'price': 2000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Large Rwenzori or Splash mineral water 1500ml.', 'img': 'https://images.unsplash.com/photo-1564419320468-6872c04a7f6e?w=600&q=80'},
            {'id': 407, 'name': 'Soda 300ml',                 'price': 1000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled 300ml soda — Coke Fanta Sprite or Pepsi.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 408, 'name': 'Soda 500ml',                 'price': 2000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled 500ml soda — Coke Fanta Sprite or Pepsi.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 409, 'name': 'Orner',                      'price': 2500, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Orner energy drink.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 410, 'name': 'Rockboom',                   'price': 2000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Rockboom energy drink. Bold and energising.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 411, 'name': 'Coffeemalt',                 'price': 2000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Coffeemalt malt drink. Rich and satisfying.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 412, 'name': 'Sting',                      'price': 2000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Sting energy drink. Sweet and powerful.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 413, 'name': 'Powerplay',                  'price': 2000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Powerplay energy drink.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 414, 'name': 'Predator',                   'price': 2000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Predator energy drink. Strong and refreshing.', 'img': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600&q=80'},
            {'id': 415, 'name': 'Fresh Milk Small',           'price': 2500, 'prep': 1, 'badge': 'Fresh', 'veg': True, 'desc': 'Fresh cold milk small size. Pure and nutritious.', 'img': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=600&q=80'},
            {'id': 416, 'name': 'Fresh Milk Big',             'price': 3500, 'prep': 1, 'badge': 'Fresh', 'veg': True, 'desc': 'Fresh cold milk large size. Pure and nutritious.', 'img': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=600&q=80'},
            {'id': 417, 'name': 'Minute Maid Small',          'price': 2500, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Minute Maid juice drink small.', 'img': 'https://images.unsplash.com/photo-1613478225719-9e5d4f3d8c3a?w=600&q=80'},
            {'id': 418, 'name': 'Minute Maid Big',            'price': 5000, 'prep': 1, 'badge': None,    'veg': True, 'desc': 'Chilled Minute Maid juice drink large.', 'img': 'https://images.unsplash.com/photo-1613478225719-9e5d4f3d8c3a?w=600&q=80'},
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

@app.context_processor
def inject_settings():
    """Make settings available in ALL templates automatically."""
    try:
        s = get_settings()
    except:
        s = {
            'restaurant_name':     'Mpombo Family Restaurant',
            'restaurant_phone':    '+256-789-123-456',
            'restaurant_whatsapp': '256789123456',
            'restaurant_email':    'info@mpombofamily.com',
            'restaurant_address':  'Opposite Petro Uganda, Lyantonde District, Uganda',
            'delivery_base_fee':   '5000',
            'delivery_per_km':     '1000',
            'max_delivery_km':     '20',
            'free_delivery_min':   '50000',
            'hours_mon_fri':       '7:00am – 10:00pm',
            'hours_saturday':      '7:00am – 11:00pm',
            'hours_sunday':        '8:00am – 9:00pm',
            'hours_delivery':      'Until 9:00pm daily',
            'delivery_base_fee_int': 5000,
            'delivery_per_km_int':   1000,
            'max_delivery_km_int':   20,
            'free_delivery_min_int': 50000,
        }
    return dict(settings=s)

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
    s=get_settings(); imgs=get_menu_images(); return render_template('index.html', config=Config, menu=MENU, settings=s, menu_images=imgs)

@app.route('/menu')
def menu():
    s=get_settings(); imgs=get_menu_images(); return render_template('menu.html', config=Config, menu=MENU, settings=s, menu_images=imgs)

@app.route('/about')
def about():
    s=get_settings(); return render_template('about.html', config=Config, settings=s)

@app.route('/contact')
def contact():
    s=get_settings(); return render_template('contact.html', config=Config, settings=s)

@app.route('/order')
def order():
    s=get_settings(); imgs=get_menu_images(); return render_template('order.html', config=Config, menu=MENU, settings=s, menu_images=imgs)

@app.route('/reserve')
def reserve():
    s=get_settings(); return render_template('reserve.html', config=Config, settings=s)

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

        subtotal  = sum(float(i['price']) * int(i['quantity']) for i in items)
        fee       = 0 if order_type != 'delivery' else (calc_delivery_fee(distance, subtotal) or 0)
        # Packaging fee (delivery + pickup only)
        packaging = data.get('packaging', [])
        pkg_cost  = 0
        if order_type in ('delivery', 'pickup'):
            pkg_cost = sum(int(p.get('qty',0)) * int(p.get('price',0)) for p in packaging)
        total     = subtotal + fee + pkg_cost
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
            'pkg_cost':      pkg_cost,
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
#  ADMIN — SETTINGS
# ═══════════════════════════════════════════════════════════

@app.route('/admin/settings/verify-pin', methods=['POST'])
@admin_required
def verify_settings_pin():
    """Verify the settings PIN and grant temporary session access."""
    try:
        data = request.json
        entered = data.get('pin', '').strip()
        cur = mysql.connection.cursor()
        cur.execute("SELECT setting_value FROM site_settings WHERE setting_key='settings_pin'")
        row = cur.fetchone()
        cur.close()
        # Default PIN is 1234 if not set
        stored_pin = row['setting_value'] if row else '1234'
        if entered == stored_pin:
            session['settings_unlocked'] = True
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Incorrect PIN. Try again.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/lock', methods=['POST'])
@admin_required
def lock_settings():
    """Lock settings — require PIN again next time."""
    session.pop('settings_unlocked', None)
    return jsonify({'success': True})

@app.route('/admin/settings')
@admin_required
def admin_settings():
    # Require PIN unlock before showing settings
    if not session.get('settings_unlocked'):
        try:
            return render_template('admin/settings_pin.html', config=Config)
        except:
            # Fallback inline PIN page if template missing
            return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Settings PIN</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600&family=Yeseva+One&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Outfit,sans-serif;background:#EDE8E0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:white;border-radius:10px;overflow:hidden;width:360px;box-shadow:0 8px 40px rgba(0,0,0,.15)}
.top{background:#1C3D2E;padding:32px;text-align:center;color:white}
.icon{font-size:40px;margin-bottom:12px}
h1{font-family:"Yeseva One",serif;font-size:22px;margin-bottom:6px}
p{font-size:13px;opacity:.6}
.body{padding:28px}
.dots{display:flex;justify-content:center;gap:12px;margin-bottom:24px}
.dot{width:14px;height:14px;border-radius:50%;border:2px solid #DDD;background:white;transition:all .2s}
.dot.on{background:#1C3D2E;border-color:#1C3D2E}
.dot.err{background:#B5251E;border-color:#B5251E}
.pad{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}
.btn{padding:16px;border:1.5px solid #EEE;border-radius:6px;background:white;
  font-size:20px;font-weight:600;color:#1C3D2E;cursor:pointer;transition:all .2s}
.btn:hover{background:#F2EAD8;border-color:#C0592A}
.btn.enter{background:#1C3D2E;color:white;font-size:12px;letter-spacing:1px;text-transform:uppercase}
.btn.enter:hover{background:#275A42}
.err-msg{text-align:center;color:#B5251E;font-size:13px;min-height:18px;margin-bottom:8px}
.hint{text-align:center;font-size:12px;color:#9B7A52;border-top:1px solid #EEE;padding-top:14px}
.hint a{color:#C0592A;cursor:pointer}
</style>
</head>
<body>
<div class="card">
  <div class="top">
    <div class="icon">🔐</div>
    <h1>Settings PIN</h1>
    <p>Enter your PIN to access Settings</p>
  </div>
  <div class="body">
    <div class="dots" id="dots">
      <div class="dot" id="d0"></div>
      <div class="dot" id="d1"></div>
      <div class="dot" id="d2"></div>
      <div class="dot" id="d3"></div>
    </div>
    <div class="err-msg" id="err"></div>
    <div class="pad">
      <button class="btn" onclick="add(1)">1</button>
      <button class="btn" onclick="add(2)">2</button>
      <button class="btn" onclick="add(3)">3</button>
      <button class="btn" onclick="add(4)">4</button>
      <button class="btn" onclick="add(5)">5</button>
      <button class="btn" onclick="add(6)">6</button>
      <button class="btn" onclick="add(7)">7</button>
      <button class="btn" onclick="add(8)">8</button>
      <button class="btn" onclick="add(9)">9</button>
      <button class="btn" onclick="del()">⌫</button>
      <button class="btn" onclick="add(0)">0</button>
      <button class="btn enter" onclick="submit()">Enter</button>
    </div>
    <div class="hint">Default PIN is <strong>1234</strong><br><a onclick="location.href='/dashboard'">← Back to Dashboard</a></div>
  </div>
</div>
<script>
let p="";
function upd(){
  const n=Math.max(4,p.length);
  const d=document.getElementById("dots");
  d.innerHTML="";
  for(let i=0;i<n;i++){
    const dot=document.createElement("div");
    dot.className="dot"+(i<p.length?" on":"");
    d.appendChild(dot);
  }
}
function add(d){p+=d;upd();document.getElementById("err").textContent="";if(p.length===4)setTimeout(submit,200)}
function del(){p=p.slice(0,-1);upd()}
function submit(){
  if(!p)return;
  fetch("/admin/settings/verify-pin",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pin:p})})
  .then(r=>r.json()).then(d=>{
    if(d.success){document.querySelectorAll(".dot").forEach(x=>{x.style.background="#347A58";x.style.borderColor="#347A58"});setTimeout(()=>location.href="/admin/settings",400)}
    else{document.getElementById("err").textContent="❌ "+d.error;document.querySelectorAll(".dot").forEach(x=>{x.style.background="#B5251E";x.style.borderColor="#B5251E"});setTimeout(()=>{p="";upd();document.getElementById("err").textContent=""},1200)}
  });
}
document.addEventListener("keydown",e=>{if(e.key>="0"&&e.key<="9")add(e.key);else if(e.key==="Backspace")del();else if(e.key==="Enter")submit()});
upd();
</script>
</body>
</html>'''
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users ORDER BY role, username")
    users = cur.fetchall()
    cur.close()
    s = get_settings()
    return render_template('admin/settings.html', config=Config, users=users, settings=s)

@app.route('/admin/settings/save-pin', methods=['POST'])
@admin_required
def settings_save_pin():
    """Save a new settings PIN."""
    try:
        data    = request.json
        new_pin = data.get('new_pin', '').strip()
        cur_pin = data.get('current_pin', '').strip()
        if len(new_pin) < 4:
            return jsonify({'success': False, 'error': 'PIN must be at least 4 characters'})
        # Verify current PIN first
        cur = mysql.connection.cursor()
        cur.execute("SELECT setting_value FROM site_settings WHERE setting_key='settings_pin'")
        row = cur.fetchone()
        stored = row['setting_value'] if row else '1234'
        if cur_pin != stored:
            cur.close()
            return jsonify({'success': False, 'error': 'Current PIN is incorrect'})
        # Save new PIN
        cur.execute("""
            INSERT INTO site_settings (setting_key, setting_value)
            VALUES ('settings_pin', %s)
            ON DUPLICATE KEY UPDATE setting_value = %s
        """, (new_pin, new_pin))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/save-restaurant', methods=['POST'])
@admin_required
def settings_save_restaurant():
    try:
        data = request.json
        keys = ['restaurant_name','restaurant_phone','restaurant_whatsapp',
                'restaurant_email','restaurant_address']
        for key in keys:
            if key in data:
                save_setting(key, data[key])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/save-delivery', methods=['POST'])
@admin_required
def settings_save_delivery():
    try:
        data = request.json
        keys = ['delivery_base_fee','delivery_per_km','max_delivery_km','free_delivery_min']
        for key in keys:
            if key in data:
                save_setting(key, str(data[key]))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/save-hours', methods=['POST'])
@admin_required
def settings_save_hours():
    try:
        data = request.json
        keys = ['hours_mon_fri','hours_saturday','hours_sunday','hours_delivery']
        for key in keys:
            if key in data:
                save_setting(key, data[key])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/change-password', methods=['POST'])
@login_required
def settings_change_password():
    try:
        data     = request.json
        current  = data.get('current', '')
        new_pass = data.get('new_password', '')
        if len(new_pass) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        if not user or not check_password_hash(user['password_hash'], current):
            cur.close()
            return jsonify({'success': False, 'error': 'Current password is incorrect'})
        cur.execute("UPDATE users SET password_hash = %s WHERE id = %s",
                    (generate_password_hash(new_pass), session['user_id']))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/add-staff', methods=['POST'])
@admin_required
def settings_add_staff():
    try:
        data = request.json
        cur  = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (username, email, phone, password_hash, role) VALUES (%s,%s,%s,%s,%s)",
            (data['username'], data['email'], data.get('phone',''),
             generate_password_hash(data['password']), data.get('role','staff'))
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/delete-user', methods=['POST'])
@admin_required
def settings_delete_user():
    try:
        data = request.json
        uid  = data.get('user_id')
        if int(uid) == int(session['user_id']):
            return jsonify({'success': False, 'error': 'You cannot delete your own account'})
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (uid,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/clear-orders', methods=['POST'])
@admin_required
def settings_clear_orders():
    try:
        cur = mysql.connection.cursor()
        for tbl in ['order_tracking', 'order_items', 'orders']:
            try:
                cur.execute(f"DELETE FROM {tbl}")
            except:
                pass
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/settings/clear-reservations', methods=['POST'])
@admin_required
def settings_clear_reservations():
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM reservations")
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ═══════════════════════════════════════════════════════════
#  ADMIN — IMAGE MANAGEMENT
# ═══════════════════════════════════════════════════════════

@app.route('/admin/images')
@admin_required
def admin_images():
    imgs = get_menu_images()
    return render_template('admin/images.html',
        config=Config, menu=MENU, menu_images=imgs)

@app.route('/admin/images/save', methods=['POST'])
@admin_required
def save_image():
    try:
        data     = request.json
        item_id  = int(data.get('item_id'))
        image_url= data.get('image_url','').strip()
        item_name= data.get('item_name','')
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO menu_images (item_id, item_name, image_url)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE image_url=%s, item_name=%s
        """, (item_id, item_name, image_url, image_url, item_name))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/images/delete', methods=['POST'])
@admin_required
def delete_image():
    try:
        item_id = int(request.json.get('item_id'))
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM menu_images WHERE item_id=%s", (item_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS menu_images (
                id INT PRIMARY KEY AUTO_INCREMENT,
                item_id INT UNIQUE NOT NULL,
                item_name VARCHAR(100),
                image_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
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


        # Add menu_images table if missing
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS menu_images (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    item_id INT UNIQUE NOT NULL,
                    item_name VARCHAR(100),
                    image_url TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            fixes.append('+ menu_images table')
        except:
            pass

        # Add site_settings table if missing
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS site_settings (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            fixes.append('+ site_settings table')
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

@app.route('/admin/settings/reset', methods=['POST'])
@admin_required
def settings_reset():
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM site_settings")
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
