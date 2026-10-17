# Nexus Install — instalación gráfica de aplicaciones

Decisión del usuario, 2026-10-17: prioridad central junto con compatibilidad Windows. Descargar un archivo, abrirlo y completar un asistente gráfico; nunca exigir comandos al usuario para el flujo admitido. Android/APK pasa a prioridad alta independiente de macOS.

## Experiencia de producto

Descargar -> abrir archivo -> Nexus muestra aplicación/formato/origen/compatibilidad y permisos -> Instalar -> progreso y cancelación -> Abrir. En la primera instalación de una plataforma, Nexus prepara su motor mediante el mismo asistente, explicando descarga, tamaño, reinicio o autorización necesarios. Descargar por sí solo no ejecuta ni instala contenido. El clic abre el asistente; cambios privilegiados y permisos sensibles requieren confirmación gráfica. No prometer un único clic literal para cualquier instalador externo con diálogos/licencia propios.

Después: todas las apps aparecen en Horizon y en la lista de aplicaciones instaladas, con abrir/desinstalar y estado. Actualizaciones, errores y dependencias se presentan sin terminal. No ocultar incompatibilidad, no abrir consola como única solución y no declarar una app instalada por crear un acceso.

## Adaptadores

| Archivo | Motor/camino propuesto | Aceptación |
| --- | --- | --- |
| .exe / .msi | Wine/Bottles; Proton/Steam para juegos que corresponda | Instalar, tarea útil, guardar/reabrir datos, desinstalar y persistir. |
| .apk | Runtime Android evaluado: Waydroid como candidato inicial | Verificar ABI, instalar, abrir app real, teclado/audio/red, permisos y persistencia. |
| .deb | Gestor de paquetes Debian mediante integración gráfica y helper autorizado | Dependencias, conflictos, autenticidad/origen y desinstalación. |
| .flatpakref / .flatpak | Flatpak con integración gráfica | Mostrar origen y permisos, preparar runtime y verificar ejecución. |
| .AppImage | Integración/ejecución gráfica verificada | Archivo ejecutable solo tras aprobación; dependencias runtime, menú y desinstalación del acceso/archivo según elección. No confundir portable con paquete instalado. |
| .rpm, scripts, otros | Mostrar estado no compatible o soporte explícito futuro | No convertir paquetes o ejecutar scripts silenciosamente en Debian. |

La extensión no basta: validar formato/contenido, arquitectura y tamaño. Una app compatible no garantiza compatibilidad de todas sus versiones. Archivos con espacios/nombres Unicode deben funcionar. No construir shell a partir del nombre del archivo. Procesar fuera de privilegios y verificar identidad del archivo antes del paso autorizado, reutilizando el broker de Nexus.

## Android: evidencia y dependencias

Waydroid ejecuta Android en contenedor Linux y documenta instalación/lanzamiento de APK: https://docs.waydro.id/ y https://docs.waydro.id/usage/install-and-run-android-applications . Su documentación advierte que APK solo ARM no funcionan directamente en x86_64. Evaluar apps Java/multiarquitectura y x86_64 primero; traducción ARM es una línea separada que requiere viabilidad, licencias y pruebas, no promesa universal.

https://docs.waydro.id/usage/install-on-desktops requiere sesión Wayland para el flujo Debian/Ubuntu y señala disponibilidad en backports para Debian 13. La base Nexus actual es XFCE/X11: NO asumir que instalar el paquete Waydroid resuelve integración gráfica. Evaluar una sesión Wayland o compositor anidado, kernel Binder, GPU/driver, permisos de dispositivos y rendimiento en laboratorio. Verificar paquetes reales y firma antes de modificar repositorios. No copiar scripts remotos a root como experiencia de producto.

Google Play Services, certificación/Play Integrity, DRM, apps bancarias, juegos y ARM tienen restricciones independientes. No prometer bypass de esos controles. Un runtime Android instalado no equivale a compatibilidad de APK objetivo. Fuentes autorizadas y APK propio de prueba antes de apps de terceros.

## Investigación e ingeniería inversa

Priorizar código abierto de Wine/Waydroid y documentación de APIs/formatos; estudiar emuladores para interoperabilidad sin copiar tecnología propietaria. Contenedor Android, traducción de APIs y emulación de CPU son mecanismos diferentes. Definir pruebas de rendimiento/memoria/arranque antes de llamar “fluida” a la experiencia.

## Orden de implementación

1. Diseñar router común y contrato de adaptadores; inspector de solo lectura y UI con estados realistas.
2. Laboratorio Wine con aplicación Windows real y launcher gráfico, como WINDOWS-FIRST-ROADMAP.md.
3. Laboratorio Android Debian: kernel/compositor/runtime, APK propio y aplicación objetivo; no esperar acabado completo del escritorio.
4. Adaptadores .deb/Flatpak/AppImage con interfaces gráficas existentes y control de permisos.
5. Enlazar asociaciones MIME/gestor de archivos a Nexus Install; abrir desde Descargas sin terminal. No registrar asociaciones antes de tener el adaptador comprobado.
6. Probar flujos completos en Nexus instalado: primera preparación del motor, error de red, espacio insuficiente, instalador incompatible, cancelación, recuperación tras fallo, segunda instalación, reinicio y desinstalación. Mantener separados el instalador del OS y el de aplicaciones.

## Estado inicial

Especificación/requisito priorizado; asistente común y Android aún no implementados ni validados. No asignar avances por abrir documentos. Próxima ejecución: laboratorio Windows ya priorizado; paralelamente investigar requisitos Android sin consumir nuevas builds ISO. TV/radio y macOS quedan secundarios. Revisión del alcance/progreso en PROJECT-PROGRESS.md.
