# -*- coding: utf-8 -*-
"""
LoginDialog — validación real con MySQL (solo rol administrador)
"""

import sys
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QLabel, QLineEdit,
    QPushButton, QMessageBox, QWidget
)
from core.resources import asset_path
from core.db_manager import DBManager  # ← import real

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1130, 800)
        Dialog.setWindowTitle("INCIDEX - Login")
        Dialog.setStyleSheet("background-color: #1E73FA;")

        # === Barra superior ===
        self.top_bar = QFrame(Dialog)
        self.top_bar.setGeometry(QRect(0, 0, 1131, 41))
        self.top_bar.setStyleSheet("background-color: #B3B3B3; border: 0.5px solid #ffffff;")

        self.btn_back = QPushButton(self.top_bar)
        self.btn_back.setGeometry(QRect(10, 5, 30, 30))
        self.btn_back.setIcon(QIcon(asset_path("icons/back.png")))
        self.btn_back.setFlat(True)
        self.btn_back.setVisible(True)
        self.btn_back.setStyleSheet("background: transparent;")

        self.btn_forward = QPushButton(self.top_bar)
        self.btn_forward.setGeometry(QRect(45, 5, 30, 30))
        self.btn_forward.setIcon(QIcon(asset_path("icons/forward.png")))
        self.btn_forward.setFlat(True)
        self.btn_forward.setVisible(True)
        self.btn_forward.setStyleSheet("background: transparent;")

        # === Segunda barra gris ===
        self.second_bar = QFrame(Dialog)
        self.second_bar.setGeometry(QRect(0, 40, 1131, 41))
        self.second_bar.setStyleSheet("background-color: #B3B3B3; border: 0.5px solid #ffffff;")

        self.btn_archivo = QPushButton("Archivo", self.second_bar)
        self.btn_archivo.setGeometry(QRect(10, 5, 61, 30))
        self._style_toolbar_button(self.btn_archivo)

        self.btn_editar = QPushButton("Editar", self.second_bar)
        self.btn_editar.setGeometry(QRect(80, 5, 61, 30))
        self._style_toolbar_button(self.btn_editar)

        self.btn_salir = QPushButton("Salir", self.second_bar)
        self.btn_salir.setGeometry(QRect(150, 5, 61, 30))
        self._style_toolbar_button(self.btn_salir)

        # === Contenedor principal ===
        self.widget = QWidget(Dialog)
        self.widget.setGeometry(QRect(0, 79, 1131, 681))
        self.widget.setStyleSheet("background-color: #1E73FA;")

        # === Título ===
        self.label_title = QLabel("LOGIN INCIDEX", self.widget)
        self.label_title.setGeometry(QRect(370, 40, 391, 81))
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setStyleSheet("""
            color: white;
            font-size: 52px;
            font-weight: bold;
        """)

        # === Marco del formulario ===
        self.frame = QFrame(self.widget)
        self.frame.setGeometry(QRect(320, 150, 491, 340))
        self.frame.setStyleSheet("background-color: white; border-radius: 8px;")

        # Campos
        self.label_user = QLabel("Correo:", self.frame)
        self.label_user.setGeometry(QRect(50, 40, 100, 20))
        self.label_user.setStyleSheet("color: black; font-weight: bold;")

        self.line_user = QLineEdit(self.frame)
        self.line_user.setGeometry(QRect(50, 70, 391, 41))
        self.line_user.setPlaceholderText("Correo electrónico")
        self._style_input(self.line_user)

        self.label_pass = QLabel("Contraseña:", self.frame)
        self.label_pass.setGeometry(QRect(50, 130, 100, 20))
        self.label_pass.setStyleSheet("color: black; font-weight: bold;")

        self.line_pass = QLineEdit(self.frame)
        self.line_pass.setGeometry(QRect(50, 160, 391, 41))
        self.line_pass.setPlaceholderText("Contraseña")
        self.line_pass.setEchoMode(QLineEdit.Password)
        self._style_input(self.line_pass)

        # Botón login
        self.btn_login = QPushButton("Ingresar", self.frame)
        self.btn_login.setGeometry(QRect(180, 230, 131, 35))
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #333; }
        """)



        # === Logo ===
        self.label_logo = QLabel(self.widget)
        self.label_logo.setGeometry(QRect(515, 520, 101, 91))
        self.label_logo.setPixmap(QPixmap(asset_path("logo.png")))
        self.label_logo.setScaledContents(True)

        # === Footer ===
        self.footer = QFrame(Dialog)
        self.footer.setGeometry(QRect(0, 760, 1131, 41))
        self.footer.setStyleSheet("background-color: #B3B3B3; border: 0.5px solid #ffffff;")

    # ---- Estilos ----
    def _style_toolbar_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 1px solid black;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)

    def _style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                border: 2px solid black;
                border-radius: 5px;
                color: black;
                font-size: 14px;
                padding: 6px;
            }
        """)

# ============================================================
#  Clase funcional del Login
# ============================================================

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self._connect_signals()

    def _connect_signals(self):
        self.ui.btn_salir.clicked.connect(self.close)
        self.ui.btn_login.clicked.connect(self._on_login)

    # === Acción de Login ===
    def _on_login(self):
        email = self.ui.line_user.text().strip()
        pwd = self.ui.line_pass.text().strip()
 
        if not email or not pwd:
            self._msg("Campos vacíos", "Por favor ingrese correo y contraseña.", QMessageBox.Warning)
            return

        user = DBManager.verificar_usuario(email, pwd)

        if not user:
            self._msg("Acceso denegado", "Credenciales incorrectas o sin permisos de administrador.", QMessageBox.Critical)
            return

        # === Guardar usuario logeado globalmente ===
        DBManager.set_user({
            'id': user['id'],
            'nombre': user['nombre'],
            'rol': 'ADMIN' if user['role_id'] == 1 else 'OTRO',
            'email': user['email']
        })

        # === Registrar acción en bitácora ===
        DBManager.insertar_bitacora(
            usuario=user['nombre'],
            rol='ADMIN' if user['role_id'] == 1 else 'OTRO',
            accion='Inicio de sesión',
            resultado='Éxito'
        )

        # === Mensaje y paso a ventana principal ===
        self._msg("Bienvenido", f"Inicio de sesión exitoso: {user['nombre']}", QMessageBox.Information)
        self._open_main()
                
    def _on_forgot(self):
        self._msg("Recuperar contraseña", "Función aún no implementada.", QMessageBox.Information)

    def _open_main(self):
        try:
            from views.main_window import MainWindow
            self.main = MainWindow()
            self.main.show()
            self.close()
        except Exception as e:
            self._msg("Error", f"No se pudo abrir la ventana principal:\n{e}", QMessageBox.Critical)

    def _msg(self, title, text, icon):
        QMessageBox(icon, title, text, QMessageBox.Ok, self).exec()

# ============================================================
#  Punto de entrada
# ============================================================

def main():
    app = QApplication(sys.argv)
    window = LoginDialog()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


