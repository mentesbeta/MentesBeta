import sys
from PySide6.QtWidgets import QApplication
from views.login_dialog import LoginDialog


def main():
    """Punto de entrada de la aplicación Incidex (Escritorio)."""
    app = QApplication(sys.argv)
    app.setApplicationName("Incidex - Escritorio")
    app.setStyleSheet("""
        QMessageBox {
            background-color: #ffffff;
        }
    """)

    # Cargar la ventana de login
    window = LoginDialog()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    