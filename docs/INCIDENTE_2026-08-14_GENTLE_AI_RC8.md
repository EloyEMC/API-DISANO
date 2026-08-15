# Incidente: bloqueo de review con Gentle AI y comparación RC8

**Fecha:** 2026-08-14

**Proyecto:** API-DISANO

**Issue upstream:** [gentle-pi#264](https://github.com/Gentleman-Programming/gentle-pi/issues/264)

## Resumen ejecutivo

Gentle AI `2.4.0-rc.8` corrige el bloqueo de transporte immutable cuando el review se ejecuta con el runtime **Codex**, pero no cuando se declara el runtime **Pi**.

El candidato staged de API-DISANO fue reconocido correctamente con Codex y alcanzó el estado `reviewer_results_required`. No se fabricaron resultados ni se creó un receipt manualmente.

## Entorno

- Sistema: Darwin arm64
- Gentle AI probado: `2.4.0-rc.8`
- Gentle AI previo: `2.4.0-rc.7`
- Pi: `0.84.2`
- Codex CLI: `0.147.0`
- Candidato: 3 archivos staged, 208 líneas añadidas
- SHA256 del binario RC8 Darwin arm64: `435c228f2d011c5df7ef134c493fa42370a4c241aa9e188c051bb2e3e7aecc55`

## Resultados

### Runtime Pi

Comando:

```text
gentle-ai review status --cwd <repo> --contract gentle-ai.review-integration/v2 --agent pi --next-transition
```

Resultado:

```text
phase: preflight
code: immutable_review_transport_unsupported
mutation_outcome: not_started
authority_applicability: not_evaluated
retry_safe: false
replayability: not_replayable
next_action: stop
```

Conclusión: RC8 mantiene el bloqueo cuando el runtime es Pi. El flujo se detiene antes de autoridad, START, consentimiento, lenses y receipt.

### Runtime Codex

Comando equivalente para el candidato staged:

```text
gentle-ai review status --cwd <repo> \
  --contract gentle-ai.review-integration/v2 \
  --agent codex \
  --projection staged \
  --gate pre-commit \
  --next-transition
```

Resultado relevante:

```text
action: finalize
forecast: reviewer_results_required
lineage_id: review-928e62404369ea59
receipt: expected_missing
projection: staged
original_changed_lines: 208
```

Conclusión: RC8 supera el bloqueo de transporte immutable con Codex, conserva el lineage existente y reconoce exactamente los tres archivos staged.

## Comparación con el error anterior

Con Gentle AI `2.3.0` y Pi `0.84.1`, el error ocurría en `answer-consent`: el binding devuelto era rechazado como desconocido, expirado o consumido. No se creaba lineage ni receipt.

Con RC8 + Pi, el error cambió a un rechazo temprano de capacidad: `immutable_review_transport_unsupported`.

Con RC8 + Codex, ese rechazo desaparece. El bloqueo restante es legítimo: faltan reviewer artifacts reales para finalizar.

## Estado de seguridad

- No se fabricaron reviewer results.
- No se fabricó ningún receipt o autorización.
- No se ejecutó un bypass del gate.
- No se creó commit ni push.
- El staging de API-DISANO permanece intacto.
- Tests focalizados del schema/enrichment: 25 passed.
- Tests focalizados de backup local: 13 passed.

## Próximo paso

Ejecutar el review completo desde el runtime Codex y capturar los reviewer artifacts mediante el transporte nativo de RC8. La captura debe realizarse con el binding, lineage, target, revision y lens que devuelva STATUS. No se deben reutilizar ni inventar tokens de Pi.

## Referencias

- [Issue upstream #264](https://github.com/Gentleman-Programming/gentle-pi/issues/264)
- [Reporte de reproducción RC8](https://github.com/Gentleman-Programming/gentle-pi/issues/264#issuecomment-5294241893)
- [Gentle AI v2.4.0-rc.8](https://github.com/Gentleman-Programming/gentle-ai/releases/tag/v2.4.0-rc.8)
