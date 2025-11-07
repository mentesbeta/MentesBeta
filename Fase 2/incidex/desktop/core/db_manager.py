# core/db_manager.py
# -*- coding: utf-8 -*-
import pymysql
import bcrypt
from core.database import get_connection
from datetime import datetime
import bcrypt

class DBManager:
    # -----------------------------------------------------------
    # ROLES
    # -----------------------------------------------------------
    @staticmethod
    def obtener_roles():
        """Devuelve los roles disponibles como lista de dicts: [{id, name}, ...]."""
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id, name FROM roles ORDER BY id ASC;")
                return cursor.fetchall()
        except Exception as e:
            print("❌ Error al obtener roles:", e)
            return []
        finally:
            conn.close()

    # -----------------------------------------------------------
    # DEPARTAMENTOS
    # -----------------------------------------------------------
    @staticmethod
    def obtener_departamentos():
        """Lista de departamentos como dicts: [{id, name}, ...]."""
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id, name FROM departments ORDER BY id ASC;")
                return cursor.fetchall()
        except Exception as e:
            print("❌ Error al obtener departamentos:", e)
            return []
        finally:
            conn.close()

    @staticmethod
    def crear_departamento(nombre: str) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO departments (name) VALUES (%s);", (nombre,))
            conn.commit()
            print(f"🟢 Departamento '{nombre}' creado correctamente.")
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al crear departamento:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def eliminar_departamento(dep_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM departments WHERE id = %s;", (dep_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al eliminar departamento:", e)
            return False
        finally:
            conn.close()

    # -----------------------------------------------------------
    # CATEGORÍAS
    # -----------------------------------------------------------
    @staticmethod
    def obtener_categorias():
        """Lista de categorías como dicts: [{id, name, description}, ...]."""
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id, name, description FROM categories ORDER BY id ASC;")
                return cursor.fetchall()
        except Exception as e:
            print("❌ Error al obtener categorías:", e)
            return []
        finally:
            conn.close()

    @staticmethod
    def crear_categoria(nombre: str, descripcion: str | None) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO categories (name, description) VALUES (%s, %s);",
                    (nombre, descripcion),
                )
            conn.commit()
            print(f"🟢 Categoría '{nombre}' creada correctamente.")
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al crear categoría:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def eliminar_categoria(cat_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM categories WHERE id = %s;", (cat_id,))
            conn.commit()
            print(f"🗑️ Categoría ID {cat_id} eliminada correctamente.")
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al eliminar categoría:", e)
            return False
        finally:
            conn.close()

    # -----------------------------------------------------------
    # USUARIOS
    # -----------------------------------------------------------
    @staticmethod
    def crear_usuario(nombre, apellido, nacimiento, correo, genero, password, rol_id, departamento_id):
        """
        Inserta un usuario y su rol asociado. 
        La contraseña se encripta automáticamente antes de guardar.
        """
        conn = get_connection()
        if not conn:
            return False
        try:
            # 🔒 Generar hash seguro antes de insertar
            password_hash = DBManager.hash_password(password)

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (names_worker, last_name, birthdate, email, gender, password_hash,
                                       department_id, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, NOW(), NOW());
                    """,
                    (nombre, apellido, nacimiento, correo, genero, password_hash, departamento_id),
                )
                user_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s);",
                    (user_id, rol_id),
                )

            conn.commit()
            print(f"✅ Usuario creado correctamente con ID: {user_id}")
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al crear usuario:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def verificar_usuario(email, password):
        """
        Verifica si el usuario existe y si la contraseña ingresada coincide con el hash almacenado.
        Solo permite usuarios activos con rol de administrador.
        """
        conn = get_connection()
        if not conn:
            return None
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT u.id,
                           u.names_worker AS nombre,
                           u.last_name AS apellido,
                           u.email,
                           u.password_hash,
                           r.name AS rol,
                           ur.role_id
                    FROM users u
                    INNER JOIN user_roles ur ON ur.user_id = u.id
                    INNER JOIN roles r ON r.id = ur.role_id
                    WHERE u.is_active = 1 AND u.email = %s;
                    """,
                    (email,),
                )
                user = cursor.fetchone()
                if not user:
                    print("⚠ Usuario no encontrado o inactivo.")
                    return None

                stored_hash = user.get("password_hash")
                if not stored_hash:
                    print("⚠ Usuario sin contraseña registrada.")
                    return None

                # 🔒 Verificar hash seguro
                if DBManager.check_password(password, stored_hash):
                    print(f"✅ Inicio de sesión exitoso: {user['nombre']} ({user['rol']})")
                    return user
                else:
                    print("❌ Contraseña incorrecta.")
                    return None
        except Exception as e:
            print("❌ Error al verificar usuario:", e)
            return None
        finally:
            conn.close()

    @staticmethod
    def obtener_usuarios():
        """Devuelve usuarios activos con su rol: [{id, nombre, apellido, correo, rol}, ...]."""
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT u.id,
                           u.names_worker AS nombre,
                           u.last_name   AS apellido,
                           u.email       AS correo,
                           r.name        AS rol
                    FROM users u
                    INNER JOIN user_roles ur ON ur.user_id = u.id
                    INNER JOIN roles r       ON r.id = ur.role_id
                    WHERE u.is_active = 1
                    ORDER BY u.id ASC;
                    """
                )
                return cursor.fetchall()
        except Exception as e:
            print("❌ Error al obtener usuarios:", e)
            return []
        finally:
            conn.close()

    @staticmethod
    def obtener_usuario_por_id(user_id: int):
        """Devuelve un usuario completo por ID (con rol y departamento)."""
        conn = get_connection()
        if not conn:
            return None
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT u.id,
                           u.names_worker AS nombre,
                           u.last_name AS apellido,
                           u.birthdate AS fecha_nacimiento,
                           u.email AS correo,
                           u.gender AS genero,
                           u.department_id,
                           d.name AS departamento,
                           ur.role_id,
                           r.name AS rol
                    FROM users u
                    LEFT JOIN departments d ON d.id = u.department_id
                    LEFT JOIN user_roles ur ON ur.user_id = u.id
                    LEFT JOIN roles r       ON r.id = ur.role_id
                    WHERE u.id = %s AND u.is_active = 1
                    LIMIT 1;
                    """,
                    (user_id,),
                )
                return cursor.fetchone()
        except Exception as e:
            print("❌ Error al obtener usuario por ID:", e)
            return None
        finally:
            conn.close()

    @staticmethod
    def desactivar_usuario(user_id: int) -> bool:
        """Marca al usuario como inactivo (soft delete)."""
        conn = get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET is_active = 0, updated_at = NOW() WHERE id = %s;",
                    (user_id,),
                )
            conn.commit()
            print(f"🟡 Usuario ID {user_id} desactivado correctamente.")
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al desactivar usuario:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def actualizar_usuario(user_id: int, data: dict) -> bool:
        """
        Actualiza datos del usuario y su rol (si se entrega).
        Si se incluye 'password', se vuelve a encriptar antes de actualizar.
        """
        conn = get_connection()
        if not conn:
            print("❌ No se pudo conectar a la base de datos.")
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET names_worker = %s,
                        last_name    = %s,
                        birthdate    = %s,
                        email        = %s,
                        gender       = %s,
                        department_id= %s,
                        updated_at   = NOW()
                    WHERE id = %s;
                    """,
                    (
                        data["nombre"],
                        data["apellido"],
                        data["fecha_nacimiento"],
                        data["correo"],
                        data["genero"],
                        data["departamento_id"],
                        user_id,
                    ),
                )

                # Actualizar rol si viene en data
                if data.get("rol_id"):
                    cursor.execute(
                        "UPDATE user_roles SET role_id = %s WHERE user_id = %s;",
                        (data["rol_id"], user_id),
                    )

                # 🔒 Si hay nueva contraseña, se hashea antes
                if data.get("password"):
                    hashed_pass = DBManager.hash_password(data["password"])
                    cursor.execute(
                        "UPDATE users SET password_hash = %s WHERE id = %s;",
                        (hashed_pass, user_id),
                    )

            conn.commit()
            print(f"🟢 Usuario ID {user_id} actualizado correctamente.")
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al actualizar usuario:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def _get_connection():
        """Devuelve una conexión activa a la base de datos."""
        from core.database import get_connection
        return get_connection()
    

    @staticmethod
    def get_priorities():
        try:
            conn = get_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id, name FROM priorities ORDER BY id ASC;")
                return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener prioridades: {e}")
            return []
        finally:
            if conn:
                conn.close()


    @staticmethod
    def get_statuses():
        try:
            conn = get_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id, name FROM statuses ORDER BY id ASC;")
                return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener estados: {e}")
            return []
        finally:
            if conn:
                conn.close()

        # -----------------------------------------------------------
    # REPORTES DE TICKETS
    # -----------------------------------------------------------
    @staticmethod
    def generar_reporte_tickets(filtros: dict):
        """
        Genera un reporte de tickets filtrado por prioridad, estado y rango de fechas.
        Devuelve lista de dicts con los campos más relevantes.
        """
        conn = get_connection()
        if not conn:
            print("❌ No se pudo conectar a la base de datos.")
            return []

        try:
            query = """
                SELECT 
                    t.id,
                    t.code,
                    t.title,
                    t.description,
                    p.name  AS prioridad,
                    s.name  AS estado,
                    d.name  AS departamento,
                    c.name  AS categoria,
                    t.created_at,
                    t.updated_at
                FROM tickets t
                LEFT JOIN priorities p  ON p.id = t.priority_id
                LEFT JOIN statuses  s   ON s.id = t.status_id
                LEFT JOIN departments d ON d.id = t.department_id
                LEFT JOIN categories  c ON c.id = t.category_id
                WHERE 1 = 1
            """

            params = []

            # --- Filtros dinámicos ---
            if filtros.get("prioridad_id"):
                query += " AND t.priority_id = %s"
                params.append(filtros["prioridad_id"])

            if filtros.get("estado_id"):
                query += " AND t.status_id = %s"
                params.append(filtros["estado_id"])

            if filtros.get("inicio") and filtros.get("fin"):
                query += " AND DATE(t.created_at) BETWEEN %s AND %s"
                params.append(filtros["inicio"].toString("yyyy-MM-dd"))
                params.append(filtros["fin"].toString("yyyy-MM-dd"))

            query += " ORDER BY t.created_at DESC;"

            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()

            return results

        except Exception as e:
            print("❌ Error al generar reporte:", e)
            return []
        finally:
            conn.close()

    _current_user = None

    @classmethod
    def set_user(cls, user_data):
        """
        Guarda la información del usuario logeado.
        user_data debe ser un dict con al menos:
        {'id': int, 'nombre': str, 'rol': str, 'email': str}
        """
        cls._current_user = user_data

    @classmethod
    def get_user(cls):
        """Devuelve el usuario actual (o None si no hay sesión activa)."""
        return cls._current_user

    @classmethod
    def clear_user(cls):
        """Limpia la sesión (por ejemplo, al cerrar sesión)."""
        cls._current_user = None


        # -----------------------------------------------------------
    # BITÁCORA DE ACCIONES
    # -----------------------------------------------------------
    @staticmethod
    def insertar_bitacora(usuario, rol, accion, resultado):
        """
        Inserta una nueva acción en la tabla bitacora.
        """
        conn = get_connection()
        if not conn:
            print("❌ No se pudo conectar a la base de datos (bitácora).")
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO bitacora (usuario, rol, accion, resultado)
                    VALUES (%s, %s, %s, %s);
                """, (usuario, rol, accion, resultado))
            conn.commit()
            print(f"📝 Acción registrada en bitácora: {accion}")
            return True
        except Exception as e:
            conn.rollback()
            print("❌ Error al insertar en bitácora:", e)
            return False
        finally:
            conn.close()
    

    @staticmethod
    def obtener_bitacora():
        """
        Devuelve todos los registros de la tabla bitacora, ordenados por fecha descendente.
        """
        conn = get_connection()
        if not conn:
            print("❌ No se pudo conectar a la base de datos (bitácora).")
            return []
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id,
                           DATE_FORMAT(fecha, '%d/%m/%Y %H:%i:%s') AS fecha,
                           usuario,
                           rol,
                           accion,
                           resultado
                    FROM bitacora
                    ORDER BY fecha DESC;
                """)
                return cursor.fetchall()
        except Exception as e:
            print("❌ Error al obtener bitácora:", e)
            return []
        finally:
            conn.close()


        # -----------------------------------------------------------
    # REPORTES DE BITÁCORA
    # -----------------------------------------------------------
    @staticmethod
    def generar_reporte_bitacora(filtros: dict):
        """
        Genera un reporte de la bitácora con filtros opcionales:
        usuario y rango de fechas (DATETIME).
        """
        from datetime import datetime, time
        conn = get_connection()
        if not conn:
            print("❌ No se pudo conectar a la base de datos.")
            return []

        try:
            # 👇 OJO: los % del DATE_FORMAT van doblados (%%) para que PyMySQL no los intente formatear
            query = """
                SELECT 
                    id,
                    DATE_FORMAT(fecha, '%%d/%%m/%%Y %%H:%%i:%%s') AS fecha,
                    usuario,
                    rol,
                    accion,
                    resultado
                FROM bitacora
                WHERE 1 = 1
            """
            params = []

            # Filtro por usuario (opcional)
            if filtros.get("usuario"):
                query += " AND usuario LIKE %s"
                params.append(f"%{filtros['usuario']}%")

            # Filtro por fechas (opcional) — columnas DATETIME
            if filtros.get("inicio") and filtros.get("fin"):
                query += " AND fecha BETWEEN %s AND %s"

                ini_q = filtros["inicio"]
                fin_q = filtros["fin"]

                # QDate → datetime
                if hasattr(ini_q, "toPython"):
                    ini_dt = datetime.combine(ini_q.toPython(), time.min)   # 00:00:00
                    fin_dt = datetime.combine(fin_q.toPython(), time.max)   # 23:59:59.999999
                else:
                    # fallback si viniera como 'YYYY-MM-DD'
                    ini_dt = datetime.strptime(str(ini_q), "%Y-%m-%d")
                    fin_dt = datetime.strptime(str(fin_q), "%Y-%m-%d")
                    fin_dt = datetime.combine(fin_dt.date(), time.max)

                params.extend([ini_dt, fin_dt])

            query += " ORDER BY fecha DESC;"

            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Debug útil para ver la query final con parámetros:
                # print(cursor.mogrify(query, tuple(params)).decode())
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()

            return rows

        except Exception as e:
            print(f"❌ Error al generar reporte de bitácora: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash seguro de la contraseña usando bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")


    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """Verifica si la contraseña ingresada coincide con el hash almacenado."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
        
        