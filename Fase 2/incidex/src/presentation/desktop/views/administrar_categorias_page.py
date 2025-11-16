# -*- coding: utf-8 -*-
"""
AdministrarCategoriasPage — Listado de categorías con conexión MySQL,
búsqueda, paginación, y botones de Modificar / Eliminar (estilo uniforme con AdministrarUsuariosPage).
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


class AdministrarCategoriasPage(QWidget):
    def __init__(self, abrir_modificar_callback=None, parent=None):
        super().__init__(parent)
        self.abrir_modificar_callback = abrir_modificar_callback

        # === Fondo azul general ===
        self.setStyleSheet("background-color: #1E73FA;")

        # === Layout general ===
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

        # === Fila superior: título + buscador ===
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title = QLabel("Administrar Categorías")
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


        # === Encabezado manual ===
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
        header_layout.setContentsMargins(10, 2, 10, 2)
        header_layout.setSpacing(20)

        headers = ["ID", "Nombre", "Descripción", "Acciones"]
        widths = [50, 120, 250, 150]
        for i, h in enumerate(headers):
            lab = QLabel(h)
            lab.setFixedWidth(widths[i])
            header_layout.addWidget(lab)

        frame_layout.addWidget(header_row)

        # === Tabla ===
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(True)
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
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 150)
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

        # === Añadir al layout principal ===
        main_layout.addWidget(frame, alignment=Qt.AlignCenter)

        # === Logo ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        main_layout.addWidget(logo_label, alignment=Qt.AlignRight | Qt.AlignBottom)

    # ---------------------------------------------------------
    #   Cargar datos
    # ---------------------------------------------------------
    def cargar_tabla(self):
        self.table.setRowCount(0)
        start = (self.current_page - 1) * self.rows_per_page
        end = start + self.rows_per_page
        datos = self.filtered_data[start:end]

        for cat in datos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(cat["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(cat["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(cat.get("description", "") or ""))

            # === Contenedor de botones ===
            container = QWidget()
            container.setStyleSheet("background-color: white;")  # ← fondo blanco fijo
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
            btn_mod.clicked.connect(lambda _, c=cat: self.abrir_modificar(c))

            btn_del = QPushButton("Eliminar")
            btn_del.setFixedSize(75, 20)
            btn_del.setStyleSheet("""
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
            btn_del.clicked.connect(lambda _, c=cat: self.eliminar_categoria(c))

            hbox.addWidget(btn_mod)
            hbox.addWidget(btn_del)
            hbox.addStretch()
            self.table.setCellWidget(row, 3, container)

    # ---------------------------------------------------------
    def abrir_modificar(self, cat):
        """Abre la vista de modificación de categoría."""
        if callable(self.abrir_modificar_callback):
            self.abrir_modificar_callback(cat)

    def eliminar_categoria(self, cat):
        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Deseas eliminar la categoría '{cat['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            ok = DBManager.eliminar_categoria(cat["id"])
            if ok:
                QMessageBox.information(self, "Éxito", "Categoría eliminada correctamente.")
                self.refrescar_datos()

                # === Registrar acción en bitácora ===
                usuario_log = DBManager.get_user()
                if usuario_log:
                    DBManager.insertar_bitacora(
                        usuario=usuario_log["nombre"],
                        rol=usuario_log["rol"],
                        accion="Eliminación de categoría",
                        resultado=f"Categoría '{cat['name']}' (ID {cat['id']}) eliminada correctamente."
                    )

            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la categoría.")
                
    def refrescar_datos(self):
        try:
            self.categorias = DBManager.obtener_categorias() or []
        except Exception as e:
            print("❌ Error al obtener categorías:", e)
            self.categorias = []

        self.filtered_data = self.categorias.copy()
        self.current_page = 1
        self.rows_per_page = 15
        self.total_pages = math.ceil(len(self.filtered_data) / self.rows_per_page)
        self.cargar_tabla()
        self.actualizar_paginacion()

    # ---------------------------------------------------------
    #   Paginación y filtro
    # ---------------------------------------------------------
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
        self.filtered_data = [
            cat for cat in self.categorias
            if any(texto in str(campo).lower() for campo in cat.values())
        ]
        self.current_page = 1
        self.total_pages = math.ceil(len(self.filtered_data) / self.rows_per_page)
        self.cargar_tabla()
        self.actualizar_paginacion()

        
