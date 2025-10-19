from flask import Blueprint, render_template
from flask_login import login_required

tickets = Blueprint('tickets', __name__, url_prefix='/app')


# ====== DASHBOARD (home del usuario) ======
@tickets.route('/dashboard', endpoint='dashboard')
@login_required
def dashboard():
    kpis = {
        "open": 12,
        "in_progress": 5,
        "overdue": 2,
        "closed_week": 8
    }
    tickets_data = []  # temporal, hasta tener base de datos
    return render_template('tickets/dashboard.html', title='Panel', kpis=kpis, tickets=tickets_data)


# ====== PLACEHOLDERS (para evitar errores 404/BuildError) ======
@tickets.route('/mine', endpoint='mine')
@login_required
def mine():
    return render_template('tickets/placeholder.html', title='Mis Tickets')

@tickets.route('/create', endpoint='create', methods=['GET', 'POST'])
@login_required
def create():
    return render_template('tickets/create.html',title='Crear Ticket')

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
