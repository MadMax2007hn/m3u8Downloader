import subprocess
from pathlib import Path

from models import DownloadResult
from utils import time_to_seconds


def get_duration(url):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            url
        ],
        capture_output=True,
        text=True,
        check=True
    )

    return float(result.stdout.strip())


def download_video(
    url,
    output_file,
    progress_callback=None
):
    output_file = Path(output_file)

    try:
        duration = get_duration(url)

        command = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", url,
            "-c", "copy",
            "-progress", "pipe:1",
            "-nostats",
            str(output_file)
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            line = line.strip()

            if line.startswith("out_time="):
                current_time = line.split("=", 1)[1]

                current_seconds = time_to_seconds(
                    current_time
                )

                percent = min(
                    current_seconds / duration * 100,
                    100
                )

                if progress_callback:
                    progress_callback(percent)

        process.wait()

        if process.returncode == 0:
            if progress_callback:
                progress_callback(100)

            return DownloadResult(
                success=True,
                output_file=output_file,
                duration=duration,
                return_code=process.returncode
            )

        return DownloadResult(
            success=False,
            output_file=output_file,
            duration=duration,
            return_code=process.returncode,
            error_message=stderr
        )

    except Exception as error:
        return DownloadResult(
            success=False,
            output_file=output_file,
            duration=0,
            return_code=-1,
            error_message=str(error)
        )