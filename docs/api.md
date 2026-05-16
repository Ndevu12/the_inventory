# REST API Documentation

**The Inventory** provides a comprehensive REST API for all inventory management operations. This guide covers authentication, common workflows, and endpoint reference.

- **Explore interactively:** Visit http://localhost:8000/api/schema/swagger/

---

## Table of Contents

- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Common Workflows](#common-workflows)
- [Endpoint Reference](#endpoint-reference)
- [Error Handling](#error-handling)
- [Pagination & Filtering](#pagination--filtering)
- [Rate Limiting](#rate-limiting)

---

## Quick Start

### 1. Get Your API Token

**Login to get JWT tokens:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "user@example.com",
    "is_superuser": false
  }
}
```

### 2. Make an API Request

**Use the access token in the Authorization header:**

```bash
curl http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 3. Explore the API

**Interactive API documentation:**
- **Swagger UI:** http://localhost:8000/api/schema/swagger/
- **Redoc:** http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

---

## Authentication

### JWT (Recommended)

JWT (JSON Web Tokens) is the recommended authentication method for API clients.

#### Login

```bash
POST /api/v1/auth/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "user@example.com",
    "is_superuser": false,
    "memberships": [
      {
        "id": 1,
        "tenant": {
          "id": 1,
          "name": "Default Tenant"
        },
        "role": "owner"
      }
    ]
  }
}
```

#### Use Access Token

Include the access token in the `Authorization` header:

```bash
Authorization: Bearer <access_token>
```

#### Refresh Token

Access tokens expire after 30 minutes. Use the refresh token to get a new access token:

```bash
POST /api/v1/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Token Authentication

For scripts and integrations, use token authentication:

```bash
Authorization: Token <api_token>
```

### Session Authentication

For browser-based requests, session cookies are automatically used.

---

## Common Workflows

### Create a Product

```bash
POST /api/v1/products/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "sku": "PROD-001",
  "name": "Widget A",
  "description": "A useful widget",
  "category": 1,
  "unit_of_measure": "pcs",
  "unit_cost": 10.50,
  "reorder_point": 50,
  "is_active": true
}
```

### Create a Stock Location

```bash
POST /api/v1/stock-locations/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Warehouse A - Shelf 1",
  "description": "Main warehouse, shelf 1",
  "is_active": true
}
```

### Record a Stock Movement

```bash
POST /api/v1/stock-movements/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product": 1,
  "from_location": null,
  "to_location": 1,
  "quantity": 100,
  "unit_cost": 10.50,
  "movement_type": "receive",
  "reference": "PO-2026-001",
  "notes": "Initial stock receipt"
}
```

### Get Current Stock Levels

```bash
GET /api/v1/stock-records/?product=1&location=1
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "sku": "PROD-001",
        "name": "Widget A"
      },
      "location": {
        "id": 1,
        "name": "Warehouse A - Shelf 1"
      },
      "quantity": 100,
      "is_low_stock": false
    }
  ]
}
```

### Create a Purchase Order

```bash
POST /api/v1/purchase-orders/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "supplier": 1,
  "order_number": "PO-2026-001",
  "order_date": "2026-05-16",
  "expected_delivery_date": "2026-05-23",
  "status": "draft",
  "lines": [
    {
      "product": 1,
      "quantity": 100,
      "unit_price": 10.50
    }
  ]
}
```

### Create a Sales Order

```bash
POST /api/v1/sales-orders/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "customer": 1,
  "order_number": "SO-2026-001",
  "order_date": "2026-05-16",
  "status": "draft",
  "lines": [
    {
      "product": 1,
      "quantity": 50
    }
  ]
}
```

---

## Endpoint Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login/` | User login (get JWT tokens) |
| `POST` | `/api/v1/auth/refresh/` | Refresh access token |
| `GET` | `/api/v1/auth/me/` | Get current user profile |
| `POST` | `/api/v1/auth/change-password/` | Change password |

