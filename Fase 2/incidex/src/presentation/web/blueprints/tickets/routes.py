from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, abort, jsonify
from flask_login import login_required, current_user

from src.presentation.web.blueprints.tickets.forms import TicketCreateForm
from src.application.use_cases.ticket_service import TicketService
from src.infrastructure.persistence.repositories.ticket_repository import TicketRepository

tickets = Blueprint('tickets', __name__, url_prefix='/app')


@tickets.route('/dashboard', endpoint='dashboard')
@login_required
def dashboard():
    # Crear el servicio con su repositorio
    svc = TicketService(TicketRepository())

    # Obtener los datos del dashboard
    data = svc.dashboard_data(current_user.id, limit=5)
    recent = list(data["recent"])
    # Renderizar la vista
    return render_template(
        'tickets/dashboard.html',
        title='Panel',
        kpis=data["kpis"],
        recent=recent,
        recent_len=len(recent)
    )

def _bind_choices(form: TicketCreateForm, svc: TicketService):
    cats = svc.catalogs()
    form.category_id.choices   = [(c["id"], c["name"]) for c in cats.categories]
    form.department_id.choices = [(d["id"], d["name"]) for d in cats.departments]
    form.priority_id.choices   = [(p["id"], p["name"]) for p in cats.priorities]
    analysts = [(0, "— Sin asignar —")] + [(a["id"], a["full_name"]) for a in cats.analysts]
    form.assignee_id.choices = analysts
    return cats 

# ======== CREATE (GET) =========
@tickets.get('/tickets/create', endpoint='create')
@login_required
def create_get():
    svc = TicketService(TicketRepository())
    form = TicketCreateForm()
    cats = _bind_choices(form, svc)
    return render_template('tickets/create.html', title='Crear Ticket', form=form, cats=cats)


@tickets.get("/analysts/by-dept")
@login_required
def api_analysts_by_dept():
    svc = TicketService(TicketRepository())
    return jsonify(svc.analysts_by_dept_map())


# ======== CREATE (POST) ========
@tickets.post('/create', endpoint='create_post')
@login_required
def create_post():
    svc = TicketService(TicketRepository())

    subject        = (request.form.get('subject') or '').strip()
    details        = (request.form.get('details') or '').strip()
    category_id    = request.form.get('category_id', type=int)
    department_id  = request.form.get('department_id', type=int)
    priority_id    = request.form.get('priority_id', type=int)
    assignee_id    = request.form.get('assignee_id', type=int)  # puede venir 0

    # Fallback de autoasignación en backend
    if (not assignee_id) and department_id:
        abd = svc.analysts_by_dept_map()
        lst = abd.get(int(department_id), [])
        if lst:
            assignee_id = int(lst[0]['id'])  # toma el primero pero revisemos si luego lo cambio

    try:
        created = svc.create(
            requester_id=current_user.id,
            subject=subject,
            details=details,
            category_id=category_id,
            department_id=department_id,
            priority_id=priority_id,
            assignee_id=assignee_id if assignee_id else None
        )
        return redirect(url_for('tickets.detail', ticket_id=created.id))
    except Exception as e:
        current_app.logger.exception("Error creando ticket")
        return redirect(url_for('tickets.create'))



# ===== DETALLE CON CAMBIOS DE ESTADO Y ASIGNAR =====
@tickets.get('/detail/<int:ticket_id>', endpoint='detail')
@login_required
def detail(ticket_id: int):
    svc = TicketService(TicketRepository())
    roles = [r.name for r in getattr(current_user, "roles", [])] if hasattr(current_user, "roles") else []
    bundle = svc.detail(ticket_id, viewer_id=current_user.id, viewer_roles=roles)
    if not bundle:
        abort(404)

    repo = TicketRepository()
    statuses = repo.get_statuses()
    tmin = repo.get_ticket_minimal(ticket_id)
    current_status_id = tmin["status_id"] if tmin else None
    current_assignee_id = tmin["assignee_id"] if tmin else None

    roles_up = {(r or "").upper() for r in roles}
    is_admin = "ADMIN" in roles_up
    is_analyst = "ANALYST" in roles_up
    is_request = "REQUESTER" in roles_up
    is_assignee = (current_assignee_id == current_user.id)

    assignables = repo.list_assignables_for_actor(current_user.id, roles_up)

    return render_template(
        'tickets/detail.html',
        title=f'{bundle.ticket["code"]} · {bundle.ticket["title"]}',
        ticket=bundle.ticket,
        comments=bundle.comments,
        attachments=bundle.attachments,
        history=bundle.history,
        can_act=bundle.can_act,
        statuses=statuses,
        current_status_id=current_status_id,
        current_assignee_id=current_assignee_id,
        assignables=assignables,
        is_admin=is_admin,
        is_analyst=is_analyst,
        is_request=is_request,
        is_assignee=is_assignee,
    )



