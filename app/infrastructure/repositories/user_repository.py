"""Repository pour l'accès aux données utilisateur."""
from app.infrastructure.database.models import User
from app import db


class UserRepository:
    """Isole l'accès aux données User (Repository Pattern)."""

    def get_by_id(self, user_id: str) -> User | None:
        return User.query.get(user_id)

    def get_by_telephone(self, telephone: str) -> User | None:
        return User.query.filter_by(telephone=telephone).first()

    def get_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email).first()

    def exists_telephone(self, telephone: str) -> bool:
        return self.get_by_telephone(telephone) is not None

    def create(self, **kwargs) -> User:
        user = User(**kwargs)
        db.session.add(user)
        db.session.commit()
        return user
