# API_DISANO Migration Guide: V1 to V2

## Introduction

### Purpose
This migration guide explains how to update your API client code from V1 to V2 of the API_DISANO service. The migration is necessary to improve code maintainability and follow industry standards.

### What Changes
The main changes are field name updates:
- Uppercase and special character fields renamed to snake_case
- Date-based dynamic fields replaced with static fields
- All field names now follow consistent naming conventions

### Timeline
- **V1 will be deprecated after 30 days from the release of this guide**
- Start migrating to V2 as soon as possible
- Both versions can be used simultaneously during the transition period

---

## Field Mapping Table

| V1 Field (Old)       | V2 Field (New) | Description                              |
|----------------------|----------------|------------------------------------------|
| CÓDIGO               | codigo         | Changed to lowercase                     |
| DESCRIPCION          | descripcion    | Changed to lowercase                     |
| PVP_26_01_26         | pvp            | New static field (no date)               |

---

## API Endpoint Changes

### V1 Endpoints (Deprecated in 30 days)
```
GET https://api.eloymartinezcuesta.com/api/productos/
```

### V2 Endpoints (Current Version)
```
GET https://api.eloymartinezcuesta.com/api/productos/v2
```

**Note:** V1 endpoints will continue to work for 30 more days. After that period, V1 will be deprecated and all requests will need to use V2 endpoints.

---

## Code Examples

### Python Example

#### OLD (V1)
```python
import requests

response = requests.get("https://api.eloymartinezcuesta.com/api/productos/")
for product in response.json():
    codigo = product["CÓDIGO"]  # Old field
    pvp = product["PVP_26_01_26"]  # Old field
    print(f"Product: {codigo}, Price: {pvp}")
```

#### NEW (V2)
```python
import requests

response = requests.get("https://api.eloymartinezcuesta.com/api/productos/v2")
for product in response.json():
    codigo = product["codigo"]  # New field
    pvp = product["pvp"]  # New field
    print(f"Product: {codigo}, Price: {pvp}")
```

---

### JavaScript Example

#### OLD (V1)
```javascript
fetch('https://api.eloymartinezcuesta.com/api/productos/')
  .then(r => r.json())
  .then(data => {
      data.forEach(p => {
          const codigo = p['CÓDIGO'];  // Old field
          const pvp = p['PVP_26_01_26'];  // Old field
          console.log(`Product: ${codigo}, Price: ${pvp}`);
      });
  });
```

#### NEW (V2)
```javascript
fetch('https://api.eloymartinezcuesta.com/api/productos/v2')
  .then(r => r.json())
  .then(data => {
      data.forEach(p => {
          const codigo = p['codigo'];  // New field
          const pvp = p['pvp'];  // New field
          console.log(`Product: ${codigo}, Price: ${pvp}`);
      });
  });
```

---

## Benefits of Migrating to V2

- ✅ **Standard snake_case naming** - Follows Python and JavaScript conventions
- ✅ **No need for fallbacks in code** - Clean, direct field access
- ✅ **More readable code** - Lowercase names are easier to read
- ✅ **Industry standard compliance** - Aligns with modern API practices
- ✅ **Better documentation** - Consistent naming improves clarity
- ✅ **Easier maintenance** - Static field names instead of date-based fields

---

## Migration Checklist

Before you complete the migration, ensure you've completed the following steps:

- [ ] Update endpoint URLs from `/api/productos/` to `/api/productos/v2`
- [ ] Update field names in code (CÓDIGO → codigo, DESCRIPCION → descripcion, PVP_26_01_26 → pvp)
- [ ] Remove any fallback logic or try-catch blocks for old field names
- [ ] Test all functionality with the V2 API
- [ ] Remove old V1 endpoint usage from production code
- [ ] Update any internal documentation to reflect V2 field names

---

## Important Notes

- ⚠️ V1 endpoints will work for 30 more days from the release of this guide
- ⚠️ After 30 days, V1 will be deprecated and will no longer be available
- 🚀 Start migrating to V2 as soon as possible to avoid disruptions
- 🔄 Both versions can be used simultaneously during the transition period
- 💬 If you have questions or encounter issues, contact support

---

## Contact Information

- 📧 **Email:** support@api.eloymartinezcuesta.com
- 📖 **Documentation:** /docs/MIGRATION_GUIDE_V1_V2.md
- 📡 **API Status:** https://api.eloymartinezcuesta.com/status

---

**Last Updated:** March 22, 2026
**Version:** 2.0
