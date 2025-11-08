from dataclasses import dataclass
from src.infrastructure.ai.gemini_client import suggest_ticket_metadata

ADMIN_ROLES = {"ADMIN"}

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

@dataclass
class AISuggestion:
    category_id: int | None
    priority_id: int | None
    department_id: int | None
    reason: str | None = None


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
    
    def ai_suggest_metadata(self, title: str, details: str) -> AISuggestion | None:
        """
        Pide a Gemini que sugiera categoría, prioridad y departamento.
        """
        cats = self.repo.get_categories()
        deps = self.repo.get_departments()
        pris = self.repo.get_priorities()

        raw = suggest_ticket_metadata(
            title=title,
            description=details,
            categories=cats,
            priorities=pris,
            departments=deps,
        )
        if not raw:
            return None

        def safe_int(key):
            try:
                v = raw.get(key)
                return int(v) if v is not None else None
            except Exception:
                return None

        return AISuggestion(
            category_id=safe_int("category_id"),
            priority_id=safe_int("priority_id"),
            department_id=safe_int("department_id"),
            reason=raw.get("reason"),
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
        return any((r or "").upper() in ADMIN_ROLES for r in (roles or []))

    # == permisos para asignar ==
    def detail(self, ticket_id: int, viewer_id: int, viewer_roles: list[str]) -> TicketBundle | None:
        t = self.repo.detail(ticket_id)
        if not t:
            return None

        roles_up = {(r or "").upper() for r in (viewer_roles or [])}
        is_admin = "ADMIN" in roles_up
        is_analyst = "ANALYST" in roles_up

        # depto del ticket y del usuario
        ticket_dept_id = getattr(t, "department_id", None)
        user_dept_id = self.repo.get_user_department_id(viewer_id)

        same_dept = (
            ticket_dept_id is not None
            and user_dept_id is not None
            and int(ticket_dept_id) == int(user_dept_id)
        )

        # Reglas de quién puede "actuar" (cambiar estado / asignar)
        can_act = False

        if is_admin:
            can_act = True
        elif is_analyst and same_dept:
            # Analista SOLO si es del mismo departamento
            can_act = True

        # El asignado SIEMPRE puede actuar sobre su ticket (rol aparte)
        if t.assignee_id == viewer_id:
            can_act = True

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

    # ====== Listado “Mis Tickets” (legacy) ======
    def mine_list(
        self,
        user_id: int,
        *,
        q: str | None = None,
        status_id: int | None = None,
        priority_id: int | None = None,
        category_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        per_page: int = 10
    ):
        items, total = self.repo.list_mine(
            user_id,
            q=q,
            status_id=status_id,
            priority_id=priority_id,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            per_page=per_page
        )
        pages = max((total + per_page - 1) // per_page, 1)
        catalogs = {
            "statuses": self.repo.get_statuses(),
            "priorities": self.repo.get_priorities(),
            "categories": self.repo.get_categories(),
        }
        filters = {
            "q": q or "",
            "status_id": int(status_id) if status_id else None,
            "priority_id": int(priority_id) if priority_id else None,
            "category_id": int(category_id) if category_id else None,
            "from": date_from or "",
            "to": date_to or "",
        }
        return {
            "items": items,
            "total": total,
            "page": int(page),
            "pages": int(pages),
            "per_page": int(per_page),
            "filters": filters,
            "catalogs": catalogs
        }

    # ====== NUEVO: Listado con alcance por rol ======
    def scoped_list(
        self,
        user_id: int,
        roles: list[str],
        *,
        q: str | None = None,
        status_id: int | None = None,
        priority_id: int | None = None,
        category_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        per_page: int = 10
    ):
        roles_up = {(r or "").upper() for r in (roles or [])}
        is_admin = "ADMIN" in roles_up
        is_analyst = "ANALYST" in roles_up

        if is_admin:
            items, total = self.repo.list_all(
                q=q, status_id=status_id, priority_id=priority_id, category_id=category_id,
                date_from=date_from, date_to=date_to, page=page, per_page=per_page
            )
        elif is_analyst:
            dept_id = self.repo.get_user_department_id(user_id)
            if not dept_id:
                items, total = [], 0
            else:
                items, total = self.repo.list_by_department_or_creator(
                    department_id=dept_id,
                    user_id=user_id,
                    q=q, status_id=status_id, priority_id=priority_id, category_id=category_id,
                    date_from=date_from, date_to=date_to, page=page, per_page=per_page
                )
        else:
            # REQUESTER: asignados o creados por él
            items, total = self.repo.list_mine(
                user_id, q=q, status_id=status_id, priority_id=priority_id, category_id=category_id,
                date_from=date_from, date_to=date_to, page=page, per_page=per_page
            )

        pages = max((total + per_page - 1) // per_page, 1)
        catalogs = {
            "statuses": self.repo.get_statuses(),
            "priorities": self.repo.get_priorities(),
            "categories": self.repo.get_categories(),
        }
        filters = {
            "q": q or "",
            "status_id": int(status_id) if status_id else None,
            "priority_id": int(priority_id) if priority_id else None,
            "category_id": int(category_id) if category_id else None,
            "from": date_from or "",
            "to": date_to or "",
        }
        return {
            "items": items,
            "total": total,
            "page": int(page),
            "pages": int(pages),
            "per_page": int(per_page),
            "filters": filters,
            "catalogs": catalogs
        }

    # ===== Cambio de estado =====

    def change_status(
        self,
        *,
        ticket_id: int,
        actor_id: int,
        actor_roles: list[str],
        to_status_id: int,
        note: str | None = None
        ):
            tmin = self.repo.get_ticket_minimal(ticket_id)
            if not tmin:
                raise ValueError("Ticket no existe")

            roles_up = {(r or "").upper() for r in (actor_roles or [])}
            is_admin    = "ADMIN" in roles_up
            is_analyst  = "ANALYST" in roles_up
            is_request  = "REQUESTER" in roles_up

            requester_id = tmin.get("requester_id")
            assignee_id  = tmin.get("assignee_id")
            status_id    = tmin.get("status_id")

            is_assignee       = (assignee_id == actor_id)
            is_ticket_creator = (requester_id == actor_id)

            # nombre del nuevo estado
            target_name = (self.repo.get_status_name(int(to_status_id)) or "").upper()

            # --- Validación normal de permisos ---
            def can_change_to(target: str) -> bool:
                t = (target or "").upper()

                if is_admin:
                    return True

                # Analista puede pasar por todo el flujo técnico
                if is_analyst:
                    return t in {"EN_PROGRESO", "ASIGNADO", "RECHAZADO", "CERRADO"}

                # Requester puede marcar resuelto si lo creó
                if is_request and t == "RESUELTO":
                    return True

                # Cualquier asignado puede avanzar a EN_PROGRESO
                if is_assignee and t == "EN_PROGRESO":
                    return True

                return False

            if not can_change_to(target_name):
                raise PermissionError("No tienes permiso para cambiar a este estado")

            # --- Actualizamos el estado ---
            self.repo.update_status_with_history(
                ticket_id=ticket_id,
                to_status_id=int(to_status_id),
                actor_user_id=actor_id,
                note=note,
            )

            # --- NUEVO: si pasa a RESUELTO por un requester ---
            if target_name == "RESUELTO":
                # buscamos depto del ticket
                dept_id = self.repo.get_ticket_minimal(ticket_id).get("department_id")
                if dept_id:
                    # elegimos el analista con menor carga
                    analyst = self.repo.get_least_busy_analyst_by_department(dept_id)
                    if analyst:
                        self.repo.update_assignee_with_history(
                            ticket_id=ticket_id,
                            new_assignee_id=analyst["id"],
                            actor_user_id=actor_id,
                            note="Autoasignado al analista para revisión y cierre (flujo automático)",
                        )
            
            # Notificación para el solicitante cuando se RESUELVE o se CIERRA
            tmin = self.repo.get_ticket_minimal(ticket_id)
            if tmin:
                requester_id = tmin.get("requester_id")
                code = tmin.get("code")
                target_name = (self.repo.get_status_name(int(to_status_id)) or "").upper()

                if requester_id and target_name in {"RESUELTO", "CERRADO"}:
                    if target_name == "RESUELTO":
                        msg = f"Tu ticket {code} ha sido marcado como RESUELTO."
                        kind = "RESOLVED"
                    else:
                        msg = f"Tu ticket {code} ha sido CERRADO."
                        kind = "CLOSED"

                    self.repo.insert_notification(
                        user_id=int(requester_id),
                        ticket_id=ticket_id,
                        kind=kind,
                        message=msg,
                    )


    # ===== Reasignar =====
    def reassign(
            self,
            *,
            ticket_id: int,
            actor_id: int,
            actor_roles: list[str] | None,
            new_assignee_id: int | None,
            note: str | None = None
        ):
            tmin = self.repo.get_ticket_minimal(ticket_id)
            if not tmin:
                raise ValueError("Ticket no existe")

            roles_up = {(r or "").upper() for r in (actor_roles or [])}
            is_admin = "ADMIN" in roles_up
            is_analyst = "ANALYST" in roles_up

            ticket_dept_id = tmin.get("department_id")
            user_dept_id = self.repo.get_user_department_id(actor_id)

            # Solo admin o analista del mismo depto
            if not is_admin:
                if not is_analyst or not ticket_dept_id or ticket_dept_id != user_dept_id:
                    raise PermissionError("No tienes permiso para reasignar este ticket")

            # Si intenta reasignar al mismo usuario → ignoramos
            if tmin["assignee_id"] == new_assignee_id:
                return

            # Validar destinatario válido
            if not new_assignee_id:
                raise PermissionError("Debes seleccionar un destinatario válido")

            # Actualizamos con historial
            self.repo.update_assignee_with_history(
                ticket_id=ticket_id,
                new_assignee_id=int(new_assignee_id),
                actor_user_id=actor_id,
                note=note,
            )

            # Notificación para el nuevo asignado
            tmin = self.repo.get_ticket_minimal(ticket_id)
            if tmin and new_assignee_id:
                msg = f"Se te ha asignado el ticket {tmin['code']}."
                self.repo.insert_notification(
                    user_id=int(new_assignee_id),
                    ticket_id=ticket_id,
                    kind="ASSIGNED",
                    message=msg,
                )


    # ===== Apoyo front (autoasignar por depto) =====

    def analysts_by_dept_map(self) -> dict[int, list[dict]]:
        """
        Devuelve { dept_id: [ {id, full_name, load}, ... ] }.
        La lista ya viene ordenada por menor carga, luego por nombre.
        """
        rows = self.repo.list_analysts_by_department_with_load()
        out: dict[int, list[dict]] = {}
        for r in rows:
            did = int(r["department_id"]) if r["department_id"] is not None else 0
            out.setdefault(did, []).append({
                "id": int(r["id"]),
                "full_name": r["full_name"],
                "load": int(r["open_count"] or 0),
            })
        return out

