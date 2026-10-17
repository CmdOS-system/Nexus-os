# Validación del escritorio antes de reconstruir ISO

2026-10-17. PR #17.

Problema observado: pruebas nativas Ubuntu 24.04 aprobaban ajustes de apariencia que fallaban en la ISO Debian Trixie / xfdesktop 4.20.1. El criterio de fondo no negro aceptaba también el wallpaper predeterminado de XFCE. No usar esos resultados como equivalencia de entorno ni aceptación visual.

Nuevo orden:
1. Sesión XFCE aislada en contenedor Debian Trixie, con desktop-base, dependencias de apariencia y registro de versiones de paquetes.
2. Inicializador real, conservación de una preferencia en ruta moderna de workspace y captura del lanzador.
3. Comparar un área de escritorio fuera del lanzador con referencia renderizada del SVG aurora: al menos 90 % de las muestras con diferencia máxima por canal <=25. Guardar PNG real, referencia, ratio, configuración y log incluso al fallar.
4. Solo si esa prueba pasa, construir la ISO y probar UEFI. La dependencia needs del workflow implementa este orden.
5. Captura QEMU del candidato exacto y chequeo por regiones negras. Revisión visual de aurora, cobertura, atajo e interacción sigue obligatoria.

Límites: el contenedor no reproduce LightDM, kernel, QEMU ni el cambio de resolución de una VM; la validación final Live permanece independiente. El contenedor no fija todas las versiones binarias: packages.txt deja trazabilidad de lo instalado. Una comparación de wallpaper no demuestra IA ni instalación.

Fuente primaria: https://packages.debian.org/trixie/xfdesktop4 (4.20.1-1). Estado: código de validación propuesto, aún pendiente de CI y sin integrar. No reconstruir reiteradamente una imagen como sustituto de reproducir el defecto en la capa correspondiente.
