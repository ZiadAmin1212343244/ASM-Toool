"""FastAPI dependencies for auth and engagement scoping."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.auth.exceptions import EngagementRequired, NotAuthenticated
from app.config import Settings, get_settings
from app.database import get_db
from app.models.engagement import Engagement, EngagementMembership
from app.models.enums import Role
from app.models.user import User


def get_session_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_session_user(request, db)
    if not user or not user.is_active:
        raise NotAuthenticated()
    return user


def require_role(*roles: Role):
    def _dep(user: User = Depends(require_user)) -> User:
        if user.role not in roles and user.role != Role.admin:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return _dep


def get_current_engagement(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> Engagement | None:
    engagement_id = request.session.get("engagement_id")
    if not engagement_id:
        return None
    membership = (
        db.query(EngagementMembership)
        .filter(
            EngagementMembership.user_id == user.id,
            EngagementMembership.engagement_id == engagement_id,
        )
        .first()
    )
    if not membership and user.role != Role.admin:
        return None
    return (
        db.query(Engagement)
        .options(joinedload(Engagement.client))
        .filter(Engagement.id == engagement_id)
        .first()
    )


def require_engagement(
    engagement: Engagement | None = Depends(get_current_engagement),
) -> Engagement:
    if engagement is None:
        raise EngagementRequired()
    return engagement


def user_engagements(db: Session, user: User) -> list[Engagement]:
    if user.role == Role.admin:
        return (
            db.query(Engagement)
            .options(joinedload(Engagement.client))
            .order_by(Engagement.name)
            .all()
        )
    return (
        db.query(Engagement)
        .join(EngagementMembership)
        .options(joinedload(Engagement.client))
        .filter(EngagementMembership.user_id == user.id)
        .order_by(Engagement.name)
        .all()
    )


def get_settings_dep() -> Settings:
    return get_settings()
