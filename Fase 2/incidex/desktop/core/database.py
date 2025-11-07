# -*- coding: utf-8 -*-
"""
database.py — Módulo de conexión con la base de datos MySQL en Docker.
"""

import os
import pymysql
from dotenv import load_dotenv

# Cargar variables del entorno (.env en la raíz del proyecto desktop o raíz global)
load_dotenv()

def get_connection():
    """Devuelve una conexión PyMySQL hacia el contenedor MySQL."""
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "incidex"),
            password=os.getenv("DB_PASSWORD", "incidex"),
            database=os.getenv("DB_NAME", "incidex_db"),
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Conectado exitosamente a la base de datos MySQL.")
        return connection
    except Exception as e:
        print(f"❌ Error al conectar con MySQL: {e}")
        return None


