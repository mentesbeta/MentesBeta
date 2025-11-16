# -*- coding: utf-8 -*-
"""
AdministrarUsuariosPage — Vista funcional con conexión a MySQL,
filtro y paginación (15 registros por página).
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QMessageBox
)
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox
from core.resources import asset_path
from core.db_manager import DBManager  # conexión real a la DB
import math


class AdministrarUsuariosPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        title = QLabel("Administrar Usuarios")
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
        frame_layout.addLayout(top_row)
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

        headers = ["ID", "Nombre", "Apellido", "Correo", "Rol", "Acciones"]
        widths = [35, 85, 85, 125, 90, 150]

        for i, h in enumerate(headers):
            lab = QLabel(h)
            lab.setFixedWidth(widths[i])
            header_layout.addWidget(lab)

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
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Anchos de columnas
        self.table.setColumnWidth(0, 35)
        self.table.setColumnWidth(1, 85)
        self.table.setColumnWidth(2, 85)
        self.table.setColumnWidth(3, 125)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 150)

        # === Obtener datos desde la base de datos ===
        self.usuarios = [
            (str(u["id"]), u["nombre"], u["apellido"], u["correo"], u["rol"])
            for u in DBManager.obtener_usuarios()
        ]

        self.filtered_data = self.usuarios.copy()
        self.current_page = 1
        self.rows_per_page = 15
        self.total_pages = math.ceil(len(self.filtered_data) / self.rows_per_page)

        # Cargar tabla inicial
        self.cargar_tabla()
        frame_layout.addWidget(self.table)

        # === Paginación ===
        self.pagination_row = QHBoxLayout()
        self.pagination_row.setContentsMargins(0, 0, 0, 0)
        self.pagination_row.addStretch()

        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setContentsMargins(0, 10, 0, 0)
        self.pagination_layout.setSpacing(4)
        self.pagination_row.addLayout(self.pagination_layout)
        frame_layout.addLayout(self.pagination_row)
        self.actualizar_paginacion()

        # === Añadir al layout principal ===
        main_layout.addWidget(frame, alignment=Qt.AlignCenter)

        # === Logo inferior ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        main_layout.addWidget(logo_label, alignment=Qt.AlignRight | Qt.AlignBottom)

    # ---------------------------------------------------------
    #   Cargar datos
    # ---------------------------------------------------------
    def cargar_tabla(self):
        """Carga solo los registros visibles en la página actual."""
        self.table.setRowCount(0)
        start = (self.current_page - 1) * self.rows_per_page
        end = start + self.rows_per_page
        datos = self.filtered_data[start:end]

        for user in datos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(user):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col == 3 and len(val) > 15:
                    item.setText(val[:13] + "…")
                self.table.setItem(row, col, item)

            # === Botones Acciones ===
            container = QWidget()
            container.setStyleSheet("background-color: white;")
            hbox = QHBoxLayout(container)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(8)

            btn_mod = QPushButton("Modificar")
            btn_mod.setFixedWidth(75)
            btn_mod.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 3px 6px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #27ae60; }
            """)

            btn_eli = QPushButton("Eliminar")
            btn_eli.setFixedWidth(75)
            btn_eli.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: 1px solid #c0392b;
                    border-radius: 4px;
                    padding: 3px 6px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)

            # ✅ FIX: el lambda congela correctamente el usuario (antes quedaba desconectado)
            btn_mod.clicked.connect(lambda _, u=user: self.abrir_modificar_usuario(u))
            btn_eli.clicked.connect(lambda _, u=user: self.eliminar_usuario(u))

            hbox.addWidget(btn_mod)
            hbox.addWidget(btn_eli)
            hbox.addStretch()
            self.table.setCellWidget(row, 5, container)

    # ---------------------------------------------------------
    #   Abrir vista de modificación
    # ---------------------------------------------------------
    def abrir_modificar_usuario(self, user_tuple):
        """Abre la página de modificar usuario usando datos completos del usuario."""
        
        user_id = int(user_tuple[0])

        # Obtener TODOS los datos reales del usuario desde la DB
        data = DBManager.obtener_usuario_por_id(user_id)

        if not data:
            QMessageBox.warning(self, "Error", "No se pudo cargar la información del usuario.")
            return

        window = QApplication.activeWindow()

        # Cargar los datos completos en la vista de modificación
        if hasattr(window, "modificar_usuario_page"):
            window.modificar_usuario_page.cargar_datos_usuario(data)
            window.stack.setCurrentWidget(window.modificar_usuario_page)


    def _volver_a_listado(self, refrescar=False):
        """Vuelve al listado y actualiza si es necesario."""
        from PySide6.QtWidgets import QApplication

        # Buscar ventana principal (MainWindow)
        window = QApplication.activeWindow()
        if not window:
            print("⚠ No se encontró la ventana principal.")
            return

        # Si debe refrescar la tabla
        if refrescar and hasattr(window, "admin_user_page"):
            window.admin_user_page.refrescar_datos()

        # Volver a la vista de administración
        if hasattr(window, "stack") and hasattr(window, "admin_user_page"):
            window.stack.setCurrentWidget(window.admin_user_page)


    # ---------------------------------------------------------
    #   Filtro
    # ---------------------------------------------------------
    def filtrar_tabla(self):
        texto = self.search_box.text().strip().lower()
        self.filtered_data = [
            user for user in self.usuarios
            if any(texto in str(campo).lower() for campo in user)
        ]
        self.current_page = 1
        self.total_pages = math.ceil(len(self.filtered_data) / self.rows_per_page)
        self.cargar_tabla()
        self.actualizar_paginacion()

    # ---------------------------------------------------------
    #   Eliminar usuario
    # ---------------------------------------------------------
    def eliminar_usuario(self, user_tuple):
        """Confirma y desactiva un usuario (is_active=0)."""
        user_id = int(user_tuple[0])
        nombre = user_tuple[1]

        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Deseas desactivar al usuario '{nombre}'?\nEl usuario no será eliminado, solo marcado como inactivo.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            ok = DBManager.desactivar_usuario(user_id)
            if ok:
                QMessageBox.information(self, "Usuario desactivado", f"El usuario '{nombre}' fue desactivado correctamente.")
                self.refrescar_datos()

                # === Registrar acción en bitácora ===
                usuario_log = DBManager.get_user()
                if usuario_log:
                    DBManager.insertar_bitacora(
                        usuario=usuario_log["nombre"],
                        rol=usuario_log["rol"],
                        accion="Desactivación de usuario",
                        resultado=f"Usuario '{nombre}' (ID {user_id}) desactivado correctamente."
                    )

            else:
                QMessageBox.critical(self, "Error", "No se pudo desactivar el usuario.")
    # ---------------------------------------------------------
    #   Refrescar tabla
    # ---------------------------------------------------------
    def refrescar_datos(self):
        """Recarga todos los usuarios activos desde la base y reconstruye la tabla."""
        self.usuarios = [
            (str(u["id"]), u["nombre"], u["apellido"], u["correo"], u["rol"])
            for u in DBManager.obtener_usuarios()
        ]
        self.filtered_data = self.usuarios.copy()
        self.cargar_tabla()
        self.actualizar_paginacion()
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
        """Actualiza los botones de paginación."""
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

        # Prev
        self.pagination_layout.addWidget(make_btn("<", lambda: self.cambiar_pagina(self.current_page - 1)))

        # Números
        for i in range(1, total_pages + 1):
            self.pagination_layout.addWidget(make_btn(str(i), lambda _, x=i: self.cambiar_pagina(x), i == self.current_page))

        # Next
        self.pagination_layout.addWidget(make_btn(">", lambda: self.cambiar_pagina(self.current_page + 1)))

    def cambiar_pagina(self, nueva_pagina):
        total_pages = max(1, math.ceil(len(self.filtered_data) / self.rows_per_page))
        if 1 <= nueva_pagina <= total_pages:
            self.current_page = nueva_pagina
            self.cargar_tabla()
            self.actualizar_paginacion()


