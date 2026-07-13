# API-DISANO V2 User Guide

## Bienvenido a API-DISANO V2

¡Hola! Esta guía te ayudará a usar la API-DISANO V2 de manera fácil y eficiente. No necesitas ser un experto en tecnología para seguir estos pasos.

**Versión:** 2.0.0  
**Última actualización:** 2024-07-11  
**Estado:** Lista para producción

---

## Tabla de Contenidos

1. [¿Qué es API-DISANO?](#qué-es-api-disano)
2. [Conceptos Básicos](#conceptos-básicos)
3. [Guía de Inicio Rápido](#guía-de-inicio-rápido)
4. [Búsqueda de Productos](#búsqueda-de-productos)
5. [Filtrado Avanzado](#filtrado-avanzado)
6. [Navegación por Páginas](#navegación-por-páginas)
7. [Ordenamiento](#ordenamiento)
8. [Familias de Productos](#familias-de-productos)
9. [Estadísticas BC3](#estadísticas-bc3)
10. [Ejemplos Prácticos](#ejemplos-prácticos)

---

## ¿Qué es API-DISANO?

API-DISANO es un servicio que te permite acceder a información detallada sobre productos Disano. Con la versión 2.0, puedes:

- 🔍 **Buscar productos** de manera eficiente
- 📄 **Navegar por páginas** grandes conjuntos de datos
- 🏷️ **Filtrar por marca, familia, precio** y más
- 📊 **Ver estadísticas** de compatibilidad BC3
- 🚀 **Obtener respuestas rápidas** (<2 segundos)

---

## Conceptos Básicos

### ¿Qué es una API?

**API** significa "Application Programming Interface" (Interfaz de Programación de Aplicaciones). En términos simples:

- Es como un **catálogo digital** de productos
- Puedes **solicitar información** y recibir respuestas
- Funciona como **buscar en Google** pero para productos específicos

### ¿Qué es JSON?

**JSON** es el formato de respuesta que recibes. Es como una tabla organizada:

```json
{
  "items": [
    {
      "codigo": "TEST001",
      "descripcion": "Producto de prueba",
      "pvp": 100.00
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_items": 8288
  }
}
```

### URL Base

Todas las solicitudes empiezan con:

```
http://localhost:8000/api
```

---

## Guía de Inicio Rápido

### Paso 1: Tu Primera Búsqueda

**Opción A: Usando el navegador**

```
En tu navegador, visita:
http://localhost:8000/api/productos/v2/paginated?page=1&per_page=5
```

**Opción B: Usando curl (línea de comandos)**

```bash
curl "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=5"
```

**Opción C: Usando una herramienta online**

- Visita: <https://reqbin.com/>
- Ingresa la URL: `http://localhost:8000/api/productos/v2/paginated?page=1&per_page=5`
- Haz clic en "Send"

**Verás una respuesta como:**

```json
{
  "items": [
    {
      "codigo": "1A001",
      "descripcion": "Luminaria emergencia LED",
      "marca": "Disano",
      "familia": "Emergencia",
      "pvp": 125.50
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 5,
    "total_items": 8288,
    "total_pages": 1658
  }
}
```

### Paso 2: Entender la Respuesta

**Partes importantes:**

1. **`items`**: Lista de productos encontrados
   - `codigo`: Código único del producto
   - `descripcion`: Nombre del producto
   - `marca`: Fabricante
   - `familia`: Categoría
   - `pvp**: Precio de venta

2. **`pagination`**: Información de navegación
   - `current_page`: Página actual
   - `per_page`: Productos por página
   - `total_items`: Total de productos
   - `total_pages`: Total de páginas

---

## Búsqueda de Productos

### Búsqueda Básica

**Buscar por texto:**

```
/api/productos/v2/paginated?buscar=luminaria
```

Esto busca "luminaria" en descripciones y códigos.

**Resultados:**

- Todos los productos que contengan "luminaria"
- Máximo 10 productos por página (por defecto)

### Búsqueda Específica

**Por marca:**

```
/api/productos/v2/paginated?marca=Disano
```

**Por familia:**

```
/api/productos/v2/paginated?familia=Emergencia
```

**Por tipo BC3:**

```
/api/productos/v2/paginated?bc3_product_type=luminaria
```

### Búsqueda Combinada

**Marca + Familia:**

```
/api/productos/v2/paginated?marca=Disano&familia=Emergencia
```

**Marca + Precio:**

```
/api/productos/v2/paginated?marca=Disano&pvp_min=10&pvp_max=200
```

---

## Filtrado Avanzado

### Filtrado por Precio

**Precio mínimo:**

```
/api/productos/v2/paginated?pvp_min=50
```

Productos desde €50

**Precio máximo:**

```
/api/productos/v2/paginated?pvp_max=200
```

Productos hasta €200

**Rango de precios:**

```
/api/productos/v2/paginated?pvp_min=10&pvp_max=100
```

Productos entre €10 y €100

### Filtrado por Características

**Productos con descripción BC3:**

```
/api/productos/v2/paginated?buscar=LED
```

Productos que mencionen "LED"

**Por tipo de producto:**

```
/api/productos/v2/paginated?bc3_product_type=columna
```

Productos de tipo "columna"

### Filtros Disponibles

| Filtro | Tipo | Descripción | Ejemplo |
|--------|------|-------------|---------|
| `buscar` | Texto | Búsqueda libre | `buscar=emergencia` |
| `marca` | Texto | Marca específica | `marca=Disano` |
| `familia` | Texto | Familia específica | `familia=Emergencia` |
| `pvp_min` | Número | Precio mínimo | `pvp_min=10` |
| `pvp_max` | Número | Precio máximo | `pvp_max=200` |
| `bc3_product_type` | Texto | Tipo BC3 | `bc3_product_type=luminaria` |

---

## Navegación por Páginas

### Concepto de Paginación

Con 8,288 productos, es mejor dividirlos en páginas:

- **10 productos por página** → 829 páginas
- **50 productos por página** → 166 páginas
- **100 productos por página** → 83 páginas

### Navegación Básica

**Primera página:**

```
/api/productos/v2/paginated?page=1&per_page=10
```

**Segunda página:**

```
/api/productos/v2/paginated?page=2&per_page=10
```

**Última página:**

```
/api/productos/v2/paginated?page=829&per_page=10
```

### Tamaño de Página

**Pequeño (5 productos):**

```
/api/productos/v2/paginated?per_page=5
```

Ideal para previsualizaciones

**Medio (20 productos):**

```
/api/productos/v2/paginated?per_page=20
```

Ideal para listas

**Grande (100 productos):**

```
/api/productos/v2/paginated?per_page=100
```

Ideal para exportación

### Navegación Inteligente

**Saber si hay más páginas:**

```json
{
  "pagination": {
    "has_next": true,
    "has_previous": false
  }
}
```

- `has_next: true` → Hay página siguiente
- `has_previous: false` → No hay página anterior

**Navegación completa:**

```
1. Primera página: /api/productos/v2/paginated?page=1&per_page=10
2. Ver si hay siguiente: has_next = true
3. Segunda página: /api/productos/v2/paginated?page=2&per_page=10
4. Continuar hasta has_next = false
```

---

## Ordenamiento

### Sintaxis de Ordenamiento

```
sort=campo:orden
```

**Campos disponibles:**

- `codigo`: Código de producto
- `descripcion`: Descripción
- `pvp`: Precio
- `marca`: Marca
- `familia`: Familia
- `bc3_product_type`: Tipo BC3

**Ordenes disponibles:**

- `asc`: Ascendente (A → Z, 0 → 9)
- `desc`: Descendente (Z → A, 9 → 0)

### Ejemplos de Ordenamiento

**Por código (A-Z):**

```
/api/productos/v2/paginated?sort=codigo:asc
```

**Por precio (bajo → alto):**

```
/api/productos/v2/paginated?sort=pvp:asc
```

**Por precio (alto → bajo):**

```
/api/productos/v2/paginated?sort=pvp:desc
```

**Por marca (A-Z):**

```
/api/productos/v2/paginated?sort=marca:asc
```

### Combinar Filtros y Ordenamiento

**Filtrar + Ordenar:**

```
/api/productos/v2/paginated?marca=Disano&sort=pvp:desc
```

Productos Disano, ordenados por precio (más caros primero)

**Búsqueda + Ordenar:**

```
/api/productos/v2/paginated?buscar=LED&sort=descripcion:asc
```

Productos con "LED", ordenados alfabéticamente

---

## Familias de Productos

### Listar Familias

**Todas las familias:**

```
/api/familias/v2/paginated?page=1&per_page=10
```

**Respuesta:**

```json
{
  "items": [
    {
      "nombre": "Emergencia",
      "total_productos": 150,
      "con_bc3": 120,
      "bc3_porcentaje": "80.0%"
    }
  ]
}
```

**Información de cada familia:**

- `nombre`: Nombre de la familia
- `total_productos`: Total de productos
- `con_bc3`: Productos compatibles BC3
- `bc3_porcentaje`: Porcentaje de compatibilidad

### Buscar Familias

**Por nombre:**

```
/api/familias/v2/paginated?buscar=emergencia
```

**Ordenar por productos:**

```
/api/familias/v2/paginated?sort=total_productos:desc
```

Familias con más productos primero

### Usos Prácticos

**Ver categorías disponibles:**

```
/api/familias/v2/paginated?per_page=50
```

**Encontrar familias con alta compatibilidad BC3:**

```
/api/familias/v2/paginated?sort=con_bc3:desc
```

---

## Estadísticas BC3

### Obtener Estadísticas Generales

**Endpoint:**

```
/api/bc3/v2/stats
```

**Respuesta:**

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

### Entender las Estadísticas

**Total:**

- `total`: Total de productos en el sistema
- `con_descripcion_corta`: Productos con descripción corta BC3
- `con_descripcion_larga`: Productos con descripción larga BC3
- `con_tipo_producto`: Productos con tipo BC3 definido

**Porcentajes:**

- `porcentajes.con_descripcion_corta`: % con descripción corta
- `porcentajes.con_descripcion_larga`: % con descripción larga
- `porcentajes.con_tipo_producto`: % con tipo definido

**Tipos:**

- `tipos.luminaria`: Cantidad de luminarias
- `tipos.columna`: Cantidad de columnas
- `tipos.banco`: Cantidad de bancos
- `tipos.señalizacion`: Cantidad de señalización
- `tipos.otros`: Otros tipos

### Usos Prácticos

**Ver nivel de compatibilidad BC3:**

```
/api/bc3/v2/stats
```

86.9% de productos tienen tipo BC3 definido

**Encontrar productos por tipo:**

```
/api/bc3/v2/paginated?bc3_product_type=luminaria
```

2,500 luminarias disponibles

---

## Ejemplos Prácticos

### Escenario 1: Encontrar Productos Económicos

**Objetivo:** Productos Disano bajo €50

**Solicitud:**

```
/api/productos/v2/paginated?marca=Disano&pvp_max=50&sort=pvp:asc
```

**Interpretación:**

- Filtra por marca "Disano"
- Máximo precio €50
- Ordena por precio (más baratos primero)

**Resultado:**

- Productos Disano más económicos
- Ordenados de menor a mayor precio

### Escenario 2: Explorar una Familia

**Objetivo:** Ver productos de "Emergencia"

**Paso 1:** Obtener información de la familia

```
/api/familias/v2/paginated?buscar=emergencia
```

**Paso 2:** Listar productos de la familia

```
/api/productos/v2/paginated?familia=Emergencia&per_page=20
```

**Paso 3:** Navegar por páginas

```
/api/productos/v2/paginated?familia=Emergencia&page=2&per_page=20
```

### Escenario 3: Buscar Luminarias LED

**Objetivo:** Encontrar luminarias LED específicas

**Solicitud:**

```
/api/productos/v2/paginated?buscar=LED&bc3_product_type=luminaria
```

**Interpretación:**

- Busca "LED" en descripciones
- Filtra por tipo "luminaria"
- Combina búsqueda y filtro BC3

### Escenario 4: Comparar Precios por Marca

**Objetivo:** Ver productos de diferentes marcas

**Paso 1:** Productos Disano

```
/api/productos/v2/paginated?marca=Disano&per_page=10&sort=pvp:asc
```

**Paso 2:** Productos de otra marca

```
/api/productos/v2/paginated?marca=OtraMarca&per_page=10&sort=pvp:asc
```

**Comparar:**

- Compara los precios de ambas marcas
- Identifica diferencias de precio

### Escenario 5: Exportación Completa

**Objetivo:** Obtener todos los productos

**Enfoque eficiente:**

```bash
# Página 1
curl "http://localhost:8000/api/productos/v2/paginated?page=1&per_page=100" > productos_page1.json

# Página 2
curl "http://localhost:8000/api/productos/v2/paginated?page=2&per_page=100" > productos_page2.json

# ... continuar hasta has_next = false
```

**Alternativa:**

- Usa un script pequeño para automatizar
- Procesa página por página
- Combina resultados en un solo archivo

---

## Solución de Problemas

### Error: "No se puede conectar"

**Causas posibles:**

- El servidor no está ejecutándose
- URL incorrecta
- Problema de red

**Soluciones:**

1. Verifica que el servidor está ejecutándose:

   ```bash
   curl http://localhost:8000/api/productos/v2/paginated?page=1&per_page=1
   ```

2. Inicia el servidor si no está ejecutándose:

   ```bash
   cd /ruta/a/api-disano
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Verifica la URL:
   - `localhost:8000` para servidor local
   - Dirección IP del servidor si es remoto

### Error: "Resultados vacíos"

**Causa:** Búsqueda demasiado específica

**Solución:**

1. Simplifica la búsqueda:
   - De `buscar=luminaria emergencia LED 2024` a `buscar=luminaria`

2. Elimina filtros:
   - De `marca=Disano&familia=Emergencia&pvp_min=10&pvp_max=20` a solo `marca=Disano`

3. Busca con términos más generales:
   - De `buscar=LED_premium` a `buscar=LED`

### Error: "Validación falló"

**Causa:** Parámetros inválidos

**Solución:**

1. Verifica `page` y `per_page`:
   - `page` debe ser ≥ 1
   - `per_page` debe ser entre 1 y 100

2. Verifica el formato de `sort`:
   - Correcto: `sort=codigo:asc`
   - Incorrecto: `sort=codigo-asc`

3. Verifica tipos de datos:
   - `pvp_min` y `pvp_max` deben ser números

### Respuestas Lentas

**Causa:** Solicitudes muy grandes o complejas

**Soluciones:**

1. Reduce el tamaño de página:
   - De `per_page=100` a `per_page=10`

2. Simplifica filtros:
   - Menos filtros = respuesta más rápida

3. Usa caché:
   - Guarda respuestas frecuentes
   - Reutiliza cuando sea posible

---

## Consejos Útiles

### Optimización de Búsquedas

**✅ HACER:**

- Usa filtros específicos
- Comina `marca` + `familia` + precio
- Usa tamaños de página razonables (10-50)

**❌ EVITAR:**

- Solicitar todos los productos a la vez
- Búsquedas demasiado generales
- Tamaños de página muy grandes (100+)

### Navegación Eficiente

**✅ HACER:**

- Verifica `has_next` antes de avanzar
- Usa `total_pages` para planificar
- Navega secuencialmente

**❌ EVITAR:**

- Ir directamente a páginas sin verificar
- Solicitar páginas inexistentes
- Navegar desordenadamente

### Gestión de Errores

**✅ HACER:**

- Maneja errores 422 (validación)
- Revisa parámetros si hay errores
- Implementa reintentos para errores 500

**❌ EVITAR:**

- Ignorar errores
- Repetir solicitudes fallidas sin cambios
- No leer mensajes de error

---

## Recursos Adicionales

### Documentación Técnica

- **API Reference:** Ver documentación técnica para desarrolladores
- **Architecture:** Ver documentación de arquitectura del sistema
- **Tests:** Ver pruebas automatizadas para más ejemplos

### Herramientas

- **Browser:** Para pruebas rápidas
- **curl:** Para línea de comandos
- **Postman:** Para pruebas avanzadas
- **Python requests:** Para integración en aplicaciones

### Soporte

- **Preguntas:** Contacta al equipo de soporte
- **Problemas:** Reporta issues técnicos
- **Sugerencias:** Comenta mejoras

---

## Resumen Rápido

### URL Importantes

```
# Productos básico
/api/productos/v2/paginated

# Productos con búsqueda
/api/productos/v2/paginated?buscar=LED

# Productos con filtros
/api/productos/v2/paginated?marca=Disano&familia=Emergencia

# Productos ordenados
/api/productos/v2/paginated?sort=pvp:desc

# Familias
/api/familias/v2/paginated

# Estadísticas BC3
/api/bc3/v2/stats
```

### Parámetros Útiles

| Parámetro | Ejemplo | Descripción |
|-----------|---------|-------------|
| `page` | `page=2` | Página específica |
| `per_page` | `per_page=20` | Productos por página |
| `sort` | `sort=pvp:desc` | Ordenar resultados |
| `buscar` | `buscar=LED` | Búsqueda de texto |
| `marca` | `marca=Disano` | Filtrar por marca |
| `familia` | `familia=Emergencia` | Filtrar por familia |
| `pvp_min` | `pvp_min=10` | Precio mínimo |
| `pvp_max` | `pvp_max=200` | Precio máximo |

### Respuestas Típicas

**Éxito (200):**

```json
{
  "items": [...],
  "pagination": {...},
  "filters_applied": {...},
  "sorting_applied": {...}
}
```

**Error de validación (422):**

```json
{
  "error": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "status": 422,
  "details": {
    "validation_errors": [...]
  }
}
```

---

## ¡Listo para Empezar

Ahora que conoces los conceptos básicos, puedes:

1. **Explorar productos** usando diferentes filtros
2. **Navegar por páginas** grandes conjuntos de datos
3. **Ordenar resultados** según tus necesidades
4. **Consultar estadísticas** para mejor comprensión
5. **Combinar funcionalidades** para búsquedas avanzadas

**¡Comienza con tu primera búsqueda!**

```
http://localhost:8000/api/productos/v2/paginated?page=1&per_page=10
```

---

## Licencia

© 2024 Disano. Todos los derechos reservados.
