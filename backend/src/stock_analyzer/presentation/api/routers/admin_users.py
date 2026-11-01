"""Admin > Users: invite codes, users, audit log."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from stock_analyzer.bootstrap import Container
from stock_analyzer.presentation.api.dependencies import CurrentAdmin, get_container
from stock_analyzer.presentation.api.schemas.auth import (
    AuditEntryResponse,
    CreateInviteBody,
    InviteResponse,
    MeResponse,
    SetDisabledBody,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.post(
    "/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invite code",
)
async def create_invite(
    body: CreateInviteBody, admin: CurrentAdmin, container: ContainerDep
) -> InviteResponse:
    """A new shareable code (default: 1 use, 7 days, role user)."""
    invite = await container.user_admin.create_invite(
        admin, body.max_uses, body.valid_days, body.role
    )
    return InviteResponse.from_domain(invite, container.clock.now())


@router.get("/invites", response_model=list[InviteResponse], summary="List invite codes")
async def list_invites(admin: CurrentAdmin, container: ContainerDep) -> list[InviteResponse]:
    """Every code, newest first."""
    now = container.clock.now()
    return [InviteResponse.from_domain(i, now) for i in await container.user_admin.invites(admin)]


@router.delete(
    "/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke a code"
)
async def revoke_invite(invite_id: UUID, admin: CurrentAdmin, container: ContainerDep) -> Response:
    """The code can't be used any more."""
    await container.user_admin.revoke_invite(admin, invite_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users", response_model=list[MeResponse], summary="List users")
async def list_users(admin: CurrentAdmin, container: ContainerDep) -> list[MeResponse]:
    """Every user."""
    return [MeResponse.from_domain(u) for u in await container.user_admin.users(admin)]


@router.put("/users/{user_id}/disabled", response_model=MeResponse, summary="Disable / enable")
async def set_disabled(
    user_id: UUID, body: SetDisabledBody, admin: CurrentAdmin, container: ContainerDep
) -> MeResponse:
    """Disabling signs the user out everywhere and blocks sign-in."""
    user = await container.user_admin.set_disabled(admin, user_id, disabled=body.is_disabled)
    return MeResponse.from_domain(user)


@router.get("/audit", response_model=list[AuditEntryResponse], summary="Audit log")
async def audit_log(
    admin: CurrentAdmin,
    container: ContainerDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditEntryResponse]:
    """Newest entries first."""
    return [
        AuditEntryResponse(at=e.at, user_id=e.user_id, action=e.action, details=e.details)
        for e in await container.user_admin.audit_log(admin, limit)
    ]
