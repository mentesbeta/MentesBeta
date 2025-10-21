import os, hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import text, func
from typing import Dict, List
from src.infrastructure.persistence.database import db
from src.domain.entities.ticket import Ticket, Status, TicketHistory
from src.domain.entities.ticket_extras import TicketAttachment, TicketComment
from werkzeug.utils import secure_filename

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


@dataclass
class TicketDetail:
    id: int
    code: str
    title: str
    description: str
    requester_id: int
    requester_name: str
    assignee_id: int | None
    assignee_name: str | None
    category_name: str | None
    priority_name: str
    status_name: str
    created_at: str
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
    
    # ===== DETALLE =====
    def detail(self, ticket_id: int):
        sql = text("""
        SELECT t.id, t.code, t.title, t.description,
               t.requester_id,
               CONCAT(rq.names_worker, ' ', rq.last_name) AS requester_name,
               t.assignee_id,
               CASE WHEN asg.id IS NULL THEN NULL ELSE CONCAT(asg.names_worker, ' ', asg.last_name) END AS assignee_name,
               c.name AS category_name,
               p.name AS priority_name,
               s.name AS status_name,
               DATE_FORMAT(t.created_at,  '%Y-%m-%d %H:%i') AS created_at,
               DATE_FORMAT(t.updated_at,  '%Y-%m-%d %H:%i') AS updated_at
        FROM tickets t
        JOIN users rq   ON rq.id = t.requester_id
        LEFT JOIN users asg ON asg.id = t.assignee_id
        LEFT JOIN categories c ON c.id = t.category_id
        JOIN priorities p ON p.id = t.priority_id
        JOIN statuses   s ON s.id = t.status_id
        WHERE t.id = :tid
        """)
        row = db.session.execute(sql, {"tid": ticket_id}).mappings().first()
        return TicketDetail(**row) if row else None

    def comments(self, ticket_id: int):
        sql = text("""
        SELECT tc.id, tc.body,
               DATE_FORMAT(tc.created_at,'%Y-%m-%d %H:%i') AS created_at,
               u.id AS author_id, CONCAT(u.names_worker,' ',u.last_name) AS author_name
        FROM ticket_comments tc
        JOIN users u ON u.id = tc.author_user_id
        WHERE tc.ticket_id = :tid
        ORDER BY tc.created_at ASC
        """)
        return db.session.execute(sql, {"tid": ticket_id}).mappings().all()

    def attachments(self, ticket_id: int):
        sql = text("""
        SELECT id, file_name, mime_type, file_size,
               DATE_FORMAT(created_at,'%Y-%m-%d %H:%i') AS created_at
        FROM ticket_attachments
        WHERE ticket_id = :tid
        ORDER BY created_at DESC
        """)
        return db.session.execute(sql, {"tid": ticket_id}).mappings().all()

    def history(self, ticket_id: int):
        sql = text("""
        SELECT th.id,
               DATE_FORMAT(th.created_at,'%Y-%m-%d %H:%i') AS created_at,
               CONCAT(u.names_worker,' ',u.last_name) AS actor,
               sf.name AS from_status,
               st.name AS to_status,
               th.note
        FROM ticket_history th
        JOIN users u   ON u.id = th.actor_user_id
        LEFT JOIN statuses sf ON sf.id = th.from_status_id
        JOIN statuses st ON st.id = th.to_status_id
        WHERE th.ticket_id = :tid
        ORDER BY th.created_at DESC
        """)
        return db.session.execute(sql, {"tid": ticket_id}).mappings().all()

    def add_comment(self, ticket_id: int, author_user_id: int, body: str):
        db.session.execute(
            text("INSERT INTO ticket_comments (ticket_id, author_user_id, body) VALUES (:t,:u,:b)"),
            {"t": ticket_id, "u": author_user_id, "b": body.strip()}
        )
        db.session.commit()

    def save_attachment(self, *, ticket_id: int, uploader_id: int, file_storage, upload_dir: str) -> int:
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = secure_filename(file_storage.filename or "")
        if not safe_name:
            raise ValueError("Archivo inválido")

        # ruta en disco
        disk_path = os.path.join(upload_dir, safe_name)
        file_storage.save(disk_path)

        # metadatos
        size = os.path.getsize(disk_path)
        sha = hashlib.sha256()
        with open(disk_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                sha.update(chunk)

        res = db.session.execute(text("""
            INSERT INTO ticket_attachments
              (ticket_id, uploader_user_id, file_name, mime_type, file_path, file_size, checksum_sha256)
            VALUES
              (:t,:u,:n,:m,:p,:s,:h)
        """), {
            "t": ticket_id,
            "u": uploader_id,
            "n": safe_name,
            "m": file_storage.mimetype or "application/octet-stream",
            "p": disk_path,
            "s": size,
            "h": sha.hexdigest()
        })
        db.session.commit()
        return res.lastrowid

    def get_attachment_path(self, att_id: int, ticket_id: int):
        row = db.session.execute(text("""
            SELECT file_path, file_name, mime_type
            FROM ticket_attachments
            WHERE id = :id AND ticket_id = :tid
        """), {"id": att_id, "tid": ticket_id}).mappings().first()
        return row