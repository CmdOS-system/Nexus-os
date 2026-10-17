# Fondo Live: topología disponible sin claves modernas

2026-10-17. PR #16.

Probe 39044057903, artefacto 12105745314, candidato ISO 9ad6b05: XFCE/xfdesktop 4.20.1, GDK_MODELS ['Virtual-1'], _NET_NUMBER_OF_DESKTOPS=4, _NET_CURRENT_DESKTOP=0. El canal xfce4-desktop contiene solo last-image antiguos monitor0/monitor1, /last-settings-migration-version=1 y el inicializador registra Horizon background deferred. La razón interna de migración prematura sigue siendo hipótesis; el estado faltante está observado directamente.

Recuperación propuesta: cuando no haya last-image por workspace, consultar GDK y EWMH; con topología válida crear las rutas del monitor real para cada workspace. No crear rutas sin display o sin workspaces; límite 64. La marca de primera inicialización conserva elecciones de usuario posteriores. Dependencias GI/GTK/xprop declaradas en imagen.

Validación local: sh -n y compilación del Python incrustado. Regresión controlada del helper: cero workspaces no produce rutas; cuatro workspaces producen cuatro rutas de Virtual-1. No sustituye prueba gráfica real. CI nativo y nueva ISO pendientes.

Aceptación: nueva ISO con SHA/checksum identificado, aurora visible tras login y cambio de resolución, cobertura completa sin zonas negras, preferencia cambiada por el usuario conservada al reiniciar sesión. No atribuir reparación del compositor al mero establecimiento de rutas.
