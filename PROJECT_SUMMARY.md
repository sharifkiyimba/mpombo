# Mpombo Family Restaurant — Project Summary

**Built by:** Claude (Anthropic AI)  
**Restaurant:** Mpombo Family Restaurant, Lyantonde District, Uganda  
**Live URL:** https://mpombo.onrender.com  
**GitHub:** https://github.com/sharifkiyimba/mpombo  

---

## What Was Built

A complete restaurant management web system — website, online ordering, reservations, admin dashboard — built with Python (Flask) and hosted free on Render.com.

---

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3 + Flask |
| Database | SQLite (built-in, no server needed) |
| Frontend | HTML + CSS + Vanilla JavaScript |
| Templates | Jinja2 |
| Hosting | Render.com (free tier) |
| Version Control | Git + GitHub |
| Fonts | Yeseva One + Outfit + Libre Baskerville |

---

## Website Pages (Public)

| Page | URL | Description |
|---|---|---|
| Homepage | `/` | Hero, featured menu, about, how to order, testimonials |
| Menu | `/menu` | Full menu with category filter tabs and cart drawer |
| Order | `/order` | 5-step ordering flow with sticky cart |
| Reserve | `/reserve` | Table reservation form |
| Outside Catering | `/catering` | Catering packages, booking form |
| Track Order | `/track` | Order status timeline |
| About | `/about` | Restaurant story, values, team |
| Contact | `/contact` | Contact form, opening hours, map |
| Login | `/login` | Staff/Admin login |
| Register | `/register` | Customer account creation |

---

## Admin Panel Pages

| Page | URL | Description |
|---|---|---|
| Dashboard | `/dashboard` | Stats, recent orders, pending reservations |
| Orders | `/admin/orders` | All orders, search, filter, status update |
| Reservations | `/admin/reservations` | Confirm/cancel reservations, assign tables |
| Customers | `/admin/customers` | All registered users |
| Sales Report | `/admin/sales` | Revenue by day, payment method, order status |
| Menu Photos | `/admin/images` | Upload real food photos per menu item |
| Settings | `/admin/settings` | Protected by PIN — change password, restaurant info, delivery fees, opening hours, staff management |

---

## Menu Categories & Items

| Category | Items | Price Range |
|---|---|---|
| Breakfast & Snacks | 29 items | UGX 500 – 7,000 |
| Lunch & Supper | 20 items | UGX 1,000 – 13,000 |
| Fast Foods | 25 items | UGX 4,000 – 21,000 |
| Drinks | 18 items | UGX 1,000 – 5,000 |

**Total: 92 menu items** — all taken from the real physical menu.

---

## Key Features

### Ordering System
- 5-step checkout: Food → Delivery type → Packaging → Details → Payment
- Sticky cart on desktop, floating bottom bar on mobile
- Delivery fee calculator (UGX 5,000 base + UGX 1,000/km)
- Free delivery on orders above UGX 50,000
- Maximum delivery range: 20km
- **Packaging fees:** Silverplate (UGX 1,000), Small Glass (UGX 1,000), Big Glass (UGX 2,000)

### Payment Methods
- MTN Mobile Money
- Airtel Money
- Cash on Delivery
- Card Payment
- WhatsApp ordering

### Reservations
- Date/time picker
- Guest count
- Special requests
- Confirmation via phone call

### Outside Catering
- 3 packages: Basic (UGX 15,000/person), Standard (UGX 22,000/person), Premium (custom)
- Event booking form that sends details to WhatsApp
- 8 occasion types (weddings, corporate, birthdays, etc.)

### Admin Dashboard
- Real-time today's stats (orders, revenue, pending)
- All-time totals
- Update order status (pending → confirmed → preparing → ready → delivered)
- Confirm reservations and assign table numbers
- Sales reports with daily breakdown

### Settings (PIN-protected)
- Change password
- Change Settings PIN (default: 1234)
- Update restaurant name, phone, WhatsApp, email, address
- Update delivery fees and maximum distance
- Update opening hours
- Add/remove staff accounts
- Clear all orders or reservations

### Menu Photo Manager
- Upload real food photos via imgbb.com (free)
- Each menu item gets its own photo
- Falls back to stock photo if none uploaded

---

## Restaurant Information

| Field | Value |
|---|---|
| Name | Mpombo Family Restaurant |
| Location | Lyantonde District, Uganda |
| Phone | 0704 691474 / 0706 139563 / 0772 902641 |
| WhatsApp | 0704 691474 |
| Delivery range | Up to 20km from restaurant |

---

## Design

- **Colours:** Forest Green (#1A3828) · Warm Clay (#B8521F) · Golden (#C8981A)
- **Kente strip:** Traditional Ugandan pattern on top of every page
- **Fonts:** Yeseva One (headings) · Outfit (body text)
- **Mobile-first:** All pages work on phones, tablets and desktops
- **WhatsApp float button:** Always visible for quick ordering

---

## Deployment

| Item | Detail |
|---|---|
| Host | Render.com (free) |
| Database | SQLite file stored on server |
| Auto-deploy | Every Git push to GitHub triggers redeploy |
| Sleep | Free tier sleeps after 15min inactivity (30sec wake) |
| Setup | Database auto-creates on first visit |

### Admin Login
- **Username:** admin  
- **Password:** admin123 *(change this!)*  
- **Settings PIN:** 1234 *(change this!)*

---

## Files in the Project

```
mpombo/
├── app.py                    ← Main Flask application (all routes + logic)
├── requirements.txt          ← Python packages needed
├── Procfile                  ← Render/Gunicorn start command
├── render.yaml               ← Render deployment config
├── .env                      ← Secret key (not in Git)
└── templates/
    ├── base.html             ← Master layout (nav, footer, design system)
    ├── index.html            ← Homepage
    ├── menu.html             ← Full menu with cart
    ├── order.html            ← 5-step order page
    ├── reserve.html          ← Table reservation
    ├── catering.html         ← Outside catering
    ├── track.html            ← Order tracking
    ├── about.html            ← About page
    ├── contact.html          ← Contact page
    ├── login.html            ← Login
    ├── register.html         ← Register
    ├── reservation_status.html
    └── admin/
        ├── base_admin.html   ← Admin layout with sidebar
        ├── dashboard.html    ← Main dashboard
        ├── orders.html       ← Order management
        ├── reservations.html ← Reservation management
        ├── customers.html    ← Customer list
        ├── sales.html        ← Sales reports
        ├── images.html       ← Menu photo manager
        ├── settings.html     ← All settings
        └── settings_pin.html ← PIN entry screen
```

---

## How to Update the Site

1. Make changes to files in `C:\Users\PRINCE\Desktop\MPOMBO`
2. Open Git Bash and run:
   ```bash
   cd /c/Users/PRINCE/Desktop/MPOMBO
   git add .
   git commit -m "Your description of change"
   git push
   ```
3. Render.com auto-redeploys in ~1 minute
4. Visit https://mpombo.onrender.com to see changes

---

*Built April 2026 — Mpombo Family Restaurant, Lyantonde, Uganda 🇺🇬*
