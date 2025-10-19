import click
from datetime import date
from sqlalchemy import text
from flask.cli import with_appcontext

from src.infrastructure.persistence.database import db
from src.domain.entities.user import User

@click.command("create-user")
@with_appcontext
@click.option("--names", prompt=True, help="Nombres del usuario")
@click.option("--last", prompt=True, help="Apellidos del usuario")
@click.option("--email", prompt=True, help="Correo único (login)")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True,
              help="Contraseña segura del usuario")
@click.option("--gender", default="X", show_default=True,
              type=click.Choice(["M", "F", "X", "N/A"]))
@click.option("--birthdate", default="1990-01-01", show_default=True,
              help="Fecha de nacimiento (YYYY-MM-DD)")
@click.option("--department-id", default=1, show_default=True,
              help="ID del departamento (de la tabla departments)")
@click.option("--role", default="ADMIN", show_default=True,
              type=click.Choice(["ADMIN", "ANALYST", "REQUESTER", "QA"]))
def create_user_cmd(names, last, email, password, gender, birthdate, department_id, role):
    """Crea un usuario real en MySQL y le asigna un rol existente."""
    try:
        # Evitar duplicados
        if User.query.filter_by(email=email.lower()).first():
            click.secho(" Ya existe un usuario con ese correo.", fg="red")
            return

        # Crear usuario
        u = User(
            names_worker=names,
            last_name=last,
            birthdate=date.fromisoformat(birthdate),
            email=email.lower(),
            gender=gender,
            department_id=department_id,
            is_active=True
        )
        u.set_password(password)
        db.session.add(u)
        db.session.flush()  # obtener u.id

        # Asignar rol
        role_id = db.session.execute(
            text("SELECT id FROM roles WHERE name = :name"),
            {"name": role}
        ).scalar()

        if not role_id:
            click.secho(f" No se encontró el rol '{role}' en roles.", fg="yellow")
        else:
            db.session.execute(
                text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid)"),
                {"uid": u.id, "rid": role_id}
            )

        db.session.commit()
        click.secho(" Usuario creado correctamente:", fg="green")
        click.echo(f"  ID: {u.id}")
        click.echo(f"  Nombre: {u.names_worker} {u.last_name}")
        click.echo(f"  Email: {u.email}")
        click.echo(f"  Rol: {role}")
    except Exception as e:
        db.session.rollback()
        click.secho(f" Error: {e}", fg="red")
