from core.database import get_connection

db = get_connection()
if db:
    with db.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tablas = cursor.fetchall()
        print("📋 Tablas disponibles:")
        for t in tablas:
            print("-", list(t.values())[0])
    db.close()
 
 