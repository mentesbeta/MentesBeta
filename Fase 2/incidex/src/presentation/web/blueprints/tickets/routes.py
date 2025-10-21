from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, abort
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
    data = svc.dashboard_data(current_user.id, limit=10)
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

# ======== CREATE (POST) ========
@tickets.post('/tickets/create', endpoint='create_post')
@login_required
def create_post():
    svc = TicketService(TicketRepository())
    form = TicketCreateForm()
    cats = _bind_choices(form, svc)

    if not form.validate_on_submit():
        return render_template('tickets/create.html', title='Crear Ticket', form=form, cats=cats), 400

    created = svc.create(
        requester_id=current_user.id,
        subject=form.subject.data,
        details=form.details.data,
        category_id=form.category_id.data,
        department_id=form.department_id.data,
        priority_id=form.priority_id.data,
        assignee_id=form.assignee_id.data,
    )
    return redirect(url_for('tickets.dashboard'))


# ===== DETALLE =====
@tickets.get('/detail/<int:ticket_id>', endpoint='detail')
@login_required
def detail(ticket_id):
    svc = TicketService(TicketRepository())
    # roles del usuario (nombres) — si no tienes un servicio, puedes sacarlos rápido
    roles = [r.name for r in getattr(current_user, "roles", [])] if hasattr(current_user, "roles") else []
    bundle = svc.detail(ticket_id, viewer_id=current_user.id, viewer_roles=roles)
    if not bundle:
        abort(404)
    return render_template('tickets/detail.html', title=f"{bundle.ticket['code']}", **bundle.__dict__)

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
        flash("Comentario agregado.", "success")
    except ValueError as e:
        flash(str(e), "error")
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


# ====== PLACEHOLDERS (para evitar errores 404/BuildError) ======
@tickets.route('/mine', endpoint='mine')
@login_required
def mine():
    return render_template('tickets/placeholder.html', title='Mis Tickets')

@tickets.route('/reports', endpoint='reports')
@login_required
def reports():
    return render_template('tickets/placeholder.html', title='Reportes')

@tickets.route('/all', endpoint='all')
@login_required
def all_tickets():
    return render_template('tickets/placeholder.html', title='Todos los Tickets')
