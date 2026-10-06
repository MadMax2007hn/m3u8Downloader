from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QAbstractItemView,
    QDialog,
    QListWidget,
    QInputDialog
)
from PySide6.QtGui import QColor, QBrush

from models import DownloadTask, CompressionMode, DownloadStatus

class MainWindow(QMainWindow):
    def __init__(self, queue_manager, favorites_manager):
        super().__init__()

        self.queue_manager = queue_manager
        self.favorites_manager = favorites_manager

        self.setWindowTitle("TUMDownload")
        self.resize(900, 600)

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_queue)
        self.timer.start(500)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("M3U8-URL")

        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Dateiname")

        layout.addWidget(QLabel("M3U8-URL"))
        layout.addWidget(self.url_input)

        layout.addWidget(QLabel("Dateiname"))
        layout.addWidget(self.filename_input)

        folder_layout = QHBoxLayout()

        self.folder_combo = QComboBox()
        self.load_favorites()

        browse_button = QPushButton("Ordner wählen")
        browse_button.clicked.connect(self.choose_folder)

        favorites_button = QPushButton("Favoriten verwalten")
        favorites_button.clicked.connect(self.manage_favorites)

        folder_layout.addWidget(self.folder_combo)
        folder_layout.addWidget(browse_button)
        folder_layout.addWidget(favorites_button)

        layout.addWidget(QLabel("Speicherort"))
        layout.addLayout(folder_layout)

        favorites_button = QPushButton(
            "Favoriten verwalten"
        )

        favorites_button.clicked.connect(
            self.manage_favorites
        )

        self.compression_combo = QComboBox()

        self.compression_combo.addItem(
            "Keine",
            CompressionMode.NONE
        )

        self.compression_combo.addItem(
            "H.264",
            CompressionMode.H264
        )

        self.compression_combo.addItem(
            "H.265",
            CompressionMode.H265
        )

        self.compression_combo.addItem(
            "AV1",
            CompressionMode.AV1
        )

        layout.addWidget(QLabel("Komprimierung"))
        layout.addWidget(self.compression_combo)

        add_button = QPushButton("Zur Warteschlange hinzufügen")
        add_button.clicked.connect(self.add_download)

        layout.addWidget(add_button)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setHorizontalHeaderLabels([
            "Dateiname",
            "Status",
            "Download",
            "Komprimierung",
            "Speicherort"
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        layout.addWidget(self.table)

        queue_buttons = QHBoxLayout()

        remove_button = QPushButton(
            "Ausgewählten entfernen"
        )

        remove_button.clicked.connect(
            self.remove_selected
        )

        remove_finished_button = QPushButton(
            "Alle fertigen entfernen"
        )

        remove_finished_button.clicked.connect(
            self.remove_finished
        )

        queue_buttons.addWidget(remove_button)
        queue_buttons.addWidget(remove_finished_button)

        layout.addLayout(queue_buttons)

        start_button = QPushButton("Warteschlange starten")
        start_button.clicked.connect(self.start_queue)

        layout.addWidget(start_button)

    def load_favorites(self):
        self.folder_combo.clear()

        for name, path in self.favorites_manager.get_all().items():
            self.folder_combo.addItem(
                f"{name} — {path}",
                path
            )

    def remove_selected(self):
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Keine Auswahl",
                "Bitte zuerst einen Download auswählen."
            )
            return

        tasks = self.queue_manager.get_all()

        if row >= len(tasks):
            return

        task = tasks[row]

        if task.status in (
                DownloadStatus.DOWNLOADING,
                DownloadStatus.COMPRESSING
        ):
            QMessageBox.warning(
                self,
                "Download läuft",
                "Ein laufender Download kann derzeit "
                "nicht entfernt werden."
            )
            return

        self.queue_manager.remove(task)

        self.refresh_queue()

    def remove_finished(self):
        self.queue_manager.remove_finished()
        self.refresh_queue()

    def manage_favorites(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(
            "Speicherort-Favoriten"
        )

        dialog.resize(600, 350)

        layout = QVBoxLayout(dialog)

        favorite_list = QListWidget()

        layout.addWidget(favorite_list)

        def refresh_list():
            favorite_list.clear()

            for name, path in (
                    self.favorites_manager
                            .get_all()
                            .items()
            ):
                favorite_list.addItem(
                    f"{name} — {path}"
                )

        refresh_list()

        buttons = QHBoxLayout()

        add_button = QPushButton(
            "Favorit hinzufügen"
        )

        remove_button = QPushButton(
            "Favorit entfernen"
        )

        close_button = QPushButton(
            "Schließen"
        )

        buttons.addWidget(add_button)
        buttons.addWidget(remove_button)
        buttons.addStretch()
        buttons.addWidget(close_button)

        layout.addLayout(buttons)

        def add_favorite():
            name, ok = QInputDialog.getText(
                dialog,
                "Favorit",
                "Name:"
            )

            if not ok or not name.strip():
                return

            folder = QFileDialog.getExistingDirectory(
                dialog,
                "Ordner auswählen"
            )

            if not folder:
                return

            self.favorites_manager.add(
                name.strip(),
                folder
            )

            refresh_list()
            self.load_favorites()

        def remove_favorite():
            row = favorite_list.currentRow()

            if row < 0:
                return

            names = list(
                self.favorites_manager
                .get_all()
                .keys()
            )

            if row >= len(names):
                return

            self.favorites_manager.remove(
                names[row]
            )

            refresh_list()
            self.load_favorites()

        add_button.clicked.connect(
            add_favorite
        )

        remove_button.clicked.connect(
            remove_favorite
        )

        close_button.clicked.connect(
            dialog.accept
        )

        dialog.exec()

    def get_status_color(self, status):
        colors = {
            DownloadStatus.WAITING: QColor("#b0b0b0"),
            DownloadStatus.DOWNLOADING: QColor("#2980b9"),
            DownloadStatus.COMPRESSING: QColor("#d68910"),
            DownloadStatus.FINISHED: QColor("#239b56"),
            DownloadStatus.FAILED: QColor("#c0392b"),
            DownloadStatus.INTERRUPTED: QColor("#8e44ad")
        }

        return colors.get(
            status,
            QColor("#808080")
        )

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Speicherordner auswählen"
        )

        if folder:
            self.folder_combo.addItem(
                folder,
                folder
            )

            self.folder_combo.setCurrentIndex(
                self.folder_combo.count() - 1
            )

    def add_download(self):
        url = self.url_input.text().strip()
        filename = self.filename_input.text().strip()

        if not url:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte eine M3U8-URL eingeben."
            )
            return

        if not filename:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte einen Dateinamen eingeben."
            )
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        if not filename.lower().endswith(".mp4"):
            filename += ".mp4"

        folder_data = self.folder_combo.currentData()

        if not folder_data:
            QMessageBox.warning(
                self,
                "Kein Speicherort",
                "Bitte einen Speicherort auswählen."
            )
            return

        output_folder = Path(folder_data)

        compression = self.compression_combo.currentData()

        task = DownloadTask(
            url=url,
            filename=filename,
            output_folder=output_folder,
            compression=compression
        )

        self.queue_manager.add(task)

        self.url_input.clear()
        self.filename_input.clear()

        self.refresh_queue()

    def start_queue(self):
        self.queue_manager.start()

    def refresh_queue(self):
        tasks = self.queue_manager.get_all()

        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # Dateiname
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(task.filename)
            )

            # Status
            status_item = QTableWidgetItem(
                task.status.value
            )

            status_item.setForeground(
                QBrush(
                    self.get_status_color(task.status)
                )
            )

            self.table.setItem(
                row,
                1,
                status_item
            )

            # Download-Fortschritt
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    f"{task.download_progress:.1f}%"
                )
            )

            # Komprimierungs-Fortschritt
            if task.compression == CompressionMode.NONE:
                compression_text = "—"
            else:
                compression_text = (
                    f"{task.compression_progress:.1f}%"
                )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(compression_text)
            )

            # Speicherort
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(
                    str(task.output_folder)
                )
            )