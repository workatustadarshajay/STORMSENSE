"""Who is calling, and what may they do.

In production the Databricks Apps proxy signs people in with their workspace account and sets the
X-Forwarded-Email header on every request; the app is not reachable any other way. Roles live in the app_users table.
"""
from __future__ import annotations

import re

from fastapi import Depends, HTTPException, Request

from .schemas import Me
from .service import Service

EMAIL = re.compile(r"^[^@\s]{1,128}@[^@\s]{1,128}$")


def problem(status: int, code: str, message: str, **headers: str) -> HTTPException:
    return HTTPException(status, detail={"code": code, "message": message}, headers=headers or None)


def get_service(request: Request) -> Service:
    return request.app.state.service


def current_user(request: Request, service: Service = Depends(get_service)) -> Me:
    email = request.headers.get("x-forwarded-email") or request.headers.get("x-forwarded-preferred-username")
    if not email and request.app.state.settings.allow_dev_identity:
        email = request.app.state.settings.dev_user_email
    if not email or not EMAIL.match(email):
        raise problem(401, "signed_out", "Please sign in again to continue.")
    return service.me(email)


def planner(user: Me = Depends(current_user)) -> Me:
    if not user.can_approve:
        raise problem(403, "read_only", "Your account can view transfers but not approve or reject them.")
    return user


def same_origin(request: Request) -> None:
    """Block cross-site form posts: browsers cannot add this header to a cross-origin request without a preflight."""
    if request.headers.get("x-requested-with") != "stormsense":
        raise problem(403, "blocked", "That request wasn't allowed.")
