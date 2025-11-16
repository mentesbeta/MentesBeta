# -*- coding: utf-8 -*-
"""
BitacoraPage — Vista visual con filtro, botón de actualización y paginación (15 registros por página),
siguiendo el mismo estilo de "AdministrarUsuariosPage".
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager
import math


class BitacoraPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Fondo azul
        self.setStyleSheet("background-color: #1E73FA;")

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 30, 40, 30)
        main_layout.setSpacing(0)

        # Marco blanco principal
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

        # === Encabezado superior: título + filtro + botón actualizar ===
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title = QLabel("Bitácora de Acciones")
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

        # === Botón actualizar ===
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.setFixedWidth(100)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #1E73FA;
                color: white;
                border-radius: 8px;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #155ec0;
            }
        """)
        self.btn_refresh.clicked.connect(self.refrescar_datos)

        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(self.search_box)
        top_row.addWidget(self.btn_refresh)
        frame_layout.addLayout(top_row)

        # === Encabezado visual (manual) ===
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

        headers = ["ID", "Fecha", "Usuario", "Rol", "Acción", "Resultado"]
        widths = [35, 160, 100, 90, 140, 130]

        for i, h in enumerate(headers):
            lbl = QLabel(h)
            lbl.setFixedWidth(widths[i])
            header_layout.addWidget(lbl)

        frame_layout.addWidget(header_row)

        # === Tabla ===
        self.table = QTableWidget()
        self.table.setColumnCount(6)
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
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Ajuste de columnas
        for i, w in enumerate(widths):
            self.table.setColumnWidth(i, w)

        # === Cargar datos iniciales ===
        registros = DBManager.obtener_bitacora()
        self.bitacora = [
            (
                str(r["id"]),
                r["fecha"],
                r["usuario"],
                r["rol"] if r["rol"] else "-",
                r["accion"],
                r["resultado"] if r["resultado"] else "-"
            )
            for r in registros
        ]

        self.filtered_data = self.bitacora.copy()
        self.current_page = 1
        self.rows_per_page = 15
        self.total_pages = math.ceil(len(self.filtered_data) / self.rows_per_page)

        self.cargar_tabla()
        frame_layout.addWidget(self.table)

        # === Paginación ===
        self.pagination_row = QHBoxLayout()
        self.pagination_row.setContentsMargins(0, 0, 0, 0)
        self.pagination_row.addStretch()
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setSpacing(4)
        self.pagination_row.addLayout(self.pagination_layout)
        frame_layout.addLayout(self.pagination_row)
        self.actualizar_paginacion()

        # === Añadir al layout principal ===
        main_layout.addWidget(frame, alignment=Qt.AlignCenter)

        # Logo
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

        for fila in datos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(fila):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, col, item)

    # ---------------------------------------------------------
    #   Paginación
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
            btn.setStyleSheet("""
                QPushButton {
                    background-color: %s;
                    color: %s;
                    border-radius: 4px;
                    font-weight: %s;
                    border: 1px solid #cccccc;
                    padding: 4px 6px;
                }
                QPushButton:hover {
                    background-color: %s;
                }
            """ % (
                ("#1E73FA" if active else "#ffffff"),
                ("white" if active else "black"),
                ("bold" if active else "normal"),
                ("#1E73FA" if active else "#e0e0e0")
            ))
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

    # ---------------------------------------------------------
    #   Filtro
    # ---------------------------------------------------------
    def filtrar_tabla(self):
        texto = self.search_box.text().strip().lower()
        self.filtered_data = [
            fila for fila in self.bitacora
            if any(texto in str(campo).lower() for campo in fila)
        ]
        self.current_page = 1
        self.total_pages = math.ceil(len(self.filtered_data) / self.rows_per_page)
        self.cargar_tabla()
        self.actualizar_paginacion()

    # ---------------------------------------------------------
    #   Refrescar datos
    # ---------------------------------------------------------
    def refrescar_datos(self):
        registros = DBManager.obtener_bitacora()
        self.bitacora = [
            (
                str(r["id"]),
                r["fecha"],
                r["usuario"],
                r["rol"] if r["rol"] else "-",
                r["accion"],
                r["resultado"] if r["resultado"] else "-"
            )
            for r in registros
        ]
        self.filtered_data = self.bitacora.copy()
        self.current_page = 1
        self.cargar_tabla()
        self.actualizar_paginacion()
        print("🔄 Bitácora actualizada.")


