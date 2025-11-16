# -*- coding: utf-8 -*-
"""
CreateUserPage — Formulario que captura variables, valida datos
y envía correo automático con credenciales al crear usuario.
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QPushButton, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
from core.resources import asset_path

import re
from datetime import date, datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from core.db_manager import DBManager
except Exception:
    DBManager = None


class CreateUserPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1E73FA;")

        # === Layout principal ===
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(72, 8, 36, 20)
        main_layout.setSpacing(24)
        main_layout.setAlignment(Qt.AlignCenter)

        # === Contenedor del formulario ===
        frame = QFrame()
        frame.setFixedWidth(600)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 16px 18px;
            }

            QLabel {
                color: #000;
                font-size: 12px;
                font-weight: 600;
                padding-left: 4px;
                margin-bottom: 2px;
                alignment: left;
            }

            QLineEdit, QComboBox, QDateEdit {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                background-color: #ffffff;
                color: #000000;        /* 🔹 texto negro dentro del input */
                min-height: 24px;
                height: 24px;
                font-weight: normal;
            }

            /* 🔹 Menús desplegables de QComboBox (lista interna) */
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #1E73FA;
                selection-color: #ffffff;
            }

            /* 🔹 Botón desplegable del QComboBox */
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #999;
                background: #f0f0f0;
            }

            /* 🔹 Calendario del QDateEdit */
            QCalendarWidget QToolButton {
                color: #000000;
                background-color: #ffffff;
                font-weight: normal;
            }

            QCalendarWidget QWidget {
                color: #000000;
                background-color: #ffffff;
                font-weight: normal;
            }

            QCalendarWidget QAbstractItemView:enabled {
                color: #000000;
                selection-background-color: #1E73FA;
                selection-color: #ffffff;
            }

            QPushButton {
                border: 1px solid black;
                border-radius: 6px;
                background-color: white;
                color: black;
                padding: 6px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #f3f3f3;
            }
        """)

        form_layout = QVBoxLayout(frame)
        form_layout.setContentsMargins(8, 6, 8, 6)
        form_layout.setSpacing(6)

        def add_field(label_text: str, widget: QWidget):
            lbl = QLabel(label_text)
            form_layout.addWidget(lbl)
            form_layout.addWidget(widget)

        # === Nombre y Apellido ===
        row = QHBoxLayout()
        row.setSpacing(10)

        col_left = QVBoxLayout()
        col_left.setSpacing(4)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre")
        col_left.addWidget(QLabel("Nombre:"))
        col_left.addWidget(self.name_edit)

        col_right = QVBoxLayout()
        col_right.setSpacing(4)
        self.last_edit = QLineEdit()
        self.last_edit.setPlaceholderText("Apellido")
        col_right.addWidget(QLabel("Apellido:"))
        col_right.addWidget(self.last_edit)

        row.addLayout(col_left)
        row.addLayout(col_right)
        form_layout.addLayout(row)

        # === Fecha nacimiento ===
        self.birth = QDateEdit()
        self.birth.setDisplayFormat("dd/MM/yyyy")
        self.birth.setCalendarPopup(True)
        self.birth.setDate(QDate.currentDate())
        add_field("Fecha Nacimiento:", self.birth)

        # === Correo ===
        self.email = QLineEdit()
        self.email.setPlaceholderText("Correo")
        add_field("Correo:", self.email)

        # === Género ===
        self.gender = QComboBox()
        self.gender.addItems(["Masculino", "Femenino", "Otro"])
        add_field("Género:", self.gender)

        # === Departamento ===
        self.department = QComboBox()
        self.department.addItem("Cargando departamentos...")
        add_field("Departamento:", self.department)
        self.cargar_departamentos()

        # === Rol ===
        self.role = QComboBox()
        self.role.addItem("Cargando roles...")
        add_field("Rol:", self.role)
        self.cargar_roles()

        # === Contraseña ===
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("Contraseña")
        self.pwd.setEchoMode(QLineEdit.Password)
        add_field("Contraseña:", self.pwd)

        self.pwd2 = QLineEdit()
        self.pwd2.setPlaceholderText("Confirmar Contraseña")
        self.pwd2.setEchoMode(QLineEdit.Password)
        add_field("Confirmar Contraseña:", self.pwd2)

        # === Botón Crear ===
        self.btn_crear = QPushButton("Crear Cuenta")
        self.btn_crear.setFixedHeight(28)
        self.btn_crear.setFixedWidth(180)
        form_layout.addSpacing(4)
        form_layout.addWidget(self.btn_crear, alignment=Qt.AlignCenter)
        self.btn_crear.clicked.connect(self.on_crear_clicked)

        # === Logo ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        right_side = QVBoxLayout()
        right_side.addStretch(1)
        right_side.addWidget(logo_label, alignment=Qt.AlignRight | Qt.AlignBottom)

        main_layout.addStretch(1)
        main_layout.addWidget(frame, alignment=Qt.AlignVCenter)
        main_layout.addLayout(right_side)
        main_layout.addStretch(1)

    # ------------------------------------------------------------------
    def cargar_roles(self):
        if DBManager is None or not hasattr(DBManager, "obtener_roles"):
            self.role.clear()
            self.role.addItem("No hay conexión a DB")
            return
        try:
            roles = DBManager.obtener_roles() or []
        except Exception as e:
            print("❌ Error al obtener roles:", e)
            roles = []
        self.role.clear()
        if not roles:
            self.role.addItem("No hay roles disponibles")
            return
        for r in roles:
            rid, rname = (r[0], r[1]) if isinstance(r, (list, tuple)) else (r["id"], r["name"])
            self.role.addItem(str(rname), rid)

    def cargar_departamentos(self):
        if DBManager is None or not hasattr(DBManager, "obtener_departamentos"):
            self.department.clear()
            self.department.addItem("No hay conexión a DB")
            return
        try:
            deps = DBManager.obtener_departamentos() or []
        except Exception as e:
            print("❌ Error al obtener departamentos:", e)
            deps = []
        self.department.clear()
        if not deps:
            self.department.addItem("No hay departamentos disponibles")
            return
        for d in deps:
            did, dname = (d[0], d[1]) if isinstance(d, (list, tuple)) else (d["id"], d["name"])
            self.department.addItem(str(dname), did)

    # ------------------------------------------------------------------
    def get_form_values(self) -> dict:
        fecha = self.birth.date()
        fecha_str = f"{fecha.year():04d}-{fecha.month():02d}-{fecha.day():02d}"
        genero_text = self.gender.currentText()
        genero_db = {"Masculino": "M", "Femenino": "F", "Otro": "X"}.get(genero_text, None)
        return {
            "nombre": self.name_edit.text().strip(),
            "apellido": self.last_edit.text().strip(),
            "fecha_nacimiento": fecha_str,
            "correo": self.email.text().strip(),
            "genero": genero_db,
            "password": self.pwd.text(),
            "password2": self.pwd2.text(),
            "rol_id": self.role.currentData(),
            "rol_name": self.role.currentText(),
            "dept_id": self.department.currentData(),
            "dept_name": self.department.currentText(),
        }

    # ------------------------------------------------------------------
    def on_crear_clicked(self):
        data = self.get_form_values()

        # === Validaciones básicas ===
        if not data["nombre"] or not data["apellido"] or not data["correo"]:
            QMessageBox.warning(self, "Campos requeridos", "Completa nombre, apellido y correo.")
            return
        if not data["password"] or not data["password2"]:
            QMessageBox.warning(self, "Campos requeridos", "Debes ingresar y confirmar la contraseña.")
            return
        if data["password"] != data["password2"]:
            QMessageBox.warning(self, "Contraseña", "Las contraseñas no coinciden.")
            return
        if not data["rol_id"] or not data["dept_id"]:
            QMessageBox.warning(self, "Error", "Selecciona un rol y un departamento válidos.")
            return

        # === Validar edad ===
        try:
            fecha_nac = datetime.strptime(data["fecha_nacimiento"], "%Y-%m-%d").date()
            hoy = date.today()
            edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            if edad < 18 or edad > 100:
                QMessageBox.warning(
                    self, "Edad no válida",
                    "La edad debe ser mayor o igual a 18 años y menor o igual a 100 años."
                )
                return
        except Exception:
            QMessageBox.warning(self, "Fecha", "La fecha de nacimiento no es válida.")
            return

        # === Validar correo ===
        patron_correo = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(patron_correo, data["correo"]):
            QMessageBox.warning(self, "Correo inválido", "El correo ingresado no tiene un formato válido.")
            return

        # === Validar contraseña ===
        patron_password = (
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)'
            r'(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
        )
        if not re.match(patron_password, data["password"]):
            QMessageBox.warning(
                self, "Contraseña insegura",
                "La contraseña debe tener al menos:\n"
                "- Una mayúscula\n"
                "- Una minúscula\n"
                "- Un número\n"
                "- Un símbolo especial (!@#$...)\n"
                "- 8 caracteres o más"
            )
            return

        # === Crear usuario ===
        ok = DBManager.crear_usuario(
            nombre=data["nombre"],
            apellido=data["apellido"],
            nacimiento=data["fecha_nacimiento"],
            correo=data["correo"],
            genero=data["genero"],
            password=data["password"],
            rol_id=data["rol_id"],
            departamento_id=data["dept_id"]
        )

        if ok:
            QMessageBox.information(self, "Éxito", "Usuario creado correctamente.")

            # Enviar correo con credenciales
            self.enviar_correo_credenciales(
                correo_destino=data["correo"],
                nombre=data["nombre"],
                correo_usuario=data["correo"],
                contraseña=data["password"]
            )

            # Registrar en bitácora
            usuario_log = DBManager.get_user()
            if usuario_log:
                DBManager.insertar_bitacora(
                    usuario=usuario_log["nombre"],
                    rol=usuario_log["rol"],
                    accion=f"Creación de usuario",
                    resultado=f"Usuario '{data['nombre']} {data['apellido']}' creado correctamente."
                )

            # Limpiar campos
            self.name_edit.clear()
            self.last_edit.clear()
            self.email.clear()
            self.pwd.clear()
            self.pwd2.clear()
            self.gender.setCurrentIndex(0)
            self.role.setCurrentIndex(0)
            self.department.setCurrentIndex(0)

            # Refrescar vista
            parent_window = self.parentWidget()
            while parent_window and not hasattr(parent_window, "stack"):
                parent_window = parent_window.parentWidget()

            if parent_window and hasattr(parent_window, "admin_user_page"):
                parent_window.admin_user_page.refrescar_datos()
                parent_window.stack.setCurrentWidget(parent_window.admin_user_page)

    # ------------------------------------------------------------------
    def enviar_correo_credenciales(self, correo_destino, nombre, correo_usuario, contraseña):
        """Envía un correo con las credenciales de acceso al nuevo usuario."""
        remitente = "incidexadmescritorio@gmail.com"
        app_password = "ivybgbsursbgdqyd"
        asunto = "Cuenta creada - Plataforma Incidex"

        mensaje_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color:#1E73FA;">¡Hola {nombre}!</h2>
                <p>Tu cuenta en <b>Incidex</b> ha sido creada exitosamente.</p>
                <p>A continuación tus credenciales de acceso:</p>
                <table style="border-collapse: collapse;">
                    <tr><td><b>Usuario:</b></td><td>{correo_usuario}</td></tr>
                    <tr><td><b>Contraseña:</b></td><td>{contraseña}</td></tr>
                </table>
                <hr>
                <p style="font-size: 12px; color: #777;">Este es un mensaje automático, por favor no responder.</p>
            </body>
        </html>
        """

        try:
            msg = MIMEMultipart()
            msg["From"] = remitente
            msg["To"] = correo_destino
            msg["Subject"] = asunto
            msg.attach(MIMEText(mensaje_html, "html"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(remitente, app_password)
                server.send_message(msg)

            print(f"✅ Correo enviado exitosamente a {correo_destino}")
            return True

        except Exception as e:
            print(f"❌ Error al enviar correo a {correo_destino}: {e}")
            return False
