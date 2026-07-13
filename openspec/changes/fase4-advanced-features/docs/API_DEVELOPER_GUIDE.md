# API-DISANO V2 Developer Guide

## Overview

API-DISANO V2 provides RESTful endpoints for accessing product information, family data, and BC3 statistics with advanced pagination, filtering, and sorting capabilities.

**Base URL:** `http://localhost:8000/api`

**Version:** 2.0.0

**Authentication:** Currently no authentication required (future versions will include API keys)

---

## Quick Start

### Basic Request Example

```bash
curl -X GET "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10"
```

**Response:**

```json
{
  "items": [...],
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total_items": 8288,
    "total_pages": 829,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {},
  "sorting_applied": null
}
```

---

## Endpoints

### 1. Products - Paginated List

Get paginated list of products with advanced filtering and sorting.

**Endpoint:** `GET /api/productos/v2/paginated`

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (min: 1) | `1` |
| `per_page` | integer | No | Items per page (min: 1, max: 100) | `10` |
| `sort` | string | No | Field and direction: `field:direction` | `codigo:asc` |
| `buscar` | string | No | Search in descripcion and codigo | `test` |
| `marca` | string | No | Filter by brand | `Disano` |
| `familia` | string | No | Filter by family | `Emergencia` |
| `pvp_min` | number | No | Minimum price filter | `10.00` |
| `pvp_max` | number | No | Maximum price filter | `200.00` |
| `bc3_product_type` | string | No | Filter by BC3 product type | `luminaria` |

**Example Requests:**

```bash
# Basic pagination
curl "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10"

# With filtering
curl "http://localhost:8000/api/productos/v2/paginated?buscar=test&marca=Disano"

# With sorting
curl "http://localhost:8000/api/productos/v2/paginated?sort=codigo:desc"

# Complex query
curl "http://localhost:8000/api/productos/v2/paginated?page=2&per_page=20&buscar=test&pvp_min=10&pvp_max=200&sort=pvp:asc"
```

**Response Structure:**

```json
{
  "items": [
    {
      "codigo": "TEST001",
      "descripcion": "Test Product",
      "marca": "Disano",
      "familia": "Emergencia",
      "pvp": 100.00,
      "bc3_descripcion_corta": "BC3 Desc",
      "bc3_descripcion_larga": "Full Description",
      "bc3_product_type": "luminaria"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total_items": 8288,
    "total_pages": 829,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "buscar": "test",
    "marca": "Disano"
  },
  "sorting_applied": {
    "field": "codigo",
    "direction": "asc"
  }
}
```

---

### 2. Families - Paginated List

Get paginated list of product families with BC3 statistics.

**Endpoint:** `GET /api/familias/v2/paginated`

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (min: 1) | `1` |
| `per_page` | integer | No | Items per page (min: 1, max: 100) | `10` |
| `sort` | string | No | Field and direction: `field:direction` | `nombre:asc` |
| `buscar` | string | No | Search in family name | `emergencia` |

**Example Requests:**

```bash
# Basic pagination
curl "http://localhost:8000/api/familias/v2/paginated?page=1&per_page=10"

# With search
curl "http://localhost:8000/api/familias/v2/paginated?buscar=emergencia"

# With sorting
curl "http://localhost:8000/api/familias/v2/paginated?sort=total_productos:desc"
```

**Response Structure:**

```json
{
  "items": [
    {
      "nombre": "Emergencia",
      "total_productos": 150,
      "con_bc3": 120,
      "bc3_porcentaje": "80.0%"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total_items": 50,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {},
  "sorting_applied": {
    "field": "total_productos",
    "direction": "desc"
  }
}
```

---

### 3. BC3 Statistics

Get comprehensive BC3 compatibility statistics.

**Endpoint:** `GET /api/bc3/v2/stats`

**Example Request:**

```bash
curl "http://localhost:8000/api/bc3/v2/stats"
```

**Response Structure:**

