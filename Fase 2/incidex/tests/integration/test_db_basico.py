def test_conexion_basica(db_conn):
    """
    Verifica que la BD responde correctamente a una consulta simple.
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT 1")
        row = cur.fetchone()

    assert row is not None