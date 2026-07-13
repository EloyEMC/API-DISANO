# API-DISANO V2 API Documentation

## Overview

The V2 API provides advanced pagination, sorting, and filtering capabilities for all endpoints, designed for production-scale applications handling large datasets.

**Key Features:**

- 📊 **Pagination**: Full support for page-based navigation with metadata
- 🔍 **Advanced Filtering**: Multiple filter criteria with flexible operators
- 📈 **Sorting**: Multi-field sorting with ascending/descending order
- 🚀 **Performance**: Optimized with caching and efficient queries
- 🛡️ **Error Handling**: Comprehensive validation and error responses

---

## Base URLs

- **Production**: `https://api.disano.com/api`
- **Staging**: `https://staging-api.disano.com/api`
- **Development**: `http://localhost:8000/api`

---

## Response Format

All V2 endpoints follow a consistent response structure:

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
  "filters_applied": {
    "search": "test",
    "marca": "Disano"
  },
  "sorting_applied": {
    "field": "codigo",
    "direction": "asc"
  }
}
```

---

## Endpoints

### 1. Productos V2 - Paginated List

Get paginated list of products with advanced filtering and sorting.

#### Endpoint

```
GET /api/productos/v2/paginated
```

#### Query Parameters

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
| `bc3_descripcion` | string | No | Filter by BC3 description | `test` |

#### Sort Directions

- `asc` - Ascending order
- `desc` - Descending order

#### Sortable Fields

- `codigo` - Product code
- `descripcion` - Product description
- `pvp` - Price
- `marca` - Brand
- `familia` - Family
- `bc3_product_type` - BC3 product type

#### Example Requests

**Basic pagination:**

```bash
curl -X GET "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10"
```

**With filtering:**

```bash
curl -X GET "http://localhost:8000/api/productos/v2/paginated?buscar=test&marca=Disano&familia=Emergencia"
```

**With sorting:**

```bash
curl -X GET "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10&sort=codigo:asc"
```

**Complex query:**

```bash
curl -X GET "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10&buscar=test&pvp_min=10&pvp_max=200&sort=pvp:desc"
```

**BC3-specific filtering:**

```bash
curl -X GET "http://localhost:8000/api/productos/v2/paginated?bc3_product_type=luminaria"
```

#### Example Response

```json
{
  "items": [
    {
      "codigo": "TEST001",
      "descripcion": "Product Description",
      "marca": "Disano",
      "familia": "Emergencia",
      "pvp": 100.00,
      "bc3_descripcion_corta": "BC3 Desc",
      "bc3_descripcion_larga": "Full BC3 Description",
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

#### Error Responses

**422 Validation Error:**

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

**404 Not Found:**

```json
{
  "error": "Requested resource not found",
  "error_code": "NOT_FOUND",
  "status": 404
}
```

---

### 2. Familias V2 - Paginated List

Get paginated list of product families with BC3 statistics.

#### Endpoint

```
GET /api/familias/v2/paginated
```

#### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (min: 1) | `1` |
| `per_page` | integer | No | Items per page (min: 1, max: 100) | `10` |
| `sort` | string | No | Field and direction: `field:direction` | `nombre:asc` |
| `buscar` | string | No | Search in family name | `emergencia` |

#### Sortable Fields

- `nombre` - Family name
- `total_productos` - Total products count
- `con_bc3` - BC3-compatible products count

#### Example Requests

**Basic pagination:**

```bash
curl -X GET "http://localhost:8000/api/familias/v2/paginated?page=1&per_page=10"
```

**With search:**

```bash
curl -X GET "http://localhost:8000/api/familias/v2/paginated?buscar=emergencia"
```

**With sorting:**

```bash
curl -X GET "http://localhost:8000/api/familias/v2/paginated?sort=total_productos:desc"
```

#### Example Response

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

### 3. BC3 V2 - Statistics

Get comprehensive BC3 compatibility statistics.

#### Endpoint

```
GET /api/bc3/v2/stats
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/api/bc3/v2/stats"
```

#### Example Response

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

### 4. BC3 V2 - Paginated List

Get paginated list of BC3-compatible products with BC3-specific filtering.

#### Endpoint

```
GET /api/bc3/v2/paginated
```

#### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (min: 1) | `1` |
| `per_page` | integer | No | Items per page (min: 1, max: 100) | `10` |
| `sort` | string | No | Field and direction | `codigo:asc` |
| `bc3_product_type` | string | No | Filter by BC3 product type | `luminaria` |
| `bc3_descripcion` | string | No | Filter by BC3 description | `test` |

#### Example Requests

**BC3 products by type:**

```bash
curl -X GET "http://localhost:8000/api/bc3/v2/paginated?bc3_product_type=luminaria"
```

**BC3 products with sorting:**

```bash
curl -X GET "http://localhost:8000/api/bc3/v2/paginated?sort=bc3_product_type:asc"
```

#### Example Response

```json
{
  "items": [
    {
      "codigo": "LUM001",
      "descripcion": "Luminaria Test",
      "marca": "Disano",
      "familia": "Alumbrado",
      "pvp": 250.00,
      "bc3_descripcion_corta": "LUMINARIA LED",
      "bc3_descripcion_larga": "LUMINARIA LED EMERGENCIA 150W",
      "bc3_product_type": "luminaria"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total_items": 2500,
    "total_pages": 250,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "bc3_product_type": "luminaria"
  },
  "sorting_applied": {
    "field": "bc3_product_type",
    "direction": "asc"
  }
}
```

---

## Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 200 | - | Success |
| 400 | BAD_REQUEST | Invalid request parameters |
| 404 | NOT_FOUND | Resource not found |
| 422 | VALIDATION_ERROR | Validation failed |
| 500 | INTERNAL_ERROR | Server error |

---

## Performance Characteristics

- **Small queries (1-10 items)**: < 500ms average response time
- **Large queries (100 items)**: < 2000ms average response time
- **Cache hit**: < 100ms response time
- **Memory efficiency**: ~670 bytes per item
- **Error rate**: < 1%
- **Concurrent handling**: Supports concurrent requests safely

---

## Rate Limiting

- **Default limit**: 100 requests per minute
- **Burst limit**: 200 requests per 5 minutes
- **Headers included**:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Authentication

Currently no authentication required. Future versions will implement API key-based authentication.

---

## Versioning

- **V1**: Legacy endpoints (deprecated, maintained for backward compatibility)
- **V2**: Current production-ready endpoints with advanced features

---

## Best Practices

1. **Pagination**: Always use pagination for large datasets
2. **Filtering**: Combine multiple filters for precise results
3. **Sorting**: Use sorting to optimize frontend display
4. **Caching**: Leverage browser caching for repeated queries
5. **Error Handling**: Always check for error responses
6. **Rate Limiting**: Implement client-side rate limiting

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

- **Documentation**: [OpenSpec](openspec/changes/fase4-advanced-features/)
- **Issues**: [GitHub Issues](https://github.com/disano/api-disano/issues)
- **Contact**: <support@disano.com>

---

## License

© 2024 Disano. All rights reserved.
