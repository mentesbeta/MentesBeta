from datetime import datetime, date
from flask_login import UserMixin
from sqlalchemy import Integer, String, Boolean, Date, DateTime, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash

from src.infrastructure.persistence.database import db
# Importas los modelos referenciados
from .department import Department
from .role import Role

# Tabla intermedia user_roles
user_roles = Table(
    "user_roles",
    db.Model.metadata,
    db.Column("user_id", Integer,
              ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", Integer,
              ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    names_worker: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name:     Mapped[str] = mapped_column(String(120), nullable=False)
    birthdate:     Mapped[date] = mapped_column(Date, nullable=False)
    email:         Mapped[str]  = mapped_column(String(120), unique=True, nullable=False)
    gender:        Mapped[str]  = mapped_column(Enum("M","F","X","N/A", name="gender_enum"), nullable=False)
    password_hash: Mapped[str]  = mapped_column(String(255), nullable=False)

    department_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("departments.id", name="fk_users_department"),
        nullable=True
    )
    # relación de conveniencia
    department: Mapped[Department | None] = relationship(Department, lazy="joined")

    is_active:  Mapped[bool]      = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Roles (many-to-many)
    roles: Mapped[list[Role]] = relationship(Role, secondary=user_roles, backref="users", lazy="joined")

    # helpers
    @property
    def name(self) -> str:
        return f"{self.names_worker} {self.last_name}".strip()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)