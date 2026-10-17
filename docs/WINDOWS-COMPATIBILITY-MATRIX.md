# Matriz de compatibilidad Windows

Actualizado: 2026-10-17. Cada fila es una aplicación/versión/entorno, no garantía general.

| Aplicación | Entorno | Instalación | Tarea útil | GUI | Persistencia OS | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| 7-Zip 26.04 Windows x64 | Debian Trixie, Wine 10.0~repack-6, Xvfb, usuario sin privilegios | EXE oficial /S, hash verificado | ZIP creado por 7z.exe Windows; contenido exacto verificado con Python zipfile; comprobado otra vez tras reiniciar Wine | 7zFM.exe abrió ventana y se inspeccionó captura; compresión no operada mediante clics | No probada; reiniciar Wine no es reiniciar Nexus | Aprobado en laboratorio, pendiente integración Nexus |

## Evidencia reproducible

- Workflow: https://github.com/CmdOS-system/Nexus-os/actions/runs/39052936193 ; success para 3ce90a2bd472e35a17212d86f9f433b09ed20c76.
- Fast Checks 39052939320: success en el mismo SHA.
- Artefacto 12107549425, nexus-windows-7zip-evidence: descargado y revisado result.txt, runtime.txt, archive-reopen.log y 7zip-windows-gui.png.
- Instalador: https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe ; enlace del sitio oficial 7-zip.org. SHA256 d54bf805f9f3704d1e8db2fa3498ae7ef2df0312b40b558e7c71c734430a665d, digest upstream verificado.
- Log tras reinicio de Wine: Everything is Ok, ZIP 216 bytes y contenido de 50 bytes verificado. No es benchmark.
- Script: agent/tests/windows_7zip_lab.sh; workflow .github/workflows/nexus-wine-lab.yml. Instalación sin interacción solo en laboratorio controlado, no equivalente al flujo gráfico del usuario.

## Siguientes criterios

1. Adaptador/asistente Nexus para abrir el instalador desde Descargas sin terminal, con origen/permisos, progreso y errores claros.
2. Instalar y abrir desde Horizon con perfil aislado; tarea útil y desinstalación.
3. Repetir dentro del Nexus instalado, reiniciando sin ISO y verificando documentos/perfil.
4. Añadir aplicación importante/difícil del usuario y caso representativo. No generalizar desde 7-Zip a Office, apps empresariales, drivers o juegos.

Windows pasa a 50 % estimado de implementación parcial/laboratorio; no significa que la mitad de las apps Windows sean compatibles. Android/APK y el instalador común siguen sin validación.
