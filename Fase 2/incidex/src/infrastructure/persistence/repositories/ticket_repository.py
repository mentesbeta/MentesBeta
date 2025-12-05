import os, hashlib
from dataclasses import dataclass
from sqlalchemy import text
from src.infrastructure.persistence.database import db
from src.domain.entities.ticket import Ticket, Status, TicketHistory
from src.domain.entities.ticket_extras import TicketAttachment, TicketComment
from src.infrastructure.notifications.support_mail import send_notification_email
from werkzeug.utils import secure_filename
from flask import current_app

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
    assignee_name: str | None
    category_name: str | None
    priority_name: str
    status_name: str
    updated_at: str
    role_for_user: str | None = None

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
    department_name: str | None 
    created_at: str
    updated_at: str


def _coalesce_int(v, default=None):
    try:
        return int(v) if v is not None else default
    except Exception:
        return default

class TicketRepository:

    # ==== CATÁLOGOS BÁSICOS ====
    def get_categories(self):
        return db.session.execute(text("SELECT id, name FROM categories ORDER BY name")).mappings().all()

    def get_departments(self):
        return db.session.execute(text("SELECT id, name FROM departments ORDER BY name")).mappings().all()

    def get_priorities(self):
        return db.session.execute(text("SELECT id, name FROM priorities ORDER BY name")).mappings().all()

    def get_statuses(self):
        return db.session.execute(text("SELECT id, name FROM statuses ORDER BY name")).mappings().all()
    
    def get_status_name(self, status_id: int) -> str | None:
        """
        Devuelve el nombre del estado (ej. 'EN_PROGRESO') dado su ID.
        """
        row = db.session.execute(
            text("SELECT name FROM statuses WHERE id = :i LIMIT 1"),
            {"i": int(status_id)}
        ).scalar()
        return row if row is not None else None


    def get_status_id_by_name(self, name: str) -> int | None:
        row = db.session.execute(
            text("SELECT id FROM statuses WHERE UPPER(name) = UPPER(:n) LIMIT 1"),
            {"n": (name or "").strip()}
        ).scalar()
        return int(row) if row is not None else None


    def get_analysts(self):
        sql = """
        SELECT u.id, CONCAT(u.names_worker, ' ', u.last_name) AS full_name
        FROM users u
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r       ON r.id = ur.role_id
        WHERE UPPER(r.name) = 'ANALYST' AND u.is_active = 1
        ORDER BY full_name
        """
        return db.session.execute(text(sql)).mappings().all()


    def list_analysts_by_department(self):
        """
        Retorna analistas agrupables por departamento para el autocompletado
        en creación de ticket (area -> primer analista).
        """
        sql = """
        SELECT
            u.id,
            u.department_id,
            CONCAT(u.names_worker, ' ', u.last_name) AS full_name
        FROM users u
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r       ON r.id = ur.role_id
        WHERE u.is_active = 1
        AND u.department_id IS NOT NULL
        AND UPPER(r.name) = 'ANALYST'
        ORDER BY u.department_id, full_name
        """
        return db.session.execute(text(sql)).mappings().all()


    # ==== CREACIÓN DE TICKET ====
    def next_ticket_code(self) -> str:
        last = db.session.execute(text("SELECT MAX(id) AS mid FROM tickets")).scalar() or 0
        return f"INC-{(last + 1):05d}"

    def default_status_id(self) -> int:
        return db.session.execute(text("SELECT id FROM statuses WHERE name='NUEVO'")).scalar()

    def insert_ticket(self, *, code, title, description, requester_id,
                      department_id, category_id, priority_id, assignee_id=None) -> CreatedTicket:
        status_id = self.default_status_id()
        res = db.session.execute(text("""
            INSERT INTO tickets
              (code, title, description, requester_id, assignee_id,
               department_id, category_id, priority_id, status_id)
            VALUES
              (:code, :title, :description, :requester_id, :assignee_id,
               :department_id, :category_id, :priority_id, :status_id)
        """), {
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
        return CreatedTicket(id=res.lastrowid, code=code)

    # ==== DASHBOARD ====
    def kpis_for_user(self, user_id: int) -> dict:
        row = db.session.execute(text("""
        SELECT
          SUM(CASE WHEN s.name IN ('NUEVO','ASIGNADO','EN_PROGRESO') THEN 1 ELSE 0 END) AS open_count,
          SUM(CASE WHEN s.name = 'EN_PROGRESO' THEN 1 ELSE 0 END)                         AS in_progress_count,
          SUM(CASE WHEN s.name = 'CERRADO' THEN 1 ELSE 0 END)                             AS closed_count
        FROM tickets t
        JOIN statuses s ON s.id = t.status_id
        WHERE (t.requester_id = :uid OR t.assignee_id = :uid)
        """), {"uid": user_id}).first()
        return {
            "open":        int(row[0] or 0),
            "in_progress": int(row[1] or 0),
            "closed_week": int(row[2] or 0),
        }

    def recent_for_user(self, user_id: int, limit: int = 5) -> list[RecentTicketRow]:
        rows = db.session.execute(text("""
        SELECT  
            t.id,
            t.code,
            t.title,
            CONCAT(rq.names_worker,' ',rq.last_name)   AS requester_name,
            CASE WHEN asg.id IS NULL THEN NULL ELSE CONCAT(asg.names_worker,' ',asg.last_name) END AS assignee_name,
            c.name                                     AS category_name,
            p.name                                     AS priority_name,
            s.name                                     AS status_name,
            DATE_FORMAT(t.updated_at, '%Y-%m-%d %H:%i') AS updated_at,
            CASE
              WHEN t.requester_id = :uid THEN 'Solicitante'
              WHEN t.assignee_id  = :uid THEN 'Asignado'
              ELSE NULL
            END AS role_for_user
        FROM tickets t
        JOIN users rq        ON rq.id = t.requester_id
        LEFT JOIN users asg  ON asg.id = t.assignee_id
        LEFT JOIN categories c ON c.id = t.category_id
        JOIN priorities p    ON p.id = t.priority_id
        JOIN statuses   s    ON s.id = t.status_id
        WHERE (t.requester_id = :uid OR t.assignee_id = :uid)
        ORDER BY t.updated_at DESC
        LIMIT :lim
        """), {"uid": user_id, "lim": limit}).mappings().all()
        return [RecentTicketRow(**row) for row in rows]

    # ==== DETALLE ====
    def detail(self, ticket_id: int):
        row = db.session.execute(text("""
            SELECT t.id, t.code, t.title, t.description,
                t.requester_id,
                CONCAT(rq.names_worker, ' ', rq.last_name) AS requester_name,
                t.assignee_id,
                CASE WHEN asg.id IS NULL THEN NULL ELSE CONCAT(asg.names_worker, ' ', asg.last_name) END AS assignee_name,
                c.name AS category_name,
                p.name AS priority_name,
                s.name AS status_name,
                d.name AS department_name,
                DATE_FORMAT(t.created_at,  '%Y-%m-%d %H:%i') AS created_at,
                DATE_FORMAT(t.updated_at,  '%Y-%m-%d %H:%i') AS updated_at
            FROM tickets t
            JOIN users rq   ON rq.id = t.requester_id
            LEFT JOIN users asg ON asg.id = t.assignee_id
            LEFT JOIN categories c ON c.id = t.category_id
            JOIN priorities p ON p.id = t.priority_id
            JOIN statuses   s ON s.id = t.status_id
            LEFT JOIN departments d ON d.id = t.department_id
            WHERE t.id = :tid
        """), {"tid": ticket_id}).mappings().first()
        return TicketDetail(**row) if row else None



    def comments(self, ticket_id: int):
        return db.session.execute(text("""
        SELECT tc.id, tc.body,
               DATE_FORMAT(tc.created_at,'%Y-%m-%d %H:%i') AS created_at,
               u.id AS author_id, CONCAT(u.names_worker,' ',u.last_name) AS author_name
        FROM ticket_comments tc
        JOIN users u ON u.id = tc.author_user_id
        WHERE tc.ticket_id = :tid
        ORDER BY tc.created_at ASC
        """), {"tid": ticket_id}).mappings().all()

    def attachments(self, ticket_id: int):
        return db.session.execute(text("""
        SELECT id, file_name, mime_type, file_size,
               DATE_FORMAT(created_at,'%Y-%m-%d %H:%i') AS created_at
        FROM ticket_attachments
        WHERE ticket_id = :tid
        ORDER BY created_at DESC
        """), {"tid": ticket_id}).mappings().all()

    def history(self, ticket_id: int):
        return db.session.execute(text("""
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
        """), {"tid": ticket_id}).mappings().all()

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

        disk_path = os.path.join(upload_dir, safe_name)
        file_storage.save(disk_path)

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
        return db.session.execute(text("""
            SELECT file_path, file_name, mime_type
            FROM ticket_attachments
            WHERE id = :id AND ticket_id = :tid
        """), {"id": att_id, "tid": ticket_id}).mappings().first()

    # ====== AUX: datos mínimos / permisos ======
    def get_ticket_minimal(self, ticket_id: int):
        return db.session.execute(text("""
            SELECT
              id,
              code,
              requester_id,
              assignee_id,
              department_id,
              status_id
            FROM tickets
            WHERE id = :tid
        """), {"tid": ticket_id}).mappings().first()



    def get_user_fullname(self, user_id: int | None) -> str | None:
        if not user_id:
            return None
        row = db.session.execute(text("""
            SELECT CONCAT(u.names_worker,' ',u.last_name) AS full_name
            FROM users u WHERE u.id = :uid
        """), {"uid": user_id}).first()
        return row[0] if row else None

    def get_user_department_id(self, user_id: int) -> int | None:
        row = db.session.execute(text("""
            SELECT department_id FROM users WHERE id = :uid
        """), {"uid": user_id}).first()
        return row[0] if row else None

    
    # ====== HISTORIAL: cambio de estado / asignación ======
    def update_status_with_history(
            self,
            *,
            ticket_id: int,
            to_status_id: int,
            actor_user_id: int,
            note: str | None = None
        ):
            try:
                # Bloqueamos el ticket actual y leemos el estado actual
                cur = db.session.execute(text("""
                    SELECT status_id
                    FROM tickets
                    WHERE id = :tid
                    FOR UPDATE
                """), {"tid": ticket_id}).first()

                if not cur:
                    raise ValueError("Ticket no encontrado")

                from_status_id = int(cur[0])

                # Averiguamos el nombre del estado destino para saber si es RESUELTO / CERRADO
                status_name = (self.get_status_name(int(to_status_id)) or "").upper()
                set_resolved = 1 if status_name == "RESUELTO" else 0
                set_closed   = 1 if status_name == "CERRADO" else 0

                # Actualizamos el ticket
                db.session.execute(text("""
                    UPDATE tickets
                    SET
                        status_id  = :to_status_id,
                        updated_at = NOW(),
                        resolved_at = CASE
                            WHEN :set_resolved = 1 AND resolved_at IS NULL THEN NOW()
                            ELSE resolved_at
                        END,
                        closed_at = CASE
                            WHEN :set_closed = 1 AND closed_at IS NULL THEN NOW()
                            ELSE closed_at
                        END
                    WHERE id = :tid
                """), {
                    "to_status_id": int(to_status_id),
                    "tid": ticket_id,
                    "set_resolved": set_resolved,
                    "set_closed": set_closed,
                })

                # Registramos en historial
                db.session.execute(text("""
                    INSERT INTO ticket_history
                        (ticket_id, actor_user_id, from_status_id, to_status_id, note, created_at)
                    VALUES
                        (:tid, :actor, :froms, :tos, :note, NOW())
                """), {
                    "tid": ticket_id,
                    "actor": actor_user_id,
                    "froms": from_status_id,
                    "tos": int(to_status_id),
                    "note": (note or "").strip() or None
                })

                db.session.commit()
            except Exception:
                db.session.rollback()
                raise


    def update_assignee_with_history(self, *, ticket_id: int, new_assignee_id: int | None, actor_user_id: int, note: str | None = None):
        try:
            cur = db.session.execute(text("""
                SELECT status_id, assignee_id
                FROM tickets
                WHERE id = :tid
                FOR UPDATE
            """), {"tid": ticket_id}).first()
            if not cur:
                raise ValueError("Ticket no encontrado")

            current_status_id = int(cur[0])
            old_assignee_id = cur[1]

            old_name = self.get_user_fullname(old_assignee_id) or "—"
            new_name = self.get_user_fullname(new_assignee_id) or "—"

            note_parts = [f"Reasignado de {old_name} a {new_name}"]
            if (note or "").strip():
                note_parts.append(note.strip())
            final_note = " — ".join(note_parts)

            db.session.execute(text("""
                UPDATE tickets
                SET assignee_id = :new_assignee,
                    updated_at  = NOW()
                WHERE id = :tid
            """), {"new_assignee": new_assignee_id, "tid": ticket_id})

            db.session.execute(text("""
                INSERT INTO ticket_history
                    (ticket_id, actor_user_id, from_status_id, to_status_id, note, created_at)
                VALUES
                    (:tid, :actor, :froms, :tos, :note, NOW())
            """), {
                "tid": ticket_id,
                "actor": actor_user_id,
                "froms": current_status_id,
                "tos": current_status_id,
                "note": final_note
            })

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    # ====== LISTAS / ASIGNABLES ======
    def list_assignable_requesters_same_dept(self, actor_user_id: int):
        dept = self.get_user_department_id(actor_user_id)
        if dept is None:
            return []
        return db.session.execute(text("""
            SELECT u.id, CONCAT(u.names_worker,' ',u.last_name) AS full_name
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r       ON r.id = ur.role_id
            WHERE u.department_id = :dept
              AND UPPER(r.name) = 'REQUESTER'
            ORDER BY full_name
        """), {"dept": dept}).mappings().all()

    def is_requester_same_dept(self, actor_user_id: int, target_user_id: int) -> bool:
        rows = db.session.execute(text("""
            SELECT 1
            FROM users ta
            JOIN user_roles ur ON ur.user_id = ta.id
            JOIN roles r       ON r.id = ur.role_id
            WHERE ta.id = :target
              AND ta.department_id = (SELECT department_id FROM users WHERE id = :actor)
              AND UPPER(r.name) = 'REQUESTER'
            LIMIT 1
        """), {"actor": actor_user_id, "target": target_user_id}).all()
        return bool(rows)

    def list_all_users_minimal(self):
        return db.session.execute(text("""
            SELECT u.id, CONCAT(u.names_worker,' ',u.last_name) AS full_name
            FROM users u
            ORDER BY full_name
        """)).mappings().all()

    def list_assignables_for_actor(self, actor_user_id: int, roles_upper: set[str]):
        if "ADMIN" in roles_upper:
            return self.list_all_users_minimal()
        return self.list_assignable_requesters_same_dept(actor_user_id)

    # ====== LISTADOS (para /app/mine con reglas por rol) ======

    def _apply_common_filters(self, where: list[str], params: dict,
                              q=None, status_id=None, priority_id=None, category_id=None,
                              date_from=None, date_to=None):
        if q:
            where.append("(t.code = :q_exact OR t.title LIKE :q_like)")
            params["q_exact"] = q.strip()
            params["q_like"] = f"%{q.strip()}%"
        if status_id:
            where.append("t.status_id = :status_id")
            params["status_id"] = int(status_id)
        if priority_id:
            where.append("t.priority_id = :priority_id")
            params["priority_id"] = int(priority_id)
        if category_id:
            where.append("t.category_id = :category_id")
            params["category_id"] = int(category_id)
        if date_from and date_to:
            where.append("DATE(t.created_at) BETWEEN :dfrom AND :dto")
            params["dfrom"] = date_from
            params["dto"] = date_to
        elif date_from:
            where.append("DATE(t.created_at) >= :dfrom")
            params["dfrom"] = date_from
        elif date_to:
            where.append("DATE(t.created_at) <= :dto")
            params["dto"] = date_to

    def _paged_items(self, where_sql: str, params: dict, page: int, per_page: int, include_role_for: int | None = None):
        limit = int(per_page or 10)
        offset = max(int(page or 1), 1)
        offset = (offset - 1) * limit

        total = db.session.execute(text(f"""
            SELECT COUNT(*)
            FROM tickets t
            WHERE {where_sql}
        """), params).scalar() or 0

        # NOTA: role_for_user solo si lo necesitamos (cuando filtramos por el propio usuario)
        role_for_case = ""
        if include_role_for is not None:
            role_for_case = """
                , CASE
                    WHEN t.requester_id = :rfu THEN 'Solicitante'
                    WHEN t.assignee_id  = :rfu THEN 'Asignado'
                    ELSE NULL
                  END AS role_for_user
            """

        items = db.session.execute(text(f"""
            SELECT
              t.id,
              t.code,
              t.title,
              CONCAT(rq.names_worker,' ',rq.last_name) AS requester_name,
              CASE WHEN asg.id IS NULL THEN NULL ELSE CONCAT(asg.names_worker,' ',asg.last_name) END AS assignee_name,
              c.name AS category_name,
              p.name AS priority_name,
              s.name AS status_name,
              DATE_FORMAT(t.updated_at, '%Y-%m-%d %H:%i') AS updated_at
              {role_for_case}
            FROM tickets t
            JOIN users rq        ON rq.id = t.requester_id
            LEFT JOIN users asg  ON asg.id = t.assignee_id
            LEFT JOIN categories c ON c.id = t.category_id
            JOIN priorities p    ON p.id = t.priority_id
            JOIN statuses   s    ON s.id = t.status_id
            WHERE {where_sql}
            ORDER BY t.updated_at DESC
            LIMIT :lim OFFSET :off
        """), {**params, "lim": limit, "off": offset, **({"rfu": include_role_for} if include_role_for is not None else {})}).mappings().all()

        out = []
        for row in items:
            d = dict(row)
            # asegura presencia de role_for_user (aunque no lo use el template)
            if "role_for_user" not in d:
                d["role_for_user"] = None
            out.append(d)
        return out, int(total)

    # --- REQUESTER: asignados o creados por él (también sirve para “Mis Tickets” legacy) ---
    def list_mine(self, user_id: int, *, q=None, status_id=None, priority_id=None, category_id=None,
                  date_from=None, date_to=None, page=1, per_page=10):
        where = ["(t.requester_id = :uid OR t.assignee_id = :uid)"]
        params = {"uid": user_id}
        self._apply_common_filters(where, params, q, status_id, priority_id, category_id, date_from, date_to)
        return self._paged_items(" AND ".join(where), params, page, per_page, include_role_for=user_id)

    # --- ADMIN: todos ---
    def list_all(self, *, q=None, status_id=None, priority_id=None, category_id=None,
                 date_from=None, date_to=None, page=1, per_page=10):
        where = ["1=1"]
        params = {}
        self._apply_common_filters(where, params, q, status_id, priority_id, category_id, date_from, date_to)
        return self._paged_items(" AND ".join(where), params, page, per_page, include_role_for=None)

    # --- ANALYST: por departamento o creados por él ---
    def list_by_department_or_creator(self, department_id: int, user_id: int, *,
                                      q=None, status_id=None, priority_id=None, category_id=None,
                                      date_from=None, date_to=None, page=1, per_page=10):
        where = ["(t.department_id = :dep OR t.requester_id = :uid)"]
        params = {"dep": int(department_id), "uid": int(user_id)}
        self._apply_common_filters(where, params, q, status_id, priority_id, category_id, date_from, date_to)
        return self._paged_items(" AND ".join(where), params, page, per_page, include_role_for=user_id)
    
    # --- ANALYST se le asigna cuando tiene poca carga ---

    def list_analysts_by_department_with_load(self):
        """
        Retorna analistas por departamento junto con su carga actual
        (cantidad de tickets abiertos asignados).
        Carga = tickets en estados NUEVO, ASIGNADO, EN_PROGRESO.
        """
        sql = """
        SELECT
            u.id,
            u.department_id,
            CONCAT(u.names_worker, ' ', u.last_name) AS full_name,
            COALESCE(SUM(
                CASE
                    WHEN s.name IN ('NUEVO','ASIGNADO','EN_PROGRESO') THEN 1
                    ELSE 0
                END
            ), 0) AS open_count
        FROM users u
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r       ON r.id = ur.role_id
        LEFT JOIN tickets t   ON t.assignee_id = u.id
        LEFT JOIN statuses s  ON s.id = t.status_id
        WHERE u.is_active = 1
          AND u.department_id IS NOT NULL
          AND UPPER(r.name) = 'ANALYST'
        GROUP BY u.id, u.department_id, full_name
        ORDER BY u.department_id, open_count ASC, full_name ASC
        """
        return db.session.execute(text(sql)).mappings().all()

    def get_least_busy_analyst_by_department(self, department_id: int):
        """
        Retorna el analista del departamento con menor carga de tickets abiertos.
        Si hay empate, retorna el primero alfabéticamente.
        """
        sql = """
        SELECT 
            u.id,
            CONCAT(u.names_worker, ' ', u.last_name) AS full_name,
            COUNT(t.id) AS open_count
        FROM users u
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id
        LEFT JOIN tickets t ON t.assignee_id = u.id AND t.status_id IN (
            SELECT id FROM statuses WHERE name IN ('NUEVO','ASIGNADO','EN_PROGRESO')
        )
        WHERE 
            u.is_active = 1
            AND u.department_id = :dept
            AND UPPER(r.name) = 'ANALYST'
        GROUP BY u.id, full_name
        ORDER BY open_count ASC, full_name ASC
        LIMIT 1
        """
        return db.session.execute(text(sql), {"dept": int(department_id)}).mappings().first()
    
    # ===== Notificaciones =====
    def insert_notification(self, *, user_id: int, ticket_id: int,
                        kind: str, message: str):
        """
        Inserta una notificación en la tabla ticket_notifications
        y, si es posible, envía un correo al usuario.
        Si el envío de correo falla, NO rompe la app.
        """
        # 1) Insertar en la BD (igual que antes)
        db.session.execute(
            text("""
                INSERT INTO ticket_notifications (user_id, ticket_id, kind, message)
                VALUES (:u, :t, :k, :m)
            """),
            {
                "u": int(user_id),
                "t": int(ticket_id),
                "k": kind,
                "m": message[:255],
            },
        )
        db.session.commit()

        # 2) Intentar enviar correo (best-effort, no crítico)
        try:
            # Traemos el correo del usuario desde la tabla users
            result = db.session.execute(
                text("SELECT email FROM users WHERE id = :uid"),
                {"uid": int(user_id)},
            )
            row = result.first()
            if not row:
                return  # no hay correo, no enviamos nada

            to_email = row[0]

            # Título amigable según tipo de notificación
            subject_map = {
                "ASSIGNED": "Nuevo ticket asignado",
                "RESOLVED": "Tu ticket ha sido resuelto",
                "CLOSED":   "Tu ticket ha sido cerrado",
            }
            title = subject_map.get(kind, "Notificación de Incidex")

            # Usamos el helper que ya tienes en support_mail.py
            send_notification_email(to_email, title, message)

        except Exception as e:
            # Importante: NO romper nada si falla el correo
            current_app.logger.warning(f"[Email Notification Error] {e}")



    def list_unread_notifications(self, user_id: int, limit: int = 10):
        return db.session.execute(text("""
            SELECT
              id,
              ticket_id,
              kind,
              message,
              is_read,
              DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') AS created_at
            FROM ticket_notifications
            WHERE user_id = :u AND is_read = 0
            ORDER BY created_at DESC
            LIMIT :lim
        """), {"u": int(user_id), "lim": int(limit)}).mappings().all()

    def mark_all_notifications_read_for_user(self, user_id: int):
        db.session.execute(text("""
            UPDATE ticket_notifications
            SET is_read = 1
            WHERE user_id = :u AND is_read = 0
        """), {"u": int(user_id)})
        db.session.commit()

