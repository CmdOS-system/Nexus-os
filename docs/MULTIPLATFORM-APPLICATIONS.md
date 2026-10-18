# Nexus: aplicaciones Linux, Windows, Android, macOS y ChromeOS
Fecha: 2026-10-17 (America/Bogota).

## Requisito central
Nexus debe ofrecer una experiencia sencilla para aplicaciones Linux, Windows y Android/APK; y una ruta de compatibilidad claramente delimitada para macOS y ChromeOS. El usuario debe poder abrir un paquete desde el explorador, revisar nombre/origen/permisos, instalar gráficamente y abrirlo desde el menú cuando el formato y el adaptador lo permitan. La compatibilidad se declara por aplicación, versión, arquitectura y equipo probado; reconocer una extensión no demuestra que funcione.

## Estado comprobado
- Global estimado: 38%, conforme a PROJECT-PROGRESS.md. Este documento no cambia la puntuación.
- Windows: 50% en la escala del proyecto. Dos paquetes aprobados en agent/app_installer.py: 7-Zip y Notepad++. La ISO Live ya probó su flujo. Word sigue 0/7; Click-to-Run falla al iniciar servicio (1053).
- Linux: el escritorio usa aplicaciones Linux, pero el instalador unificado de paquetes descargados sigue 0%. No confundir aplicación preinstalada con instalación gráfica validada.
- APK: 0%. No hay ejecución Android validada.
- KVM: motor ejecutado en laboratorio; no hay Windows instalado ni Word aprobado por esa vía.

## Arquitectura de implementación
Nexus Install será la interfaz común. Cada adaptador conservará su propio ciclo de vida, recibo, registros, permisos y errores; no se enviarán todos los formatos a Wine.
| Familia | Adaptador previsto | Primera entrega verificable |
| --- | --- | --- |
| Linux Flatpak | Flatpak por usuario y repositorio explícito | Instalar una app oficial, abrirla, crear/guardar archivo, reiniciar y desinstalar gráficamente |
| Linux .deb | Gestor nativo con resolución de dependencias y autorización gráfica para cambios del sistema | Paquete oficial compatible con la base Debian, dependencias resueltas, menú y retirada comprobados |
| Linux AppImage | Integración por usuario tras validar formato, arquitectura y procedencia | Copia administrada, permisos, acceso al menú, ejecución real y retirada; comprobar FUSE o alternativa soportada |
| Windows .exe/.msi | Wine con perfil y receta por aplicación; alternativa VM explícita | Mantener pruebas de paquetes aprobados; completar Word según OFFICE-DESKTOP-ACCEPTANCE.md |
| Android .apk | Waydroid, sujeto al diagnóstico del host | APK de prueba con fuente y licencia conocidas: instalar, abrir, guardar estado, reiniciar y desinstalar |
| macOS .app/.dmg | No ejecutar directamente en Linux; priorizar versiones web o multiplataforma. Investigar VM macOS solo en hardware y licencia permitidos | Matriz de apps seleccionadas; separar acceso web, build nativo y virtualización. No declarar .dmg compatible sin ejecución autorizada |
| ChromeOS | PWA/web; paquetes Linux mediante entorno Linux soportado; Android según modelo/disponibilidad | Nexus como sistema y Nexus dentro del entorno Linux de ChromeOS son pruebas distintas. Validar Chromebook/modelo, gráficos, archivos y persistencia |

Flatpak es el primer adaptador Linux propuesto por su integración gráfica y ámbito de usuario. No añadir automáticamente repositorios desconocidos desde un .flatpakref: mostrar origen y permisos antes de instalar. Un .deb puede ejecutar scripts con privilegios; su instalación pertenece al gestor del sistema, con autorización gráfica, no a un ejecutable arbitrario lanzado como administrador.

Para APK: comprobar compositor Wayland, soporte binder y ashmem o memfd, GPU, arquitectura CPU y servicios del contenedor. El escritorio Live actual basado en X11 no es por sí mismo prueba suficiente. Comparar sesión Wayland nativa frente a compositor anidado en un laboratorio antes de cambiar Horizon. No prometer compatibilidad de APK ARM en x86, Google Play, DRM, banca o juegos con antitrampas sin pruebas individuales. La mera presencia del ejecutable waydroid no significa que el contenedor esté listo.