@tickets.post('/detail/<int:ticket_id>/status', endpoint='change_status')
@login_required
def change_status(ticket_id: int):
    svc = TicketService(TicketRepository())
    roles = [r.name for r in getattr(current_user, "roles", [])] if hasattr(current_user, "roles") else []
    bundle = svc.detail(ticket_id, viewer_id=current_user.id, viewer_roles=roles)
    if not bundle:
        abort(404)
    if not bundle.can_act:
        abort(403)

    to_status_id = request.form.get("to_status_id", type=int)
    note = request.form.get("note", "")

    if not to_status_id:
        print("Selecciona un estado válido.", "error")
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))

    try:
        svc.change_status(
            ticket_id=ticket_id,
            actor_id=current_user.id,
            actor_roles=roles,
            to_status_id=to_status_id,
            note=note
        )
        print("Estado actualizado y registrado en el historial.", "ok")
    except PermissionError as e:
        print(str(e), "error")
        return abort(403)
    except Exception as e:
        print(str(e), "error")
        print("No se pudo cambiar el estado.", "error")

    return redirect(url_for('tickets.detail', ticket_id=ticket_id))

@tickets.post('/detail/<int:ticket_id>/assign', endpoint='assign')
@login_required
def assign(ticket_id: int):
    svc = TicketService(TicketRepository())
    roles = [r.name for r in getattr(current_user, "roles", [])] if hasattr(current_user, "roles") else []
    bundle = svc.detail(ticket_id, viewer_id=current_user.id, viewer_roles=roles)
    if not bundle:
        abort(404)
    if not bundle.can_act:
        abort(403)

    new_assignee_id = request.form.get("assignee_id", type=int)
    note = request.form.get("note", "")

    try:
        svc.reassign(
            ticket_id=ticket_id,
            actor_id=current_user.id,
            actor_roles=roles,
            new_assignee_id=new_assignee_id,
            note=note
        )
    except PermissionError as e:
        print(str(e), "error")
        return abort(403)
    except Exception:
        print("No se pudo actualizar la asignación.", "error")

    return redirect(url_for('tickets.detail', ticket_id=ticket_id))

# ===== COMENTAR =====
@tickets.post('/detail/<int:ticket_id>/comment', endpoint='comment')
@login_required
def add_comment(ticket_id):
    svc = TicketService(TicketRepository())
    roles = [r.name for r in getattr(current_user, "roles", [])] if hasattr(current_user, "roles") else []
    bundle = svc.detail(ticket_id, viewer_id=current_user.id, viewer_roles=roles)
    if not bundle:
        abort(404)
    if not bundle.can_act:
        abort(403)

    try:
        svc.add_comment(ticket_id, current_user.id, request.form.get("body", ""))
        print("Comentario agregado.", "success")
    except ValueError as e:
        print(str(e), "error")
    return redirect(url_for('tickets.detail', ticket_id=ticket_id))

# ===== ADJUNTAR ARCHIVO =====
@tickets.post('/detail/<int:ticket_id>/upload', endpoint='upload')
@login_required
def upload(ticket_id):
    svc = TicketService(TicketRepository())
    roles = [r.name for r in getattr(current_user, "roles", [])] if hasattr(current_user, "roles") else []
    bundle = svc.detail(ticket_id, viewer_id=current_user.id, viewer_roles=roles)
    if not bundle:
        abort(404)
    if not bundle.can_act:
        abort(403)

    file = request.files.get("file")
    try:
        att_id = svc.add_attachment(ticket_id, current_user.id, file, current_app.config.get("UPLOAD_FOLDER", "var/uploads"))
        flash("Archivo adjuntado.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for('tickets.detail', ticket_id=ticket_id))

# ===== DESCARGA SEGURA =====
@tickets.get('/detail/<int:ticket_id>/file/<int:att_id>', endpoint='download')
@login_required
def download(ticket_id, att_id):
    repo = TicketRepository()
    meta = repo.get_attachment_path(att_id, ticket_id)
    if not meta:
        abort(404)
    # (opcional) validar que el usuario puede ver el ticket (requester o assignee)
    return send_file(meta["file_path"], as_attachment=True, download_name=meta["file_name"])


@tickets.route('/mine', endpoint='mine')
@login_required
def mine():
    svc = TicketService(TicketRepository())

    # Parámetros GET
    q            = request.args.get("q") or None
    status_id    = request.args.get("status_id", type=int)
    priority_id  = request.args.get("priority_id", type=int)
    category_id  = request.args.get("category_id", type=int)
    date_from    = request.args.get("from") or None
    date_to      = request.args.get("to") or None
    page         = request.args.get("page", default=1, type=int)
    per_page     = request.args.get("per_page", default=10, type=int)

    roles = [r.name for r in getattr(current_user, "roles", [])] if hasattr(current_user, "roles") else []

    data = svc.scoped_list(
        current_user.id, roles,
        q=q, status_id=status_id, priority_id=priority_id, category_id=category_id,
        date_from=date_from, date_to=date_to, page=page, per_page=per_page
    )

    # título según rol
    roles_up = {(r or "").upper() for r in roles}
    if "ADMIN" in roles_up:
        page_title = "Todos los tickets"
    elif "ANALYST" in roles_up:
        page_title = "Tickets del departamento y propios"
    else:
        page_title = "Mis Tickets (creados o asignados)"

    return render_template(
        'tickets/list.html',
        title=page_title,
        items=data["items"],
        total=data["total"],
        page=data["page"],
        pages=data["pages"],
        per_page=data["per_page"],
        filters=data["filters"],
        catalogs=data["catalogs"]
    )



# ====== PLACEHOLDERS (para evitar errores 404/BuildError) ======

@tickets.route('/reports', endpoint='reports')
@login_required
def reports():
    return render_template('tickets/placeholder.html', title='Reportes')


