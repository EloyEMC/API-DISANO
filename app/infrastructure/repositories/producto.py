from datetime import datetime, timedelta, timezone
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.application.dto.bc3_enrichment import (
    BC3_ENRICHMENT_FIELDS,
    hash_bc3_enrichment_items,
)
from app.application.dto.catalog_import import (
    CatalogImportRequest,
    CatalogProductRow,
    canonical_catalog_payload,
    catalog_payload_hash,
    row_to_raw_values,
)
from app.application.services.github_approval import (
    GitHubApprovalEvidence,
    GitHubApprovalReference,
)
from app.domain.entities.producto import ProductoEntity
from app.domain.exceptions.not_found import ProductoNotFoundException
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.infrastructure.cache.pagination_cache import get_pagination_cache
from app.infrastructure.models.catalog_import import (
    CatalogImportRowAuditModel,
    CatalogImportSnapshotModel,
)
from app.infrastructure.models.enrichment import (
    BC3EnrichmentJobItemModel as _BC3EnrichmentJobItemModel,
)
from app.infrastructure.models.enrichment import (
    BC3EnrichmentJobModel as _BC3EnrichmentJobModel,
)
from app.infrastructure.models.enrichment import (
    BC3EnrichmentPreviewItemModel as _BC3EnrichmentPreviewItemModel,
)
from app.infrastructure.models.enrichment import (
    BC3EnrichmentPreviewModel as _BC3EnrichmentPreviewModel,
)
from app.infrastructure.models.producto import ProductoRawModel as _ProductoRawModel
from app.infrastructure.models.producto_clean import (
    ProductoModelClean as _ProductoModel,
)

# These legacy ORM models use untyped SQLAlchemy ``Column`` declarations.
# Keep the repository runtime behavior unchanged while containing that typing debt.
ProductoModel = cast(Any, _ProductoModel)
ProductoRawModel = cast(Any, _ProductoRawModel)
BC3EnrichmentJobItemModel = cast(Any, _BC3EnrichmentJobItemModel)
BC3EnrichmentJobModel = cast(Any, _BC3EnrichmentJobModel)
BC3EnrichmentPreviewModel = cast(Any, _BC3EnrichmentPreviewModel)
BC3EnrichmentPreviewItemModel = cast(Any, _BC3EnrichmentPreviewItemModel)
CatalogImportSnapshot = cast(Any, CatalogImportSnapshotModel)
CatalogImportRowAudit = cast(Any, CatalogImportRowAuditModel)


