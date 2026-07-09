# Security Model — 3-Tier RBAC and IDOR Closure

> **Status**: Authoritative reference. Last updated 2026-06-23 (v0.9.8).
> **Scope**: Authorization and visibility for the `presupuesto` domain.
> **Related**: `app/domain/presupuesto/visibility.py`,
> `openspec/changes/foundation-realignment/w1-idor-matrix.md`.

## 1. Motivation

BC3-Suite is an internal CRM for a sales team organized into geographic
**zones**. Each commercial creates and owns `presupuestos` (budgets). A
**coordinator** oversees a zone and must read every presupuesto in it; an
**administrator** must read and act on all of them. The original implementation
enforced ownership with a single SQL clause, `presupuesto.usuario_id == caller`,
which has no concept of zone. The result was a CRITICAL IDOR (Insecure Direct
Object Reference, audit item A4.1):

- coordinators were **wrongly denied** read on zone-mates' presupuestos
  (functional bug), and
- several handlers returned HTTP **403** on denial, leaking the existence of a
  presupuesto the caller should not know about (information disclosure).

This document captures the model that closed A4.1 across all 16 live
presupuesto-scoped handlers in release 0.9.8.

## 2. The 3-tier RBAC model

Authorization is role-based with three tiers. The "coordinator" is **not** a
top-level role; it is a per-zone sub-role expressed through `rol_en_zona`.

| Tier        | Condition                                              | Sees                          | Mutates |
| ----------- | ------------------------------------------------------ | ----------------------------- | ------- |
| Admin       | `user.role in {"super_admin", "admin"}`                | all presupuestos              | all     |
| Coordinator | `user.rol_en_zona == "coordinador" AND user.zona_id`   | zone-mates' + own             | own only¹ |
| Sales       | otherwise (pure sales, or coordinator without zone)    | own only                      | own     |

¹ W1 grants coordinators **read** on zone-mates. Coordinator **mutate**
(write/delete/estado) on zone-mates is deliberately own-only. Extending
coordinator mutate to zone-mates is a separate product decision, documented as
a follow-up; it is **not** a security regression.

The coordinator check **must precede** the sales check in code. A coordinator
has `role="sales"` at the top level; checking `role == "sales"` first would
swallow coordinators into own-only visibility. See `visibility.py`.

## 3. The canonical API

`app/domain/presupuesto/visibility.py` exposes two functions. Every
presupuesto-scoped handler calls exactly one of them.

```python
def can_access_presupuesto(user: User, presupuesto: Presupuesto) -> bool: ...

def can_access_presupuesto_by_id(
    db_session, user: User, presupuesto_id: int
) -> tuple[bool, Presupuesto | None]: ...
```

`can_access_presupuesto_by_id` is a convenience wrapper: it loads the
presupuesto (returning `(False, None)` if missing) and returns the loaded
object alongside the access boolean, so the handler avoids a second DB call.

### Denial contract

Denied access returns **HTTP 404**, never 403. A 404 hides the existence of
the resource; a 403 confirms it. This is uniform across every handler after
W1-C5. Pre-W1, two handlers returned 403 (`export/pdf`, `enviar-con-seguimiento`);
both were normalized to 404.

## 4. Where the check lives

**At the route, never at the service.** Routes call
`can_access_presupuesto[_by_id]` before touching the service. Services trust
the caller. This is the opposite of the pre-W1 design, where some services had
a naive `usuario_id != caller` check that the route bypassed. Mixing the two
layers produced contradictions for non-sales roles (obs 1467).

The single-writer principle applies: there is exactly one authorization
decision per handler, at the route boundary.

## 5. The 19-handler matrix

Every presupuesto-scoped route handler was enumerated empirically from
`app/blueprints/presupuesto/routes/`. The full matrix — file:handler × action ×
role → expected HTTP code — lives in
`openspec/changes/foundation-realignment/w1-idor-matrix.md`. Summary:

| Category                          | Count | Status                                   |
| --------------------------------- | ----- | ---------------------------------------- |
| Handlers enforcing `can_access`   | 16    | all green, 404 on denial                 |
| Dead code (duplicate `estado`)    | 1     | `presupuesto_crud.py` never imported     |
| Out of scope (session-based)      | 1     | `add-fichas` operates on browser session |
| Collection route (listar)         | 1     | repo-level visibility (W1-C2)            |

**Zero live presupuesto-scoped handlers use the naive `usuario_id != caller`
check.** The grep-verify in the matrix file confirms it; the only remaining
`usuario_id !=` matches are comments, the dead duplicate, and the
`Template`-domain check in `templates.py` (a different model with its own
`is_shared` flag).

## 6. Dual-path feature flags

`tracking.py` and `presupuesto_tracking.py` carry `if USE_SPECIFICATION_PATTERN`
branches. In production `USE_SPECIFICATION_PATTERN = False`, so only the
`else` (inline) branch executes. W1-C4b/C5 fixed the inline branch; the spec
branch retains the naive anti-pattern but is dead code. If the flag is ever
enabled, the spec branch needs the same `can_access` fix.

## 7. Test coverage

`tests/integration/auth/test_presupuesto_idor.py` holds 42 negative-authorization
tests across five classes:

| Class                                  | Covers                       | Wave |
| -------------------------------------- | ---------------------------- | ---- |
| `TestPresupuestoIdorSalesToSales`      | create / get / delete / estado | earlier |
| `TestPresupuestoListarVisibility`      | list (zone + own)            | W1-C2 |
| `TestPresupuestoPointMutationVisibility` | clone / load / template     | W1-C4a |
| `TestPresupuestoTrackingVisibility`    | seguimientos × 4             | W1-C4b |
| `TestPresupuestoNaiveHandlerVisibility` | detalle / pdf-preview / export-pdf / cleanup / enviar-seguimiento | W1-C5 |

The matrix's role×action grid has a green test on every red cell.

## 8. Production footprint (as of 0.9.8)

33 users: 4 pure super-admin, 1 super-admin with `rol_en_zona=coordinador`,
28 pure sales. **Zero pure coordinators exist**, so the coordinator branch is
exercised by tests but latent in production until a user with
`role="sales" + rol_en_zona="coordinador" + zona_id` is assigned. The IDOR
closure is live and correct regardless of current data shape.

Only 2 presupuestos exist in production, both owned by a single super-admin.
The A4.1 IDOR had a small blast radius given this data, but the authorization
bypass was real and is now closed.

## 9. Forward

The model is intentionally minimal: three tiers, one check site (route), one
denial code (404). Open items tracked outside this document:

- **Wave Auth/2FA** (planned): adds email-OTP second factor; does **not** change
  the 3-tier model, only the authentication step preceding it.
- **W2**: non-IDOR HIGHs (H1–H9) from the original audit.
- **Coordinator mutate on zone-mates**: a product decision, not a security fix.
