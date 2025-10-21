from typing import Optional
from sqlalchemy.orm import Session
from src.domain.entities.user import User
from src.domain.repositories.user_repository import IUserRepository

class UserRepository(IUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_active_by_email(self, email: str) -> Optional[User]:
        return (
            self.session.query(User)
            .filter(User.email == email, User.is_active == True)
            .first()
        )
