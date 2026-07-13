# API-DISANO V2 Developer Guide

## Welcome to API-DISANO V2

This guide helps developers integrate with API-DISANO V2, understand the architecture, and implement advanced features efficiently.

**Version:** 2.0.0  
**Last Updated:** 2024-07-11  
**Status:** Production Ready

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start Tutorial](#quick-start-tutorial)
4. [Core Concepts](#core-concepts)
5. [API Integration Guide](#api-integration-guide)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Performance Optimization](#performance-optimization)
9. [Testing Guide](#testing-guide)
10. [Deployment](#deployment)

---

## Getting Started

### Prerequisites

- Python 3.8+
- FastAPI 0.100+
- SQLite 3+
- Basic HTTP client (curl, requests, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/disano/api-disano.git
cd api-disano

# Install dependencies
pip install -r requirements.txt

# Set environment
export ENVIRONMENT=development

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Quick Test

```bash
# Test the API is running
curl http://localhost:8000/api/productos/v2/paginated?page=1&per_page=1

# Expected response:
# {"items":[...],"pagination":{"current_page":1,...},...}
```

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Layer (FastAPI)                      │
│  ┌───────────────┬───────────────┬────────────────────────┐ │
│  │  V2 Endpoints │  Error Handler │  Response Serializer   │ │
│  └───────────────┴───────────────┴────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  ┌───────────────┬───────────────┬────────────────────────┐ │
│  │   Services    │   DTOs        │  Query Parameter Parser│ │
│  └───────────────┴───────────────┴────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                             │
│  ┌───────────────┬───────────────┬────────────────────────┐ │
│  │   Entities    │   Interfaces  │  Repositories          │ │
│  └───────────────┴───────────────┴────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                          │
│  ┌───────────────┬───────────────┬────────────────────────┐ │
│  │  Database     │   Cache       │  Monitoring           │ │
│  └───────────────┴───────────────┴────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **HTTP Layer:** FastAPI endpoints, request handling, response formatting
2. **Application Layer:** Business logic, DTOs, parameter parsing
3. **Domain Layer:** Entities, interfaces, repositories
4. **Infrastructure Layer:** Database, caching, monitoring

---

## Quick Start Tutorial

### Step 1: Basic Request

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Get first page of products
response = requests.get(f"{BASE_URL}/productos/v2/paginated?page=1&per_page=5")

if response.status_code == 200:
    data = response.json()
    products = data['items']
    pagination = data['pagination']
    
    print(f"Got {len(products)} products")
    print(f"Total pages: {pagination['total_pages']}")
```

### Step 2: Add Filtering

```python
# Filter products by brand and price range
response = requests.get(
    f"{BASE_URL}/productos/v2/paginated",
    params={
        'marca': 'Disano',
        'pvp_min': 10,
        'pvp_max': 200,
        'per_page': 10
    }
)

data = response.json()
print(f"Found {len(data['items'])} Disano products in price range")
print(f"Filters applied: {data['filters_applied']}")
```

### Step 3: Add Sorting

```python
# Sort products by price (descending)
response = requests.get(
    f"{BASE_URL}/productos/v2/paginated",
    params={
        'page': 1,
        'per_page': 20,
        'sort': 'pvp:desc'  # Highest prices first
    }
)

data = response.json()
if data['items']:
    print(f"Most expensive product: {data['items'][0]['descripcion']}")
    print(f"Cheapest product: {data['items'][-1]['descripcion']}")
```

### Step 4: Navigate Pagination

```python
def get_all_products():
    page = 1
    all_products = []
    
    while True:
        response = requests.get(
            f"{BASE_URL}/productos/v2/paginated",
            params={'page': page, 'per_page': 100}
        )
        
        data = response.json()
        products = data['items']
        all_products.extend(products)
        
        # Check if there are more pages
        pagination = data['pagination']
        if not pagination['has_next']:
            break
            
        page += 1
    
    print(f"Retrieved {len(all_products)} total products")
    return all_products

products = get_all_products()
```

---

## Core Concepts

### 1. Pagination

**Structure:**

```json
{
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total_items": 8288,
    "total_pages": 829,
    "has_next": true,
    "has_previous": false
  }
}
```

**Usage:**

- Use `has_next` to determine if navigation is possible
- Use `total_pages` for progress indicators
- Keep `per_page` between 1-100 for optimal performance

### 2. Filtering

**Filter Types:**

- **Text search:** `buscar` parameter (searches multiple fields)
- **Exact match:** `marca`, `familia`, `bc3_product_type`
- **Range filtering:** `pvp_min`, `pvp_max`

**Filter Combinations:**

```python
# Multiple filters work together
params = {
    'buscar': 'test',           # Text search
    'marca': 'Disano',          # Exact match
    'pvp_min': 10,              # Price range
    'pvp_max': 200,
    'bc3_product_type': 'luminaria'  # BC3 filter
}
```

### 3. Sorting

**Syntax:** `sort=field:direction`

**Sortable Fields:**

- Products: `codigo`, `descripcion`, `pvp`, `marca`, `familia`, `bc3_product_type`
- Families: `nombre`, `total_productos`, `con_bc3`
- BC3: `codigo`, `descripcion`, `bc3_product_type`

**Directions:** `asc` (ascending), `desc` (descending)

### 4. Error Handling

**Error Response Format:**

```json
{
  "error": "Validation failed for one or more fields",
  "error_code": "VALIDATION_ERROR",
  "status": 422,
  "details": {
    "validation_errors": [
      {
        "field": "page",
        "message": "Page number must be at least 1"
      }
    ]
  }
}
```

**Common Errors:**

- `400 BAD_REQUEST` - Invalid request
- `404 NOT_FOUND` - Resource not found  
- `422 VALIDATION_ERROR` - Parameter validation failed
- `500 INTERNAL_ERROR` - Server error

---

## API Integration Guide

### Client Library Pattern

```python
class APIDISANOV2Client:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_products(self, page=1, per_page=10, **filters):
        """Get paginated products with optional filters"""
        params = {'page': page, 'per_page': per_page}
        params.update(filters)
        
        response = self.session.get(
            f"{self.base_url}/productos/v2/paginated",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_families(self, page=1, per_page=10, **filters):
        """Get paginated families with optional filters"""
        params = {'page': page, 'per_page': per_page}
        params.update(filters)
        
        response = self.session.get(
            f"{self.base_url}/familias/v2/paginated",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_bc3_stats(self):
        """Get BC3 compatibility statistics"""
        response = self.session.get(f"{self.base_url}/bc3/v2/stats")
        response.raise_for_status()
        return response.json()

# Usage
client = APIDISANOV2Client()
products = client.get_products(page=1, per_page=10, marca='Disano')
```

### Pagination Helper

```python
class PaginatedIterator:
    def __init__(self, client, endpoint, per_page=50, **filters):
        self.client = client
        self.endpoint = endpoint
        self.per_page = per_page
        self.filters = filters
        self.current_page = 1
        self.has_next = True
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if not self.has_next:
            raise StopIteration
        
        response = self.client.get_products(
            page=self.current_page,
            per_page=self.per_page,
            **self.filters
        )
        
        products = response['items']
        pagination = response['pagination']
        
        self.has_next = pagination['has_next']
        self.current_page += 1
        
        return products

# Usage
client = APIDISANOV2Client()

# Iterate through all products efficiently
for page_products in PaginatedIterator(client, 'productos', per_page=50):
    for product in page_products:
        process_product(product)
```

---

## Advanced Features

### 1. Complex Filtering

```python
def get_products_by_multiple_criteria():
    """Advanced filtering with multiple criteria"""
    params = {
        # Text search
        'buscar': 'emergencia',
        
        # Exact matches
        'marca': 'Disano',
        'familia': 'Emergencia',
        
        # Price range
        'pvp_min': 10,
        'pvp_max': 200,
        
        # BC3 specific
        'bc3_product_type': 'luminaria',
        
        # Sorting
        'sort': 'pvp:desc',
        
        # Pagination
        'page': 1,
        'per_page': 20
    }
    
    response = requests.get(
        f"{BASE_URL}/productos/v2/paginated",
        params=params
    )
    
    data = response.json()
    return data['items']
```

### 2. Bulk Operations

```python
def get_all_products_in_family(family_name):
    """Get all products in a family using pagination"""
    all_products = []
    page = 1
    
    while True:
        response = requests.get(
            f"{BASE_URL}/productos/v2/paginated",
            params={
                'familia': family_name,
                'page': page,
                'per_page': 100  # Maximum page size
            }
        )
        
        data = response.json()
        products = data['items']
        all_products.extend(products)
        
        if not data['pagination']['has_next']:
            break
            
        page += 1
    
    return all_products

def get_family_statistics():
    """Get statistics for all families"""
    families = []
    page = 1
    
    while True:
        response = requests.get(
            f"{BASE_URL}/familias/v2/paginated",
            params={'page': page, 'per_page': 100}
        )
        
        data = response.json()
        families.extend(data['items'])
        
        if not data['pagination']['has_next']:
            break
            
        page += 1
    
    # Calculate statistics
    total_families = len(families)
    total_products = sum(f['total_productos'] for f in families)
    bc3_compatible = sum(f['con_bc3'] for f in families)
    
    return {
        'total_families': total_families,
        'total_products': total_products,
        'bc3_compatible': bc3_compatible,
        'bc3_percentage': (bc3_compatible / total_products * 100) if total_products > 0 else 0
    }
```

### 3. Error Recovery

```python
def robust_api_request(url, params=None, max_retries=3):
    """Make robust API requests with retry logic"""
    import time
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                # Validation error - don't retry
                raise
            elif e.response.status_code >= 500:
                # Server error - retry with backoff
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
            else:
                # Other errors - don't retry
                raise
                
        except requests.exceptions.RequestException as e:
            # Network error - retry
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    
    raise Exception(f"Request failed after {max_retries} attempts")
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

**Problem:** `requests.exceptions.ConnectionError`

**Solution:**

```bash
# Check if server is running
curl http://localhost:8000/api/productos/v2/paginated?page=1&per_page=1

# Start server if not running
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Validation Errors

**Problem:** 422 status code with validation errors

**Solution:**

```python
# Check validation errors in response
response = requests.get(
    f"{BASE_URL}/productos/v2/paginated",
    params={'page': -1}
)

if response.status_code == 422:
    error_data = response.json()
    print(f"Error: {error_data['error']}")
    print(f"Details: {error_data['details']}")
```

#### 3. Slow Response Times

**Problem:** Response times > 2000ms

**Solution:**

```python
# Use smaller page sizes
params = {'page': 1, 'per_page': 10}  # Instead of 100

# Use filters to reduce result set
params = {'marca': 'Disano', 'per_page': 20}

# Use caching for repeated requests
import requests_cache
requests_cache.install_cache('api_cache')
```

#### 4. Empty Results

**Problem:** No items returned despite matching criteria

**Solution:**

```python
# Check pagination metadata
response = requests.get(
    f"{BASE_URL}/productos/v2/paginated",
    params={'buscar': 'xyz'}
)

data = response.json()
print(f"Total items: {data['pagination']['total_items']}")
print(f"Current items: {len(data['items'])}")

# Try broader search
response = requests.get(
    f"{BASE_URL}/productos/v2/paginated",
    params={'buscar': 'xyz_nonexistent_12345'}
)
```

---

## Performance Optimization

### 1. Caching Strategy

```python
import requests_cache
from datetime import timedelta

# Enable caching with 5-minute expiration
requests_cache.install_cache(
    'api_cache',
    expire_after=timedelta(minutes=5)
)

# Subsequent requests use cache
response1 = requests.get(f"{BASE_URL}/bc3/v2/stats")  # Fresh
response2 = requests.get(f"{BASE_URL}/bc3/v2/stats")  # Cached
```

### 2. Pagination Optimization

```python
# Use appropriate page sizes
OPTIMAL_PAGE_SIZES = {
    'small_results': 10,    # For preview/thumbnails
    'medium_results': 50,   # For list views
    'large_results': 100    # For export/batch processing
}

def get_optimal_page_size(use_case):
    return OPTIMAL_PAGE_SIZES.get(use_case, 50)
```

### 3. Batch Processing

```python
def process_products_in_batches():
    """Process products in optimal batch sizes"""
    batch_size = 50
    page = 1
    processed_count = 0
    
    while True:
        response = requests.get(
            f"{BASE_URL}/productos/v2/paginated",
            params={'page': page, 'per_page': batch_size}
        )
        
        data = response.json()
        products = data['items']
        
        # Process batch
        for product in products:
            process_product(product)
            processed_count += 1
        
        # Progress tracking
        if processed_count % 100 == 0:
            print(f"Processed {processed_count} products...")
        
        # Check for more pages
        if not data['pagination']['has_next']:
            break
            
        page += 1
```

---

## Testing Guide

### Unit Testing

```python
import pytest
import requests
from unittest.mock import patch, MagicMock

def test_pagination():
    """Test pagination functionality"""
    response = requests.get(
        f"{BASE_URL}/productos/v2/paginated?page=1&per_page=5"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate pagination metadata
    assert 'pagination' in data
    assert data['pagination']['current_page'] == 1
    assert data['pagination']['per_page'] == 5
    assert len(data['items']) == 5

def test_filtering():
    """Test filtering functionality"""
    response = requests.get(
        f"{BASE_URL}/productos/v2/paginated",
        params={'marca': 'Disano'}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate filter was applied
    assert 'filters_applied' in data
    assert data['filters_applied']['marca'] == 'Disano'

def test_sorting():
    """Test sorting functionality"""
    response = requests.get(
        f"{BASE_URL}/productos/v2/paginated",
        params={'sort': 'pvp:desc'}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate sorting was applied
    assert 'sorting_applied' in data
    assert data['sorting_applied']['field'] == 'pvp'
    assert data['sorting_applied']['direction'] == 'desc'
```

### Integration Testing

```python
def test_full_workflow():
    """Test complete API workflow"""
    # Step 1: Get products
    products_response = requests.get(
        f"{BASE_URL}/productos/v2/paginated?page=1&per_page=10"
    )
    assert products_response.status_code == 200
    
    # Step 2: Apply filters
    filtered_response = requests.get(
        f"{BASE_URL}/productos/v2/paginated",
        params={'marca': 'Disano', 'per_page': 10}
    )
    assert filtered_response.status_code == 200
    
    # Step 3: Apply sorting
    sorted_response = requests.get(
        f"{BASE_URL}/productos/v2/paginated",
        params={'sort': 'pvp:desc', 'per_page': 10}
    )
    assert sorted_response.status_code == 200
    
    # Step 4: Get BC3 stats
    stats_response = requests.get(f"{BASE_URL}/bc3/v2/stats")
    assert stats_response.status_code == 200
    
    print("✅ Full workflow test passed")
```

---

## Deployment

### Environment Configuration

```python
# config.py
import os

class Settings:
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/tarifa_disano.db')
    
    # Cache
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes
    
    # API
    API_PREFIX = os.getenv('API_PREFIX', '/api')
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # Performance
    MAX_PER_PAGE = int(os.getenv('MAX_PER_PAGE', '100'))
    DEFAULT_PER_PAGE = int(os.getenv('DEFAULT_PER_PAGE', '10'))
```

### Production Deployment

```bash
# Set production environment
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:password@host:port/database
export CACHE_ENABLED=true
export CACHE_TTL=600

# Install dependencies
pip install -r requirements.txt

# Run with production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://user:password@db:5432/database
      - CACHE_ENABLED=true
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=database
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

---

## Support & Resources

### Documentation

- **API Reference:** See `openspec/changes/fase4-advanced-features/docs/V2_API_DOCUMENTATION.md`
- **Architecture:** See `docs/FASE3_ARCHITECTURE_HEXAGONAL.md`
- **Test Coverage:** See `tests/` directory

### Getting Help

- **Issues:** Report bugs via GitHub issues
- **Questions:** Contact development team
- **Status:** Check API health endpoint

### Best Practices

1. **Always use pagination** - Never request all items at once
2. **Implement error handling** - Handle validation errors gracefully
3. **Use caching** - Cache frequently accessed data
4. **Monitor performance** - Track response times and error rates
5. **Test thoroughly** - Write integration tests for critical workflows

---

## Quick Reference

### Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/productos/v2/paginated` | GET | Get paginated products |
| `/api/familias/v2/paginated` | GET | Get paginated families |
| `/api/bc3/v2/stats` | GET | Get BC3 statistics |
| `/api/bc3/v2/paginated` | GET | Get paginated BC3 products |

### Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (min: 1) |
| `per_page` | int | Items per page (min: 1, max: 100) |
| `sort` | string | Field and direction: `field:direction` |
| `buscar` | string | Free-text search |
| `marca` | string | Filter by brand |
| `familia` | string | Filter by family |
| `pvp_min` | number | Minimum price |
| `pvp_max` | number | Maximum price |

---

## License

© 2024 Disano. All rights reserved.
