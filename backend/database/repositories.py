"""
Repository pattern for User CRUD operations.
Centralises all database queries to keep routes thin.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import User
from core.security import get_password_hash, verify_password


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> User:
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_preferences(self, user_id: uuid.UUID, preferences: dict) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.preferences = {**(user.preferences or {}), **preferences}
        await self.db.flush()
        return user

    async def deactivate(self, user_id: uuid.UUID) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.is_active = False
        await self.db.flush()
        return True
