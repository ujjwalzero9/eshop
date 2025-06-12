# Product Catalog API with Caching

A Django-based RESTful API for managing an e-commerce product catalog. It includes a Redis caching layer using a Singleton pattern, logging, Prometheus metrics, and Sentry for error tracking. PostgreSQL is used as the primary database (hosted on AWS).

---

## 🚀 Features

- **Product Catalog API**
  - Fetch all products
  - Fetch single product by ID
  - Filter by category, price range, and availability
  - Create, update, and delete products
- **Caching with Redis (Upstash)**
  - Singleton Redis client
  - Caching for product listings and details
  - Automatic invalidation on update/delete
  - 10-minute cache expiration for listings
- **Monitoring & Logging**
  - Custom logging middleware
  - Prometheus metrics support
  - Sentry integration for error tracking

---

## 🧱 Tech Stack

- **Backend**: Django (DRF)
- **Database**: PostgreSQL (Amazon RDS/AWS)
- **Cache**: Redis (Upstash) using Singleton pattern
- **Monitoring**: Prometheus, Sentry
- **Testing**: Django `TestCase` and `APITestCase`

---

## 📦 Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/product-catalog-api.git
cd product-catalog-api
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

Create a `.env` file and configure the following:

```env
REDIS_READ_URL=redis://<read_url>
REDIS_WRITE_URL=redis://<write_url>
DATABASE_URL=postgres://<username>:<password>@<host>:<port>/<db>
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

---

## 🧪 API Endpoints

| Method | Endpoint         | Description                            |
| ------ | ---------------- | -------------------------------------- |
| GET    | `/products`      | List all products (supports filtering) |
| GET    | `/products/{id}` | Get product details by ID              |
| POST   | `/products`      | Add a new product                      |
| PUT    | `/products/{id}` | Update a product                       |
| DELETE | `/products/{id}` | Delete a product                       |

### Example Filters:

```
/products?category=Books&price_min=100&price_max=300
```

---

## 🧠 Caching Strategy

| Endpoint             | Cache Key Format                 | Expiry              |
| -------------------- | -------------------------------- | ------------------- |
| GET `/products/{id}` | `product:v1:{id}`                | Until update/delete |
| GET `/products?...`  | `product_list:v1:{query_params}` | 10 minutes          |

* **Cache is invalidated** on `POST`, `PUT`, and `DELETE` operations.
* Singleton Redis client ensures efficient reuse across app lifecycle.

---

## 📊 Monitoring & Logging

* Prometheus captures request latency and cache hit/miss metrics.
* All Redis exceptions are logged (non-fatal).
* Sentry captures unhandled application errors and exceptions.

---

## ✅ Running Tests

```bash
python manage.py test
```

Includes:

* Unit tests for cache and key generation logic
* Integration tests for all API endpoints

---

## 📈 Performance Gains

Benchmark results show significant performance improvements on cached endpoints:

| Scenario         | Avg. Response Time |
| ---------------- | ------------------ |
| Without Redis    | \~450ms            |
| With Redis Cache | \~60ms             |

---

## 📁 Project Structure

```
├── products/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── services/
│       └── product_service.py
├── eshop/
│   └── cache/
│       └── redis_utils.py
├── tests/
│   ├── test_api.py
│   └── test_redis.py
└── README.md
```

---

## 🙌 Author

Built with ❤️ by Ujjwal Kumar.


---
