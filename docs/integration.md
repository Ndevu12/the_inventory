# Integration Guide

This guide explains how to integrate **The Inventory** backend API with a frontend application or third-party service.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Authentication](#authentication)
- [CORS Configuration](#cors-configuration)
- [Common Integration Patterns](#common-integration-patterns)
- [Frontend Integration](#frontend-integration)
- [Third-Party Integration](#third-party-integration)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

**The Inventory** is a **headless REST API** designed to be consumed by any frontend or service.

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Frontend                             │
│              (Next.js, React, Vue, etc.)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/REST
                     │ JSON
                     │
┌────────────────────▼────────────────────────────────────────┐
│         The Inventory Backend API                            │
│              (Django REST Framework)                         │
│                                                              │
│  ├── /api/v1/products/                                      │
│  ├── /api/v1/stock-movements/                               │
│  ├── /api/v1/purchase-orders/                               │
│  ├── /api/v1/sales-orders/                                  │
│  └── /api/v1/reports/                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ SQL
                     │
┌────────────────────▼────────────────────────────────────────┐
│              PostgreSQL Database                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Authentication

### JWT Authentication (Recommended)

JWT (JSON Web Tokens) is the recommended authentication method for frontend applications.

#### Step 1: Login

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password'
  })
});

const data = await response.json();
const accessToken = data.access;
const refreshToken = data.refresh;
```

#### Step 2: Store Tokens

Store tokens securely (HTTP-only cookies recommended):

```javascript
// Store in HTTP-only cookie (secure)
document.cookie = `access_token=${accessToken}; HttpOnly; Secure; SameSite=Lax`;
document.cookie = `refresh_token=${refreshToken}; HttpOnly; Secure; SameSite=Lax`;

// Or in localStorage (less secure)
localStorage.setItem('access_token', accessToken);
localStorage.setItem('refresh_token', refreshToken);
```

#### Step 3: Make Authenticated Requests

```javascript
const response = await fetch('http://localhost:8000/api/v1/products/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const products = await response.json();
```

#### Step 4: Refresh Token

When access token expires (30 minutes), refresh it:

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/refresh/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh: refreshToken })
});

const data = await response.json();
const newAccessToken = data.access;
```

### Token Authentication

For scripts and integrations:

```bash
curl http://localhost:8000/api/v1/products/ \
  -H "Authorization: Token your-api-token"
```

---

## CORS Configuration

### Development (Localhost)

By default, CORS is configured for localhost:

```
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production

Set `CORS_ALLOWED_ORIGINS` to your frontend URL:

```
CORS_ALLOWED_ORIGINS=https://app.example.com
```

### Multiple Frontends

For multiple frontend URLs:

```
CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

### Wildcard (Not Recommended)

For development only:

```
CORS_ALLOW_ALL_ORIGINS=true
```

---

## Common Integration Patterns

### Pattern 1: Simple REST Client

```javascript
class InventoryAPI {
  constructor(baseURL, accessToken) {
    this.baseURL = baseURL;
    this.accessToken = accessToken;
  }

  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  async getProducts() {
    return this.request('/api/v1/products/');
  }

  async createProduct(data) {
    return this.request('/api/v1/products/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getStockMovements() {
    return this.request('/api/v1/stock-movements/');
  }
}

// Usage
const api = new InventoryAPI('http://localhost:8000', accessToken);
const products = await api.getProducts();
```

### Pattern 2: React Hook

```javascript
import { useState, useEffect } from 'react';

function useInventoryAPI(endpoint) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1${endpoint}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint]);

  return { data, loading, error };
}

// Usage
function ProductList() {
  const { data, loading, error } = useInventoryAPI('/products/');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {data.results.map(product => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}
```

### Pattern 3: GraphQL Wrapper

If you prefer GraphQL, you can wrap the REST API:

```javascript
const resolvers = {
  Query: {
    products: async (_, __, { api }) => {
      const response = await api.request('/api/v1/products/');
      return response.results;
    },
    product: async (_, { id }, { api }) => {
      return api.request(`/api/v1/products/${id}/`);
    }
  },
  Mutation: {
    createProduct: async (_, { input }, { api }) => {
      return api.request('/api/v1/products/', {
        method: 'POST',
        body: JSON.stringify(input)
      });
    }
  }
};
```

---

## Frontend Integration

### Next.js Example

**Environment Variables** (`.env.local`):

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**API Client** (`lib/api.ts`):

```typescript
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
) {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  const token = localStorage.getItem('access_token');

  const response = await fetch(`${baseURL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// Usage
export async function getProducts() {
  return apiRequest('/products/');
}

export async function createProduct(data: any) {
  return apiRequest('/products/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}
```

**Component** (`components/ProductList.tsx`):

```typescript
'use client';

import { useEffect, useState } from 'react';
import { getProducts } from '@/lib/api';

export default function ProductList() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProducts()
      .then(data => setProducts(data.results))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <ul>
      {products.map(product => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}
```

### React Example

**API Client** (`src/api/client.js`):

```javascript
export const apiClient = {
  async request(endpoint, options = {}) {
    const baseURL = process.env.REACT_APP_API_URL;
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  },

  products: {
    list: () => apiClient.request('/products/'),
    get: (id) => apiClient.request(`/products/${id}/`),
    create: (data) => apiClient.request('/products/', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }
};
```

---

## Third-Party Integration

### Zapier Integration

Connect **The Inventory** to Zapier for automation:

1. Create a Zapier account
2. Create a new Zap
3. Choose trigger: "Webhook" or "REST API"
4. Configure action to call The Inventory API

**Example:** When a product is created in another system, create it in The Inventory:

```javascript
// Zapier action
const response = await fetch('http://localhost:8000/api/v1/products/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.INVENTORY_API_TOKEN}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sku: inputData.sku,
    name: inputData.name,
    category: inputData.category_id,
    unit_of_measure: 'pcs',
    unit_cost: inputData.price
  })
});
```

### Webhook Integration

Listen for events from The Inventory:

```javascript
// Your webhook endpoint
app.post('/webhooks/inventory', (req, res) => {
  const event = req.body;

  if (event.type === 'stock_movement_created') {
    // Handle stock movement
    console.log('Stock moved:', event.data);
  }

  res.json({ ok: true });
});
```

### Accounting System Integration

Sync inventory data with accounting software:

```javascript
// Sync products to QuickBooks
async function syncToQuickBooks() {
  const products = await apiClient.products.list();

  for (const product of products.results) {
    await quickbooks.items.create({
      Name: product.name,
      SKU: product.sku,
      UnitPrice: product.unit_cost
    });
  }
}
```

---

## Troubleshooting

### CORS Error

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
1. Check `CORS_ALLOWED_ORIGINS` includes your frontend URL
2. Verify frontend URL matches exactly (including protocol and port)
3. Check browser console for exact error

### Authentication Error

```
401 Unauthorized
```

**Solution:**
1. Verify access token is included in Authorization header
2. Check token hasn't expired (refresh if needed)
3. Verify token format: `Bearer <token>`

### Token Expired

```
401 Token is invalid or expired
```

**Solution:**
Refresh the token:

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/refresh/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh: refreshToken })
});

const data = await response.json();
localStorage.setItem('access_token', data.access);
```

### Network Error

```
Failed to fetch
```

**Solution:**
1. Verify backend is running
2. Check backend URL is correct
3. Check firewall allows connection
4. Check CORS headers in response

---

## Next Steps

- **API Reference:** See [API Documentation](api.md)
- **Features:** See [Features Guide](features.md)
- **Deployment:** See [Deployment Guide](deployment.md)
- **Frontend Repo:** https://github.com/Ndevu12/the-inventory-ui

---

## Example Frontend Repository

For a complete example, see the official frontend:
**https://github.com/Ndevu12/the-inventory-ui**

This Next.js application demonstrates:
- JWT authentication
- API integration patterns
- Error handling
- Loading states
- Real-world usage
