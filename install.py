#!/usr/bin/env python3

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"


def run(command, check=True):
    print("\n>", " ".join(map(str, command)))
    return subprocess.run(command, check=check)


def command_exists(command):
    return shutil.which(command) is not None


def get_venv_python():
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def create_venv():
    python = get_venv_python()

    if python.exists():
        print("[OK] Virtuelle Umgebung existiert bereits.")
        return python

    print("[INFO] Virtuelle Python-Umgebung wird erstellt...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])

    if not python.exists():
        raise RuntimeError("Die virtuelle Umgebung konnte nicht erstellt werden.")

    print("[OK] Virtuelle Umgebung erstellt.")
    return python


def install_python_dependencies(python):
    print("[INFO] pip wird aktualisiert...")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])

    requirements = PROJECT_DIR / "requirements.txt"

    if requirements.exists():
        print("[INFO] requirements.txt gefunden.")
        run([
            str(python),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements)
        ])
    else:
        print("[INFO] Keine requirements.txt gefunden.")
        print("[INFO] PySide6 wird installiert...")
        run([
            str(python),
            "-m",
            "pip",
            "install",
            "PySide6"
        ])

    print("[OK] Python-Abhängigkeiten installiert.")


def read_linux_id():
    os_release = Path("/etc/os-release")

    if not os_release.exists():
        return ""

    values = {}

    for line in os_release.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')

    return values.get("ID", "").lower()


def install_ffmpeg_windows():
    if not command_exists("winget"):
        raise RuntimeError(
            "FFmpeg fehlt und winget wurde nicht gefunden.\n"
            "Bitte installiere FFmpeg manuell und füge es zum PATH hinzu."
        )

    print("[INFO] FFmpeg wird mit winget installiert...")
    run([
        "winget",
        "install",
        "-e",
        "--id",
        "Gyan.FFmpeg",
        "--accept-package-agreements",
        "--accept-source-agreements"
    ])


def install_ffmpeg_macos():
    if not command_exists("brew"):
        raise RuntimeError(
            "FFmpeg fehlt und Homebrew wurde nicht gefunden.\n"
            "Installiere zuerst Homebrew von https://brew.sh/ "
            "oder installiere FFmpeg manuell."
        )

    print("[INFO] FFmpeg wird mit Homebrew installiert...")
    run(["brew", "install", "ffmpeg"])


def install_ffmpeg_linux():
    distro = read_linux_id()

    if distro == "fedora":
        print("[INFO] Fedora erkannt.")
        print("[INFO] FFmpeg wird mit dnf installiert...")
        run(["sudo", "dnf", "install", "-y", "ffmpeg"])

    elif distro in {
        "ubuntu",
        "debian",
        "linuxmint",
        "pop"
    }:
        print("[INFO] Debian/Ubuntu-basiertes Linux erkannt.")
        run(["sudo", "apt", "update"])
        run(["sudo", "apt", "install", "-y", "ffmpeg"])

    elif distro in {
        "arch",
        "manjaro",
        "endeavouros"
    }:
        print("[INFO] Arch-basiertes Linux erkannt.")
        run(["sudo", "pacman", "-S", "--needed", "--noconfirm", "ffmpeg"])

    elif distro in {
        "opensuse-tumbleweed",
        "opensuse-leap",
        "suse"
    }:
        print("[INFO] openSUSE erkannt.")
        run(["sudo", "zypper", "--non-interactive", "install", "ffmpeg"])

    else:
        raise RuntimeError(
            f"Linux-Distribution '{distro or 'unbekannt'}' wird für die "
            "automatische FFmpeg-Installation noch nicht unterstützt.\n"
            "Bitte FFmpeg über den Paketmanager deines Systems installieren."
        )


def install_ffmpeg():
    if command_exists("ffmpeg") and command_exists("ffprobe"):
        print("[OK] FFmpeg und FFprobe wurden gefunden.")
        return

    print("[INFO] FFmpeg oder FFprobe fehlt.")

    system = platform.system()

    if system == "Windows":
        install_ffmpeg_windows()
    elif system == "Darwin":
        install_ffmpeg_macos()
    elif system == "Linux":
        install_ffmpeg_linux()
    else:
        raise RuntimeError(
            f"Nicht unterstütztes Betriebssystem: {system}"
        )

    print()
    print("[INFO] FFmpeg-Installation wurde ausgeführt.")

    if not command_exists("ffmpeg"):
        print(
            "[HINWEIS] FFmpeg ist in dieser Sitzung noch nicht im PATH.\n"
            "          Öffne ggf. ein neues Terminal und starte install.py erneut."
        )


def show_start_command(python):
    main_file = PROJECT_DIR / "main.py"

    if not main_file.exists():
        print("[WARNUNG] main.py wurde nicht gefunden.")
        return

    print()
    print("m3u8Downloader kannst du starten mit:")
    print()
    print(f'    "{python}" "{main_file}"')


def main():
    print("=" * 48)
    print("          m3u8Downloader - Installation")
    print("=" * 48)
    print()
    print(f"Betriebssystem: {platform.system()} {platform.release()}")
    print(f"Python:         {platform.python_version()}")
    print(f"Projektordner:  {PROJECT_DIR}")

    try:
        python = create_venv()
        install_python_dependencies(python)
        install_ffmpeg()

        print()
        print("=" * 48)
        print("       Installation abgeschlossen")
        print("=" * 48)

        show_start_command(python)

    except subprocess.CalledProcessError as error:
        print()
        print(
            f"[FEHLER] Ein Installationsbefehl ist fehlgeschlagen "
            f"(Code {error.returncode})."
        )
        sys.exit(error.returncode or 1)

    except Exception as error:
        print()
        print(f"[FEHLER] {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
