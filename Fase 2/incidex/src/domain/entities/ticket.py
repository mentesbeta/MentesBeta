from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.persistence.database import db

class Ticket(db.Model):
    __tablename__ = "tickets"

    id: Mapped[int]               = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str]             = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str]            = mapped_column(String(200), nullable=False)
    description: Mapped[str]      = mapped_column(Text, nullable=False)
    requester_id: Mapped[int]     = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id: Mapped[int | None]   = mapped_column(Integer, ForeignKey("users.id"))
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"))
    category_id: Mapped[int | None]   = mapped_column(Integer, ForeignKey("categories.id"))
    priority_id: Mapped[int]          = mapped_column(Integer, ForeignKey("priorities.id"), nullable=False)
    status_id: Mapped[int]            = mapped_column(Integer, ForeignKey("statuses.id"), nullable=False)
    created_at: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    closed_at: Mapped[datetime | None]   = mapped_column(DateTime)

class TicketHistory(db.Model):
    __tablename__ = "ticket_history"

    id: Mapped[int]          = mapped_column(BigInteger, primary_key=True)
    ticket_id: Mapped[int]   = mapped_column(BigInteger, ForeignKey("tickets.id"), nullable=False)
    actor_user_id: Mapped[int]= mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    from_status_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("statuses.id"))
    to_status_id: Mapped[int] = mapped_column(Integer, ForeignKey("statuses.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
