# database.py
import os
import sys
import sqlite3
import shutil

def resource_path(relative_path):
    """Devuelve ruta absoluta compatible con ejecutables PyInstaller."""
    try:
        base_path = sys._MEIPASS  # cuando se ejecuta desde el .exe
    except Exception:
        base_path = os.path.abspath(".")  # modo desarrollo normal
    return os.path.join(base_path, relative_path)


# 📌 Ruta final donde se guardará la base de datos del usuario
DB_PATH = os.path.expanduser("~\\AppData\\Local\\InventarioApp\\inventario.db")

# 📦 Copiar base de datos inicial si no existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
if not os.path.exists(DB_PATH):
    try:
        shutil.copy(resource_path("inventario.db"), DB_PATH)
        print(f"✅ Base de datos creada en: {DB_PATH}")
    except Exception as e:
        print(f"⚠️ Error copiando base de datos: {e}")


# 📚 Conexión a la base de datos
def connect():
    """Devuelve una conexión SQLite a la base de datos del sistema."""
    return sqlite3.connect(DB_PATH)



def crear_tablas():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            fecha TEXT,
            factura TEXT,
            cantidad INTEGER,
            comentario TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS salidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            fecha TEXT,
            estado TEXT,
            destino TEXT,
            cantidad INTEGER,
            comentario TEXT
        )
    """)

    conn.commit()
    conn.close()

# Funciones de CRUD Entradas
def agregar_entrada(nombre, fecha, factura, cantidad, comentario):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO entradas (nombre, fecha, factura, cantidad, comentario) VALUES (?, ?, ?, ?, ?)",
                (nombre, fecha, factura, cantidad, comentario))
    conn.commit()
    conn.close()

def obtener_entradas(filtro=None):
    conn = connect()
    cur = conn.cursor()
    if filtro:
        cur.execute("SELECT * FROM entradas WHERE nombre LIKE ?", (f"%{filtro}%",))
    else:
        cur.execute("SELECT * FROM entradas")
    resultados = cur.fetchall()
    conn.close()
    return resultados

def eliminar_entrada(id_entrada):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM entradas WHERE id = ?", (id_entrada,))
    conn.commit()
    conn.close()

def actualizar_entrada(id_entrada, nombre, fecha, factura, cantidad, comentario):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE entradas
        SET nombre = ?, fecha = ?, factura = ?, cantidad = ?, comentario = ?
        WHERE id = ?
    """, (nombre, fecha, factura, cantidad, comentario, id_entrada))
    conn.commit()
    conn.close()

# Funciones de CRUD Salidas
def agregar_salida(nombre, fecha, estado, destino, cantidad, comentario):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO salidas (nombre, fecha, estado, destino, cantidad, comentario)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, fecha, estado, destino, cantidad, comentario))
    conn.commit()
    conn.close()


def obtener_salidas(filtro=None):
    conn = connect()
    cur = conn.cursor()
    if filtro:
        cur.execute("SELECT * FROM salidas WHERE nombre LIKE ?", (f"%{filtro}%",))
    else:
        cur.execute("SELECT * FROM salidas")
    resultados = cur.fetchall()
    conn.close()
    return resultados

def eliminar_salida(id_salida):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM salidas WHERE id = ?", (id_salida,))
    conn.commit()
    conn.close()

def actualizar_salida(id_salida, nombre, fecha, estado, destino, cantidad, comentario):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE salidas
        SET nombre = ?, fecha = ?, estado = ?, destino = ?, cantidad = ?, comentario = ?
        WHERE id = ?
    """, (nombre, fecha, estado, destino, cantidad, comentario, id_salida))
    conn.commit()
    conn.close()

# Función para Inventario
def calcular_inventario():
    conn = connect()
    cur = conn.cursor()
    
    # Total de entradas por producto
    cur.execute("SELECT nombre, SUM(cantidad) FROM entradas GROUP BY nombre")
    entradas = {row[0]: row[1] for row in cur.fetchall()}

    # Total de salidas por producto
    cur.execute("SELECT nombre, SUM(cantidad) FROM salidas GROUP BY nombre")
    salidas = {row[0]: row[1] for row in cur.fetchall()}

    inventario = []
    for nombre in set(entradas) | set(salidas):
        entrada = entradas.get(nombre, 0)
        salida = salidas.get(nombre, 0)
        total = entrada - salida
        inventario.append((nombre, entrada, salida, total))

    conn.close()
    return inventario

# Función para verificar si una factura ya existe
def factura_existe(factura):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM entradas WHERE factura = ?", (factura,))
    count = cur.fetchone()[0]
    conn.close()
    return count > 0
