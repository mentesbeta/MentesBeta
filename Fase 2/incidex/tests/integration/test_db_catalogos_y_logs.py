# tests/integration/test_db_catalogos_y_logs.py

import uuid


# =========================
#   CATÁLOGOS BÁSICOS
# =========================

def test_roles_tiene_registros(db_conn):
    """
    Verifica que la tabla roles tenga al menos un registro.
    (Catálogo básico para el sistema de usuarios/roles).
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM roles")
        count = cur.fetchone()[0]

    assert count > 0


def test_statuses_tiene_registros(db_conn):
    """
    Verifica que la tabla statuses tenga al menos un registro.
    (Catálogo básico para el flujo de estados de los tickets).
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM statuses")
        count = cur.fetchone()[0]

    assert count > 0


def test_priorities_tiene_registros(db_conn):
    """
    Verifica que la tabla priorities tenga al menos un registro.
    (Catálogo básico para la criticidad de los tickets).
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM priorities")
        count = cur.fetchone()[0]

    assert count > 0


# =========================
#         BITÁCORA
# =========================

def test_bitacora_insert_fecha_automatica(db_conn):
    """
    Inserta un registro en bitacora y verifica que la columna fecha
    se complete automáticamente (NOT NULL + DEFAULT CURRENT_TIMESTAMP).
    """
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bitacora (usuario, rol, accion, resultado)
            VALUES (%s, %s, %s, %s)
            """,
            (
                "pytest_user",
                "pytest_rol",
                "Acción de prueba",
                "OK",
            )
        )

        bitacora_id = cur.lastrowid

        cur.execute(
            "SELECT fecha, usuario, accion FROM bitacora WHERE id = %s",
            (bitacora_id,)
        )
        row = cur.fetchone()

    fecha = row[0]
    usuario = row[1]
    accion = row[2]

    assert fecha is not None
    assert usuario == "pytest_user"
    assert accion == "Acción de prueba"


def test_bitacora_tiene_indice_fecha(db_conn):
    """
    Verifica que exista el índice idx_bitacora_fecha en la columna fecha,
    tal como está definido en el script SQL.
    """
    with db_conn.cursor() as cur:
        cur.execute(
            "SHOW INDEX FROM bitacora WHERE Key_name = 'idx_bitacora_fecha'"
        )
        row = cur.fetchone()

    assert row is not None, "No existe el índice idx_bitacora_fecha en bitacora"


# =========================
#   NOTIFICACIONES
# =========================

def _crear_ticket_minimo(cur, requester_id: int) -> int:
    """
    Helper interno: crea un ticket mínimo válido para usarlo
    en pruebas de ticket_notifications.
    """
    # Obtenemos prioridad y estado cualquiera
    cur.execute("SELECT id FROM priorities LIMIT 1")
    pri_row = cur.fetchone()
    assert pri_row is not None, "No hay registros en priorities"
    priority_id = pri_row[0]

    cur.execute("SELECT id FROM statuses LIMIT 1")
    sta_row = cur.fetchone()
    assert sta_row is not None, "No hay registros en statuses"
    status_id = sta_row[0]

    code = f"NTF-{uuid.uuid4().hex[:8]}"

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
            "Ticket para notificación",
            "Ticket generado para probar notificaciones",
            int(requester_id),
            priority_id,
            status_id,
        )
    )
    return cur.lastrowid


def test_ticket_notifications_insercion_valida(db_conn, test_user):
    """
    Verifica que se pueda insertar una notificación válida
    asociada a un usuario y un ticket de prueba.
    """
    with db_conn.cursor() as cur:
        # 1) Creamos ticket mínimo
        ticket_id = _crear_ticket_minimo(cur, test_user)

        # 2) Insertamos una notificación
        cur.execute(
            """
            INSERT INTO ticket_notifications
                (user_id, ticket_id, kind, message)
            VALUES
                (%s, %s, %s, %s)
            """,
            (
                int(test_user),
                ticket_id,
                "CREATED",
                "Se ha creado un nuevo ticket",
            )
        )

        notif_id = cur.lastrowid

        # 3) Recuperamos la notificación
        cur.execute(
            """
            SELECT user_id, ticket_id, kind, message, is_read, created_at
            FROM ticket_notifications
            WHERE id = %s
            """,
            (notif_id,)
        )
        row = cur.fetchone()

    user_id = row[0]
    ticket_id_db = row[1]
    kind = row[2]
    message = row[3]
    is_read = row[4]
    created_at = row[5]

    assert user_id == int(test_user)
    assert ticket_id_db == ticket_id
    assert kind == "CREATED"
    assert message == "Se ha creado un nuevo ticket"
    # Por defecto debe ser 0 según el esquema
    assert is_read == 0
    assert created_at is not None


def test_ticket_notifications_indices_existen(db_conn):
    """
    Verifica que existan los índices definidos para ticket_notifications:
      - idx_notif_user
      - idx_notif_ticket
      - idx_notif_created
    """
    with db_conn.cursor() as cur:
        cur.execute(
            "SHOW INDEX FROM ticket_notifications WHERE Key_name = 'idx_notif_user'"
        )
        idx_user = cur.fetchone()

        cur.execute(
            "SHOW INDEX FROM ticket_notifications WHERE Key_name = 'idx_notif_ticket'"
        )
        idx_ticket = cur.fetchone()

        cur.execute(
            "SHOW INDEX FROM ticket_notifications WHERE Key_name = 'idx_notif_created'"
        )
        idx_created = cur.fetchone()

    assert idx_user is not None, "No existe idx_notif_user en ticket_notifications"
    assert idx_ticket is not None, "No existe idx_notif_ticket en ticket_notifications"
    assert idx_created is not None, "No existe idx_notif_created en ticket_notifications"
