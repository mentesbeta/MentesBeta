# tests/integration/test_db_integridad.py

import pytest
import pymysql.err


def test_ai_suggestions_rechaza_ticket_inexistente(db_conn):
    """
    Intenta insertar una sugerencia de IA con un ticket inexistente.
    Se espera un error de integridad referencial (Foreign Key fk_ai_ticket).
    """
    with db_conn.cursor() as cur:
        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO ai_suggestions (ticket_id, model, summary)
                VALUES (%s, %s, %s)
                """,
                (999999, "pytest-model", "test summary"),
            )


def test_users_rechaza_email_null(db_conn):
    """
    Intenta crear un usuario sin email (NULL).
    Se espera un error de integridad (NOT NULL en email).
    """
    with db_conn.cursor() as cur:
        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO users
                    (names_worker, last_name, birthdate, email, gender,
                     password_hash, department_id, is_active)
                VALUES
                    (%s, %s, %s, %s, %s,
                     %s, %s, %s)
                """,
                (
                    "UsuarioPruebaNull",
                    "SinEmail",
                    "1990-01-01",
                    None,              # email NULL → debe fallar
                    "M",
                    "hash_de_prueba",
                    1,
                    1,
                )
            )


def test_email_unico_en_users(db_conn, test_user):
    """
    Verifica que no se pueda crear otro usuario con el mismo email
    que el usuario de prueba (test@example.com).
    """
    with db_conn.cursor() as cur:
        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO users
                    (names_worker, last_name, birthdate, email, gender,
                     password_hash, department_id, is_active)
                VALUES
                    (%s, %s, %s, %s, %s,
                     %s, %s, %s)
                """,
                (
                    "OtroUsuario",
                    "Duplicado",
                    "1995-01-01",
                    "test@example.com",  # mismo email que el fixture
                    "M",
                    "hash_de_prueba",
                    1,
                    1,
                )
            )


def test_ticket_rechaza_requester_inexistente(db_conn):
    """
    Intenta crear un ticket con requester_id que no existe en users.
    Debe fallar por FK fk_t_req.
    """
    with db_conn.cursor() as cur:
        # usamos prioridades/estados válidos
        cur.execute("SELECT id FROM priorities LIMIT 1")
        pri_row = cur.fetchone()
        assert pri_row is not None
        priority_id = pri_row[0]

        cur.execute("SELECT id FROM statuses LIMIT 1")
        sta_row = cur.fetchone()
        assert sta_row is not None
        status_id = sta_row[0]

        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO tickets
                    (code, title, description, requester_id,
                     priority_id, status_id)
                VALUES
                    (%s, %s, %s, %s,
                     %s, %s)
                """,
                (
                    "BAD-REQ-1",
                    "Ticket con requester inválido",
                    "No debería insertarse",
                    999999,          # requester_id inexistente
                    priority_id,
                    status_id,
                )
            )


def test_user_roles_rechaza_user_inexistente(db_conn):
    """
    Intenta insertar en user_roles con user_id inexistente.
    Debe fallar por FK fk_ur_user.
    """
    with db_conn.cursor() as cur:
        # Tomamos un role_id existente
        cur.execute("SELECT id FROM roles LIMIT 1")
        row = cur.fetchone()
        assert row is not None, "No hay registros en roles"
        role_id = row[0]

        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
                """,
                (999999, role_id)  # user inexistente
            )


def test_user_roles_rechaza_role_inexistente(db_conn, test_user):
    """
    Intenta insertar en user_roles con role_id inexistente.
    Debe fallar por FK fk_ur_role.
    """
    with db_conn.cursor() as cur:
        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
                """,
                (int(test_user), 999999)  # role inexistente
            )


