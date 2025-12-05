# tests/integration/test_db_users_tickets.py
import uuid
import pytest
import pymysql.err


def test_users_timestamps_automaticos(db_conn):
    """
    Verifica que al insertar un usuario, los campos created_at y updated_at
    se completen automáticamente con valores no nulos.
    """
    email_unico = f"pytest_{uuid.uuid4()}@example.com"

    with db_conn.cursor() as cur:
        # Insertamos un usuario de prueba SIN especificar created_at/updated_at
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
                "TimestampNombre",
                "TimestampApellido",
                "1990-01-01",
                email_unico,
                "M",
                "hash_de_prueba",
                None,   # department_id es NULL-able
                1,
            )
        )

        user_id = cur.lastrowid

        # Consultamos los timestamps
        cur.execute(
            "SELECT created_at, updated_at FROM users WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()

    created_at = row[0]
    updated_at = row[1]

    assert created_at is not None
    assert updated_at is not None


def test_creacion_ticket_valido_happy_path(db_conn, test_user):
    """
    Verifica que se pueda crear un ticket válido respetando las FKs mínimas
    y que created_at/updated_at se completen automáticamente.
    """
    with db_conn.cursor() as cur:
        # 1) Obtenemos priority_id y status_id existentes
        cur.execute("SELECT id FROM priorities LIMIT 1")
        pri_row = cur.fetchone()
        assert pri_row is not None, "No hay registros en priorities"
        priority_id = pri_row[0]

        cur.execute("SELECT id FROM statuses LIMIT 1")
        sta_row = cur.fetchone()
        assert sta_row is not None, "No hay registros en statuses"
        status_id = sta_row[0]

        # 2) Creamos un código único para el ticket
        code = f"TCK-{uuid.uuid4().hex[:10]}"

        # 3) Insertamos un ticket de prueba (campos mínimos obligatorios)
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
                code,
                "Ticket pytest válido",
                "Descripción de prueba para happy path",
                int(test_user),    # requester_id válido
                priority_id,
                status_id,
            )
        )
        ticket_id = cur.lastrowid

        # 4) Verificamos que se haya insertado y que created_at no sea NULL
        cur.execute(
            "SELECT code, created_at, updated_at FROM tickets WHERE id = %s",
            (ticket_id,)
        )
        row = cur.fetchone()

    ticket_code = row[0]
    created_at = row[1]
    updated_at = row[2]

    assert ticket_code == code
    assert created_at is not None
    assert updated_at is not None


def test_ticket_code_unico_en_tickets(db_conn, test_user):
    """
    Verifica que el campo code en tickets tenga restricción UNIQUE.
    Crea un ticket con un code dado y luego intenta crear otro con el mismo code.
    Se espera IntegrityError.
    """
    with db_conn.cursor() as cur:
        # Tomamos prioridad y estado existentes
        cur.execute("SELECT id FROM priorities LIMIT 1")
        pri_row = cur.fetchone()
        assert pri_row is not None, "No hay registros en priorities"
        priority_id = pri_row[0]

        cur.execute("SELECT id FROM statuses LIMIT 1")
        sta_row = cur.fetchone()
        assert sta_row is not None, "No hay registros en statuses"
        status_id = sta_row[0]

        code = f"DUP-{uuid.uuid4().hex[:8]}"

        # 1) Primer ticket con ese code (debe pasar)
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
                code,
                "Ticket original",
                "Ticket con código único",
                int(test_user),
                priority_id,
                status_id,
            )
        )

        # 2) Segundo ticket con el MISMO code → debe fallar
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
                    code,  # mismo code
                    "Ticket duplicado",
                    "No debería poder crearse",
                    int(test_user),
                    priority_id,
                    status_id,
                )
            )

def test_ai_suggestions_creacion_valida(db_conn, test_user):
    """
    Crea un ticket válido y luego una sugerencia de IA asociada,
    usando categoría y prioridad válidas. Verifica que se inserte correctamente.
    """
    with db_conn.cursor() as cur:
        # 1) Sacamos priority, status y category válidos
        cur.execute("SELECT id FROM priorities LIMIT 1")
        pri_row = cur.fetchone()
        assert pri_row is not None, "No hay registros en priorities"
        priority_id = pri_row[0]

        cur.execute("SELECT id FROM statuses LIMIT 1")
        sta_row = cur.fetchone()
        assert sta_row is not None, "No hay registros en statuses"
        status_id = sta_row[0]

        cur.execute("SELECT id FROM categories LIMIT 1")
        cat_row = cur.fetchone()
        assert cat_row is not None, "No hay registros en categories"
        category_id = cat_row[0]

        # 2) Creamos ticket base
        code = f"AI-OK-{uuid.uuid4().hex[:8]}"
        cur.execute(
            """
            INSERT INTO tickets
                (code, title, description, requester_id,
                 priority_id, status_id, category_id)
            VALUES
                (%s, %s, %s, %s,
                 %s, %s, %s)
            """,
            (
                code,
                "Ticket para sugerencia IA",
                "Ticket generado para caso feliz de ai_suggestions",
                int(test_user),
                priority_id,
                status_id,
                category_id,
            )
        )
        ticket_id = cur.lastrowid

        # 3) Creamos sugerencia de IA válida
        cur.execute(
            """
            INSERT INTO ai_suggestions
                (ticket_id, model, suggested_category_id,
                 suggested_priority_id, confidence,
                 summary, recommendation, accepted, accepted_by)
            VALUES
                (%s, %s, %s,
                 %s, %s,
                 %s, %s, %s, %s)
            """,
            (
                ticket_id,
                "pytest-model",
                category_id,
                priority_id,
                0.85,
                "Resumen de prueba",
                "Recomendación de prueba",
                1,
                int(test_user),
            )
        )
        suggestion_id = cur.lastrowid

        # 4) Recuperamos y validamos
        cur.execute(
            """
            SELECT ticket_id, model, suggested_category_id,
                   suggested_priority_id, confidence, accepted, accepted_by
            FROM ai_suggestions
            WHERE id = %s
            """,
            (suggestion_id,)
        )
        row = cur.fetchone()

    ticket_id_db = row[0]
    model_db = row[1]
    cat_id_db = row[2]
    pri_id_db = row[3]
    confidence_db = float(row[4]) if row[4] is not None else None
    accepted_db = row[5]
    accepted_by_db = row[6]

    assert ticket_id_db == ticket_id
    assert model_db == "pytest-model"
    assert cat_id_db == category_id
    assert pri_id_db == priority_id
    assert abs(confidence_db - 0.85) < 0.0001
    assert accepted_db == 1
    assert accepted_by_db == int(test_user)
