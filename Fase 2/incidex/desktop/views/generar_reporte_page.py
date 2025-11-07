# -*- coding: utf-8 -*-
"""
GenerarReportePage — vista unificada con selector superior (Tickets / Bitácora).
Diseño visual mejorado: texto negro, acordeón limpio y campos bien definidos.
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QComboBox, QDateEdit, QPushButton, QTableView, QLineEdit, QStackedWidget
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QPixmap, QStandardItemModel, QStandardItem
from core.resources import asset_path
from core.db_manager import DBManager
from PySide6.QtWidgets import QFileDialog

class GenerarReportePage(QWidget):
    generarReporte = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBManager()

        self.setStyleSheet("background-color: #1E73FA;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 30, 40, 30)
        main_layout.setSpacing(10)

        # === SELECTOR SUPERIOR (ACORDEÓN) ===
        selector_frame = QFrame()
        selector_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #cccccc;
            }
        """)
        selector_layout = QHBoxLayout(selector_frame)
        selector_layout.setContentsMargins(20, 10, 20, 10)
        selector_layout.setSpacing(10)

        self.btn_tickets = QPushButton("Reporte de Tickets")
        self.btn_bitacora = QPushButton("Reporte de Bitácora")

        for btn in (self.btn_tickets, self.btn_bitacora):
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #1E73FA;
                    border-radius: 6px;
                    font-weight: 600;
                    color: #000000;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #e6f0ff;
                }
                QPushButton:checked {
                    background-color: #1E73FA;
                    color: white;
                }
            """)

        self.btn_tickets.setChecked(True)
        selector_layout.addStretch()
        selector_layout.addWidget(self.btn_tickets)
        selector_layout.addWidget(self.btn_bitacora)
        selector_layout.addStretch()
        main_layout.addWidget(selector_frame)

        # === CONTENEDOR DINÁMICO ===
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, alignment=Qt.AlignCenter)

        # === SUBPÁGINAS ===
        self.stack.addWidget(self._build_ticket_report())
        self.stack.addWidget(self._build_bitacora_report())

        self.btn_tickets.clicked.connect(lambda: self._switch_page(0))
        self.btn_bitacora.clicked.connect(lambda: self._switch_page(1))

        # === LOGO INFERIOR ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        main_layout.addWidget(logo_label, alignment=Qt.AlignRight | Qt.AlignBottom)

    # ============================================================
    #   SUBPÁGINA: REPORTES DE TICKETS
    # ============================================================
    def _build_ticket_report(self):
        frame = QFrame()
        frame.setMinimumSize(640, 560)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
            QLabel {
                color: #000000;
                font-weight: 600;
                font-size: 12px;
            }
            QComboBox, QDateEdit {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                background-color: #ffffff;
                color: #000000;
                min-height: 26px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #e0e0e0;
            }
            QCalendarWidget QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #1E73FA;
                selection-color: #ffffff;
            }
            QPushButton#btn_generar_tickets {
                background-color: #00cc44;
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton#btn_generar_tickets:hover {
                background-color: #00aa38;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 15, 25, 15)

        title = QLabel("Reporte de Tickets")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #000;")
        layout.addWidget(title)

        # === FILTROS ===
        row1 = QHBoxLayout()
        row1.setSpacing(20)

        col1 = QVBoxLayout()
        lbl_prioridad = QLabel("Prioridad:")
        self.combo_prioridad = QComboBox()
        col1.addWidget(lbl_prioridad)
        col1.addWidget(self.combo_prioridad)

        col2 = QVBoxLayout()
        lbl_estado = QLabel("Estado:")
        self.combo_estado = QComboBox()
        col2.addWidget(lbl_estado)
        col2.addWidget(self.combo_estado)

        row1.addLayout(col1)
        row1.addLayout(col2)
        layout.addLayout(row1)

        # === FECHAS ===
        row2 = QHBoxLayout()
        row2.setSpacing(20)
        hoy = QDate.currentDate()

        col3 = QVBoxLayout()
        lbl_inicio = QLabel("Fecha Inicio:")
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(hoy)
        col3.addWidget(lbl_inicio)
        col3.addWidget(self.fecha_inicio)

        col4 = QVBoxLayout()
        lbl_fin = QLabel("Fecha Fin:")
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(hoy)
        col4.addWidget(lbl_fin)
        col4.addWidget(self.fecha_fin)

        row2.addLayout(col3)
        row2.addLayout(col4)
        layout.addLayout(row2)

        self._load_filters()

        # === PREVISUALIZACIÓN ===
        layout.addWidget(QLabel("Previsualización:"))
        self.ticket_table = QTableView()
        self.ticket_model = QStandardItemModel(self.ticket_table)
        self.ticket_table.setModel(self.ticket_model)
        layout.addWidget(self.ticket_table)

        # === BOTÓN GENERAR ===
        self.btn_generar_tickets = QPushButton("Generar Reporte")
        self.btn_generar_tickets.setObjectName("btn_generar_tickets")
        layout.addWidget(self.btn_generar_tickets, alignment=Qt.AlignCenter)

        return frame


    # ============================================================
    #   SUBPÁGINA: REPORTES DE BITÁCORA
    # ============================================================
    def _build_bitacora_report(self):
        frame = QFrame()
        frame.setMinimumSize(640, 560)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
            QLabel {
                color: #000000;
                font-weight: 600;
                font-size: 12px;
            }
            QComboBox, QDateEdit {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                background-color: #ffffff;
                color: #000000;
                min-height: 26px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #e0e0e0;
            }
            /* 🔹 Calendario emergente: fondo y texto negros */
            QCalendarWidget QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #1E73FA;
                selection-color: #ffffff;
            }
            QCalendarWidget QToolButton {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px 6px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e6f0ff;
            }
            QCalendarWidget QSpinBox {
                color: #000000;
                background: #ffffff;
            }
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {
                width: 12px;
                background-color: #f0f0f0;
            }
            QCalendarWidget QSpinBox::up-button:hover,
            QCalendarWidget QSpinBox::down-button:hover {
                background-color: #d0e2ff;
            }
            QPushButton#btn_generar_bit {
                background-color: #1E73FA;
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton#btn_generar_bit:hover {
                background-color: #155ec0;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 15, 25, 15)

        title = QLabel("Reporte de Bitácora")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #000;")
        layout.addWidget(title)

        # === FILTROS ===
        row1 = QHBoxLayout()
        row1.setSpacing(15)

        # === Usuario (ComboBox con admins activos) ===
        col1 = QVBoxLayout()
        lbl_usuario = QLabel("Usuario:")
        self.input_usuario = QComboBox()
        self.input_usuario.addItem("(todos)", None)

        try:
            admins = self.db.obtener_usuarios() or []
            for a in admins:
                if str(a.get("rol", "")).lower() in ["administrador", "admin"]:
                    nombre_completo = f"{a['nombre']} {a['apellido']}".strip()
                    nombre_corto = a['nombre']
                    self.input_usuario.addItem(nombre_completo, nombre_corto)
        except Exception as e:
            print("❌ Error al cargar administradores en bitácora:", e)

        col1.addWidget(lbl_usuario)
        col1.addWidget(self.input_usuario)
        row1.addLayout(col1)
        layout.addLayout(row1)

        # === FECHAS ===
        row2 = QHBoxLayout()
        hoy = QDate.currentDate()
        col3 = QVBoxLayout()
        lbl_inicio = QLabel("Desde:")
        self.fecha_inicio_bit = QDateEdit()
        self.fecha_inicio_bit.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_bit.setCalendarPopup(True)
        self.fecha_inicio_bit.setDate(hoy)
        col3.addWidget(lbl_inicio)
        col3.addWidget(self.fecha_inicio_bit)

        col4 = QVBoxLayout()
        lbl_fin = QLabel("Hasta:")
        self.fecha_fin_bit = QDateEdit()
        self.fecha_fin_bit.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_bit.setCalendarPopup(True)
        self.fecha_fin_bit.setDate(hoy)
        col4.addWidget(lbl_fin)
        col4.addWidget(self.fecha_fin_bit)

        row2.addLayout(col3)
        row2.addLayout(col4)
        layout.addLayout(row2)

        # === PREVISUALIZACIÓN ===
        layout.addWidget(QLabel("Previsualización:"))
        self.bit_table = QTableView()
        self.bit_model = QStandardItemModel(self.bit_table)
        self.bit_table.setModel(self.bit_model)
        self.bit_table.setStyleSheet("""
            QTableView {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #cccccc;
                selection-background-color: #1E73FA;
                selection-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #ccc;
                font-weight: bold;
                padding: 4px;
            }
        """)
        layout.addWidget(self.bit_table)

        # === BOTÓN GENERAR ===
        self.btn_generar_bit = QPushButton("Generar Informe Bitácora")
        self.btn_generar_bit.setObjectName("btn_generar_bit")
        layout.addWidget(self.btn_generar_bit, alignment=Qt.AlignCenter)

        return frame


    # ============================================================
    #   AUXILIARES
    # ============================================================
    def _switch_page(self, index):
        self.btn_tickets.setChecked(index == 0)
        self.btn_bitacora.setChecked(index == 1)
        self.stack.setCurrentIndex(index)

    def _load_filters(self):
        self.combo_prioridad.clear()
        self.combo_estado.clear()
        prioridades = self.db.get_priorities()
        estados = self.db.get_statuses()
        self.combo_prioridad.addItem("(todas)", None)
        for p in prioridades:
            self.combo_prioridad.addItem(p["name"], p["id"])
        self.combo_estado.addItem("(todos)", None)
        for e in estados:
            self.combo_estado.addItem(e["name"], e["id"])

    def _load_admins(self):
        """Carga los usuarios con rol 'Administrador'."""
        self.combo_admin.clear()
        self.combo_admin.addItem("(Todos los administradores)", None)
        admins = [
            u for u in DBManager.obtener_usuarios()
            if u["rol"].lower() == "administrador"
        ]
        for adm in admins:
            nombre_completo = f"{adm['nombre']} {adm['apellido']}"
            self.combo_admin.addItem(nombre_completo, adm["id"])


    def conectar_acciones(self, bitacora_callback):
        """Conecta el botón de la bitácora con el callback principal."""
        self.btn_generar_bit.clicked.connect(lambda: self._emit_bitacora_filters(bitacora_callback))

    def _emit_bitacora_filters(self, callback):
        """Recolecta los filtros de la bitácora y llama al callback."""
        filtros = {
            "usuario": self.input_usuario.currentData(),
            "inicio": self.fecha_inicio_bit.date(),
            "fin": self.fecha_fin_bit.date(),
        }
        if callable(callback):
            callback(filtros)


        #   ... dentro de la clase GenerarReportePage
    def ask_save_csv(self, default_name="reporte.csv"):
        """Abre un cuadro de diálogo para guardar el reporte en formato CSV."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte CSV",
            default_name,
            "CSV (*.csv)"
        )
        return path or None
    
    def conectar_tickets(self, tickets_callback):
        """Conecta el botón del reporte de tickets con el callback principal."""
        self.btn_generar_tickets.clicked.connect(lambda: self._emit_ticket_filters(tickets_callback))

    def _emit_ticket_filters(self, callback):
        """Recolecta los filtros del reporte de tickets y llama al callback."""
        filtros = {
            "prioridad_id": self.combo_prioridad.currentData(),
            "estado_id": self.combo_estado.currentData(),
            "inicio": self.fecha_inicio.date(),
            "fin": self.fecha_fin.date(),
        }
        if callable(callback):
            callback(filtros)

    def set_loading(self, is_loading: bool):
        """
        Muestra o oculta un estado de carga simple mientras se genera el reporte.
        """
        try:
            if is_loading:
                print("⏳ Generando reporte, por favor espera...")
                self.setEnabled(False)
            else:
                print("✅ Proceso de generación finalizado.")
                self.setEnabled(True)
        except Exception as e:
            print("⚠ Error al cambiar estado de carga:", e)

    def load_preview_rows(self, headers, rows):
        """
        Carga los datos del reporte de tickets en la tabla de previsualización.
        """
        try:
            self.ticket_model.clear()

            # Si no hay datos
            if not rows:
                self.ticket_model.setHorizontalHeaderLabels(["Sin resultados"])
                return

            # Configurar encabezados
            self.ticket_model.setHorizontalHeaderLabels(headers)

            # Agregar filas
            for row in rows:
                items = [QStandardItem(str(x)) for x in row]
                self.ticket_model.appendRow(items)

            # Estilizar tabla
            self.ticket_table.setStyleSheet("""
                QTableView {
                    background-color: #ffffff;
                    color: #000000;
                    gridline-color: #cccccc;
                    selection-background-color: #1E73FA;
                    selection-color: #ffffff;
                    border-radius: 8px;
                    border: 1px solid #ddd;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #ccc;
                    font-weight: bold;
                    padding: 4px;
                }
            """)
            self.ticket_table.resizeColumnsToContents()

            print(f"✅ Previsualización cargada con {len(rows)} registros.")

        except Exception as e:
            print(f"❌ Error al cargar previsualización: {e}")
        
            


