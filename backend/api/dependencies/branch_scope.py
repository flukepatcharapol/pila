"""
api/dependencies/branch_scope.py

Branch-access scope helpers for multi-branch users.

After the multi-branch refactor, User.branch_id no longer exists. Branch
membership is stored via the `user_branches` association table and exposed
on JWT access tokens as `branch_ids: list[str] | None`.

Contract:
  get_user_branch_ids(user_or_payload) -> list[UUID] | None
    None          → unrestricted (DEVELOPER / OWNER)
    list[UUID]    → the branches this user may access
    []            → role is scoped but no branches assigned (effectively no access)

`user_or_payload` accepts:
  - dict        → JWT access payload (has "role" and "branch_ids")
  - User model  → reads .role + .branches (requires session-loaded relationship)
"""
from __future__ import annotations
import uuid
from typing import Any
from fastapi import HTTPException, status


_UNRESTRICTED_ROLES = {"DEVELOPER", "OWNER"}


def _to_uuid(v) -> uuid.UUID | None:
    if v is None:
        return None
    if isinstance(v, uuid.UUID):
        return v
    try:
        return uuid.UUID(str(v))
    except (ValueError, AttributeError, TypeError):
        return None


def get_user_branch_ids(user_or_payload: Any) -> list[uuid.UUID] | None:
    """Return list of allowed branch UUIDs, or None for unrestricted access."""
    # dict (JWT payload) path
    if isinstance(user_or_payload, dict):
        role = (user_or_payload.get("role") or "").upper()
        if role in _UNRESTRICTED_ROLES:
            return None
        raw_list = user_or_payload.get("branch_ids")
        if raw_list is None:
            # legacy callers that set just role — treat as no branches
            return []
        return [u for u in (_to_uuid(x) for x in raw_list) if u is not None]

    # User model path (has .role and .branches)
    role_attr = getattr(user_or_payload, "role", None) or ""
    role = str(role_attr).upper()
    if role in _UNRESTRICTED_ROLES:
        return None
    branches = getattr(user_or_payload, "branches", None) or []
    return [b.id for b in branches]


def assert_branch_access(user_or_payload: Any, branch_id) -> None:
    """Raise 403 if the user cannot access branch_id. No-op for unrestricted users."""
    allowed = get_user_branch_ids(user_or_payload)
    if allowed is None:
        return
    bid = _to_uuid(branch_id)
    if bid is None or bid not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Branch access denied",
        )
