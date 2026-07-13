# Task for sdd-spec

Create detailed SDD spec for Fase 3.4-3.5 (Dependency Injection + Testing Migration) based on proposal.

**Context:**
- Proposal accepted: Migrate to Hexagonal Architecture with FastAPI Depends
- Scope: Fase 3.4 (DI setup) + Fase 3.5 (Testing migration)
- Current state: Fase 3.1-3.3 completed (Domain + Infrastructure + Application layers)
- 21/35 tests passing, 68% coverage domain layer

**Requirements from Proposal:**
1. Functional requirements (Fase 3.4.1-3.4.5, Fase 3.5.1-3.5.5)
2. Non-functional requirements (coverage, performance, type safety)
3. Business requirements (BC3 compatibility, zero downtime, rollback)
4. API contracts (endpoint specifications)
5. Data contracts (DTO definitions)
6. Use cases (CQRS operations)
7. Acceptance criteria (granular, testable)
8. Error handling specifications
9. Security requirements
10. Testing requirements

**Inputs to Read:**
- Read proposal.md from openspec/changes/fase3-architecture-hexagonal/
- Read current routers/productos.py for API contract
- Read domain/services/producto.py for business logic
- Read application/dto/producto.py for DTO definitions
- Read tests/unit/domain/ for test patterns

**Output:**
Create `spec.md` with:
1. Functional Requirements (numbered, testable)
2. API Contracts (endpoint specs, request/response)
3. Data Contracts (DTOs, entities, repository interfaces)
4. Use Cases (CQRS: queries and commands)
5. Non-Functional Requirements (performance, coverage, security)
6. Acceptance Criteria (given-when-then format where applicable)
7. Error Handling (HTTP status codes, exception mapping)
8. Testing Requirements (unit, integration, BC3 compatibility)

Do NOT create design.md or tasks.md - this is spec phase only.

Strict TDD compliance: All acceptance criteria must be testable.

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