### macOS
Una app macOS compilada para Darwin no se convierte en aplicación Linux al reconocer `.app` o `.dmg`; las APIs, el formato ejecutable y la firma/notarización son propios de Apple. Para la experiencia de Nexus, primero favorecer aplicaciones web o ediciones Linux del mismo proveedor. Una VM macOS es una vía de laboratorio condicionada por hardware Apple compatible y los términos de licencia vigentes; no crear un acceso que instale macOS en hardware no autorizado ni extraer componentes propietarios. Registrar por separado cada aplicación, chip/arquitectura y método probado.

### ChromeOS
Diferenciar (1) instalar Nexus como sistema operativo en equipo compatible y probar arranque/driver, de (2) ejecutar aplicaciones Linux dentro del entorno Linux de un Chromebook ChromeOS. ChromeOS tiene un entorno Linux aislado cuya disponibilidad puede depender del dispositivo y de políticas escolares/empresariales; integración USB/periféricos y GPU requieren pruebas. En algunos Chromebook también existe soporte Android, pero eso depende del dispositivo. Una app `.deb`/Flatpak para Nexus no se convierte en paquete ChromeOS ni demuestra que arranque como sistema operativo ChromeOS.

## Contrato común antes de ejecutar
1. Identificar el contenido y la arquitectura; extensión y nombre sirven de pista, no de validación.
2. Preparar una copia privada y verificar los mismos bytes que finalmente se ejecutarán.
3. Mostrar aplicación, motor, origen, tamaño, permisos y limitaciones conocidas. Un motor ausente se presenta como preparación pendiente, nunca como instalación exitosa.
4. Ejecutar el adaptador sin bloquear la interfaz, con límite de tiempo y registro de la etapa que falla.
5. Registrar éxito solo después de verificar la instalación y el inicio real. Mantener estados separados: reconocido, preparado, instalado, abierto y aceptado.
6. Crear entrada de menú coherente y asociar archivos cuando corresponda.
7. Conservar datos del usuario al actualizar o retirar; explicar cualquier retirada de perfil/datos.

## Orden de trabajo y cierre
1. Windows: analizar el diagnóstico del servicio ClickToRunSvc de PR32 y continuar Word; no repetir sin hipótesis o nuevos registros.
2. Linux: laboratorio Flatpak por usuario con una aplicación oficial. Después integrar adaptador y ventana, asociación por doble clic y prueba dentro de Nexus.
3. Android: diagnóstico del host y decisión Wayland/binder/GPU; después APK de prueba real antes de ofrecer instalación al usuario.
4. Integración: una sola lista de aplicaciones con plataforma, versión, motor, estado, abrir y desinstalar.
5. Validar todas las plataformas sobre Nexus instalado en disco y tras reinicio sin ISO. Añadir pruebas de cancelación, falta de red/espacio, arquitectura incompatible y recuperación.

Cada plataforma requiere evidencia de instalación, apertura, tarea útil, persistencia tras reinicio, integración gráfica y desinstalación. El fallo de un adaptador no debe modificar ni eliminar los perfiles de otro. Ninguna compatibilidad universal queda demostrada por pasar este plan.

## Fuentes primarias consultadas
- https://docs.flatpak.org/en/latest/using-flatpak.html
- https://docs.flatpak.org/en/latest/repositories.html
- https://docs.waydro.id/usage/install-on-desktops
- https://docs.waydro.id/debugging/getting-essential-information
- https://support.google.com/chromebook/answer/9145439 (entorno Linux de Chromebook y límites)
- https://developers.google.com/chromeos/app-development/develop
- https://developer.apple.com/documentation/virtualization (virtualización en plataforma Apple)
- https://www.apple.com/es/legal/sla/ (términos vigentes de macOS)

## Instrucción para la siguiente IA
Conéctate al repositorio CmdOS-system/Nexus-os, consulta la rama main y los PR abiertos, lee AGENTS.md si existe, PROJECT-CONTINUITY.md, PROJECT-PROGRESS.md, AI-HANDOFF.md y este documento. Comprueba los resultados actuales de Actions y sus artefactos antes de atribuir éxitos. Continúa con implementación y pruebas reales del siguiente punto pendiente; preserva cambios ajenos y no confundas este diseño con una función implementada. Mantén el porcentaje global y el estado de cada plataforma ligados a evidencia. Prioridades centrales: Linux, Windows y APK con instalación gráfica sencilla; compatibilidad macOS y ChromeOS explícita, sin prometer ejecución binaria fuera de soporte; Word es la aceptación relevante de Office.
