import json
import threading
from pathlib import Path

from downloader import download_video
from models import DownloadTask, DownloadStatus, CompressionMode
from compressor import compress_video


class QueueManager:
    def __init__(self, file_path="data/queue.json"):
        self.file_path = Path(file_path)
        self.tasks = []

        self.lock = threading.Lock()
        self.worker = None

        self.load()

    def add(self, task: DownloadTask):
        with self.lock:
            self.tasks.append(task)
            self.save_locked()

    def remove(self, task):
        with self.lock:
            self.tasks.remove(task)
            self.save_locked()

    def remove_finished(self):
        with self.lock:
            self.tasks = [
                task
                for task in self.tasks
                if task.status != DownloadStatus.FINISHED
            ]

            self.save_locked()

    def get_all(self):
        with self.lock:
            return list(self.tasks)

    def save_locked(self):
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = [
            task.to_dict()
            for task in self.tasks
        ]

        with open(
            self.file_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    def save(self):
        with self.lock:
            self.save_locked()

    def load(self):
        if not self.file_path.exists():
            return

        with open(
            self.file_path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        self.tasks = [
            DownloadTask.from_dict(item)
            for item in data
        ]

        # Falls das Programm während eines Downloads
        # beendet wurde:
        for task in self.tasks:
            if task.status in (
                    DownloadStatus.DOWNLOADING,
                    DownloadStatus.COMPRESSING
            ):
                task.status = DownloadStatus.INTERRUPTED

        self.save()

    def start(self, progress_callback=None):
        if self.worker and self.worker.is_alive():
            print("Warteschlange läuft bereits.")
            return

        self.worker = threading.Thread(
            target=self.run,
            args=(progress_callback,),
            daemon=True
        )

        self.worker.start()

    def run(self, progress_callback=None):
        while True:
            with self.lock:
                task = next(
                    (
                        task
                        for task in self.tasks
                        if task.status == DownloadStatus.WAITING
                    ),
                    None
                )

                if task is None:
                    break

                task.status = DownloadStatus.DOWNLOADING
                task.progress = 0.0
                task.error_message = None

                self.save_locked()

            def update_progress(percent):
                with self.lock:
                    task.download_progress = percent

                if progress_callback:
                    progress_callback(task)

            result = download_video(
                url=task.url,
                output_file=task.output_file,
                progress_callback=update_progress
            )

            if result.success:

                if task.compression != CompressionMode.NONE:

                    # Nur Status ändern -> kurz locken
                    with self.lock:
                        task.status = DownloadStatus.COMPRESSING
                        task.download_progress = 100.0
                        task.compression_progress = 0.0

                        self.save_locked()

                    if progress_callback:
                        progress_callback(task)

                    def update_compression_progress(percent):
                        with self.lock:
                            task.compression_progress = percent

                        if progress_callback:
                            progress_callback(task)

                    # WICHTIG:
                    # compress_video AUSSERHALB des Locks!
                    success, _, error = compress_video(
                        input_file=task.output_file,
                        mode=task.compression,
                        duration=result.duration,
                        progress_callback=update_compression_progress
                    )

                    # Erst danach wieder kurz locken
                    with self.lock:
                        task.status = DownloadStatus.FINISHED
                        task.download_progress = 100.0

                        if task.compression != CompressionMode.NONE:
                            task.compression_progress = 100.0

                        self.save_locked()

                else:
                    with self.lock:
                        task.status = DownloadStatus.FINISHED
                        task.progress = 100.0
                        self.save_locked()

            else:
                with self.lock:
                    task.status = DownloadStatus.FAILED
                    task.error_message = result.error_message
                    self.save_locked()

            if progress_callback:
                progress_callback(task)