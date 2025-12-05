# -- coding: utf-8 --
"""
database.py — Módulo de conexión con la base de datos MySQL en Docker.
"""

import os
import pymysql
from dotenv import load_dotenv

# Cargar variables del entorno (.env)
load_dotenv()

def get_connection():
    """Devuelve una conexión PyMySQL usando las variables del .env."""
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),  # Puedes usar 127.0.0.1 siempre
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Conectado exitosamente a la base de datos MySQL.")
        return connection
    except Exception as e:
        print(f"❌ Error al conectar con MySQL: {e}")
        return None