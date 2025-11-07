# -*- coding: utf-8 -*-
"""
ModificarDepartamentoPage — formulario para editar el nombre de un departamento.
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager


class ModificarDepartamentoPage(QWidget):
    def __init__(self, departamento=None, volver_callback=None, parent=None):
        super().__init__(parent)
        self.departamento = departamento
        self.volver_callback = volver_callback
        self.setStyleSheet("background-color: #1E73FA;")

        # === Contenedor blanco ===
        frame = QFrame()
        frame.setFixedWidth(400)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
            QLabel {
                color: #000;
                font-weight: 600;
                font-size: 12px;
            }
            QLineEdit {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                background-color: #ffffff;
                color: #000;
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

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        form = QVBoxLayout(frame)
        form.setSpacing(10)

        lbl_title = QLabel("Modificar Departamento")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #000;")
        form.addWidget(lbl_title, alignment=Qt.AlignCenter)

        form.addWidget(QLabel("Nombre:"))
        self.name_edit = QLineEdit()
        self.name_edit.setText(departamento["name"] if departamento else "")
        form.addWidget(self.name_edit)

        # === Botones ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.clicked.connect(self.guardar_cambios)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_guardar)
        btn_row.addWidget(self.btn_cancelar)
        btn_row.addStretch()

        form.addLayout(btn_row)
        layout.addWidget(frame)

        # === Logo ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        layout.addWidget(logo_label, alignment=Qt.AlignRight | Qt.AlignBottom)

    # -----------------------------------------------------
    def cargar_datos_departamento(self, dep):
        """Carga los datos de un departamento desde el listado."""
        self.departamento = dep
        self.name_edit.setText(dep.get("name", ""))

    # -----------------------------------------------------
    def guardar_cambios(self):
        nuevo_nombre = self.name_edit.text().strip()
        if not nuevo_nombre:
            QMessageBox.warning(self, "Campo vacío", "El nombre no puede estar vacío.")
            return

        ok = self.actualizar_departamento(self.departamento["id"], nuevo_nombre)
        if ok:
            QMessageBox.information(self, "Éxito", "Departamento actualizado correctamente.")

            # === Registrar acción en bitácora ===
            usuario_log = DBManager.get_user()
            if usuario_log:
                DBManager.insertar_bitacora(
                    usuario=usuario_log["nombre"],
                    rol=usuario_log["rol"],
                    accion="Modificación de departamento",
                    resultado=f"Departamento ID {self.departamento['id']} actualizado a '{nuevo_nombre}'."
                )

            if callable(self.volver_callback):
                self.volver_callback(refrescar=True)
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar el departamento.")

    def actualizar_departamento(self, dep_id, nombre):
        """Actualiza el departamento en la base de datos."""
        from core.database import get_connection
        conn = get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE departments SET name = %s WHERE id = %s", (nombre, dep_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar departamento: {e}")
            return False
        finally:
            conn.close()

    # -----------------------------------------------------
    def cancelar(self):
        """Vuelve al listado sin guardar cambios."""
        if callable(self.volver_callback):
            self.volver_callback(refrescar=False)