class SQLAlchemyProductoRepository(ProductoRepositoryInterface):
    """
    SQLAlchemy implementation of Producto repository.

    This class implements the ProductoRepositoryInterface contract
    using SQLAlchemy ORM for database operations. It maps between
    domain entities (ProductoEntity) and database models (ProductoModel).
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_codigo(self, codigo: str) -> ProductoEntity:
        """
        Get product by code.

        Args:
            codigo: Unique product identifier

        Returns:
            ProductoEntity: The found product

        Raises:
            ProductoNotFoundException: If product doesn't exist
        """
        model = self.session.query(ProductoModel).filter(ProductoModel.codigo == codigo).first()

        if not model:
            raise ProductoNotFoundException(codigo)

        return model.to_entity()

    def buscar_productos(
        self,
        termino: str = "",
        limit: int = 10,
        marca: str = "",
        familia: str = "",
    ) -> list[ProductoEntity]:
        """
        Search products with text search and filters.

        Args:
            termino: Search term (searches in description, code, BC3 fields)
            limit: Maximum number of results
            marca: Filter by brand
            familia: Filter by family

        Returns:
            List[ProductoEntity]: Matching products
        """
        query = self.session.query(ProductoModel)

        # Apply text search if term provided
        if termino:
            search_pattern = f"%{termino}%"
            query = query.filter(
                or_(
                    ProductoModel.descripcion.ilike(search_pattern),
                    ProductoModel.codigo.ilike(search_pattern),
                    ProductoModel.descripcion_corta.ilike(search_pattern),
                    ProductoModel.bc3_descripcion_corta.ilike(search_pattern),
                    ProductoModel.bc3_descripcion_completa.ilike(search_pattern),
                    ProductoModel.marca.ilike(search_pattern),
                    ProductoModel.familia.ilike(search_pattern),
                )
            )

        # Apply marca filter if provided
        if marca:
            query = query.filter(ProductoModel.marca == marca)

        # Apply familia filter if provided
        if familia:
            query = query.filter(ProductoModel.familia == familia)

        # Apply limit
        if limit > 0:
            query = query.limit(limit)

        # Convert models to entities
        return [model.to_entity() for model in query.all()]

    def get_all(self, skip: int = 0, limit: int = 100) -> list[ProductoEntity]:
        """
        Get all products with pagination.

        Args:
            skip: Number of products to skip
            limit: Maximum number to return

        Returns:
            List[ProductoEntity]: Products in specified range
        """
        query = (
            self.session.query(ProductoModel)
            .order_by(asc(ProductoModel.codigo))
            .offset(skip)
            .limit(limit)
        )
        return [model.to_entity() for model in query.all()]

    def save(self, producto: ProductoEntity) -> ProductoEntity:
        """
        Save product (create or update).

        Args:
            producto: Product entity to save

        Returns:
            ProductoEntity: Saved product with any DB-generated fields
        """
        # Create model from entity
        model = ProductoModel.from_entity(producto)

        # Use merge to handle both create and update
        self.session.merge(model)
        self.session.flush()  # Flush without commit

        return model.to_entity()

    def delete(self, codigo: str) -> bool:
        """
        Delete product by code.

        Args:
            codigo: Product identifier to delete

        Returns:
            bool: True if deleted, False if not found
        """
        model = self.session.query(ProductoModel).filter(ProductoModel.codigo == codigo).first()

        if not model:
            return False

        self.session.delete(model)
        self.session.flush()

        return True

    def count_total(self) -> int:
        """
        Get total count of products.

        Returns:
            int: Total number of products in database
        """
        return self.session.query(ProductoModel).count()

    def buscar_productos_paginado(self, dto: dict) -> tuple[list[ProductoEntity], int]:
        """Execute paginated query with sorting and filtering.

        This method wraps the actual query with caching logic to improve
        performance for frequently accessed pagination queries.

        Args:
            dto: Complete pagination request DTO with filters and sorting

        Returns:
            Tuple[list[ProductoEntity], int]:
                - List of entities for current page
                - Total count of matching items
        """
        # Get pagination cache wrapper
        cache = get_pagination_cache()

        # Extract parameters for cache key
        page = dto.get("page", 1)
        per_page = dto.get("per_page", 10)
        sort = dto.get("sort")
        filters = dto.get("filters", {})

        # Try to get from cache first
        cached_result = cache.get("productos", page, per_page, sort, filters)
        if cached_result is not None:
            # Convert cached data back to entities
            entities_data = cached_result.get("entities", [])
            total_count = cached_result.get("total", 0)
            entities = [ProductoEntity(**data) for data in entities_data]
            return entities, total_count

        # Cache miss - execute actual query
        entities, total_count = self._execute_pagination_query(dto)

        # Cache the result
        cache_data = {
            "entities": [entity.model_dump() for entity in entities],
            "total": total_count,
        }
        cache.set("productos", page, per_page, sort, filters, cache_data)

        return entities, total_count

    def _execute_pagination_query(self, dto: dict) -> tuple[list[ProductoEntity], int]:
        """Execute the actual pagination query (without caching).

        This is the internal query execution method that can be reused
        by the cached wrapper method.

        Args:
            dto: Complete pagination request DTO with filters and sorting

        Returns:
            Tuple[list[ProductoEntity], int]:
                - List of entities for current page
                - Total count of matching items
        """
        # Base query
        query = self.session.query(ProductoModel)

        # Apply filters
        filters = dto.get("filters", {})
        if filters.get("marca"):
            query = query.filter(ProductoModel.marca == filters["marca"])

        if filters.get("familia"):
            query = query.filter(ProductoModel.familia == filters["familia"])

        if filters.get("pvp_min") is not None:
            query = query.filter(ProductoModel.pvp >= filters["pvp_min"])

        if filters.get("pvp_max") is not None:
            query = query.filter(ProductoModel.pvp <= filters["pvp_max"])

        if filters.get("bc3_product_type"):
            query = query.filter(ProductoModel.bc3_product_type == filters["bc3_product_type"])

        if filters.get("bc3_has_descripcion_corta") is not None:
            if filters["bc3_has_descripcion_corta"]:
                query = query.filter(ProductoModel.bc3_descripcion_corta.isnot(None))
            else:
                query = query.filter(ProductoModel.bc3_descripcion_corta.is_(None))

        if filters.get("buscar"):
            query = self._apply_text_search(query, filters["buscar"])

        # Get total count BEFORE pagination
        total_count = query.count()

        # Apply sorting
        sort_string = dto.get("sort")
        if sort_string:
            query = self._apply_sorting(query, sort_string)

        # Apply pagination
        query = query.offset(dto["offset"]).limit(dto["per_page"])

        # Execute query
        models = query.all()

        # Convert to entities
        entities = [model.to_entity() for model in models]

        return entities, total_count

    def _apply_sorting(self, query, sort_string: str):
        """Apply sorting to query."""
        parts = sort_string.split(":")
        field = parts[0]
        order = parts[1].lower() if len(parts) > 1 else "asc"

        field_mapping = {
            "codigo": ProductoModel.codigo,
            "descripcion": ProductoModel.descripcion,
            "marca": ProductoModel.marca,
            "familia": ProductoModel.familia,
            "pvp": ProductoModel.pvp,
            "bc3_descripcion_corta": ProductoModel.bc3_descripcion_corta,
            "bc3_product_type": ProductoModel.bc3_product_type,
        }

        if field in field_mapping:
            order_func = desc if order == "desc" else asc
            return query.order_by(order_func(field_mapping[field]))

        return query

    def _apply_text_search(self, query, search_pattern: str):
        """Apply text search to query."""
        pattern = f"%{search_pattern}%"
        return query.filter(
            or_(
                ProductoModel.codigo.ilike(pattern),
                ProductoModel.descripcion.ilike(pattern),
                ProductoModel.descripcion_corta.ilike(pattern),
                ProductoModel.bc3_descripcion_corta.ilike(pattern),
                ProductoModel.bc3_descripcion_completa.ilike(pattern),
            )
        )

    def get_private_by_codigo(self, codigo: str) -> ProductoEntity:
        """Read a private BC3 product directly from the raw table."""
        model = (
            self.session.query(ProductoRawModel).filter(ProductoRawModel.codigo == codigo).first()
        )
        if not model:
            raise ProductoNotFoundException(codigo)
        return model.to_entity()

    def create_bc3_preview(
        self,
        items: list[dict],
        actor_id: str,
        source_snapshot_id: str,
        github_pr: GitHubApprovalReference,
    ) -> dict[str, object]:
        """Persist an immutable, expiring compare-and-set snapshot."""
        from app.application.dto.bc3_enrichment import canonicalize_bc3_enrichment_items
        from app.config import get_settings

        now = datetime.now(timezone.utc)
        codes = [item["codigo"] for item in items]
        products = {
            model.codigo: model
            for model in self.session.query(ProductoRawModel)
            .filter(ProductoRawModel.codigo.in_(codes))
            .all()
        }
        preview_id = str(uuid4())
        settings = get_settings()
        approval_mode = getattr(settings, "bc3_approval_mode", "github_review")
        preview = BC3EnrichmentPreviewModel(
            preview_id=preview_id,
            payload_hash=hash_bc3_enrichment_items(items),
            canonical_payload=canonicalize_bc3_enrichment_items(items),
            source_snapshot_id=source_snapshot_id,
            actor_id=actor_id,
            scope=settings.bc3_approval_scope,
            approval_mode=approval_mode,
            status="pending",
            github_repository=github_pr.repository,
            github_pr_number=github_pr.pull_request_number,
            github_head_sha=github_pr.head_sha,
            expires_at=now + timedelta(seconds=settings.bc3_preview_ttl_seconds),
        )
        self.session.add(preview)
        self.session.flush()
        for item in items:
            product = products.get(item["codigo"])
            values = {field: item[field] for field in BC3_ENRICHMENT_FIELDS if field in item}
            current = {field: getattr(product, field) for field in values} if product else {}
            self.session.add(
                BC3EnrichmentPreviewItemModel(
                    preview_id=preview_id,
                    codigo=item["codigo"],
                    current_values=current,
                    proposed_values=values,
                )
            )
        self.session.commit()
        return {
            "preview_id": preview_id,
            "request_hash": preview.payload_hash,
            "expires_at": preview.expires_at,
            "missing_codes": [code for code in codes if code not in products],
            "github_approval_mode": approval_mode,
        }

    def approve_bc3_preview(
        self,
        preview_id: str,
        actor_id: str,
        scope: str,
        github_pr: GitHubApprovalReference,
        evidence: GitHubApprovalEvidence,
    ) -> None:
        """Atomically consume the pending approval state for one actor."""
        with self.session.begin():
            preview = (
                self.session.query(BC3EnrichmentPreviewModel)
                .filter(BC3EnrichmentPreviewModel.preview_id == preview_id)
                .with_for_update()
                .one_or_none()
            )
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if (
                preview is None
                or preview.status != "pending"
                or preview.actor_id != actor_id
                or preview.scope != scope
                or preview.expires_at <= now
                or preview.github_repository != github_pr.repository
                or preview.github_pr_number != github_pr.pull_request_number
                or preview.github_head_sha != github_pr.head_sha
                or preview.source_snapshot_id != github_pr.head_sha
                or (preview.approval_mode or "github_review") != evidence.approval_mode
            ):
                raise ValueError("preview is not eligible for approval")
            preview.status = "approved"
            preview.approved_at = now
            preview.approval_actor_id = actor_id
            preview.approval_mode = evidence.approval_mode
            preview.github_approval_count = evidence.approval_count
            preview.github_approval_verified_at = evidence.verified_at

    def apply_bc3_enrichment(
        self,
        items: list[dict],
        idempotency_key: str,
        preview_id: str,
        actor_id: str,
        github_pr: GitHubApprovalReference,
    ) -> dict[str, object]:
        """Apply only an approved snapshot; all checks precede product writes."""
        from app.config import get_settings

        request_hash = hash_bc3_enrichment_items(items)
        approval_mode = getattr(get_settings(), "bc3_approval_mode", "github_review")
        with self.session.begin():
            preview = (
                self.session.query(BC3EnrichmentPreviewModel)
                .filter(BC3EnrichmentPreviewModel.preview_id == preview_id)
                .with_for_update()
                .one_or_none()
            )
            if (
                preview is None
                or preview.github_repository != github_pr.repository
                or preview.github_pr_number != github_pr.pull_request_number
                or preview.github_head_sha != github_pr.head_sha
                or preview.source_snapshot_id != github_pr.head_sha
                or (preview.approval_mode or "github_review") != approval_mode
            ):
                raise ValueError(
                    "approved preview is invalid, expired, used, or does not match payload"
                )

            existing = (
                self.session.query(BC3EnrichmentJobModel)
                .filter(BC3EnrichmentJobModel.idempotency_key == idempotency_key)
                .with_for_update()
                .first()
            )
            if existing is not None:
                if (
                    existing.request_hash != request_hash
                    or existing.preview_id != preview_id
                    or existing.actor_id != actor_id
                ):
                    raise ValueError(
                        "idempotency key has already been used with a different request"
                    )
                return self._bc3_apply_result(existing)

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if (
                preview is None
                or preview.status != "approved"
                or preview.actor_id != actor_id
                or preview.expires_at <= now
                or preview.payload_hash != request_hash
                or preview.github_repository != github_pr.repository
                or preview.github_pr_number != github_pr.pull_request_number
                or preview.github_head_sha != github_pr.head_sha
                or preview.source_snapshot_id != github_pr.head_sha
            ):
                raise ValueError(
                    "approved preview is invalid, expired, used, or does not match payload"
                )

            snapshots = {
                row.codigo: row
                for row in self.session.query(BC3EnrichmentPreviewItemModel)
                .filter(BC3EnrichmentPreviewItemModel.preview_id == preview_id)
                .all()
            }
            products = {
                model.codigo: model
                for model in self.session.query(ProductoRawModel)
                .filter(ProductoRawModel.codigo.in_(list(snapshots)))
                .with_for_update()
                .all()
            }
            if set(products) != set(snapshots) or any(
                any(
                    getattr(products[codigo], field) != value
                    for field, value in row.current_values.items()
                )
                for codigo, row in snapshots.items()
            ):
                raise ValueError("approved preview snapshot is missing or drifted")

            job = BC3EnrichmentJobModel(
                job_id=str(uuid4()),
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                status="completed",
                total_items=len(items),
                actor_id=actor_id,
                preview_id=preview_id,
                completed_at=now,
            )
            self.session.add(job)
            self.session.flush()
            updated, unchanged = [], []
            for codigo, row in snapshots.items():
                product, before, after = (
                    products[codigo],
                    row.current_values,
                    row.proposed_values,
                )
                changed = before != after
                if changed:
                    for field, value in after.items():
                        setattr(product, field, value)
                    updated.append(codigo)
                else:
                    unchanged.append(codigo)
                self.session.add(
                    BC3EnrichmentJobItemModel(
                        job_id=job.job_id,
                        codigo=codigo,
                        result_status="updated" if changed else "unchanged",
                        before_values=before,
                        after_values=after,
                        **{
                            field: after[field]
                            for field in BC3_ENRICHMENT_FIELDS
                            if field in after and hasattr(BC3EnrichmentJobItemModel, field)
                        },
                    )
                )
            preview.status, preview.used_at = "used", now
            job.updated_items, job.unchanged_items = len(updated), len(unchanged)
            return {
                "updated_codes": updated,
                "unchanged_codes": unchanged,
                "missing_codes": [],
                "job_id": job.job_id,
                "status": job.status,
            }

    def apply_bc3_enrichment_legacy(
        self, items: list[dict], idempotency_key: str
    ) -> dict[str, object]:
        """Apply one idempotent BC3 enrichment transaction."""
        request_hash = hash_bc3_enrichment_items(items)
        with self.session.begin():
            existing = (
                self.session.query(BC3EnrichmentJobModel)
                .filter(BC3EnrichmentJobModel.idempotency_key == idempotency_key)
                .first()
            )
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise ValueError(
                        "idempotency key has already been used with a different request"
                    )
                return self._bc3_apply_result(existing)
            job = BC3EnrichmentJobModel(
                job_id=str(uuid4()),
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                status="running",
                total_items=len(items),
            )
            self.session.add(job)
            self.session.flush()
            products = {
                model.codigo: model
                for model in self.session.query(ProductoRawModel)
                .filter(ProductoRawModel.codigo.in_([item["codigo"] for item in items]))
                .all()
            }
            updated_codes: list[str] = []
            unchanged_codes: list[str] = []
            missing_codes: list[str] = []
            for item in items:
                product = products.get(item["codigo"])
                values = {field: item[field] for field in BC3_ENRICHMENT_FIELDS if field in item}
                if product is None:
                    result_status = "missing"
                    missing_codes.append(item["codigo"])
                else:
                    changed = any(
                        getattr(product, field) != value for field, value in values.items()
                    )
                    if changed:
                        for field, value in values.items():
                            setattr(product, field, value)
                        result_status = "updated"
                        updated_codes.append(item["codigo"])
                    else:
                        result_status = "unchanged"
                        unchanged_codes.append(item["codigo"])
                self.session.add(
                    BC3EnrichmentJobItemModel(
                        job_id=job.job_id,
                        codigo=item["codigo"],
                        result_status=result_status,
                        **values,
                    )
                )
            job.status = "completed"
            job.updated_items = len(updated_codes)
            job.unchanged_items = len(unchanged_codes)
            job.missing_items = len(missing_codes)
            job.completed_at = datetime.now(timezone.utc)
            self.session.flush()
            return {
                "updated_codes": updated_codes,
                "unchanged_codes": unchanged_codes,
                "missing_codes": missing_codes,
                "job_id": job.job_id,
                "status": job.status,
            }

    def _bc3_apply_result(self, job: Any) -> dict[str, object]:
        items = (
            self.session.query(BC3EnrichmentJobItemModel)
            .filter(BC3EnrichmentJobItemModel.job_id == job.job_id)
            .order_by(BC3EnrichmentJobItemModel.id.asc())
            .all()
        )
        return {
            "updated_codes": [item.codigo for item in items if item.result_status == "updated"],
            "unchanged_codes": [item.codigo for item in items if item.result_status == "unchanged"],
            "missing_codes": [item.codigo for item in items if item.result_status == "missing"],
            "job_id": job.job_id,
            "status": job.status,
        }

    def get_bc3_enrichment_job_status(self, job_id: str) -> dict[str, object] | None:
        """Return the persisted status projection for an enrichment job."""
        job = (
            self.session.query(BC3EnrichmentJobModel)
            .filter(BC3EnrichmentJobModel.job_id == job_id)
            .first()
        )
        if job is None:
            return None
        items = (
            self.session.query(BC3EnrichmentJobItemModel)
            .filter(BC3EnrichmentJobItemModel.job_id == job_id)
            .order_by(BC3EnrichmentJobItemModel.codigo.asc())
            .all()
        )
        return {
            "job_id": cast(str, job.job_id),
            "status": cast(str, job.status),
            "total_items": cast(int, job.total_items),
            "updated_items": cast(int, job.updated_items),
            "unchanged_items": cast(int, job.unchanged_items),
            "missing_items": cast(int, job.missing_items),
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "items": [
                {
                    "codigo": cast(str, item.codigo),
                    "result_status": cast(str, item.result_status),
                    "error_message": cast(str | None, item.error_message),
                }
                for item in items
            ],
        }

    def existing_catalog_codes(self, codes: list[str]) -> set[str]:
        """Return raw product codes already present in the catalog."""
        if not codes:
            return set()
        return {
            row.codigo
            for row in self.session.query(ProductoRawModel.codigo)
            .filter(ProductoRawModel.codigo.in_(codes))
            .all()
        }

    def catalog_import_preview(
        self,
        *,
        snapshot_id: str,
        actor_id: str,
        request: CatalogImportRequest,
        accepted: list[CatalogProductRow],
        rejected: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Persist a catalog import preview and its row audit records."""
        from app.config import get_settings

        approval_mode = getattr(get_settings(), "bc3_approval_mode", "github_review")
        snapshot = CatalogImportSnapshot(
            snapshot_id=snapshot_id,
            idempotency_key=f"preview:{snapshot_id}",
            source_snapshot_id=request.source_snapshot_id,
            source_hash=request.source_hash,
            payload_hash=catalog_payload_hash(request.rows),
            canonical_payload=canonical_catalog_payload(request.rows),
            actor_id=actor_id,
            approval_mode=approval_mode,
            status="pending",
            github_repository=request.github_pr.repository,
            github_pr_number=request.github_pr.pull_request_number,
            github_head_sha=request.github_pr.head_sha,
        )
        self.session.add(snapshot)
        self.session.flush()
        for row in accepted:
            self.session.add(
                CatalogImportRowAudit(
                    snapshot_id=snapshot_id,
                    code=row.code,
                    result_status="accepted",
                    after_values=row.model_dump(mode="json"),
                )
            )
        for item in rejected:
            self.session.add(
                CatalogImportRowAudit(
                    snapshot_id=snapshot_id,
                    code=item["code"],
                    result_status="rejected",
                    reason=item["reason"],
                )
            )
        self.session.commit()
        return {
            "snapshot_id": snapshot_id,
            "status": "pending",
            "payload_hash": snapshot.payload_hash,
            "source_hash": request.source_hash,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "github_approval_mode": approval_mode,
        }

    def catalog_import_approve(
        self,
        snapshot_id: str,
        actor_id: str,
        github_pr: GitHubApprovalReference,
        evidence: GitHubApprovalEvidence,
    ) -> None:
        """Persist verified approval evidence for a catalog snapshot."""
        with self.session.begin():
            snapshot = (
                self.session.query(CatalogImportSnapshot)
                .filter_by(snapshot_id=snapshot_id)
                .with_for_update()
                .one_or_none()
            )
            if (
                snapshot is None
                or snapshot.status != "pending"
                or snapshot.actor_id != actor_id
                or snapshot.github_repository != github_pr.repository
                or snapshot.github_pr_number != github_pr.pull_request_number
                or snapshot.github_head_sha != github_pr.head_sha
                or (snapshot.approval_mode or "github_review") != evidence.approval_mode
            ):
                raise ValueError("catalog import snapshot is not eligible for approval")
            snapshot.status = "approved"
            snapshot.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            snapshot.approval_mode = evidence.approval_mode
            snapshot.github_approval_count = evidence.approval_count
            snapshot.github_approval_verified_at = evidence.verified_at.replace(tzinfo=None)

    def catalog_import_apply(
        self,
        *,
        snapshot_id: str,
        actor_id: str,
        request: CatalogImportRequest,
        idempotency_key: str,
        expected_payload_hash: str,
    ) -> dict[str, Any]:
        """Apply an approved catalog snapshot idempotently."""
        from app.config import get_settings

        approval_mode = getattr(get_settings(), "bc3_approval_mode", "github_review")
        with self.session.begin():
            prior = (
                self.session.query(CatalogImportSnapshot)
                .filter_by(idempotency_key=idempotency_key)
                .with_for_update()
                .one_or_none()
            )
            if prior is not None:
                if (
                    prior.snapshot_id != snapshot_id
                    or prior.payload_hash != expected_payload_hash
                    or prior.actor_id != actor_id
                    or (prior.approval_mode or "github_review") != approval_mode
                ):
                    raise ValueError(
                        "idempotency key has already been used with a different request"
                    )
                created = [
                    audit.code
                    for audit in self.session.query(CatalogImportRowAudit)
                    .filter_by(snapshot_id=snapshot_id, result_status="created")
                    .all()
                ]
                rejected = [
                    audit.code
                    for audit in self.session.query(CatalogImportRowAudit)
                    .filter_by(snapshot_id=snapshot_id, result_status="rejected")
                    .all()
                ]
                return {
                    "snapshot_id": snapshot_id,
                    "status": "completed",
                    "created_codes": created,
                    "rejected_codes": rejected,
                }
            snapshot = (
                self.session.query(CatalogImportSnapshot)
                .filter_by(snapshot_id=snapshot_id)
                .with_for_update()
                .one_or_none()
            )
            if (
                snapshot is None
                or (snapshot.approval_mode or "github_review") != approval_mode
                or snapshot.status != "approved"
                or snapshot.actor_id != actor_id
                or snapshot.payload_hash != expected_payload_hash
                or snapshot.source_hash != request.source_hash
                or snapshot.github_repository != request.github_pr.repository
                or snapshot.github_pr_number != request.github_pr.pull_request_number
                or snapshot.github_head_sha != request.github_pr.head_sha
            ):
                raise ValueError(
                    "approved catalog import snapshot is invalid or does not match request"
                )
            accepted = [
                row
                for row in request.rows
                if row.code
                in {
                    audit.code
                    for audit in self.session.query(CatalogImportRowAudit)
                    .filter_by(snapshot_id=snapshot_id, result_status="accepted")
                    .all()
                }
            ]
            current = self.existing_catalog_codes([row.code for row in accepted])
            if current:
                raise ValueError("approved catalog import snapshot has drifted existing codes")
            created: list[str] = []
            for row in accepted:
                values = row_to_raw_values(row)
                self.session.add(ProductoRawModel(**values))
                audit = (
                    self.session.query(CatalogImportRowAudit)
                    .filter_by(snapshot_id=snapshot_id, code=row.code, result_status="accepted")
                    .one()
                )
                audit.result_status = "created"
                audit.before_values = {}
                audit.after_values = row.model_dump(mode="json")
                created.append(row.code)
            snapshot.idempotency_key = idempotency_key
            snapshot.status = "used"
            snapshot.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
            return {
                "snapshot_id": snapshot_id,
                "status": "completed",
                "created_codes": created,
                "rejected_codes": [
                    a.code
                    for a in self.session.query(CatalogImportRowAudit)
                    .filter_by(snapshot_id=snapshot_id, result_status="rejected")
                    .all()
                ],
            }

    def buscar_productos_privado(self, dto: dict) -> tuple[list[ProductoEntity], int]:
        """Paginate private BC3 products from the raw ``productos`` table."""

        query = self.session.query(ProductoRawModel)
        filters = dto.get("filters", {})
        if filters.get("marca"):
            query = query.filter(ProductoRawModel.marca == filters["marca"])
        if filters.get("familia"):
            query = query.filter(ProductoRawModel.familia_web == filters["familia"])
        if filters.get("buscar"):
            pattern = f"%{filters['buscar']}%"
            query = query.filter(
                or_(
                    ProductoRawModel.codigo.ilike(pattern),
                    ProductoRawModel.descripcion.ilike(pattern),
                    ProductoRawModel.marca.ilike(pattern),
                    ProductoRawModel.familia_web.ilike(pattern),
                    ProductoRawModel.bc3_descripcion_corta.ilike(pattern),
                )
            )

        total_count = query.count()
        models = query.offset(dto["offset"]).limit(dto["per_page"]).all()
        return [model.to_entity() for model in models], total_count

    def get_private_by_codigos(self, codigos: list[str]) -> dict[str, ProductoEntity]:
        """Read the requested BC3 products without mutating the session."""
        if not codigos:
            return {}
        models = (
            self.session.query(ProductoRawModel).filter(ProductoRawModel.codigo.in_(codigos)).all()
        )
        return {model.codigo: model.to_entity() for model in models}
