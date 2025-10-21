from dataclasses import dataclass
from sqlalchemy import text
from src.infrastructure.persistence.database import db

@dataclass
class CreatedTicket:
    id: int
    code: str

class TicketRepository:
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
