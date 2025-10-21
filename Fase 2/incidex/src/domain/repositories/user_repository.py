from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.user import User

class IUserRepository(ABC):
    @abstractmethod
    def get_active_by_email(self, email: str) -> Optional[User]:
        ...
