from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class DownloadStatus(Enum):
    WAITING = "Wartend"
    DOWNLOADING = "Lädt"
    COMPRESSING = "Wird komprimiert"
    FINISHED = "Fertig"
    FAILED = "Fehler"
    INTERRUPTED = "Unterbrochen"


class CompressionMode(Enum):
    NONE = "Keine"
    H264 = "H.264"
    H265 = "H.265"
    AV1 = "AV1"


@dataclass
class DownloadTask:
    url: str
    filename: str
    output_folder: Path

    compression: CompressionMode = CompressionMode.NONE

    status: DownloadStatus = DownloadStatus.WAITING

    download_progress: float = 0.0
    compression_progress: float = 0.0

    error_message: str | None = None

    @property
    def output_file(self):
        return self.output_folder / self.filename

    def to_dict(self):
        return {
            "url": self.url,
            "filename": self.filename,
            "output_folder": str(self.output_folder),
            "compression": self.compression.name,
            "status": self.status.name,
            "download_progress": self.download_progress,
            "compression_progress": self.compression_progress,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data):
        # Kompatibel mit deiner alten queue.json
        old_progress = data.get("progress", 0.0)

        return cls(
            url=data["url"],
            filename=data["filename"],
            output_folder=Path(data["output_folder"]),
            compression=CompressionMode[
                data.get("compression", "NONE")
            ],
            status=DownloadStatus[data["status"]],
            download_progress=data.get(
                "download_progress",
                old_progress
            ),
            compression_progress=data.get(
                "compression_progress",
                0.0
            ),
            error_message=data.get("error_message")
        )


@dataclass
class DownloadResult:
    success: bool
    output_file: Path
    duration: float
    return_code: int
    error_message: str | None = None