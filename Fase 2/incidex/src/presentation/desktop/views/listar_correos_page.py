# -*- coding: utf-8 -*-
"""
ListarCorreosPage — Vista coherente con Incidex.
Versión final con ventana emergente real (sin botón de cierre) que se cierra automáticamente.
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem, QPushButton, QTextEdit, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap
from core.resources import asset_path
from core.db_manager import DBManager


# =========================================================
#   Worker (hilo secundario)
# =========================================================
class CorreosWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, usuario, contraseña):
        super().__init__()
        self.usuario = usuario
        self.contraseña = contraseña
        self._running = True

    def run(self):
        """Ejecuta la consulta IMAP sin bloquear la UI."""
        try:
            if not self._running:
                return
            correos = DBManager.obtener_correos_usuario(self.usuario, self.contraseña)
            if self._running:
                self.finished.emit(correos)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._running = False


# =========================================================
#   Ventana emergente (sin botón de cierre)
# =========================================================
class CargandoVentana(QDialog):
    """Ventana emergente independiente, centrada, bloqueante y sin botón de cierre."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._permitir_cierre = False  # 🔒 bloquea cierre manual
        self.setModal(True)
        self.setWindowTitle("Cargando correos...")
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        # Customizamos ventana: solo título, sin cerrar/minimizar/maximizar

        self.setFixedSize(300, 150)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E73FA;
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Cargando correos")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.dots = QLabel("")
        self.dots.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.dots)

        # Animación de puntos suspensivos (...)
        self.dot_seq = ["", ".", "..", "..."]
        self.index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(400)

    def _animate(self):
        self.dots.setText(self.dot_seq[self.index])
        self.index = (self.index + 1) % len(self.dot_seq)

    def showEvent(self, e):
        """Centrar la ventana en pantalla."""
        screen = self.screen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )
        super().showEvent(e)

    def closeEvent(self, e):
        """Evita que el usuario cierre la ventana manualmente."""
        if self._permitir_cierre:
            self.timer.stop()
            e.accept()
        else:
            e.ignore()

    def cerrar_programaticamente(self):
        """Permite cerrar la ventana desde el código (no manualmente)."""
        self._permitir_cierre = True
        self.close()
        self._permitir_cierre = False


# =========================================================
#   Página principal
# =========================================================
class ListarCorreosPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBManager()
        self.usuario = "incidexadmescritorio@gmail.com"
        self.contraseña = "ivybgbsursbgdqyd"
        self._correos_cargados = False
        self.worker = None
        self.loading_window = None
        self._setup_ui()

    # ---------------------------------------------------------
    #   Interfaz visual principal
    # ---------------------------------------------------------
    def _setup_ui(self):
        self.setStyleSheet("background-color: #1E73FA;")

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

        # === Título + botón actualizar ===
        top_row = QHBoxLayout()
        title = QLabel("Bandeja de Correos")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #000;")

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
            QPushButton:hover { background-color: #155ec0; }
        """)
        self.btn_refresh.clicked.connect(self.cargar_correos)

        top_row.addWidget(title)
        top_row.addStretch()
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
        headers = ["Asunto", "Acción"]
        widths = [500, 90]
        for i, h in enumerate(headers):
            lab = QLabel(h)
            lab.setFixedWidth(widths[i])
            header_layout.addWidget(lab)
        frame_layout.addWidget(header_row)

        # === Tabla ===
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
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
        self.table.setColumnWidth(0, 500)
        self.table.setColumnWidth(1, 90)
        frame_layout.addWidget(self.table)

        # === Etiqueta sin correos ===
        self.no_data_label = QLabel("No hay correos disponibles")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setStyleSheet("color: #777; font-size: 12px; font-style: italic;")
        frame_layout.addWidget(self.no_data_label)
        self.no_data_label.hide()

        # === Logo inferior ===
        logo_label = QLabel()
        logo_pix = QPixmap(asset_path("logo.png")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        main_layout.addWidget(frame, alignment=Qt.AlignCenter)
        main_layout.addWidget(logo_label, alignment=Qt.AlignRight | Qt.AlignBottom)

    # ---------------------------------------------------------
    #   Cargar correos (ventana emergente)
    # ---------------------------------------------------------
    def cargar_correos(self):
        """Abre una ventana emergente real mientras se cargan los correos."""
        if self.worker and self.worker.isRunning():
            return

        self.table.setRowCount(0)
        self.no_data_label.hide()

        # Mostrar ventana emergente bloqueante
        self.loading_window = CargandoVentana()
        self.loading_window.setWindowModality(Qt.ApplicationModal)
        self.loading_window.show()

        # Crear hilo secundario
        self.worker = CorreosWorker(self.usuario, self.contraseña)
        self.worker.finished.connect(self._on_worker_ok)
        self.worker.error.connect(self._on_worker_err)
        self.worker.start()

        # Ejecutar la ventana modal (bloqueante)
        self.loading_window.exec()

    # ---------------------------------------------------------
    #   Éxito
    # ---------------------------------------------------------
    def _on_worker_ok(self, correos):
        if self.loading_window and self.loading_window.isVisible():
            self.loading_window.cerrar_programaticamente()

        if not correos:
            self.no_data_label.show()
        else:
            self.table.setRowCount(len(correos))
            for row, correo in enumerate(correos):
                item_asunto = QTableWidgetItem(correo["asunto"])
                item_asunto.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, 0, item_asunto)

                btn_ver = QPushButton("Ver")
                btn_ver.setFixedWidth(75)
                btn_ver.setStyleSheet("""
                    QPushButton {
                        background-color: #1E73FA;
                        color: white;
                        border: 1px solid #125BDB;
                        border-radius: 4px;
                        padding: 3px 6px;
                        font-weight: 600;
                        font-size: 11px;
                    }
                    QPushButton:hover { background-color: #125BDB; }
                """)
                btn_ver.clicked.connect(lambda _, c=correo: self.ver_correo(c))
                self.table.setCellWidget(row, 1, btn_ver)

        if self.worker:
            self.worker.quit()
            self.worker.wait()
            self.worker = None
        self._correos_cargados = True

    # ---------------------------------------------------------
    #   Error
    # ---------------------------------------------------------
    def _on_worker_err(self, msg):
        if self.loading_window and self.loading_window.isVisible():
            self.loading_window.cerrar_programaticamente()

        self.no_data_label.setText(f"⚠ Error al cargar correos:\n{msg}")
        self.no_data_label.show()

        if self.worker:
            self.worker.quit()
            self.worker.wait()
            self.worker = None

    # ---------------------------------------------------------
    #   Cierre seguro
    # ---------------------------------------------------------
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        event.accept()

    # ---------------------------------------------------------
    #   Ver correo
    # ---------------------------------------------------------
    def ver_correo(self, correo):
        dialog = QDialog(self)
        dialog.setWindowTitle("Detalle del correo")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)
        lbl_asunto = QLabel(f"<b>Asunto:</b> {correo['asunto']}")
        lbl_remitente = QLabel(f"<b>Remitente:</b> {correo['remitente']}")
        lbl_fecha = QLabel(f"<b>Fecha:</b> {correo['fecha']}")

        txt_contenido = QTextEdit()
        txt_contenido.setReadOnly(True)
        txt_contenido.setPlainText(correo["contenido"])

        layout.addWidget(lbl_asunto)
        layout.addWidget(lbl_remitente)
        layout.addWidget(lbl_fecha)
        layout.addWidget(txt_contenido)

        dialog.exec()
