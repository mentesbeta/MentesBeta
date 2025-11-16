from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from core.resources import asset_path


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1E73FA;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setContentsMargins(20, 40, 20, 20)

        # Título principal
        title = QLabel("Home")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            color: white;
            font-weight: bold;
            background-color: #1E73FA;
            padding: 10px 30px;
        """)
        layout.addWidget(title)

        # Marco blanco central
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border-radius: 12px;")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setAlignment(Qt.AlignCenter)

        # Imagen centrada sin texto
        home_image = QLabel()
        home_image.setPixmap(QPixmap(asset_path("HOME.png")))
        home_image.setScaledContents(True)
        home_image.setFixedSize(380, 380)
        frame_layout.addWidget(home_image)

        layout.addWidget(frame)
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from core.resources import asset_path


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1E73FA;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setContentsMargins(20, 40, 20, 20)

        # Título principal
        title = QLabel("Home")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            color: white;
            font-weight: bold;
            background-color: #1E73FA;
            padding: 10px 30px;
        """)
        layout.addWidget(title)

        # Marco blanco central
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border-radius: 12px;")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setAlignment(Qt.AlignCenter)

        # Imagen centrada sin texto
        home_image = QLabel()
        home_image.setPixmap(QPixmap(asset_path("HOME.png")))
        home_image.setScaledContents(True)
        home_image.setFixedSize(380, 380)
        frame_layout.addWidget(home_image)

        layout.addWidget(frame)


