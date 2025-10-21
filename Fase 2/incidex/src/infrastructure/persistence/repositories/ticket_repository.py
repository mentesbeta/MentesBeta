from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import text, func
from typing import Dict, List
from src.infrastructure.persistence.database import db
from src.domain.entities.ticket import Ticket, Status

@dataclass
class CreatedTicket:
    id: int
    code: str

@dataclass
class RecentTicketRow:
    id: int
    code: str
    title: str
    requester_name: str
    category_name: str | None
    priority_name: str
    status_name: str
    updated_at: str 

class TicketRepository:

    # ==== CREACIÓN DE TICKET ====

    def get_categories(self):
        rows = db.session.execute(text("SELECT id, name FROM categories ORDER BY name")).mappings().all()
        return rows

    def get_departments(self):
        rows = db.session.execute(text("SELECT id, name FROM departments ORDER BY name")).mappings().all()
        return rows

    def get_priorities(self):
        rows = db.session.execute(text("SELECT id, name FROM priorities ORDER BY name")).mappings().all()
        return rows

    def get_analysts(self):
        # usuarios con rol ANALYST
        sql = """
        SELECT u.id, CONCAT(u.names_worker, ' ', u.last_name) AS full_name
        FROM users u
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r       ON r.id = ur.role_id
        WHERE r.name = 'ANALYST' AND u.is_active = 1
        ORDER BY full_name
        """
        return db.session.execute(text(sql)).mappings().all()

    def next_ticket_code(self) -> str:
        # obtiene el último y suma
        last = db.session.execute(text("SELECT MAX(id) AS mid FROM tickets")).scalar() or 0
        return f"INC-{(last + 1):05d}"

    def default_status_id(self) -> int:
        # NUEVO como estado inicial
        return db.session.execute(text("SELECT id FROM statuses WHERE name='NUEVO'")).scalar()

    def insert_ticket(self, *, code, title, description, requester_id,
                      department_id, category_id, priority_id, assignee_id=None) -> CreatedTicket:
        status_id = self.default_status_id()
        sql = text("""
            INSERT INTO tickets
              (code, title, description, requester_id, assignee_id,
               department_id, category_id, priority_id, status_id)
            VALUES
              (:code, :title, :description, :requester_id, :assignee_id,
               :department_id, :category_id, :priority_id, :status_id)
        """)
        res = db.session.execute(sql, {
            "code": code,
            "title": title,
            "description": description,
            "requester_id": requester_id,
            "assignee_id": assignee_id if assignee_id and assignee_id > 0 else None,
            "department_id": department_id,
            "category_id": category_id,
            "priority_id": priority_id,
            "status_id": status_id
        })
        db.session.commit()
        new_id = res.lastrowid
        return CreatedTicket(id=new_id, code=code)
    
    # ==== DASHBOARD MÉTRICAS ====

    def kpis_for_user(self, user_id: int) -> dict:
        sql = text("""
        SELECT
          SUM(CASE WHEN s.name IN ('NUEVO','ASIGNADO','EN_PROGRESO') THEN 1 ELSE 0 END) AS open_count,
          SUM(CASE WHEN s.name = 'EN_PROGRESO' THEN 1 ELSE 0 END)                         AS in_progress_count,
          SUM(CASE WHEN s.name = 'CERRADO' THEN 1 ELSE 0 END)                             AS closed_count
        FROM tickets t
        JOIN statuses s ON s.id = t.status_id
        WHERE (t.requester_id = :uid OR t.assignee_id = :uid)
        """)
        row = db.session.execute(sql, {"uid": user_id}).first()
        return {
            "open":        int(row[0] or 0),
            "in_progress": int(row[1] or 0),
            "closed_week": int(row[2] or 0),  # si quieres “últimos 7 días”, ajusta el WHERE con fecha
        }

    def recent_for_user(self, user_id: int, limit: int = 10) -> list[RecentTicketRow]:
        sql = text("""
        SELECT  t.id,
                t.code,
                t.title,
                CONCAT(rq.names_worker,' ',rq.last_name)   AS requester_name,
                c.name                                     AS category_name,
                p.name                                     AS priority_name,
                s.name                                     AS status_name,
                DATE_FORMAT(t.updated_at, '%Y-%m-%d %H:%i') AS updated_at
        FROM tickets t
        JOIN users rq     ON rq.id = t.requester_id
        LEFT JOIN categories c ON c.id = t.category_id
        JOIN priorities p ON p.id = t.priority_id
        JOIN statuses   s ON s.id = t.status_id
        WHERE (t.requester_id = :uid OR t.assignee_id = :uid)
        ORDER BY t.updated_at DESC
        LIMIT :lim
        """)
        rows = db.session.execute(sql, {"uid": user_id, "lim": limit}).mappings().all()
        return [RecentTicketRow(**row) for row in rows]