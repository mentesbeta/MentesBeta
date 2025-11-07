# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QPushButton, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager


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
    def cargar_datos_usuario(self, data):
        """Carga los datos de un usuario para modificarlos."""
        self.usuario_id = data["id"]
        self.name_edit.setText(data["nombre"])
        self.last_edit.setText(data["apellido"])
        self.email.setText(data["correo"])

        try:
            fecha = QDate.fromString(data["fecha_nacimiento"], "yyyy-MM-dd")
            if fecha.isValid():
                self.birth.setDate(fecha)
        except Exception:
            pass

        genero_map = {"M": "Masculino", "F": "Femenino", "X": "Otro"}
        idx = self.gender.findText(genero_map.get(data.get("genero"), ""), Qt.MatchFixedString)
        if idx >= 0:
            self.gender.setCurrentIndex(idx)

        rol_idx = self.role.findData(data.get("rol_id"))
        if rol_idx >= 0:
            self.role.setCurrentIndex(rol_idx)

        dept_idx = self.department.findData(data.get("departamento_id"))
        if dept_idx >= 0:
            self.department.setCurrentIndex(dept_idx)

    # ------------------------------------------------------------------
    def modificar_usuario(self):
        """Actualiza el usuario después de confirmar."""
        if not self.usuario_id:
            QMessageBox.warning(self, "Error", "No se ha cargado ningún usuario.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar modificación",
            "¿Deseas guardar los cambios de este usuario?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

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

        if data["password"] and self.pwd.text() != self.pwd2.text():
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            return

        ok = DBManager.actualizar_usuario(self.usuario_id, data)
        if ok:
            QMessageBox.information(self, "Éxito", "Usuario actualizado correctamente.")

            # === Registrar acción en bitácora ===
            usuario_log = DBManager.get_user()
            if usuario_log:
                DBManager.insertar_bitacora(
                    usuario=usuario_log["nombre"],
                    rol=usuario_log["rol"],
                    accion="Modificación de usuario",
                    resultado=f"Usuario ID {self.usuario_id} ({data['nombre']} {data['apellido']}) modificado correctamente."
                )

            if callable(self.volver_callback):
                # compatibilidad: el callback puede o no aceptar argumentos
                try:
                    self.volver_callback(True)
                except TypeError:
                    self.volver_callback()

    # ------------------------------------------------------------------
    def cancelar(self):
        """Vuelve al listado sin guardar cambios."""
        if callable(self.volver_callback):
            try:
                self.volver_callback(False)
            except TypeError:
                self.volver_callback()


