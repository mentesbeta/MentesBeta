# tests/integration/test_db_cascade.py
import uuid


def _crear_ticket_basico(cur, requester_id: int) -> int:
    """
    Helper interno: crea un ticket mínimo válido y devuelve su id.
    """
    # Obtenemos prioridad y estado existentes
    cur.execute("SELECT id FROM priorities LIMIT 1")
    pri_row = cur.fetchone()
    assert pri_row is not None, "No hay prioridades en la tabla priorities"
    priority_id = pri_row[0]

    cur.execute("SELECT id FROM statuses LIMIT 1")
    sta_row = cur.fetchone()
    assert sta_row is not None, "No hay estados en la tabla statuses"
    status_id = sta_row[0]

    code = f"TCK-{uuid.uuid4().hex[:8]}"

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
            "Ticket de prueba cascade",
            "Descripción de prueba para cascada",
            int(requester_id),
            priority_id,
            status_id,
        )
    )
    return cur.lastrowid


def test_delete_ticket_elimina_comentarios_cascade(db_conn, test_user):
    """
    Verifica que al borrar un ticket, sus comentarios se eliminan
    automáticamente gracias a ON DELETE CASCADE en ticket_comments.
    """
    with db_conn.cursor() as cur:
        # 1) Creamos ticket de prueba
        ticket_id = _crear_ticket_basico(cur, test_user)

        # 2) Insertamos un comentario asociado
        cur.execute(
            """
            INSERT INTO ticket_comments
                (ticket_id, author_user_id, body)
            VALUES
                (%s, %s, %s)
            """,
            (
                ticket_id,
                int(test_user),
                "Comentario de prueba",
            )
        )

        # 3) Confirmamos que existe
        cur.execute(
            "SELECT COUNT(*) FROM ticket_comments WHERE ticket_id = %s",
            (ticket_id,)
        )
        count_before = cur.fetchone()[0]
        assert count_before == 1

        # 4) Borramos el ticket
        cur.execute(
            "DELETE FROM tickets WHERE id = %s",
            (ticket_id,)
        )

        # 5) Comentarios deben haberse ido
        cur.execute(
            "SELECT COUNT(*) FROM ticket_comments WHERE ticket_id = %s",
            (ticket_id,)
        )
        count_after = cur.fetchone()[0]

    assert count_after == 0


def test_delete_ticket_elimina_historial_cascade(db_conn, test_user):
    """
    Verifica que al borrar un ticket, sus registros en ticket_history
    se eliminan automáticamente por ON DELETE CASCADE.
    """
    with db_conn.cursor() as cur:
        # 1) Creamos ticket de prueba
        ticket_id = _crear_ticket_basico(cur, test_user)

        # 2) Insertamos un registro en ticket_history
        cur.execute(
            """
            INSERT INTO ticket_history
                (ticket_id, actor_user_id, from_status_id, to_status_id, note)
            SELECT
                %s, %s, NULL, s.id, %s
            FROM statuses s
            LIMIT 1
            """,
            (
                ticket_id,
                int(test_user),
                "Cambio inicial de estado",
            )
        )

        # 3) Confirmamos que exista historial
        cur.execute(
            "SELECT COUNT(*) FROM ticket_history WHERE ticket_id = %s",
            (ticket_id,)
        )
        before_count = cur.fetchone()[0]
        assert before_count >= 1

        # 4) Borramos el ticket
        cur.execute(
            "DELETE FROM tickets WHERE id = %s",
            (ticket_id,)
        )

        # 5) Historial debe haberse ido
        cur.execute(
            "SELECT COUNT(*) FROM ticket_history WHERE ticket_id = %s",
            (ticket_id,)
        )
        after_count = cur.fetchone()[0]

    assert after_count == 0


