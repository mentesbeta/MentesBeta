# -*- coding: utf-8 -*-
"""
AdministrarDepartamentosPage — listado de departamentos con búsqueda,
paginación y acciones de Modificar / Eliminar (uniforme con otros listados).
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager
import math


class AdministrarDepartamentosPage(QWidget):
    def __init__(self, abrir_modificar_callback=None, parent=None):
        super().__init__(parent)
        self.abrir_modificar_callback = abrir_modificar_callback

        # === Fondo general ===
        self.setStyleSheet("background-color: #1E73FA;")

        # === Layout principal ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 30, 40, 30)
        main_layout.setSpacing(0)

        # === Contenedor blanco ===
        frame = QFrame()
        frame.setFixedSize(700, 700)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(15)

        # === Cabecera: título + buscador ===
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title = QLabel("Administrar Departamentos")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #000;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar...")
        self.search_box.setFixedWidth(220)
        self.search_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 15px;
                padding: 6px 12px;
                background-color: #f8f9fa;
                color: #333;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #1E73FA;
                background-color: #fff;
            }
        """)
        self.search_box.textChanged.connect(self.filtrar_tabla)

        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(self.search_box)

        # === Botón actualizar ===
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.setFixedWidth(90)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #1E73FA;
                color: white;
                border-radius: 8px;
                padding: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #155ec0;
            }
        """)
        self.btn_refresh.clicked.connect(self.refrescar_datos)
        top_row.addWidget(self.btn_refresh)

        frame_layout.addLayout(top_row)

        # === Encabezado ===
        header_row = QFrame()
        header_row.setStyleSheet("""
            QFrame {
                background-color: #dfe4ea;
                border-radius: 6px;
                padding: 6px;
            }
            QLabel {
                font-weight: bold;
                color: #000;
                font-size: 11px;
            }
        """)
        header_layout = QHBoxLayout(header_row)
        headers = ["ID", "Nombre", "Acciones"]
        widths = [50, 350, 150]
        for i, h in enumerate(headers):
            lab = QLabel(h)
            lab.setFixedWidth(widths[i])
            header_layout.addWidget(lab)
        frame_layout.addWidget(header_row)

        # === Tabla ===
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dcdcdc;
                background-color: #ffffff;
                font-size: 11px;
                color: #000;
                border: none;
            }
        """)
        self.table.verticalHeader().setDefaultSectionSize(20)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 350)
        self.table.setColumnWidth(2, 150)

        frame_layout.addWidget(self.table)

        # === Paginación ===
        self.pagination_row = QHBoxLayout()
        self.pagination_row.setContentsMargins(0, 0, 0, 0)
        self.pagination_row.addStretch()

        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setSpacing(4)
        self.pagination_row.addLayout(self.pagination_layout)
        frame_layout.addLayout(self.pagination_row)

        # === Cargar datos ===
        self.refrescar_datos()

        # === Agregar contenedor al layout principal ===
        main_layout.addWidget(frame, alignment=Qt.AlignCenter)

        # === Logo ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        main_layout.addWidget(logo_label, alignment=Qt.AlignRight | Qt.AlignBottom)

    # -----------------------------------------------------
    def cargar_tabla(self):
        self.table.setRowCount(0)
        start = (self.current_page - 1) * self.rows_per_page
        end = start + self.rows_per_page
        datos = self.filtered_data[start:end]

        for dep in datos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(dep["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(dep["name"]))

            # --- Acciones ---
            container = QWidget()
            container.setStyleSheet("background-color: white;")
            hbox = QHBoxLayout(container)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(8)

            btn_mod = QPushButton("Modificar")
            btn_mod.setFixedSize(75, 20)
            btn_mod.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #27ae60; }
            """)
            btn_mod.clicked.connect(lambda _, d=dep: self.abrir_modificar_departamento(d))

            btn_eli = QPushButton("Eliminar")
            btn_eli.setFixedSize(75, 20)
            btn_eli.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: 1px solid #c0392b;
                    border-radius: 4px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            btn_eli.clicked.connect(lambda _, d=dep: self.eliminar_departamento(d))

            hbox.addWidget(btn_mod)
            hbox.addWidget(btn_eli)
            hbox.addStretch()
            self.table.setCellWidget(row, 2, container)

    # -----------------------------------------------------
    def abrir_modificar_departamento(self, dep):
        """Abre la vista para modificar un departamento."""
        if callable(self.abrir_modificar_callback):
            self.abrir_modificar_callback(dep)

    def eliminar_departamento(self, dep):
        confirm = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Deseas eliminar el departamento '{dep['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            ok = DBManager.eliminar_departamento(dep["id"])
            if ok:
                QMessageBox.information(self, "Éxito", "Departamento eliminado correctamente.")
                self.refrescar_datos()

                # === Registrar acción en bitácora ===
                usuario_log = DBManager.get_user()
                if usuario_log:
                    DBManager.insertar_bitacora(
                        usuario=usuario_log["nombre"],
                        rol=usuario_log["rol"],
                        accion="Eliminación de departamento",
                        resultado=f"Departamento '{dep['name']}' (ID {dep['id']}) eliminado correctamente."
                    )

            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el departamento.")
        # -----------------------------------------------------
    def refrescar_datos(self):
        try:
            self.departamentos = DBManager.obtener_departamentos() or []
        except Exception as e:
            print("❌ Error al obtener departamentos:", e)
            self.departamentos = []

        self.filtered_data = self.departamentos.copy()
        self.current_page = 1
        self.rows_per_page = 15
        self.total_pages = math.ceil(len(self.filtered_data) / self.rows_per_page)
        self.cargar_tabla()
        self.actualizar_paginacion()

    def _limpiar_paginacion(self):
        while self.pagination_layout.count():
            item = self.pagination_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def actualizar_paginacion(self):
        self._limpiar_paginacion()
        total_pages = max(1, math.ceil(len(self.filtered_data) / self.rows_per_page))

        def make_btn(text, cb, active=False):
            btn = QPushButton(text)
            btn.setFixedWidth(30)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#1E73FA' if active else '#ffffff'};
                    color: {'white' if active else 'black'};
                    border-radius: 4px;
                    border: 1px solid #cccccc;
                    font-weight: {'bold' if active else 'normal'};
                    padding: 4px 6px;
                }}
                QPushButton:hover {{
                    background-color: {'#1E73FA' if active else '#e0e0e0'};
                }}
            """)
            btn.clicked.connect(cb)
            return btn

        self.pagination_layout.addWidget(make_btn("<", lambda: self.cambiar_pagina(self.current_page - 1)))
        for i in range(1, total_pages + 1):
            self.pagination_layout.addWidget(make_btn(str(i), lambda _, x=i: self.cambiar_pagina(x), i == self.current_page))
        self.pagination_layout.addWidget(make_btn(">", lambda: self.cambiar_pagina(self.current_page + 1)))

    def cambiar_pagina(self, nueva_pagina):
        total_pages = max(1, math.ceil(len(self.filtered_data) / self.rows_per_page))
        if 1 <= nueva_pagina <= total_pages:
            self.current_page = nueva_pagina
            self.cargar_tabla()
            self.actualizar_paginacion()

    def filtrar_tabla(self):
        texto = self.search_box.text().strip().lower()
        self.filtered_data = [d for d in self.departamentos if texto in d["name"].lower()]
        self.current_page = 1
        self.cargar_tabla()
        self.actualizar_paginacion()


