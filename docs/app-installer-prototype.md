# Nexus Install — primer prototipo gráfico

PR #21. Alcance inicial: instalador oficial Windows 7-Zip26.04 x64 con hash aprobado. El archivo se selecciona/verifica sin ejecutar; solo el botón Instalar autoriza ejecución. Motor Wine debe estar previamente disponible. Prefijo separado del usuario, sin root y sin shell construido desde nombres de archivo. Progreso indeterminado: no inventa porcentajes del instalador externo. Abrir solo se habilita al encontrar ejecutable esperado tras instalación exitosa.

Código: agent/app_installer.py. Acepta ruta como argumento para futura asociación MIME o selección gráfica. Todavía no se empaqueta en ISO/menú ni se registra como asociación. APK/.deb/Flatpak/AppImage y otros EXE NO implementados. No descargar/preparar Wine automáticamente en este corte. No incluye aún desinstalación, cancelación del proceso activo ni rollback: durante instalación el cierre pide esperar para no simular una cancelación completada.

Pruebas locales: cuatro unit tests aprobados, compilación Python; rechazo de archivo no aprobado, symlink, alteración de copia preparada y conservación de copia ante reemplazo del origen, y guardia de ejecución antes de preparación. Estas pruebas no equivalen al flujo Wine real.

Prueba E2E propuesta en Debian13: descargar instalador de origen oficial, seleccionar en la ventana, comprobar que todavía no exista prefijo, pulsar Instalar, comprobar resultado, pulsar Abrir, exigir ventana real 7-Zip y guardar captura. CI pendiente al publicar; no anunciarlo como disponible a usuarios.

Siguiente tras E2E: revisar logs/captura, integrar código, diseñar asociación de archivos/asistente inicial de motor y desinstalación; extender adaptadores con pruebas por plataforma. Mantener Android y Linux pendientes explícitos. No subir porcentaje de instalador por código aún no validado.


## Resultado posterior confirmado

GUI Wine Lab39053538833 aprobado; artefacto12108338331 descargado e inspeccionado, logs y captura. Selección no ejecutó instalador, confirmación gráfica instaló y Abrir produjo ventana7-Zip. PR #21 integrada02d6bdb. Sustituye el estado CI pendiente anterior. Los límites de formato, empaquetado, motor y persistencia siguen vigentes.
