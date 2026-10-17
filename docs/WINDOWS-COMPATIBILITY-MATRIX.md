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


## Flujo Windows confirmado dentro de Nexus Live — 2026-10-17

ISO Gate39064997881 aprobado (fuente791625cd119717fa5195a51477a70c00e6a90e65). Captura39066298801 aprobada; artefacto12113313508 descargado y revisado. SHA256 ISO: eb480efef282fa109f1f5eb35d609aa77656f8b0269bff7485c444d02b544520. El asistente empaquetado verifica el instalador oficial7-Zip26.04 x64, no crea prefijo antes de confirmar, instala mediante su botón y abre ventana7-Zip real. Marcadores NEXUS_WINDOWS_ISO_PREPARED/OPEN/PASS presentes. Ocho capturas1920x1080 pasan controles de cobertura; dos capturas clave guardadas en docs/evidence/2026-10-17/.

Alcance exacto: máquina QEMU/UEFI Live descartable, confirmación del botón programática, un paquete Windows; consulta MIME aprobada. No afirmar clic físico en Thunar, persistencia tras reinicio, compatibilidad general o certificación. La reapertura del asistente implementada en PR #25 se probó aparte en Debian/Wine y es posterior a esta ISO.

Avance: instalador común25→50 por componentes integrados y flujo parcial validado en ISO, junto con MIME y reapertura probados en laboratorio. Sigue sin APK/Linux, desinstalación o aceptación completa; no corresponde75%. Windows permanece50 por amplitud del módulo. Peso8 añade2 puntos:35.75→37.75≈38% global. Siguiente entrega funcional: acceso a la aplicación instalada desde el menú, manejo de desinstalación y ampliar matriz Windows; priorizar Android y Linux después de estabilizar este flujo.


## Segunda aplicación Windows: Notepad++ — 2026-10-17

Se añade laboratorio real para Notepad++8.9.8.1 x64, instalador de https://github.com/notepad-plus-plus/notepad-plus-plus/releases/tag/v8.9.8.1 con SHA25626f3bcced788fadbac4e7e577b430ea2ce6060cf3bcad993ef4612ecd7d743da (digest del asset oficial). Manual primario https://github.com/notepad-plus-plus/npp-usermanual/blob/master/content/docs/command-prompt.md: /S y /noUpdater documentados. El probe instala sin root en prefijo descartable, abre un archivo cuyo nombre tiene espacios, enfoca la ventana real, escribe con teclado y guarda; verifica bytes del archivo y conserva captura/logs. CI pendiente. No añadir Notepad++ al catálogo gráfico aprobado ni afirmar soporte dentro de ISO hasta validar e implementar su adaptador. Global≈38%, Windows50%.


### Notepad++ confirmado en laboratorio

PR #27 integrada170cfd9e2515cd388c50efa72b2782b5b56f2de1. Windows Lab39068787928 y Fast Checks39068790547 aprobados. Artefacto12114811229 descargado y revisado: Notepad++8.9.8.1 x64 instalado, archivo Nexus sample.txt abierto, texto escrito por teclado y guardado con Ctrl+S; contenido exacto verificado. Captura y muestra guardadas en docs/evidence/2026-10-17/notepad-edit-save.png y notepad-saved-sample.txt.

Primer intento39068603099 falló con syswow64/ntdll.dll ausentes: el laboratorio solo tenía Wine64. Se habilitó i386 y wine32:i386 junto a Wine64 según README Debian Wine10; se repitieron7-Zip/asistente/reapertura/menú/MIME y también aprobaron. La configuración mixta está probada en laboratorio, aún no en imagen. Manual primario: https://sources.debian.org/src/wine/10.0~repack-6/debian/README.debian .

Siguiente prioridad concreta: integrar segundo paquete en Nexus Install (identificación por hash y perfil separado) y preparar motor mixto automáticamente en próxima ISO, con prueba de ambos. No marcar Notepad++ como instalable desde asistente actual: solo7-Zip está integrado. No demuestra plugins, impresión, actualizaciones, hardware o persistencia. Global≈38%, Windows50%, instalador50%, APK0%.


## Catálogo gráfico de dos aplicaciones y siguiente ISO — 2026-10-17

Nexus Install reconoce por hash7-Zip26.04 x64 y Notepad++8.9.8.1 x64 sin confiar en el nombre del archivo. Elige perfil, binario, argumentos y entrada de menú propios; --application permite abrir el programa correcto. Registro local de instalación y nueva verificación del binario siguen activos. El selector bloquea Abrir mientras se identifica el paquete, y cancelar/cerrar el asistente limpia su temporizador Tk. Diez unit tests locales aprobados, incluidos perfiles separados, selección sin ejecución y acceso específico Notepad++.

Se amplía Wine GUI Lab para instalar Notepad++ desde el propio asistente y abrirlo desde su acceso sin alterar registro7-Zip. CI pendiente. Se prepara hook chroot030 para habilitar i386 y wine32:i386 al construir la ISO (sin comandos del usuario). Se amplía prueba Live a ambos programas y acciones de menú, con10 capturas y6GBRAM de laboratorio. Captura automática solo después de ISO Gate exitoso; ejecución manual exige id/SHA del candidato exacto para evitar intentar una imagen antigua.

Fuentes: manual Debian Live de hooks https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-contents.en y README Debian Wine10 https://sources.debian.org/src/wine/10.0~repack-6/debian/README.debian . Pendiente revisar GUI lab, integrar, construir una sola nueva ISO y revisar capturas/markers. ISO791625cd anterior solo acredita7-Zip y no incluye este catálogo ni runtime mixto. Global≈38%, Windows50%, instalador50%, APK0%; no elevar por código pendiente de validación.


### Integración gráfica de Notepad++ validada

PR #28 integrada4b3565acff56842f1f51f369125507b858379d47. Fast Checks39073201045 aprobó6jobs; Wine Lab39073199395 aprobó instalación gráfica, Abrir y acceso de menú para ambos programas, registro7-Zip sin cambios, MIME y edición/guardadoNotepad++. Artefacto12115259388 descargado, notepad-assistant-result.txt y captura nexus-notepad-install.png revisados. Sustituye CI pendiente de la nota anterior. Nueva ISO Gate39073455863 iniciada con runtime mixto y catálogo de ambos programas; aún pendiente construcción/captura Live. La ISO anterior no acredita estos cambios. Global≈38%.
