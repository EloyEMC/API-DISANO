# Task for sdd-apply

Implement Fase 3.4-3.5 Architecture Hexagonal Migration following SDD workflow with strict TDD.

**Context:**
- SDD artifacts completed: explore.md, proposal.md, spec.md, design.md, tasks.md
- 10 tasks to implement (13.5 hours total)
- Strict TDD methodology: RED → GREEN → REFACTOR for each task
- Change ID: fase3-architecture-hexagonal
- Artifact Store: openspec (file-based)

**Tasks to Execute (from tasks.md):**

**Phase 3.4: DI Setup (6.5 hours)**
1. TASK-3.4.1: DI Configuration in main.py (30 min)
2. TASK-3.4.2: HTTP Interface Layer Created (2 hours)
3. TASK-3.4.3: V2 Endpoints Migrated (2 hours)
4. TASK-3.4.4: V1 Backward Compatibility (1 hour)
5. TASK-3.4.5: BC3 Suite Compatibility (1 hour)

**Phase 3.5: Testing Migration (7 hours)**
6. TASK-3.5.1: Service Tests Fixing (1 hour)
7. TASK-3.5.2: Coverage Maintenance (2 hours)
8. TASK-3.5.3: Integration Tests for DI Flow (2 hours)
9. TASK-3.5.4: Performance Testing (1 hour)
10. TASK-3.5.5: Type Safety (1 hour)

**Execution Order:**
- Phase 3.4: Complete sequentially (3.4.1 → 3.4.2 → 3.4.3 → 3.4.4 → 3.4.5)
- Phase 3.5: Can run 3.5.1 + 3.5.2 + 3.5.5 in parallel
- Must run 3.5.3 + 3.5.4 after Phase 3.4 complete

**TDD Compliance Requirements:**
1. **RED Phase:** Write FAILING tests before implementation
2. **GREEN Phase:** Implement minimal code to make tests pass
3. **REFACTOR Phase:** Improve code while tests remain passing
4. **Evidence:** Git commits show test-first approach
5. **No Implementation Without Tests:** All code must have tests first

**Acceptance Criteria (from tasks.md):**
Each task has specific acceptance criteria. All must be satisfied before marking tasks complete.

**Output:**
Update apply-progress artifact at openspec/changes/fase3-architecture-hexagonal/apply-progress.md with:
- Tasks completed (checkboxes)
- Time spent per task
- Issues encountered
- Evidence of TDD compliance
- Total time spent

**Strict TDD Mode:**
This project has strict TDD mode enabled. Follow RED → GREEN → REFACTOR cycle for every task. No shortcuts.

**Files to Read:**
- openspec/changes/fase3-architecture-hexagonal/tasks.md (detailed tasks)
- openspec/changes/fase3-architecture-hexagonal/spec.md (acceptance criteria)
- openspec/changes/fase3-architecture-hexagonal/design.md (technical guidance)

**Action Plan:**
1. Read tasks.md to understand all 10 tasks
2. Execute Phase 3.4 tasks sequentially (3.4.1 → 3.4.2 → 3.4.3 → 3.4.4 → 3.4.5)
3. Execute Phase 3.5 tasks in batches
4. Update apply-progress.md with completion status
5. Return completion report with time spent and issues encountered

**DO NOT skip TDD steps.** This is strict TDD mode.

IMPORTANT: This is apply phase, NOT design or spec. All artifacts already exist. Follow the tasks.md implementation plan exactly.

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