```json
{
  "total": 8288,
  "con_descripcion_corta": 7000,
  "con_descripcion_larga": 6500,
  "con_tipo_producto": 7200,
  "porcentajes": {
    "con_descripcion_corta": "84.5%",
    "con_descripcion_larga": "78.4%",
    "con_tipo_producto": "86.9%"
  },
  "tipos": {
    "luminaria": 2500,
    "columna": 1800,
    "banco": 1500,
    "señalizacion": 1200,
    "otros": 1288
  }
}
```

---

### 4. BC3 Products - Paginated List

Get paginated list of BC3-compatible products with BC3-specific filtering.

**Endpoint:** `GET /api/bc3/v2/paginated`

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (min: 1) | `1` |
| `per_page` | integer | No | Items per page (min: 1, max: 100) | `10` |
| `sort` | string | No | Field and direction: `field:direction` | `codigo:asc` |
| `bc3_product_type` | string | No | Filter by BC3 product type | `luminaria` |

**Example Requests:**

```bash
# Basic pagination
curl "http://localhost:8000/api/bc3/v2/paginated?page=1&per_page=10"

# BC3-specific filtering
curl "http://localhost:8000/api/bc3/v2/paginated?bc3_product_type=luminaria"

# With sorting
curl "http://localhost:8000/api/bc3/v2/paginated?sort=bc3_product_type:asc"
```

---

## Pagination

All paginated endpoints follow the same pagination structure:

**Pagination Metadata:**

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

**Pagination Rules:**

- `page`: Minimum value is 1
- `per_page`: Minimum value is 1, maximum is 100
- `total_pages`: Calculated automatically from `total_items` and `per_page`
- `has_next`: Indicates if there are more pages available
- `has_previous`: Indicates if previous page exists

**Navigation Example:**

```bash
# First page
curl "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10"

# Next page (if has_next is true)
curl "http://localhost:8000/api/productos/v2/paginated?page=2&per_page=10"

# Last page
curl "http://localhost:8000/api/productos/v2/paginated?page=829&per_page=10"
```

---

## Sorting

### Sorting Syntax

```
sort=field:direction
```

**Sortable Fields:**

- **Products:** `codigo`, `descripcion`, `pvp`, `marca`, `familia`, `bc3_product_type`
- **Families:** `nombre`, `total_productos`, `con_bc3`
- **BC3 Products:** `codigo`, `descripcion`, `bc3_product_type`

**Sort Directions:**

- `asc`: Ascending order (default)
- `desc`: Descending order

**Example Requests:**

```bash
# Sort by product code ascending
curl "http://localhost:8000/api/productos/v2/paginated?sort=codigo:asc"

# Sort by price descending
curl "http://localhost:8000/api/productos/v2/paginated?sort=pvp:desc"

# Sort by family name ascending
curl "http://localhost:8000/api/familias/v2/paginated?sort=nombre:asc"
```

---

## Filtering

### Filter Parameters

**Product Filters:**

- `buscar`: Free-text search in descripcion and codigo
- `marca`: Filter by brand
- `familia`: Filter by family
- `pvp_min`: Minimum price
- `pvp_max`: Maximum price
- `bc3_product_type`: Filter by BC3 product type

**Family Filters:**

- `buscar`: Free-text search in family name

**BC3 Filters:**

- `bc3_product_type`: Filter by BC3 product type

**Example Requests:**

```bash
# Single filter
curl "http://localhost:8000/api/productos/v2/paginated?marca=Disano"

# Multiple filters
curl "http://localhost:8000/api/productos/v2/paginated?buscar=test&marca=Disano&familia=Emergencia"

# Price range filtering
curl "http://localhost:8000/api/productos/v2/paginated?pvp_min=10&pvp_max=200"

# BC3-specific filtering
curl "http://localhost:8000/api/productos/v2/paginated?bc3_product_type=luminaria"
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Error message",
  "error_code": "ERROR_CODE",
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

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 200 | - | Success |
| 400 | BAD_REQUEST | Invalid request parameters |
| 404 | NOT_FOUND | Resource not found |
| 422 | VALIDATION_ERROR | Validation failed |
| 500 | INTERNAL_ERROR | Server error |

### Error Examples

```bash
# Invalid page number
curl "http://localhost:8000/api/productos/v2/paginated?page=-1"