def test_delete_ticket_elimina_adjuntos_cascade(db_conn, test_user):
    """
    Verifica que al borrar un ticket, sus adjuntos en ticket_attachments
    se eliminan automáticamente por ON DELETE CASCADE.
    """
    with db_conn.cursor() as cur:
        # 1) Creamos ticket de prueba
        ticket_id = _crear_ticket_basico(cur, test_user)

        # 2) Insertamos un adjunto asociado
        cur.execute(
            """
            INSERT INTO ticket_attachments
                (ticket_id, uploader_user_id, file_name,
                 mime_type, file_path, file_size, checksum_sha256)
            VALUES
                (%s, %s, %s,
                 %s, %s, %s, %s)
            """,
            (
                ticket_id,
                int(test_user),
                "archivo_prueba.txt",
                "text/plain",
                "/tmp/archivo_prueba.txt",
                1234,
                None,
            )
        )

        # 3) Confirmamos que existe el adjunto
        cur.execute(
            "SELECT COUNT(*) FROM ticket_attachments WHERE ticket_id = %s",
            (ticket_id,)
        )
        before_count = cur.fetchone()[0]
        assert before_count == 1

        # 4) Borramos el ticket
        cur.execute(
            "DELETE FROM tickets WHERE id = %s",
            (ticket_id,)
        )

        # 5) El adjunto debe haberse eliminado
        cur.execute(
            "SELECT COUNT(*) FROM ticket_attachments WHERE ticket_id = %s",
            (ticket_id,)
        )
        after_count = cur.fetchone()[0]

    assert after_count == 0


def test_delete_ticket_elimina_watchers_cascade(db_conn, test_user):
    """
    Verifica que al borrar un ticket, sus registros en ticket_watchers
    se eliminan automáticamente por ON DELETE CASCADE.
    """
    with db_conn.cursor() as cur:
        # 1) Creamos ticket de prueba
        ticket_id = _crear_ticket_basico(cur, test_user)

        # 2) Insertamos un watcher
        cur.execute(
            """
            INSERT INTO ticket_watchers
                (ticket_id, user_id)
            VALUES
                (%s, %s)
            """,
            (
                ticket_id,
                int(test_user),
            )
        )

        # 3) Confirmamos que existe watcher
        cur.execute(
            "SELECT COUNT(*) FROM ticket_watchers WHERE ticket_id = %s",
            (ticket_id,)
        )
        before_count = cur.fetchone()[0]
        assert before_count == 1

        # 4) Borramos ticket
        cur.execute(
            "DELETE FROM tickets WHERE id = %s",
            (ticket_id,)
        )

        # 5) Watcher debe haberse eliminado
        cur.execute(
            "SELECT COUNT(*) FROM ticket_watchers WHERE ticket_id = %s",
            (ticket_id,)
        )
        after_count = cur.fetchone()[0]

    assert after_count == 0


def test_delete_user_elimina_watchers_cascade(db_conn, test_user):
    """
    Verifica que al borrar un usuario, sus registros en ticket_watchers
    se eliminen automáticamente (ON DELETE CASCADE en user_id).

    Importante:
    - El usuario watcher NO debe ser requester del ticket, para no romper fk_t_req.
    """
    with db_conn.cursor() as cur:
        # 1) Creamos un usuario watcher temporal
        email = f"watcher_{uuid.uuid4().hex[:8]}@example.com"
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
                "Watcher",
                "Temporal",
                "1990-01-01",
                email,
                "M",
                "hash_de_prueba",
                None,
                1,
            )
        )
        watcher_id = cur.lastrowid

        # 2) Creamos un ticket básico, pero el requester es test_user,
        #    NO el watcher, para que no bloquee el DELETE del watcher.
        ticket_id = _crear_ticket_basico(cur, int(test_user))

        # 3) Insertamos el watcher para ese ticket
        cur.execute(
            """
            INSERT INTO ticket_watchers
                (ticket_id, user_id)
            VALUES
                (%s, %s)
            """,
            (ticket_id, watcher_id)
        )

        # Confirmamos que exista el watcher
        cur.execute(
            """
            SELECT COUNT(*)
            FROM ticket_watchers
            WHERE ticket_id = %s AND user_id = %s
            """,
            (ticket_id, watcher_id)
        )
        before_count = cur.fetchone()[0]
        assert before_count == 1

        # 4) Borramos el usuario watcher
        cur.execute(
            "DELETE FROM users WHERE id = %s",
            (watcher_id,)
        )

        # 5) Los registros en ticket_watchers ligados a ese user_id
        # deben desaparecer por ON DELETE CASCADE
        cur.execute(
            """
            SELECT COUNT(*)
            FROM ticket_watchers
            WHERE user_id = %s
            """,
            (watcher_id,)
        )
        after_count = cur.fetchone()[0]

    assert after_count == 0
