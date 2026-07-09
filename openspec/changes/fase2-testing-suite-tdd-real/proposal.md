# Propuesta: Fase 2 - Testing Suite con TDD Real

## Resumen Ejecutivo

Implementar **Testing Suite con TDD Real** para API-DISANO siguiendo patrones BC3-Suite, alcanzando ≥80% coverage con ≈250 tests automatizados que validan comportamiento real, no solo estructura.

## Estado Actual

**Coverage:** 22% (de 5% inicial, +17%)
**Tests existentes:** 154 tests unitarios (principalmente de estructura)
**Problemas identificados:**

- Tests de estructura, no de comportamiento real
- Sin ciclo TDD (RED→GREEN→REFACTOR)
- Sin refactorización de código para hacerlo testeable
- Coverage como meta, no como resultado

## Objetivos

### Objetivos de Negocio

- Asegurar calidad y estabilidad del código
- Prevenir regresiones en cambios futuros
- Facilitar refactorización segura
- Cumplir con estándares BC3-Suite (≥80% coverage)

### Objetivos Técnicos

- Crear ≈250 tests automatizados (unitarios + integración)
- Alcanzar ≥80% coverage de código real
- Implementar TDD real (RED→GREEN→REFACTOR)
- Crear factories BC3-Suite para datos de prueba
- Tests de comportamiento real, no estructura

## Alcance

### INCLUYE

- Tests unitarios (≈100 tests): config, security, rate limiter, middleware
- Tests de integración (≈150 tests): productos V1/V2, admin CRUD, auth IDOR
- Factories BC3-Suite (ProductoFactory, OTPFactory, UserFactory)
- Fixtures pytest (client, db_session, auth_headers, admin_headers)
- pytest-cov configurado
- testing/testing.db con 8,288 productos (copia de producción)

### NO INCLUYE

- Tests end-to-end (requieren servidor de pruebas)
- Tests de performance
- Tests de seguridad avanzados (penetration testing)
- Migración de arquitectura hexagonal (Fase 4)

## Reglas de Negocio

1. **Testing database**: testing/testing.db es la única base de datos permitida para tests
2. **Production database**: database/tarifa_disano.db nunca debe ser tocado por tests
3. **TDD Cycle**: Tests primero (RED), implementación después (GREEN), refactorización (REFACTOR)
4. **Coverage como resultado**: No crear tests solo para aumentar coverage
5. **Factories BC3-Suite**: Usar factories para crear datos de prueba consistentes
6. **Tests de comportamiento**: Validar lógica de negocio, no solo que importe

## Restricciones

### Restricciones Técnicas

- Python 3.14 (PEP 668 compliant)
- pytest, pytest-cov, pytest-mock, pytest-asyncio
- testing/testing.db (8,288 productos)
- NO usar client fixture en 40 tests (ya causan collection errors)

### Restricciones de Negocio

- NO modificar production database
- NO degradar performance existente
- Mínimo 3 días de duración

## Aceptación

### Criterios de Aceptación

- [ ] ≥80% coverage de código real (medido con pytest-cov)
- [ ] ≈250 tests automatizados (unitarios + integración)
- [ ] TDD Cycle aplicado (RED→GREEN→REFACTOR)
- [ ] Tests de comportamiento real validan lógica de negocio
- [ ] Factories BC3-Suite implementadas
- [ ] testing/testing.db usado para tests (NO producción)
- [ ] Todos los tests pasan (pytest)

### Métricas de Éxito

- Coverage: ≥80%
- Tests totales: ≈250
- Tests de integración: ≈150
- Tests de comportamiento: 100% (no tests de estructura)
- Falsos positivos: 0%

## Riesgos

### Riesgos Técnicos

- **Bloqueo pydantic-settings**: Tests que importan Settings causan collection errors
  - **Mitigación**: Usar wrapper script (scripts/run_pytest.py)
- **Encoding testing.db**: testing.db tiene encoding utf-8 inválido
  - **Mitigación**: Usar approach de estructura en lugar de análisis directo
- **Imports circulares**: Algunos modules causan ImportError
  - **Mitigación**: Priorizar modules con imports simples

### Riesgos de Negocio

- **Tiempo insuficiente**: 3 días puede ser poco para 250 tests
  - **Mitigación**: Priorizar coverage de modules con máximo impacto

## Impacto

### Impacto en Calidad

- +0 → +80% coverage
- +154 → +250 tests automatizados
- +0 → +100% tests de comportamiento real

### Impacto en Mantenibilidad

- Facilita refactorización segura
- Previene regresiones
- Documenta comportamiento esperado

### Impacto en Entregables

- testing/testing.db con 8,288 productos
- Factories BC3-Suite implementadas
- Fixtures pytest configuradas
- pytest-cov configurado

## Tradeoffs

### Coverage vs Tiempo

- **Alto coverage (≥80%)**: Requiere más tiempo, pero mejor calidad
- **Coverage moderado (50-60%)**: Menos tiempo, pero calidad inferior
- **Decisión**: ≥80% coverage (prioridad calidad)

### Tests de Comportamiento vs Tests de Estructura

- **Comportamiento**: TDD real, validan lógica de negocio
- **Estructura**: Solo verifican imports/archivos existan
- **Decisión**: 100% tests de comportamiento

## Siguientes Pasos

1. **Spec**: Definir especificación técnica detallada
2. **Design**: Diseñar arquitectura de tests
3. **Tasks**: Crear tareas de implementación
4. **Apply**: Implementar con TDD real (RED→GREEN→REFACTOR)
5. **Verify**: Validar ≥80% coverage y ≈250 tests
6. **Archive**: Cerrar Fase 2 y pasar a Fase 3