def test_ai_suggestions_rechaza_categoria_inexistente(db_conn, test_user):
    """
    Intenta insertar ai_suggestions con suggested_category_id inexistente.
    Debe fallar por FK fk_ai_cat.
    """
    with db_conn.cursor() as cur:
        # Creamos primero un ticket válido real
        cur.execute("SELECT id FROM priorities LIMIT 1")
        pri_row = cur.fetchone()
        assert pri_row is not None
        priority_id = pri_row[0]

        cur.execute("SELECT id FROM statuses LIMIT 1")
        sta_row = cur.fetchone()
        assert sta_row is not None
        status_id = sta_row[0]

        cur.execute(
            """
            INSERT INTO tickets
                (code, title, description, requester_id,
                 priority_id, status_id)
            VALUES
                ('AI-CAT-1', 'Ticket IA cat', 'Para probar FK cat',
                 %s, %s, %s)
            """,
            (int(test_user), priority_id, status_id)
        )
        ticket_id = cur.lastrowid

        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO ai_suggestions
                    (ticket_id, model, suggested_category_id)
                VALUES (%s, %s, %s)
                """,
                (ticket_id, "pytest-model", 999999)  # categoría inexistente
            )


def test_ai_suggestions_rechaza_prioridad_inexistente(db_conn, test_user):
    """
    Intenta insertar ai_suggestions con suggested_priority_id inexistente.
    Debe fallar por FK fk_ai_pri.
    """
    with db_conn.cursor() as cur:
        # Creamos ticket válido
        cur.execute("SELECT id FROM priorities LIMIT 1")
        pri_row = cur.fetchone()
        assert pri_row is not None
        priority_id = pri_row[0]

        cur.execute("SELECT id FROM statuses LIMIT 1")
        sta_row = cur.fetchone()
        assert sta_row is not None
        status_id = sta_row[0]

        cur.execute(
            """
            INSERT INTO tickets
                (code, title, description, requester_id,
                 priority_id, status_id)
            VALUES
                ('AI-PRI-1', 'Ticket IA pri', 'Para probar FK pri',
                 %s, %s, %s)
            """,
            (int(test_user), priority_id, status_id)
        )
        ticket_id = cur.lastrowid

        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO ai_suggestions
                    (ticket_id, model, suggested_priority_id)
                VALUES (%s, %s, %s)
                """,
                (ticket_id, "pytest-model", 999999)  # prioridad inexistente
            )


def test_ai_suggestions_rechaza_accepted_by_inexistente(db_conn, test_user):
    """
    Intenta insertar ai_suggestions con accepted_by apuntando a user inexistente.
    Debe fallar por FK fk_ai_user.
    """
    with db_conn.cursor() as cur:
        # Creamos ticket válido
        cur.execute("SELECT id FROM priorities LIMIT 1")
        pri_row = cur.fetchone()
        assert pri_row is not None
        priority_id = pri_row[0]

        cur.execute("SELECT id FROM statuses LIMIT 1")
        sta_row = cur.fetchone()
        assert sta_row is not None
        status_id = sta_row[0]

        cur.execute(
            """
            INSERT INTO tickets
                (code, title, description, requester_id,
                 priority_id, status_id)
            VALUES
                ('AI-ACC-1', 'Ticket IA accepted', 'Para probar FK accepted_by',
                 %s, %s, %s)
            """,
            (int(test_user), priority_id, status_id)
        )
        ticket_id = cur.lastrowid

        with pytest.raises(pymysql.err.IntegrityError):
            cur.execute(
                """
                INSERT INTO ai_suggestions
                    (ticket_id, model, accepted_by)
                VALUES (%s, %s, %s)
                """,
                (ticket_id, "pytest-model", 999999)  # user inexistente
            )

def test_users_rechaza_gender_invalido(db_conn):
    """
    Intenta crear un usuario con gender fuera del ENUM('M','F','X','N/A').
    Debe fallar por restricción de ENUM.
    """
    with db_conn.cursor() as cur:
        with pytest.raises(pymysql.err.DataError):
            cur.execute(
                """
                INSERT INTO users
                    (names_worker, last_name, birthdate, email, gender,
                     password_hash, department_id, is_active)
                VALUES
                    (%s, %s, %s, %s, %s,
                     %s, %s, %s)
                """,
                (
                    "UsuarioEnum",
                    "GeneroInvalido",
                    "1990-01-01",
                    "enum_invalido@example.com",
                    "Z",                # valor inválido
                    "hash_de_prueba",
                    None,
                    1,
                )
            )
