# Nexus Install — primer prototipo gráfico

PR #21. Alcance inicial: instalador oficial Windows 7-Zip26.04 x64 con hash aprobado. El archivo se selecciona/verifica sin ejecutar; solo el botón Instalar autoriza ejecución. Motor Wine debe estar previamente disponible. Prefijo separado del usuario, sin root y sin shell construido desde nombres de archivo. Progreso indeterminado: no inventa porcentajes del instalador externo. Abrir solo se habilita al encontrar ejecutable esperado tras instalación exitosa.

Código: agent/app_installer.py. Acepta ruta como argumento para futura asociación MIME o selección gráfica. Todavía no se empaqueta en ISO/menú ni se registra como asociación. APK/.deb/Flatpak/AppImage y otros EXE NO implementados. No descargar/preparar Wine automáticamente en este corte. No incluye aún desinstalación, cancelación del proceso activo ni rollback: durante instalación el cierre pide esperar para no simular una cancelación completada.

Pruebas locales: cuatro unit tests aprobados, compilación Python; rechazo de archivo no aprobado, symlink, alteración de copia preparada y conservación de copia ante reemplazo del origen, y guardia de ejecución antes de preparación. Estas pruebas no equivalen al flujo Wine real.

Prueba E2E propuesta en Debian13: descargar instalador de origen oficial, seleccionar en la ventana, comprobar que todavía no exista prefijo, pulsar Instalar, comprobar resultado, pulsar Abrir, exigir ventana real 7-Zip y guardar captura. CI pendiente al publicar; no anunciarlo como disponible a usuarios.

Siguiente tras E2E: revisar logs/captura, integrar código, diseñar asociación de archivos/asistente inicial de motor y desinstalación; extender adaptadores con pruebas por plataforma. Mantener Android y Linux pendientes explícitos. No subir porcentaje de instalador por código aún no validado.


## Resultado posterior confirmado

GUI Wine Lab39053538833 aprobado; artefacto12108338331 descargado e inspeccionado, logs y captura. Selección no ejecutó instalador, confirmación gráfica instaló y Abrir produjo ventana7-Zip. PR #21 integrada02d6bdb. Sustituye el estado CI pendiente anterior. Los límites de formato, empaquetado, motor y persistencia siguen vigentes.


## Integración de archivos e imagen (2026-10-17)

Se incorpora app_installer.py al runtime preparado por image/build.sh; entrada de menú Nexus Install y asociaciones EXE para perfiles nuevos mediante mimeapps.list. Wine/wine64/fonts-wine se incluyen en la lista de paquetes. Abrir un EXE entrega su ruta al asistente; no autoriza ejecutarlo: se conserva verificación de hash y confirmación. Solo está aprobado 7-Zip26.04 x64. APK, MSI y paquetes Linux siguen pendientes. Esta integración requiere validar apertura desde Thunar y generar/probar una nueva ISO; el E2E anterior demuestra el asistente en Debian/Xvfb, no esta nueva integración en Nexus. Avance global permanece ≈36%, instalador25%, Windows50%, Android0%. Siguiente: comprobar MIME con archivo cuyo nombre tenga espacios, ausencia de ejecución al abrir y confirmación/resultado en ISO; no reconstruir repetidamente sin revisar el fallo concreto.


## Asociación EXE validada en laboratorio — 2026-10-17

PR #22, código probado5a287001204cd7ae956287874fc769b92e549cde. Windows Application Lab39062209497 aprobado: instalación CLI real, confirmación/instalación/apertura gráfica y asociación instalada mediante desktop-file-validate + xdg-mime + GIO. MIME observado application/vnd.microsoft.portable-executable. Nombre con espacios llega como argumento exacto al asistente; captura muestra paquete verificado esperando confirmación; no se crea prefijo Wine al abrir. Artefacto12111667022 descargado y revisado (file-association-result.txt y file-association.png). Fast Checks39062213140 y Native Desktop Smoke39062212953 aprobados. Primer intento39062066021 falló porque faltaba file en el contenedor mínimo para xdg-mime; se añadió esa dependencia y pasó. No se cambió la ISO para resolver un fallo del laboratorio.

Estado: asistente, entrada de menú, asociaciones para perfiles nuevos y paquetes Wine preparados para imagen. Pendiente generar/verificar la nueva ISO, interacción real con Thunar y confirmar que los paquetes Wine se resuelven en live-build. Este laboratorio NO demuestra un clic dentro de Nexus, persistencia tras reiniciar ni soporte general EXE/MSI/APK/Linux. Mantener global≈36%, Windows50%, instalador25%, Android0%. Próximo trabajo: revisar ISO Gate y validar ruta Descargas→asistente→confirmación en máquina virtual, conservando logs/capturas; después mejorar recuperación/desinstalación y ampliar aplicaciones mediante casos probados.
