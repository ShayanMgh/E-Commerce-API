# 🛒 Django E-Commerce Backend

A minimal but complete **e-commerce backend** built with **Django + DRF + Stripe**.  
It demonstrates real-world concepts such as authentication, product catalog, shopping cart, order management, and payment flows — all using clean, modular APIs.

---

## 🚀 Features

✅ User registration & JWT login  
✅ Product catalog (categories, search, filtering)  
✅ Add/remove items in cart  
✅ Create order from cart  
✅ Stripe payment intent creation  
✅ Stripe webhook to mark orders as *paid*  
✅ Refund API  
✅ Admin panel for catalog & orders  
✅ Optional simple HTML frontend for testing

---

## 🧩 Project Structure

```
ecom/
├── ecom/                # Main project (settings, URLs, etc.)
├── users/               # Authentication (JWT)
├── catalog/             # Products & categories
├── cart/                # Cart and cart items
├── orders/              # Orders & order items
├── payments/            # Stripe payment & refund flow
└── templates/           # Optional minimal frontend
```

---

## ⚙️ Setup Instructions

### 1. Clone & create environment
```bash
git clone <your-repo-url> ecom
cd ecom
conda create -n django python=3.12
conda activate django
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file at the project root:

```bash
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
DEBUG=True
```

### 3. Run migrations & load sample data
```bash
python manage.py migrate
python manage.py loaddata catalog/fixtures/sample_catalog.json
```

### 4. Create superuser
```bash
python manage.py createsuperuser
```

### 5. Run server
```bash
python manage.py runserver
```

App is available at:  
👉 **http://localhost:8000/**

---

## 🧪 Quick API Test (via cURL)

### Register or log in
```bash
curl -s -X POST http://localhost:8000/api/auth/login   -H "Content-Type: application/json"   -d '{"email":"alice@example.com","password":"A-secure-pass1"}' | jq .
```

Save your access token:
```bash
export USER_ACCESS=<paste_access_token_here>
```

### List products
```bash
curl -s http://localhost:8000/api/products/ | jq .
```

### Add to cart
```bash
curl -s -X POST http://localhost:8000/api/cart/items/   -H "Authorization: Bearer $USER_ACCESS"   -H "Content-Type: application/json"   -d '{"product_id": 1, "qty": 2}' | jq .
```

### Create order from cart
```bash
curl -s -X POST http://localhost:8000/api/checkout/create-order/   -H "Authorization: Bearer $USER_ACCESS" | jq .
```

### Create Stripe payment intent
```bash
curl -s -X POST http://localhost:8000/api/payments/create-intent/   -H "Authorization: Bearer $USER_ACCESS"   -H "Content-Type: application/json"   -d '{"order_id": 1}' | jq .
```

### Simulate Stripe webhook
```bash
curl -s -X POST http://localhost:8000/api/payments/webhook/   -H "Content-Type: application/json"   -d '{
        "id": "evt_test_1",
        "type": "payment_intent.succeeded",
        "data": { "object": {
          "id": "pi_test_1",
          "metadata": {"order_id": "1"},
          "amount": 159800, "currency": "usd"
        } }
      }' | jq .
```

### Refund (optional)
```bash
curl -s -X POST http://localhost:8000/api/payments/refund/   -H "Authorization: Bearer $USER_ACCESS"   -H "Content-Type: application/json"   -d '{"order_id": 1}' | jq .
```

---

## 🧮 Admin Panel

```
http://localhost:8000/admin/
```

You can manage:
- Products and categories
- Orders and order items
- Payments and refunds
- Users

---

## 🧱 Optional Simple Frontend

Access minimal server-rendered pages:
```
/store/       → product list
/store/p/<slug>/ → product detail
/cart/        → view cart
```

---

## 🧪 Run Tests

```bash
python manage.py test orders.tests.test_core -v 2
```

---

## 🧠 Learning Highlights

This project demonstrates:

- RESTful Django app architecture  
- Atomic transactions and optimistic locking (`select_for_update()`)  
- Stripe integration (PaymentIntent & Webhook pattern)  
- JWT auth and permissions  
- Modular apps (users, catalog, cart, orders, payments)  
- Fixtures, serializers, and DRF viewsets  
- End-to-end checkout lifecycle

---

## 🪄 Future Improvements

- Add shipping & tax models  
- Email notifications on payment success  
- Address management  
- Product images / inventory sync  
- Pagination and filtering for large catalogs  
- Deploy to production with gunicorn + nginx

---

## 🧑‍💻 Author
**Shayan Moghaddas**  
AI & Software Engineer  
🔗 [LinkedIn](https://www.linkedin.com/in/shayan-moghaddas-079b5a334/)  
💡 Focus: AI Agents, LLM Apps, and Production Django Systems

