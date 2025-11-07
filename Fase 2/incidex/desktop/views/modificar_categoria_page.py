# -*- coding: utf-8 -*-
"""
ModificarCategoriaPage — formulario para editar una categoría existente.
Incluye confirmación, actualización en DB y retorno al listado.
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTextEdit, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager


class ModificarCategoriaPage(QWidget):
    def __init__(self, volver_callback=None, parent=None):
        super().__init__(parent)
        self.volver_callback = volver_callback
        self.categoria_id = None

        # === Fondo azul general ===
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

            QLineEdit, QTextEdit {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 11px;
                background-color: #ffffff;
                color: #000000;
            }

            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
                color: white;
            }

            QPushButton#btn_guardar {
                background-color: #2ecc71;
            }

            QPushButton#btn_guardar:hover {
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
        form_layout.setSpacing(8)

        # === Campo: Nombre ===
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre de la categoría")
        form_layout.addWidget(QLabel("Nombre:"))
        form_layout.addWidget(self.name_edit)

        # === Campo: Descripción ===
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Descripción de la categoría...")
        self.desc_edit.setFixedHeight(100)
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.desc_edit)

        # === Botones inferiores ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.setFixedWidth(160)
        self.btn_guardar.clicked.connect(self.guardar_cambios)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.setFixedWidth(160)
        self.btn_cancelar.clicked.connect(self.cancelar)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_guardar)
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
    def cargar_datos_categoria(self, cat):
        """Carga los datos de la categoría seleccionada."""
        self.categoria_id = cat["id"]
        self.name_edit.setText(cat["name"])
        self.desc_edit.setPlainText(cat.get("description", "") or "")

    # ------------------------------------------------------------------
    def guardar_cambios(self):
        """Guarda los cambios en la base de datos tras confirmar."""
        if not self.categoria_id:
            QMessageBox.warning(self, "Error", "No se ha cargado ninguna categoría.")
            return

        nombre = self.name_edit.text().strip()
        descripcion = self.desc_edit.toPlainText().strip()

        if not nombre:
            QMessageBox.warning(self, "Campos requeridos", "El nombre de la categoría es obligatorio.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar modificación",
            f"¿Deseas guardar los cambios de la categoría '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            conn = DBManager._get_connection()
            with conn.cursor() as cursor:
                query = "UPDATE categories SET name=%s, description=%s WHERE id=%s"
                cursor.execute(query, (nombre, descripcion, self.categoria_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Éxito", "Categoría actualizada correctamente.")

            # === Registrar acción en bitácora ===
            usuario_log = DBManager.get_user()
            if usuario_log:
                DBManager.insertar_bitacora(
                    usuario=usuario_log["nombre"],
                    rol=usuario_log["rol"],
                    accion="Modificación de categoría",
                    resultado=f"Categoría ID {self.categoria_id} ('{nombre}') modificada correctamente."
                )

            if callable(self.volver_callback):
                self.volver_callback(refrescar=True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la categoría.\n\n{e}")

    # ------------------------------------------------------------------
    def cancelar(self):
        """Vuelve al listado sin guardar cambios."""
        if callable(self.volver_callback):
            self.volver_callback(refrescar=False)


            
