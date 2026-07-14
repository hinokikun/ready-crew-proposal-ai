from fastapi import APIRouter, Depends

from app.auth import require_roles
from app.db import get_db
from app.models import OrganizationCreateRequest, WorkspaceContextSwitchRequest, WorkspaceCreateRequest, WorkspaceMembershipRequest
from app.organization import add_user_to_workspace, create_organization, create_workspace, list_user_contexts, switch_workspace_context
from app.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("/context")
async def get_context(user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return list_user_contexts(db, user)


@router.patch("/context")
async def patch_context(
    payload: WorkspaceContextSwitchRequest,
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return {"current": switch_workspace_context(db, user=user, organization_id=payload.organization_id, workspace_id=payload.workspace_id)}


@router.post("", dependencies=[Depends(rate_limit_dependency("admin"))])
async def post_organization(payload: OrganizationCreateRequest, user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        organization = create_organization(db, name=payload.name, slug=payload.slug, created_by=int(user["id"]))
        return {"organization": organization}


@router.post("/{organization_id}/workspaces", dependencies=[Depends(rate_limit_dependency("admin"))])
async def post_workspace(
    organization_id: int,
    payload: WorkspaceCreateRequest,
    user: dict = Depends(require_roles("admin")),
) -> dict:
    with get_db() as db:
        workspace = create_workspace(db, organization_id=organization_id, name=payload.name, slug=payload.slug, created_by=int(user["id"]))
        return {"workspace": workspace}


@router.post("/memberships", dependencies=[Depends(rate_limit_dependency("admin"))])
async def post_membership(payload: WorkspaceMembershipRequest, user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        membership = add_user_to_workspace(
            db,
            user_id=payload.user_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            membership_role=payload.membership_role,
            actor_id=int(user["id"]),
        )
        return {"membership": membership}
