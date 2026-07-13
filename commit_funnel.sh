#!/bin/bash
# Commit solo los archivos nuevos del funnel

echo "Archivos nuevos del funnel:"
echo "============================="
ls -1 app/blueprints/presupuesto/routes/funnel_routes.py \
       app/database/models/presupuesto_estado_history.py \
       app/repositories/presupuesto_estado_history_repository.py \
       app/services/presupuesto/funnel_service.py \
       app/schemas/funnel.py \
       migrations/versions/20260609_add_presupuesto_estado_history.py \
       tests/integration/blueprints/test_funnel_routes.py \
       tests/unit/domain/test_estado_change.py \
       tests/unit/domain/test_estado_value_object.py \
       tests/unit/repositories/test_presupuesto_repository_funnel.py \
       tests/unit/repositories/test_presupuesto_estado_history_repository.py \
       tests/unit/schemas/test_funnel_schemas.py \
       tests/unit/services/test_funnel_service.py

echo ""
echo "¿Quieres hacer commit de SOLO estos archivos? (s/n)"
read -r respuesta

if [ "$respuesta" = "s" ]; then
  git add \
    app/blueprints/presupuesto/routes/funnel_routes.py \
    app/database/models/presupuesto_estado_history.py \
    app/repositories/presupuesto_estado_history_repository.py \
    app/services/presupuesto/funnel_service.py \
    app/schemas/funnel.py \
    migrations/versions/20260609_add_presupuesto_estado_history.py \
    tests/integration/blueprints/test_funnel_routes.py \
    tests/unit/domain/test_estado_change.py \
    tests/unit/domain/test_estado_value_object.py \
    tests/unit/repositories/test_presupuesto_repository_funnel.py \
    tests/unit/repositories/test_presupuesto_estado_history_repository.py \
    tests/unit/schemas/test_funnel_schemas.py \
    tests/unit/services/test_funnel_service.py
  
  echo "Staged files:"
  git status --short
  
  echo ""
  echo "Commit message sugerido:"
  echo "feat: add sales funnel visual endpoint with RBAC"
  echo ""
  echo "¿Hacer commit con este mensaje? (s/n)"
  read -r confirmar
  
  if [ "$confirmar" = "s" ]; then
    git commit -m "feat: add sales funnel visual endpoint with RBAC

- Add GET /api/v1/presupuestos/funnel endpoint
- Implement RBAC filtering (admin, sales, coordinator)
- Add state history tracking table and repository
- Add funnel metrics aggregation in repository layer
- Add Pydantic schemas for request/response validation
- Add 23 tests (unit + integration) with 100% passing
- Update documentation (README, API contracts)
- Follow strict TDD methodology (RED → GREEN → TRIANGULATE → REFACTOR)
- Clean architecture: Blueprint → Service → Repository → Database

Files:
- app/blueprints/presupuesto/routes/funnel_routes.py
- app/services/presupuesto/funnel_service.py
- app/schemas/funnel.py
- app/repositories/presupuesto_estado_history_repository.py
- app/repositories/presupuesto.py (extended)
- migrations/versions/20260609_add_presupuesto_estado_history.py
- tests/unit/schemas/test_funnel_schemas.py
- tests/unit/repositories/test_presupuesto_repository_funnel.py
- tests/unit/services/test_funnel_service.py
- tests/integration/blueprints/test_funnel_routes.py"
    
    echo "✅ Commit realizado"
    echo ""
    echo "¿Quieres hacer push a origin/main? (s/n)"
    read -r push
    
    if [ "$push" = "s" ]; then
      git push origin main
      echo "✅ Push realizado"
    fi
  fi
fi

