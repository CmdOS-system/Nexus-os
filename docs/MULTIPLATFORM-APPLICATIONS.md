# Nexus: aplicaciones Linux, Windows y Android
Fecha: 2026-10-17 (America/Bogota).

## Requisito central
Nexus debe ofrecer una experiencia común para aplicaciones Linux, Windows y Android/APK: abrir el paquete desde el explorador, revisar nombre/origen/permisos, instalar gráficamente, abrir desde el menú y desinstalar desde el mismo centro. El usuario no debe escribir comandos. La compatibilidad se declara por aplicación, versión, arquitectura y equipo probado; reconocer una extensión no demuestra que funcione.

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

Flatpak es el primer adaptador Linux propuesto por su integración gráfica y ámbito de usuario. No añadir automáticamente repositorios desconocidos desde un .flatpakref: mostrar origen y permisos antes de instalar. Un .deb puede ejecutar scripts con privilegios; su instalación pertenece al gestor del sistema, con autorización gráfica, no a un ejecutable arbitrario lanzado como administrador.

Para APK: comprobar compositor Wayland, soporte binder y ashmem o memfd, GPU, arquitectura CPU y servicios del contenedor. El escritorio Live actual basado en X11 no es por sí mismo prueba suficiente. Comparar sesión Wayland nativa frente a compositor anidado en un laboratorio antes de cambiar Horizon. No prometer compatibilidad de APK ARM en x86, Google Play, DRM, banca o juegos con antitrampas sin pruebas individuales. La mera presencia del ejecutable waydroid no significa que el contenedor esté listo.

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

## Instrucción para la siguiente IA
Conéctate al repositorio CmdOS-system/Nexus-os, consulta la rama main y los PR abiertos, lee AGENTS.md si existe, PROJECT-CONTINUITY.md, PROJECT-PROGRESS.md, AI-HANDOFF.md y este documento. Comprueba los resultados actuales de Actions y sus artefactos antes de atribuir éxitos. Continúa con implementación y pruebas reales del siguiente punto pendiente; preserva cambios ajenos y no confundas este diseño con una función implementada. Mantén el porcentaje global y el estado de cada plataforma ligados a evidencia. Prioridades centrales: Linux, Windows y APK con instalación gráfica sencilla; Word es la aceptación relevante de Office.
