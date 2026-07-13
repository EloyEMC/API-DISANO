# Task for sdd-design

Create detailed SDD design for Fase 3.4-3.5 (DI + Testing) based on spec.

**Design Goals:**
- Hexagonal architecture with FastAPI Depends DI
- Clear separation of concerns
- TDD-friendly patterns
- BC3 Suite compatibility
- Performance optimization

**Design Areas Required:**

1. **Architecture Diagram**
   - Three-layer structure (Domain, Infrastructure, Application/Interfaces)
   - Component relationships
   - Data flow from HTTP to Database
   - Dependency injection points

2. **Component Responsibilities**
   - Domain Layer: Entities, Services, Repository Interfaces, Exceptions
   - Infrastructure Layer: Database Connection, Repositories, ORM Models
   - Application Layer: DTOs, Use Cases
   - Interfaces Layer: HTTP Routers, Dependency Functions

3. **Design Patterns**
   - Repository Pattern (abstraction)
   - Dependency Injection (FastAPI Depends)
   - DTO Pattern (data transfer)
   - Service Layer Pattern (business logic)
   - CQRS (Command Query Responsibility Segregation)

4. **Data Flow**
   - HTTP Request → FastAPI Depends → Service → Repository → Database → Response
   - Error flow: Exceptions → HTTP Status Codes → Error Responses
   - Validation flow: Pydantic → Business Rules → Repository Constraints

5. **Technical Decisions**
   - FastAPI Depends vs dependency-injector vs custom DI (justify choice)
   - Database session management (scoped sessions vs per-request)
   - Error handling strategy (exception mapping)
   - Testing strategy (mocks, fixtures, integration)

6. **Trade-offs Analysis**
   - Pros/cons of design decisions
   - Alternative approaches considered
   - Risks and mitigations

7. **Implementation Guidance**
   - File structure for interfaces/http/
   - DI setup in main.py
   - Router migration patterns
   - Test fixture patterns
   - BC3 compatibility notes

**Inputs to Read:**
- Read spec.md from openspec/changes/fase3-architecture-hexagonal/
- Read explore.md for context and risks
- Read existing domain/infrastructure/application code
- Read current routers/productos.py for migration patterns

**Output:**
Create `design.md` with detailed technical design following the areas above.

Do NOT create tasks.md - this is design phase only.

Focus on clarity and implementability. The design should enable any developer to implement the solution without questions.

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