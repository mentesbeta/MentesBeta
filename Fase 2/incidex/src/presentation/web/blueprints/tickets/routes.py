from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from src.presentation.web.blueprints.tickets.forms import TicketCreateForm
from src.application.use_cases.ticket_service import TicketService
from src.infrastructure.persistence.repositories.ticket_repository import TicketRepository

tickets = Blueprint('tickets', __name__, url_prefix='/app')


@tickets.route('/dashboard', endpoint='dashboard')
@login_required
def dashboard():
    kpis = {"open": 12, "in_progress": 5, "overdue": 2, "closed_week": 8}
    tickets_data = []
    return render_template('tickets/dashboard.html', title='Panel', kpis=kpis, tickets=tickets_data)

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

@tickets.route('/detail/<int:ticket_id>', endpoint='detail')
@login_required
def detail(ticket_id):
    return render_template('tickets/placeholder.html', title=f'Ticket {ticket_id}')
