from typing import Optional
from src.domain.entities.user import User
from src.domain.repositories.user_repository import IUserRepository

class AuthService:
    def __init__(self, users: IUserRepository):
        self.users = users

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.users.get_active_by_email(email)
        if not user or not user.check_password(password):
            return None
        return user
