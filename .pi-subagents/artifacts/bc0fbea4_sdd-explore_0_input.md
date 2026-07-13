# Task for sdd-explore

Explorar migración a Architecture Hexagonal para API-DISANO Fase 3.

Contexto:
- Fase 3.1 (Domain Layer): COMPLETADA - ProductoEntity, ProductoRepositoryInterface, exceptions
- Fase 3.2 (Infrastructure Layer): COMPLETADA - SQLAlchemy 2.0.51, ProductoModelClean, database connection
- Fase 3.3 (Application Layer): COMPLETADA - DTOs (ProductoCreateDTO, etc.), ProductoService con business logic
- Fase 3.4 (Dependency Injection): PENDIENTE - Configurar DI en FastAPI main.py
- Fase 3.5 (Testing Migration): PENDIENTE - Adaptar tests a hexagonal architecture

Task:
1. Analizar estructura actual de app/main.py (FastAPI setup, routers, dependencies)
2. Revisar archivos creados en Fase 3.1-3.3 (app/domain/, app/infrastructure/, app/application/)
3. Explorar estrategia DI: usar FastAPI Depends vs contenedor DI (dependency-injector)
4. Identificar routers a migrar: productos.py, familias.py, bc3.py
5. Analizar compatibilidad BC3 Suite durante migration
6. Identificar risks: backward compatibility V1 endpoints, database migration, deployment

Output:
- Estructura actual main.py (routers, includes, middleware)
- Lista archivos hexagonal creados + estado
- Opciones DI recomendadas (pros/contras)
- Lista routers a migrar con prioridad
- BC3 Suite compatibility notes
- Risks y mitigations
- Recomendación: FastAPI Depends vs contenedor DI vs custom setup

NO crear archivos, solo exploración y análisis.

## Acceptance Contract
Acceptance level: reviewed
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Implement the requested change without widening scope
- criterion-2: Return evidence sufficient for an independent acceptance review

Required evidence: changed-files, tests-added, commands-run, validation-output, residual-risks, no-staged-files

Review gate: required by reviewer.

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```