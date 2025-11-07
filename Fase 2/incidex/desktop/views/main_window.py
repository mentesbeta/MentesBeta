# -*- coding: utf-8 -*-
"""
MainWindow — Ventana principal de Incidex con menú lateral completo,
barras superiores, navegación entre vistas y Bitácora de Acciones.
Incluye: Usuarios, Categorías, Departamentos y Reportes.
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget
)
from core.resources import asset_path
from core.db_manager import DBManager

# === Imports de vistas ===
from views.home_page import HomePage
from views.create_user_page import CreateUserPage
from views.administrar_usuarios_page import AdministrarUsuariosPage
from views.modificar_usuario_page import ModificarUsuarioPage
from views.bitacora_page import BitacoraPage

# Nuevas vistas
from views.create_categoria_page import CreateCategoriaPage
from views.administrar_categorias_page import AdministrarCategoriasPage
from views.create_departamento_page import CreateDepartamentoPage
from views.administrar_departamentos_page import AdministrarDepartamentosPage
from views.generar_reporte_page import GenerarReportePage
from views.modificar_categoria_page import ModificarCategoriaPage
from views.modificar_departamento_page import ModificarDepartamentoPage
from views.generar_reporte_page import GenerarReportePage

from PySide6.QtGui import QStandardItem


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Incidex - Escritorio")
        self.resize(1130, 800)

        # === Contenedor base ===
        central_widget = QWidget(self)
        central_widget.setStyleSheet("background-color: #1E73FA;")
        self.setCentralWidget(central_widget)
        usuario = DBManager.get_user()
        if usuario:
            print(f"Usuario logeado: {usuario['nombre']} ({usuario['rol']})")
        else:
            print("⚠ No hay usuario en sesión.")

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === Barras superiores ===
        self._build_top_bars(layout)

        # === Contenido principal ===
        main_content = QHBoxLayout()
        main_content.setContentsMargins(0, 0, 0, 0)
        main_content.setSpacing(0)
        layout.addLayout(main_content)

        # === Menú lateral ===
        self.sidebar = self._build_sidebar()
        main_content.addWidget(self.sidebar, 1)

        # === Contenedor dinámico ===
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #1E73FA;")
        main_content.addWidget(self.stack, 4)

        # === Páginas ===
        self.home_page = HomePage()
        self.create_user_page = CreateUserPage()
        self.create_categoria_page = CreateCategoriaPage()
        self.create_departamento_page = CreateDepartamentoPage()
        self.admin_categoria_page = AdministrarCategoriasPage(
            abrir_modificar_callback=lambda cat: self.abrir_modificar_categoria(cat)
        )
        self.admin_departamentos_page = AdministrarDepartamentosPage(
            abrir_modificar_callback=lambda dep: self.abrir_modificar_departamento(dep)
        )
        self.admin_user_page = AdministrarUsuariosPage()
        self.modificar_usuario_page = ModificarUsuarioPage(
            volver_callback=lambda refrescar=False: self.volver_a_administrar(refrescar)
        )

        self.modificar_categoria_page = ModificarCategoriaPage(
            volver_callback=lambda refrescar=False: self.volver_a_admin_categorias(refrescar)
        )

        self.modificar_departamento_page = ModificarDepartamentoPage(
            volver_callback=lambda refrescar=False: self.volver_a_admin_departamentos(refrescar)
        )
        # Crear la página
        self.report_page = GenerarReportePage()
        self.report_page.generarReporte.connect(self.on_generar_reporte)
        self.report_page.conectar_tickets(self.on_generar_reporte)
        self.report_page.conectar_acciones(self.on_generar_bitacora)

        self.bitacora_page = BitacoraPage()

        # === Añadir páginas al stack ===
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.create_user_page)
        self.stack.addWidget(self.create_categoria_page)
        self.stack.addWidget(self.create_departamento_page)
        self.stack.addWidget(self.admin_user_page)
        self.stack.addWidget(self.modificar_usuario_page)
        self.stack.addWidget(self.admin_categoria_page)
        self.stack.addWidget(self.admin_departamentos_page)
        self.stack.addWidget(self.report_page)
        self.stack.addWidget(self.bitacora_page)
        self.stack.addWidget(self.modificar_categoria_page)
        self.stack.addWidget(self.modificar_departamento_page)

        self.stack.setCurrentWidget(self.home_page)

        # === Footer ===
        self.footer = QFrame()
        self.footer.setFixedHeight(40)
        self.footer.setStyleSheet("background-color: #B3B3B3; border: 0.5px solid #ffffff;")
        layout.addWidget(self.footer)

        # === Conectar botones de administrar usuarios ===
        self.conectar_botones_administrar()

    # ---------------------------------------------------------
    #   Barras superiores
    # ---------------------------------------------------------
    def _build_top_bars(self, parent_layout):
        top_bar = QFrame()
        top_bar.setFixedHeight(40)
        top_bar.setStyleSheet("background-color: #B3B3B3; border: 0.5px solid #ffffff;")

        btn_back = QPushButton(top_bar)
        btn_back.setGeometry(QRect(10, 5, 30, 30))
        btn_back.setIcon(QIcon(asset_path("icons/back.png")))
        btn_back.setFlat(True)
        btn_back.setStyleSheet("background: transparent;")

        btn_forward = QPushButton(top_bar)
        btn_forward.setGeometry(QRect(45, 5, 30, 30))
        btn_forward.setIcon(QIcon(asset_path("icons/forward.png")))
        btn_forward.setFlat(True)
        btn_forward.setStyleSheet("background: transparent;")

        parent_layout.addWidget(top_bar)

        second_bar = QFrame()
        second_bar.setFixedHeight(40)
        second_bar.setStyleSheet("background-color: #B3B3B3; border: 0.5px solid #ffffff;")

        btn_archivo = self._toolbar_button("Archivo")
        btn_editar = self._toolbar_button("Editar")
        btn_salir = self._toolbar_button("Salir")

        bar_layout = QHBoxLayout(second_bar)
        bar_layout.setContentsMargins(10, 0, 0, 0)
        bar_layout.setSpacing(8)
        bar_layout.addWidget(btn_archivo)
        bar_layout.addWidget(btn_editar)
        bar_layout.addWidget(btn_salir)
        bar_layout.addStretch()

        btn_salir.clicked.connect(self.close)
        parent_layout.addWidget(second_bar)

    def _toolbar_button(self, text):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 1px solid black;
                border-radius: 5px;
                padding: 5px;
                min-width: 60px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f0f0f0; }
        """)
        return btn

    # ---------------------------------------------------------
    #   Barra lateral (menú)
    # ---------------------------------------------------------
    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame { background-color: #ffffff; border-right: 1px solid #dddddd; }
        """)
        sidebar.setFixedWidth(230)

        root = QVBoxLayout(sidebar)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        button_style = """
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px;
                text-align: left;
            }
            QPushButton:hover { background-color: #f0f0f0; }
            QPushButton:pressed { background-color: #e0e0e0; }
        """

        def make_menu_button(es_text: str, en_text: str, callback=None) -> QPushButton:
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(button_style)
            btn.setMinimumHeight(56)

            container = QWidget(btn)
            container.setStyleSheet("background: transparent;")
            v = QVBoxLayout(container)
            v.setContentsMargins(12, 8, 12, 8)
            v.setSpacing(2)

            l_es = QLabel(es_text, container)
            l_es.setStyleSheet("color: #000; font-weight: 600; font-size: 13px;")
            l_en = QLabel(en_text, container)
            l_en.setStyleSheet("color: #666; font-weight: 400; font-size: 11px;")

            v.addWidget(l_es)
            v.addWidget(l_en)

            lay_btn = QVBoxLayout(btn)
            lay_btn.setContentsMargins(0, 0, 0, 0)
            lay_btn.addWidget(container)

            if callback:
                btn.clicked.connect(callback)
            return btn

        # ---- Botones del menú ----
        root.addWidget(make_menu_button("Inicio", "Home", lambda: self.stack.setCurrentWidget(self.home_page)))
        root.addWidget(make_menu_button("Crear Usuario", "Create User", lambda: self.stack.setCurrentWidget(self.create_user_page)))
        root.addWidget(make_menu_button("Crear Categoría", "Create Category", lambda: self.stack.setCurrentWidget(self.create_categoria_page)))
        root.addWidget(make_menu_button("Crear Departamento", "Create Department", lambda: self.stack.setCurrentWidget(self.create_departamento_page)))
        root.addWidget(make_menu_button("Administrar Usuarios", "Manage Users", lambda: self.stack.setCurrentWidget(self.admin_user_page)))
        root.addWidget(make_menu_button("Administrar Categorías", "Manage Categories", lambda: self.stack.setCurrentWidget(self.admin_categoria_page)))
        root.addWidget(make_menu_button("Administrar Departamentos", "Manage Departments", lambda: self.stack.setCurrentWidget(self.admin_departamentos_page)))
        root.addWidget(make_menu_button("Generar Reporte", "Generate Report", lambda: self.stack.setCurrentWidget(self.report_page)))
        root.addWidget(make_menu_button("Bitácora de Acciones", "Action Log", lambda: self.stack.setCurrentWidget(self.bitacora_page)))

        root.addStretch(1)

        # ---- Cerrar sesión ----
        btn_logout = make_menu_button("Cerrar Sesión", "INCIDEX", self._volver_al_login)
        root.addWidget(btn_logout)

        return sidebar

    # ---------------------------------------------------------
    #   Funciones para "Administrar Usuarios"
    # ---------------------------------------------------------
    def conectar_botones_administrar(self):
        """Conecta los botones Modificar de la tabla con la vista de ModificarUsuario."""
        table = self.admin_user_page.table
        for row in range(table.rowCount()):
            cell_widget = table.cellWidget(row, 5)
            if cell_widget:
                for btn in cell_widget.findChildren(QPushButton):
                    if btn.text() == "Modificar":
                        btn.clicked.connect(lambda _, r=row: self.ir_a_modificar_usuario(r))

    def ir_a_modificar_usuario(self, row):
        """Carga los datos del usuario seleccionado y abre la vista de modificación."""
        datos = []
        for col in range(5):  # ID, Nombre, Apellido, Correo, Rol
            item = self.admin_user_page.table.item(row, col)
            datos.append(item.text() if item else "")
        self.modificar_usuario_page.cargar_datos_usuario({
            "id": int(datos[0]),
            "nombre": datos[1],
            "apellido": datos[2],
            "correo": datos[3],
            "rol": datos[4]
        })
        self.stack.setCurrentWidget(self.modificar_usuario_page)

    # ---------------------------------------------------------
    #   Volver al login
    # ---------------------------------------------------------
    def _volver_al_login(self):
        """Cierra esta ventana, registra en bitácora, limpia la sesión y vuelve al login."""
        from core.db_manager import DBManager
        from views.login_dialog import LoginDialog

        usuario = DBManager.get_user()
        if usuario:
            DBManager.insertar_bitacora(
                usuario=usuario['nombre'],
                rol=usuario['rol'],
                accion='Cierre de sesión',
                resultado='Éxito'
            )

        # Limpiar usuario logeado
        DBManager.clear_user()
        print("🔒 Sesión cerrada correctamente.")

        # Cerrar ventana principal y volver al login
        self.hide()
        self.login = LoginDialog()
        self.login.show()
        
    # ---------------------------------------------------------
    #   Navegación entre vistas dinámicas
    # ---------------------------------------------------------
    def volver_a_administrar(self, refrescar=False):
        """Vuelve al listado de usuarios y refresca si se modificó algo."""
        if refrescar and hasattr(self, "admin_user_page"):
            self.admin_user_page.refrescar_datos()
        self.stack.setCurrentWidget(self.admin_user_page)

    def abrir_modificar_categoria(self, cat):
        self.modificar_categoria_page.cargar_datos_categoria(cat)
        self.stack.setCurrentWidget(self.modificar_categoria_page)

    def abrir_modificar_departamento(self, dep):
        self.modificar_departamento_page.cargar_datos_departamento(dep)
        self.stack.setCurrentWidget(self.modificar_departamento_page)

    def volver_a_admin_categorias(self, refrescar=False):
        """Vuelve al listado de categorías y refresca si se modificó algo."""
        if refrescar and hasattr(self, "admin_categoria_page"):
            self.admin_categoria_page.refrescar_datos()
        self.stack.setCurrentWidget(self.admin_categoria_page)

    def volver_a_admin_departamentos(self, refrescar=False):
        """Vuelve al listado de departamentos y refresca si se modificó algo."""
        if refrescar and hasattr(self, "admin_departamentos_page"):
            self.admin_departamentos_page.refrescar_datos()
        self.stack.setCurrentWidget(self.admin_departamentos_page)

    def on_generar_reporte(self, filtros):
        """Callback que se ejecuta al presionar 'Generar Reporte'."""
        from core.db_manager import DBManager
        try:
            self.report_page.set_loading(True)
            resultados = DBManager.generar_reporte_tickets(filtros)
            self.report_page.set_loading(False)

            if not resultados:
                self.report_page.load_preview_rows([], [])
                print("⚠ No se encontraron tickets con esos filtros.")
                return

            headers = [
                "ID", "Código", "Título", "Prioridad", "Estado",
                "Departamento", "Categoría", "Creado", "Actualizado"
            ]
            rows = [
                [
                    r["id"], r["code"], r["title"],
                    r.get("prioridad", "-"), r.get("estado", "-"),
                    r.get("departamento", "-"), r.get("categoria", "-"),
                    r["created_at"].strftime("%d/%m/%Y"),
                    r["updated_at"].strftime("%d/%m/%Y"),
                ]
                for r in resultados
            ]

            # Mostrar en previsualización
            self.report_page.load_preview_rows(headers, rows)
            print(f"✅ {len(rows)} tickets cargados correctamente en el reporte.")

            # === Exportar a CSV ===
            path = self.report_page.ask_save_csv()
            if path:
                import csv
                try:
                    with open(path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(rows)
                    print(f"✅ Reporte exportado correctamente a: {path}")
                except Exception as e:
                    print(f"❌ Error al exportar CSV: {e}")
            else:
                print("ℹ️ Exportación cancelada por el usuario.")

        except Exception as e:
            print("❌ Error al generar reporte:", e)
            self.report_page.set_loading(False)


    def closeEvent(self, event):
        """
        Captura cualquier tipo de cierre de la aplicación (botón salir, X, Alt+F4)
        y registra un cierre de sesión automático en la bitácora.
        """
        from core.db_manager import DBManager

        usuario = DBManager.get_user()
        if usuario:
            # Registrar en bitácora el cierre de sesión
            DBManager.insertar_bitacora(
                usuario=usuario["nombre"],
                rol=usuario["rol"],
                accion="Cierre de sesión",
                resultado="Aplicación cerrada"
            )
            print(f"🔒 Cierre de sesión registrado para {usuario['nombre']}.")

            # Limpiar sesión global
            DBManager.clear_user()

        # Aceptar el evento para que se cierre la app
        event.accept()

    def on_generar_bitacora(self, filtros):
        """Genera el reporte de bitácora, muestra y exporta el CSV."""
        from core.db_manager import DBManager
        try:
            resultados = DBManager.generar_reporte_bitacora(filtros)

            if not resultados:
                self.report_page.bit_model.clear()
                print("⚠ No se encontraron registros de bitácora con esos filtros.")
                return

            headers = ["ID", "Fecha", "Usuario", "Rol", "Acción", "Resultado"]
            rows = [
                [r["id"], r["fecha"], r["usuario"], r["rol"], r["accion"], r["resultado"]]
                for r in resultados
            ]

            # Mostrar previsualización
            self.report_page.bit_model.clear()
            self.report_page.bit_model.setHorizontalHeaderLabels(headers)
            for r in rows:
                self.report_page.bit_model.appendRow([QStandardItem(str(x)) for x in r])

            print(f"✅ {len(rows)} registros de bitácora cargados correctamente.")

            # === Exportar a CSV ===
            path = self.report_page.ask_save_csv()
            if path:
                import csv
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)
                print(f"✅ Reporte de bitácora exportado a: {path}")
            else:
                print("ℹ️ Exportación cancelada por el usuario.")

        except Exception as e:
            print("❌ Error al generar reporte de bitácora:", e)
  

  