# 🛍️ E‑Commerce API (Django + Stripe + Redis + Docker + Nginx)

A production‑ready learning project demonstrating how to build a complete e‑commerce backend using **Django REST Framework**, **Stripe**, **Redis caching**, **Docker**, and **Nginx**.

---

## 🚀 Features

- 🔐 **User Authentication** — JWT‑based sign‑up, login, and profile.
- 🛒 **Shopping Cart** — Add, remove, and update cart items.
- 💳 **Orders & Payments** — Stripe integration for checkout, webhook handling, and refunds.
- 🧩 **Product Catalog** — Browse, search, and manage inventory.
- 🧑‍💼 **Admin Panel** — Manage users, products, and orders securely.
- ⚡ **Caching with Redis** — Speeds up database and API operations.
- 🐳 **Dockerized Deployment** — Run Django, Redis, and Nginx as containers.
- 🧱 **Nginx Reverse Proxy** — Serves static files and routes traffic to Django backend.

---

## 🧠 Architecture Overview

```
+-------------+      +-----------+      +--------+
|   Nginx     | ---> |   Django  | ---> |  Redis |
|  (reverse   |      |  (API +   |      | (cache) |
|   proxy)    |      |   Stripe) |      +--------+
+-------------+      +-----------+
         |
         v
   Browser / Frontend
```

---

## 🐍 Local Development Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/ShayanMgh/E-Commerce-API.git
cd E-Commerce-API
```

### 2️⃣ Create and Activate Environment
```bash
conda create -n django python=3.12 -y
conda activate django
pip install -r requirements.txt
```

### 3️⃣ Apply Migrations and Load Sample Data
```bash
python manage.py migrate
python manage.py loaddata catalog/fixtures/sample_catalog.json
```

### 4️⃣ Run the App
```bash
python manage.py runserver
```

Then visit: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## 🐳 Docker Setup

### Start All Services (Django, Redis, Nginx)
```bash
docker compose up -d
```

### Check Running Containers
```bash
docker ps
```

### Test Redis Connection
```bash
docker exec -it ecom-redis-1 redis-cli ping
# should return PONG
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

```bash
DEBUG=True
SECRET_KEY=your_django_secret_key
STRIPE_SECRET_KEY=your_stripe_secret
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 🧾 API Highlights

| Endpoint | Method | Description |
|-----------|--------|--------------|
| `/api/auth/signup/` | POST | Register new user |
| `/api/auth/login/` | POST | Obtain JWT tokens |
| `/api/catalog/products/` | GET | List products |
| `/api/cart/items/` | POST/GET/DELETE | Manage cart items |
| `/api/checkout/create-order/` | POST | Create order from cart |
| `/api/payments/create-intent/` | POST | Stripe payment intent |
| `/api/payments/webhook/` | POST | Handle Stripe webhook |
| `/api/payments/refund/` | POST | Issue refund |

---

## 🧰 Technologies

- **Django 5 + DRF**
- **Stripe Payments API**
- **Redis** (caching + sessions)
- **Docker Compose**
- **Nginx** (reverse proxy)
- **SQLite / PostgreSQL**
- **JWT Authentication**

---

## 🧪 Running Tests

```bash
python manage.py test orders.tests.test_core -v 2
```

---

## 🧱 Production Settings

See `ecom/settings/prod.py` for:
- Secure cookies and headers
- Redis‑based cache backend
- Nginx proxy compatibility
- HSTS and HTTPS configurations

---

## 🧑‍💻 Author

**Shayan Moghaddas**  
🔗 [LinkedIn](https://www.linkedin.com/in/shayan-moghaddas-079b5a334/)  
📦 GitHub: [ShayanMgh](https://github.com/ShayanMgh)

