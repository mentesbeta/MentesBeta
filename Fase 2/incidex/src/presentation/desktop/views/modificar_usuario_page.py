# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QPushButton, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager

import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date


class ModificarUsuarioPage(QWidget):
    def __init__(self, volver_callback=None, parent=None):
        super().__init__(parent)
        self.volver_callback = volver_callback
        self.usuario_id = None

        self.setStyleSheet("background-color: #1E73FA;")

        # === Layout principal ===
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(72, 8, 36, 20)
        main_layout.setSpacing(24)
        main_layout.setAlignment(Qt.AlignCenter)

        # === Contenedor blanco ===
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
            }

            QLineEdit, QComboBox, QDateEdit {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                background-color: #ffffff;
                color: #000000;
                min-height: 24px;
                height: 24px;
            }

            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #e0e0e0;
                selection-color: #000000;
            }

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
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
                color: white;
            }

            QPushButton#btn_modificar {
                background-color: #2ecc71;
            }

            QPushButton#btn_modificar:hover {
                background-color: #27ae60;
            }

            QPushButton#btn_cancelar {
                background-color: #e74c3c;
            }

            QPushButton#btn_cancelar:hover {
                background-color: #c0392b;
            }
        """)

        form_layout = QVBoxLayout(frame)
        form_layout.setContentsMargins(8, 6, 8, 6)
        form_layout.setSpacing(6)

        # Helper
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
        col_left.addWidget(QLabel("Nombre:"))
        col_left.addWidget(self.name_edit)

        col_right = QVBoxLayout()
        col_right.setSpacing(4)
        self.last_edit = QLineEdit()
        col_right.addWidget(QLabel("Apellido:"))
        col_right.addWidget(self.last_edit)

        row.addLayout(col_left)
        row.addLayout(col_right)
        form_layout.addLayout(row)

        # === Fecha nacimiento ===
        self.birth = QDateEdit()
        self.birth.setDisplayFormat("dd/MM/yyyy")
        self.birth.setCalendarPopup(True)
        add_field("Fecha Nacimiento:", self.birth)

        # === Correo ===
        self.email = QLineEdit()
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
        self.pwd.setPlaceholderText("Nueva contraseña (opcional)")
        self.pwd.setEchoMode(QLineEdit.Password)
        add_field("Contraseña:", self.pwd)

        self.pwd2 = QLineEdit()
        self.pwd2.setPlaceholderText("Confirmar contraseña (opcional)")
        self.pwd2.setEchoMode(QLineEdit.Password)
        add_field("Confirmar Contraseña:", self.pwd2)

        # === Botones inferiores ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        self.btn_modificar = QPushButton("Modificar Usuario")
        self.btn_modificar.setObjectName("btn_modificar")
        self.btn_modificar.setFixedWidth(160)
        self.btn_modificar.clicked.connect(self.modificar_usuario)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.setFixedWidth(160)
        self.btn_cancelar.clicked.connect(self.cancelar)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_modificar)
        btn_row.addWidget(self.btn_cancelar)
        btn_row.addStretch()
        form_layout.addLayout(btn_row)

        # === Logo ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(80, 80)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        right_side = QVBoxLayout()
        right_side.addStretch()
        right_side.addWidget(logo_label)

        main_layout.addStretch()
        main_layout.addWidget(frame)
        main_layout.addLayout(right_side)
        main_layout.addStretch()

    # ------------------------------------------------------------------
    def cargar_roles(self):
        try:
            roles = DBManager.obtener_roles() or []
        except:
            roles = []
        self.role.clear()
        if not roles:
            self.role.addItem("No hay roles disponibles")
            return
        for r in roles:
            self.role.addItem(r["name"], r["id"])

    def cargar_departamentos(self):
        try:
            deps = DBManager.obtener_departamentos() or []
        except:
            deps = []
        self.department.clear()
        if not deps:
            self.department.addItem("No hay departamentos disponibles")
            return
        for d in deps:
            self.department.addItem(d["name"], d["id"])

    # ------------------------------------------------------------------
    def cargar_datos_usuario(self, data):
        """Carga los datos de un usuario para modificarlos."""
        if not data:
            QMessageBox.warning(self, "Error", "No se pudo cargar la información del usuario.")
            return

        # ID
        self.usuario_id = data.get("id")

        # Nombre, apellido, correo
        self.name_edit.setText(data.get("nombre", ""))
        self.last_edit.setText(data.get("apellido", ""))
        self.email.setText(data.get("correo", ""))

        # Fecha de nacimiento (puede venir como string o como date/datetime)
        try:
            fecha_raw = data.get("fecha_nacimiento")
            fecha_qt = QDate()

            if isinstance(fecha_raw, str):
                # Asumimos formato yyyy-MM-dd desde la BD
                fecha_qt = QDate.fromString(fecha_raw, "yyyy-MM-dd")
            elif isinstance(fecha_raw, (date, datetime)):
                fecha_qt = QDate(fecha_raw.year, fecha_raw.month, fecha_raw.day)

            if fecha_qt.isValid():
                self.birth.setDate(fecha_qt)
        except Exception as e:
            print("⚠ Error al interpretar fecha_nacimiento:", e)

        # Género
        genero_map = {"M": "Masculino", "F": "Femenino", "X": "Otro"}
        genero_codigo = data.get("genero")
        genero_texto = genero_map.get(genero_codigo, "")
        if genero_texto:
            idx_gen = self.gender.findText(genero_texto, Qt.MatchFixedString)
            if idx_gen >= 0:
                self.gender.setCurrentIndex(idx_gen)

        # --- Rol: aceptar tanto 'rol_id' como 'role_id' ---
        rol_id = data.get("rol_id")
        if rol_id is None:
            rol_id = data.get("role_id")  # por si la columna viene sin alias

        if rol_id is not None:
            idx_rol = self.role.findData(rol_id)
            if idx_rol >= 0:
                self.role.setCurrentIndex(idx_rol)
        else:
            print("⚠ data sin 'rol_id' ni 'role_id':", data)

        # --- Departamento: aceptar 'departamento_id' o 'department_id' ---
        dept_id = data.get("departamento_id")
        if dept_id is None:
            dept_id = data.get("department_id")

        if dept_id is not None:
            idx_dep = self.department.findData(dept_id)
            if idx_dep >= 0:
                self.department.setCurrentIndex(idx_dep)

    # ------------------------------------------------------------------
    def modificar_usuario(self):
        if not self.usuario_id:
            QMessageBox.warning(self, "Error", "No se ha cargado ningún usuario.")
            return

        # === Confirmación ===
        confirm = QMessageBox.question(
            self, "Confirmar modificación",
            "¿Deseas guardar los cambios de este usuario?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # === Capturar datos ===
        data = {
            "nombre": self.name_edit.text().strip(),
            "apellido": self.last_edit.text().strip(),
            "correo": self.email.text().strip(),
            "fecha_nacimiento": self.birth.date().toString("yyyy-MM-dd"),
            "genero": {"Masculino": "M", "Femenino": "F", "Otro": "X"}[self.gender.currentText()],
            "rol_id": self.role.currentData(),
            "departamento_id": self.department.currentData(),
            "password": self.pwd.text().strip() if self.pwd.text().strip() else None
        }

        # ============================================
        # VALIDACIONES (igual que en CREAR USUARIO)
        # ============================================

        # Edad
        try:
            fn = datetime.strptime(data["fecha_nacimiento"], "%Y-%m-%d").date()
            hoy = date.today()
            edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))
            if edad < 18 or edad > 100:
                QMessageBox.warning(self, "Edad inválida", "La edad debe ser entre 18 y 100 años.")
                return
        except:
            QMessageBox.warning(self, "Fecha inválida", "La fecha de nacimiento no es válida.")
            return

        # Correo
        patron_correo = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(patron_correo, data["correo"]):
            QMessageBox.warning(self, "Correo inválido", "El correo ingresado no es válido.")
            return

        # Contraseña
        if data["password"]:
            patron_password = (
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)'
                r'(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
            )
            if not re.match(patron_password, data["password"]):
                QMessageBox.warning(
                    self, "Contraseña insegura",
                    "La contraseña debe tener:\n"
                    "- 1 mayúscula\n"
                    "- 1 minúscula\n"
                    "- 1 número\n"
                    "- 1 símbolo especial\n"
                    "- mínimo 8 caracteres"
                )
                return

            if self.pwd.text() != self.pwd2.text():
                QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
                return

        # ============================================
        # ACTUALIZAR USUARIO
        # ============================================
        ok = DBManager.actualizar_usuario(self.usuario_id, data)

        if ok:
            QMessageBox.information(self, "Éxito", "Usuario actualizado correctamente.")

            # Enviar correo
            self.enviar_correo_notificacion(
                correo=data["correo"],
                nombre=data["nombre"],
                apellido=data["apellido"],
                nueva_contraseña=data["password"]
            )

            # Bitácora
            usuario_log = DBManager.get_user()
            if usuario_log:
                DBManager.insertar_bitacora(
                    usuario=usuario_log["nombre"],
                    rol=usuario_log["rol"],
                    accion="Modificación de usuario",
                    resultado=f"Usuario {data['nombre']} modificado correctamente."
                )

            # Volver
            if callable(self.volver_callback):
                try:
                    self.volver_callback(True)
                except:
                    self.volver_callback()

    # ------------------------------------------------------------------
    def enviar_correo_notificacion(self, correo, nombre, apellido, nueva_contraseña=None):
        remitente = "incidexadmescritorio@gmail.com"
        app_password = "ivybgbsursbgdqyd"
        asunto = "Actualización de tu cuenta - Incidex"

        mensaje = f"""
        <html><body>
        <h3 style="color:#1E73FA;">Hola {nombre} {apellido},</h3>
        <p>Tu cuenta ha sido modificada correctamente.</p>
        """

        if nueva_contraseña:
            mensaje += f"<p><b>Nueva contraseña:</b> {nueva_contraseña}</p>"

        mensaje += """
        <p></p>
        <hr>
        <p style="font-size:12px;color:#777;">Mensaje automático, por favor no responder.</p>
        </body></html>
        """

        try:
            msg = MIMEMultipart()
            msg["From"] = remitente
            msg["To"] = correo
            msg["Subject"] = asunto
            msg.attach(MIMEText(mensaje, "html"))

            s = smtplib.SMTP("smtp.gmail.com", 587)
            s.starttls()
            s.login(remitente, app_password)
            s.send_message(msg)
            s.quit()

            print(f"📨 Correo enviado a {correo}")
        except Exception as e:
            print("❌ Error al enviar correo:", e)

    # ------------------------------------------------------------------
    def cancelar(self):
        if callable(self.volver_callback):
            try:
                self.volver_callback(False)
            except:
                self.volver_callback()
