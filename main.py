import sys

from PySide6.QtWidgets import QApplication

from queue_manager import QueueManager
from favorites import FavoritesManager
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #e6e6e6;
            font-size: 14px;
        }

        QLineEdit,
        QComboBox,
        QTableWidget,
        QListWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }

        QPushButton {
            background-color: #333333;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 5px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: #444444;
        }

        QPushButton:pressed {
            background-color: #555555;
        }

        QHeaderView::section {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #444444;
            padding: 6px;
        }

        QTableWidget {
            gridline-color: #444444;
            selection-background-color: #3a5f8a;
            selection-color: #ffffff;
        }

        QComboBox QAbstractItemView {
            background-color: #2b2b2b;
            color: #ffffff;
            selection-background-color: #3a5f8a;
        }

        QScrollBar:vertical {
            background: #252525;
            width: 12px;
        }

        QScrollBar::handle:vertical {
            background: #555555;
            border-radius: 5px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #666666;
        }
    """)

    queue_manager = QueueManager()
    favorites_manager = FavoritesManager()

    window = MainWindow(
        queue_manager,
        favorites_manager
    )

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()