# -*- coding: utf-8 -*-
"""
CreateDepartamentoPage — Formulario para crear nuevos departamentos.
Diseño coherente con CreateUserPage y CreateCategoriaPage.
Campos:
- Nombre de departamento
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager


class CreateDepartamentoPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

            QLineEdit {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                background-color: #ffffff;
                color: #000000;
                min-height: 24px;
                height: 24px;
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

        # === Layout del formulario ===
        form_layout = QVBoxLayout(frame)
        form_layout.setContentsMargins(8, 6, 8, 6)
        form_layout.setSpacing(10)

        # === Título ===
        title = QLabel("Crear Departamento")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #000; padding-bottom: 8px;")
        form_layout.addWidget(title, alignment=Qt.AlignCenter)

        # === Campo: Nombre ===
        self.nombre_edit = QLineEdit()
        self.nombre_edit.setPlaceholderText("Ingrese nombre del departamento")
        form_layout.addWidget(QLabel("Nombre:"))
        form_layout.addWidget(self.nombre_edit)

        # === Botón Crear ===
        self.btn_crear = QPushButton("Crear Departamento")
        self.btn_crear.setFixedHeight(28)
        self.btn_crear.setFixedWidth(180)
        form_layout.addSpacing(10)
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
    def on_crear_clicked(self):
        """Inserta el departamento en la base de datos."""
        nombre = self.nombre_edit.text().strip()

        if not nombre:
            QMessageBox.warning(self, "Campos requeridos", "El nombre del departamento es obligatorio.")
            return

        ok = DBManager.crear_departamento(nombre)
        if ok:
            QMessageBox.information(self, "Éxito", "Departamento creado correctamente.")

            # === Registrar acción en bitácora ===
            usuario_log = DBManager.get_user()
            if usuario_log:
                DBManager.insertar_bitacora(
                    usuario=usuario_log["nombre"],
                    rol=usuario_log["rol"],
                    accion="Creación de departamento",
                    resultado=f"Departamento '{nombre}' creado correctamente."
                )

            # Limpiar campo
            self.nombre_edit.clear()
        else:
            QMessageBox.critical(self, "Error", "No se pudo crear el departamento. Revisa la consola.")

            