### Inventory Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/products/` | List products |
| `POST` | `/api/v1/products/` | Create product |
| `GET` | `/api/v1/products/{id}/` | Get product details |
| `PUT` | `/api/v1/products/{id}/` | Update product |
| `PATCH` | `/api/v1/products/{id}/` | Partial update |
| `DELETE` | `/api/v1/products/{id}/` | Delete product |
| `GET` | `/api/v1/categories/` | List categories |
| `POST` | `/api/v1/categories/` | Create category |
| `GET` | `/api/v1/stock-locations/` | List stock locations |
| `POST` | `/api/v1/stock-locations/` | Create stock location |
| `GET` | `/api/v1/stock-records/` | List stock records |
| `GET` | `/api/v1/stock-movements/` | List stock movements |
| `POST` | `/api/v1/stock-movements/` | Create stock movement |

### Procurement Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/suppliers/` | List suppliers |
| `POST` | `/api/v1/suppliers/` | Create supplier |
| `GET` | `/api/v1/purchase-orders/` | List purchase orders |
| `POST` | `/api/v1/purchase-orders/` | Create purchase order |
| `GET` | `/api/v1/purchase-orders/{id}/` | Get purchase order |
| `POST` | `/api/v1/purchase-orders/{id}/confirm/` | Confirm purchase order |
| `POST` | `/api/v1/purchase-orders/{id}/cancel/` | Cancel purchase order |
| `GET` | `/api/v1/goods-received-notes/` | List GRNs |
| `POST` | `/api/v1/goods-received-notes/` | Create GRN |

### Sales Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/customers/` | List customers |
| `POST` | `/api/v1/customers/` | Create customer |
| `GET` | `/api/v1/sales-orders/` | List sales orders |
| `POST` | `/api/v1/sales-orders/` | Create sales order |
| `GET` | `/api/v1/sales-orders/{id}/` | Get sales order |
| `POST` | `/api/v1/sales-orders/{id}/confirm/` | Confirm sales order |
| `POST` | `/api/v1/sales-orders/{id}/cancel/` | Cancel sales order |
| `GET` | `/api/v1/dispatches/` | List dispatches |
| `POST` | `/api/v1/dispatches/` | Create dispatch |

### Reporting Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/reports/stock-valuation/` | Stock valuation report |
| `GET` | `/api/v1/reports/movements/` | Movement history report |
| `GET` | `/api/v1/reports/low-stock/` | Low stock report |
| `GET` | `/api/v1/reports/overstock/` | Overstock report |
| `GET` | `/api/v1/reports/purchases/` | Purchase summary report |
| `GET` | `/api/v1/reports/sales/` | Sales summary report |

### Tenant Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tenants/current/` | Get current tenant |
| `GET` | `/api/v1/tenants/memberships/` | List user memberships |

---

## Error Handling

### Error Response Format

All errors return a JSON response with status code and error details:

```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

### Common Error Codes

| Status | Code | Meaning |
|--------|------|---------|
| `400` | `bad_request` | Invalid request data |
| `401` | `unauthorized` | Missing or invalid authentication |
| `403` | `permission_denied` | User doesn't have permission |
| `404` | `not_found` | Resource not found |
| `409` | `conflict` | Resource conflict (e.g., duplicate SKU) |
| `500` | `server_error` | Server error |

### Example Error Response

```bash
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Content-Type: application/json" \
  -d '{"sku": "PROD-001"}'
```

**Response (400):**
```json
{
  "name": ["This field is required."],
  "category": ["This field is required."]
}
```

---

## Pagination & Filtering

### Pagination

All list endpoints support pagination:

```bash
GET /api/v1/products/?page=1&page_size=25
```

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/products/?page=2",
  "previous": null,
  "results": [...]
}
```

### Filtering

Filter results using query parameters:

```bash
# Filter by category
GET /api/v1/products/?category=1

# Filter by status
GET /api/v1/products/?is_active=true

# Filter by date range
GET /api/v1/stock-movements/?created_at__gte=2026-01-01&created_at__lte=2026-12-31
```

### Searching

Search across multiple fields:

```bash
GET /api/v1/products/?search=widget
```

### Ordering

Sort results:

```bash
# Ascending
GET /api/v1/products/?ordering=name

# Descending
GET /api/v1/products/?ordering=-created_at
```

---

## Rate Limiting

Currently, there is no rate limiting. For production deployments, consider implementing rate limiting based on your needs.

---

## Next Steps

- **Explore interactively:** Visit http://localhost:8000/api/schema/swagger/
- **Integration guide:** See [Integration Guide](integration.md)
- **Deployment:** See [Deployment Guide](deployment.md)
- **Troubleshooting:** See [Troubleshooting Guide](troubleshooting.md)
