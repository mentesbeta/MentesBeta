from dataclasses import dataclass
from typing import Any, Dict, List

ADMIN_ROLES = {"ADMIN", "ANALYST"}

@dataclass
class CatalogsDTO:
    categories: list
    departments: list
    priorities: list
    analysts: list

@dataclass
class KPIsDTO:
    open: int
    in_progress: int
    closed_week: int

@dataclass
class TicketBundle:
    ticket: dict
    comments: list
    attachments: list
    history: list
    can_act: bool

class TicketService:
    def __init__(self, repo):
        self.repo = repo

    def catalogs(self) -> CatalogsDTO:
        return CatalogsDTO(
            categories = self.repo.get_categories(),
            departments = self.repo.get_departments(),
            priorities = self.repo.get_priorities(),
            analysts = self.repo.get_analysts()
        )

    # ======= Crear ticket =======
    def create(self, *, requester_id: int, subject: str, details: str,
               category_id: int, department_id: int, priority_id: int, assignee_id: int | None):
        code = self.repo.next_ticket_code()
        created = self.repo.insert_ticket(
            code=code,
            title=subject.strip(),
            description=details.strip(),
            requester_id=requester_id,
            department_id=department_id,
            category_id=category_id,
            priority_id=priority_id,
            assignee_id=assignee_id
        )
        return created
    
    def dashboard_data(self, user_id: int, limit: int = 10):
        return {
            "kpis": self.repo.kpis_for_user(user_id),
            "recent": self.repo.recent_for_user(user_id, limit=limit),
        }
    
    def _has_role(self, roles: list[str]) -> bool:
        # roles es una lista de nombres de rol del usuario
        return any(r in ADMIN_ROLES for r in roles)

    def detail(self, ticket_id: int, viewer_id: int, viewer_roles: list[str]) -> TicketBundle | None:
        t = self.repo.detail(ticket_id)
        if not t:
            return None
        can_act = (t.assignee_id == viewer_id) or self._has_role(viewer_roles)
        return TicketBundle(
            ticket=t.__dict__,
            comments=self.repo.comments(ticket_id),
            attachments=self.repo.attachments(ticket_id),
            history=self.repo.history(ticket_id),
            can_act=can_act
        )

    def add_comment(self, ticket_id: int, author_id: int, text: str):
        text = (text or "").strip()
        if not text:
            raise ValueError("Comentario vacío")
        self.repo.add_comment(ticket_id, author_id, text)

    def add_attachment(self, ticket_id: int, uploader_id: int, file_storage, upload_dir: str):
        if not file_storage or not file_storage.filename:
            raise ValueError("Archivo requerido")
        return self.repo.save_attachment(
            ticket_id=ticket_id, uploader_id=uploader_id,
            file_storage=file_storage, upload_dir=upload_dir
        )
