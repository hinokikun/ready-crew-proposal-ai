from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import require_roles
from app.db import get_db
from app.models import ReleasePublishRequest, ReleaseRecordCreateRequest, ReleaseRecordUpdateRequest
from app.releases import create_release_record, list_releases, publish_release_record, update_release_record

router = APIRouter(prefix="/api/releases", tags=["releases"])


@router.get("")
async def get_releases(
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return {"releases": list_releases(db, str(user["role"]), limit)}


@router.post("")
async def post_release(payload: ReleaseRecordCreateRequest, user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        release = create_release_record(db, int(user["id"]), payload.dict())
    return {"ok": True, "release": release}


@router.patch("/{release_id}")
async def patch_release(
    release_id: int,
    payload: ReleaseRecordUpdateRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    update_payload = payload.dict(exclude_unset=True)
    with get_db() as db:
        release = update_release_record(db, release_id, int(user["id"]), update_payload)
    if not release:
        raise HTTPException(status_code=404, detail="リリース記録が見つかりません。")
    return {"ok": True, "release": release}


@router.post("/{release_id}/publish")
async def post_release_publish(
    release_id: int,
    payload: ReleasePublishRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        release = publish_release_record(db, release_id, int(user["id"]), payload.comment)
    if not release:
        raise HTTPException(status_code=404, detail="リリース記録が見つかりません。")
    return {"ok": True, "release": release}