# Response:
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

---

## Best Practices

### 1. Pagination

**DO:**

```bash
# Use pagination for large datasets
curl "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=50"
```

**DON'T:**

```bash
# Don't request too many items at once
curl "http://localhost:8000/api/productos/v2/paginated?per_page=999"  # Returns error
```

### 2. Filtering

**DO:**

```bash
# Use specific filters for precise results
curl "http://localhost:8000/api/productos/v2/paginated?marca=Disano&familia=Emergencia&pvp_min=10&pvp_max=200"
```

**DON'T:**

```bash
# Don't rely on client-side filtering
curl "http://localhost:8000/api/productos/v2/paginated"  # Then filter 8000+ items
```

### 3. Sorting

**DO:**

```bash
# Sort results for better user experience
curl "http://localhost:8000/api/productos/v2/paginated?sort=pvp:asc"
```

**DON'T:**

```bash
# Don't sort large datasets client-side
curl "http://localhost:8000/api/productos/v2/paginated"  # Then sort 8000+ items
```

### 4. Error Handling

**DO:**

```bash
# Always handle error responses gracefully
response=$(curl -s -w "%{http_code}" "http://localhost:8000/api/productos/v2/paginated?page=-1")
status_code=${response: -3}

if [ $status_code -eq 422 ]; then
  echo "Validation error - check parameters"
elif [ $status_code -eq 200 ]; then
  echo "Success"
fi
```

**DON'T:**

```bash
# Don't assume all requests succeed
curl "http://localhost:8000/api/productos/v2/paginated?page=-1" | jq '.items'  # May fail
```

### 5. Caching

**DO:**

```bash
# Leverage caching for repeated queries
curl "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10" --cache-control=max-age=60
```

---

## Performance Guidelines

### Response Time Expectations

- **Small datasets (1-10 items):** < 500ms
- **Large datasets (100 items):** < 2000ms
- **Cache hits:** < 100ms

### Memory Usage

- **Per item:** ~670 bytes
- **10 items:** ~6.7KB
- **100 items:** ~67KB

### Rate Limiting

Currently no rate limiting is implemented, but future versions may include:

- **Default limit:** 100 requests per minute
- **Burst limit:** 200 requests per 5 minutes

---

## Testing

### Manual Testing

```bash
# Test basic functionality
curl "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=5"

# Test with filters
curl "http://localhost:8000/api/productos/v2/paginated?buscar=test&marca=Disano"

# Test sorting
curl "http://localhost:8000/api/productos/v2/paginated?sort=codigo:desc"

# Test error handling
curl "http://localhost:8000/api/productos/v2/paginated?page=-1"
```

### Automated Testing

```python
import requests

BASE_URL = "http://localhost:8000/api"

def test_pagination():
    response = requests.get(f"{BASE_URL}/productos/v2/paginated?page=1&per_page=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) == 10
    assert data['pagination']['current_page'] == 1
    print("✅ Pagination test passed")

def test_filtering():
    response = requests.get(f"{BASE_URL}/productos/v2/paginated?marca=Disano")
    assert response.status_code == 200
    data = response.json()
    assert 'filters_applied' in data
    print("✅ Filtering test passed")

if __name__ == "__main__":
    test_pagination()
    test_filtering()
```

---

## Changelog

### Version 2.0.0 (Current)

- ✅ Advanced pagination with metadata
- ✅ Multi-criteria filtering
- ✅ Multi-field sorting
- ✅ BC3-specific features
- ✅ Performance optimizations
- ✅ Comprehensive error handling

### Version 1.0.0 (Deprecated)

- Basic product listing
- Simple pagination
- Limited filtering

---

## Support

- **Documentation:** See OpenSpec artifacts in `openspec/changes/fase4-advanced-features/`
- **Issues:** Report issues via the project issue tracker
- **Contact:** Support team via email

---

## License

© 2024 Disano. All rights reserved.
