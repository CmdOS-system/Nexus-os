"""Identify common application packages and suggest a Nexus compatibility route.

This module only reads bounded metadata. It never extracts, installs, downloads,
or executes the selected file. An identified format is not a compatibility claim.
"""
from __future__ import annotations

import configparser
import os
from pathlib import Path
import stat
import zipfile

MAX_METADATA = 2 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 50_000


def _result(kind, platform, adapter, status, reason, architecture="unknown"):
    return {
        "format": kind,
        "platform": platform,
        "adapter": adapter,
        "status": status,
        "architecture": architecture,
        "reason": reason,
        "executed": False,
    }


def _deb_archive(path: Path) -> bool:
    """Check ar member headers without extracting data or running maintainer scripts."""
    with path.open("rb") as stream:
        if stream.read(8) != b"!<arch>\n":
            return False
        names = set()
        while header := stream.read(60):
            if len(header) != 60 or header[58:60] != b"`\n":
                return False
            raw_name = header[:16].decode("ascii", "replace").strip().rstrip("/")
            try:
                size = int(header[48:58].decode("ascii").strip())
            except ValueError:
                return False
            if size < 0:
                return False
            names.add(raw_name)
            stream.seek(size + (size & 1), os.SEEK_CUR)
        return "debian-binary" in names and any(n.startswith("control.tar") for n in names) and any(n.startswith("data.tar") for n in names)


def _apk(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as package:
            infos = package.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                return False
            names = {item.filename for item in infos}
            return "AndroidManifest.xml" in names and any(
                name.startswith(("classes", "lib/", "resources.arsc")) for name in names
            )
    except (OSError, zipfile.BadZipFile, NotImplementedError):
        return False


def _pe_architecture(path: Path) -> str:
    with path.open("rb") as stream:
        stream.seek(0x3C)
        offset_bytes = stream.read(4)
        if len(offset_bytes) != 4:
            return "unknown"
        offset = int.from_bytes(offset_bytes, "little")
        if offset > 1024 * 1024:
            return "unknown"
        stream.seek(offset)
        if stream.read(4) != b"PE\0\0":
            return "unknown"
        machine = int.from_bytes(stream.read(2), "little")
    return {0x014C: "x86", 0x8664: "x86_64", 0xAA64: "arm64"}.get(machine, "unknown")


def inspect_package(path) -> dict:
    """Return a safe, evidence-based route recommendation for one local package."""
    source = Path(path)
    try:
        info = source.lstat()
    except OSError as error:
        return _result("unknown", "unknown", "none", "unavailable", f"No se puede leer el archivo: {error.strerror or 'error de acceso'}.")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return _result("unknown", "unknown", "none", "rejected", "Selecciona un archivo normal; no se siguen enlaces ni carpetas en esta versión.")
    if info.st_size <= 0:
        return _result("unknown", "unknown", "none", "rejected", "El archivo está vacío.")
    suffix = source.suffix.lower()
    try:
        with source.open("rb") as stream:
            head = stream.read(MAX_METADATA)
            if info.st_size > 512:
                stream.seek(-512, os.SEEK_END)
                tail = stream.read(512)
            else:
                tail = head
    except OSError as error:
        return _result("unknown", "unknown", "none", "unavailable", f"No se pudo inspeccionar el contenido: {error.strerror or 'error de lectura'}.")

    if head.startswith(b"!<arch>\n") and suffix == ".deb":
        if _deb_archive(source):
            return _result("deb", "linux", "nexus-native-package-manager", "recognized", "Paquete Debian reconocido. Debe revisarse origen, arquitectura y scripts antes de autorizar la instalación.")
        return _result("unknown", "linux", "none", "rejected", "La cabecera ar existe, pero faltan miembros requeridos de un paquete Debian.")

    if suffix == ".flatpakref":
        try:
            text = head.decode("utf-8-sig")
            parser = configparser.ConfigParser(interpolation=None)
            parser.read_string(text)
            if "Flatpak Ref" in parser and parser["Flatpak Ref"].get("Name"):
                return _result("flatpakref", "linux", "flatpak-user", "recognized", "Referencia Flatpak válida a nivel básico. Nexus debe mostrar el repositorio remoto y sus permisos antes de confirmar; no se contactó al servidor.")
        except (UnicodeDecodeError, configparser.Error):
            pass
        return _result("unknown", "linux", "none", "rejected", "El archivo no tiene una sección Flatpak Ref válida o excede la lectura segura.")

    if head.startswith(b"MZ"):
        arch = _pe_architecture(source)
        label = "Windows PE" if arch != "unknown" else "archivo DOS/PE sin cabecera PE verificable"
        return _result("windows-pe", "windows", "wine-or-windows-vm", "recognized" if arch != "unknown" else "unverified", f"{label}. Se requiere receta y prueba por aplicación; algunos programas requieren servicios de Windows o drivers.", arch)

    if head.startswith(bytes.fromhex("d0cf11e0a1b11ae1")) and suffix == ".msi":
        return _result("windows-msi", "windows", "wine-or-windows-vm", "recognized", "Contenedor MSI reconocido. Falta validar instalación, dependencias y uso de la aplicación.")

    if head.startswith(b"Cr24"):
        version = int.from_bytes(head[4:8], "little") if len(head) >= 8 else 0
        return _result("chrome-extension", "chrome", "chromium-extension-manager", "recognized", f"Extensión Chromium CRX versión {version}; se instala en un navegador compatible, no como aplicación ChromeOS completa.")

    if head.startswith(b"\x7fELF"):
        machine = int.from_bytes(head[18:20], "little") if len(head) >= 20 else 0
        arch = {3: "x86", 62: "x86_64", 40: "arm", 183: "arm64"}.get(machine, "unknown")
        if suffix == ".appimage":
            return _result("appimage-candidate", "linux", "appimage-runtime", "candidate", "ELF Linux executable con sufijo AppImage. La estructura de imagen y dependencias aún deben validarse antes de abrir.", arch)
        return _result("linux-elf", "linux", "native-loader", "recognized", "Ejecutable ELF Linux. La arquitectura coincide o debe compararse con este equipo; dependencias y origen pendientes.", arch)

    if head.startswith(b"PK\x03\x04") and suffix == ".apk":
        if _apk(source):
            return _result("android-apk", "android", "waydroid", "recognized", "Paquete APK reconocido por su manifiesto y contenido ZIP. Requiere Waydroid listo, arquitectura compatible y prueba real por aplicación.")
        return _result("unknown", "android", "none", "rejected", "Es un ZIP, pero no se pudo confirmar que contenga estructura de aplicación Android.")

    if head.startswith(b"xar!") and suffix == ".pkg":
        return _result("macos-pkg", "macos", "darling-or-macos-vm", "candidate", "Paquete XAR de macOS. No se ejecuta en Nexus; compatibilidad Darling es experimental y VM depende del equipo y licencia.")

    if tail[-4:] == b"koly" and suffix == ".dmg":
        return _result("macos-dmg", "macos", "darling-or-macos-vm", "candidate", "Imagen de disco Apple reconocida. No se instala directamente en Linux; buscar versión Linux/web o probar ruta autorizada por aplicación.")

    if suffix in {".deb", ".apk", ".exe", ".msi", ".dmg", ".pkg", ".crx", ".appimage", ".flatpakref"}:
        return _result("unknown", "unknown", "none", "rejected", "La extensión no coincide con una estructura reconocida; Nexus no debe ejecutar el archivo por su nombre.")
    return _result("unknown", "unknown", "none", "unsupported", "Formato no reconocido todavía. Mantén el archivo sin ejecutar y consulta el catálogo de compatibilidad.")
