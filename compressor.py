import subprocess
from pathlib import Path

from models import CompressionMode
from utils import time_to_seconds


def compress_video(
    input_file,
    mode,
    duration,
    progress_callback=None
):
    input_file = Path(input_file)

    if mode == CompressionMode.NONE:
        return True, input_file, None

    temp_file = input_file.with_name(
        input_file.stem + "_compressed.mp4"
    )

    if mode == CompressionMode.H264:
        codec_options = [
            "-c:v", "libopenh264",
            "-b:v", "4M",
            "-c:a", "aac",
            "-b:a", "128k"
        ]

    elif mode == CompressionMode.H265:
        codec_options = [
            "-c:v", "libx265",
            "-preset", "medium",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k"
        ]

    elif mode == CompressionMode.AV1:
        codec_options = [
            "-c:v", "libsvtav1",
            "-preset", "8",
            "-crf", "32",
            "-c:a", "libopus",
            "-b:a", "96k"
        ]

    else:
        return False, input_file, "Unbekannter Komprimierungsmodus"

    command = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-i", str(input_file),
        *codec_options,
        "-progress", "pipe:1",
        "-stats_period", "0.5",
        "-nostats",
        str(temp_file)
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        text=True
    )

    for line in process.stdout:
        line = line.strip()

        if line.startswith("out_time_us="):
            value = line.split("=", 1)[1]

            try:
                current_seconds = int(value) / 1_000_000

                percent = min(
                    current_seconds / duration * 100,
                    100
                )

                if progress_callback is not None:
                    progress_callback(percent)
                else:
                    print("KEIN callback vorhanden")

            except ValueError as error:
                print("ValueError:", error)

    _, stderr = process.communicate()

    if process.returncode != 0:
        return False, input_file, stderr

    input_file.unlink()
    temp_file.rename(input_file)

    if progress_callback:
        progress_callback(100)

    return True, input_file, None