# Live ISO: pantalla negra en captura real

2026-10-16. Problema reproducido en QEMU; causa raíz aún no determinada.

## Evidencia

ISO construida y aprobada por ISO Gate 38978527786, SHA de fuentes 98e23179b2feddbb4fc8e4ec6abb26c675f24c81. SHA256 de la ISO: 520d1cb499a19504151ba9117952e0b67eb60fa90a742d7ad0b097361389761e.

Captura independiente 38980101821, código d1d750a56c805f3ea0ad138af0d2d7571ee8bafb, artefacto 12080767543. QEMU q35 TCG, 2 GiB, 2 CPU, VGA std, OVMF, arranque ISO desechable. El script detectó marcadores Live/gráficos/XFCE y usó QMP screendump PNG.

Se inspeccionaron visualmente tres PNG de 1280x800: escritorio, intento de menú Alt-F1 e intento de diálogo Alt-F2. Los tres muestran fondo negro; el primero contiene puntero. No se observó menú, panel ni diálogo. Los nombres indican acciones intentadas, no UI efectivamente visible.

## Interpretación

La ejecución del mecanismo de captura terminó con success, pero esto NO es una validación visual del escritorio. Los marcadores comprueban servicios/procesos, no píxeles de un escritorio utilizable. El estado anterior de UEFI/XFCE readiness se conserva como evidencia limitada; la experiencia visual Live permanece bloqueada.

La primera ejecución de captura 38979740620 falló antes de iniciar QEMU. Se amplió detección de firmware para cubrir rutas alternativas y el segundo intento sí capturó pantalla real. No atribuir la pantalla negra actual a ese primer fallo.

## Próxima investigación

- Captura tardía tras readiness y actividad para descartar transición de inicio o bloqueo/DPMS.
- Comprobar VT/display, salida gráfica activa y framebuffer seleccionado.
- Obtener logs de LightDM, xfce4-session, xfwm4, xfdesktop y xfce4-panel desde el huésped.
- Comparar VGA std/virtio y compositor; registrar configuración exacta.
- Añadir rechazo de capturas casi uniformes al gate visual, conservando imagen y logs como diagnóstico.

No se ha confirmado ninguna de esas hipótesis. No presentar capturas Xvfb de componentes como sustituto de esta evidencia Live.
