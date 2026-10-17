# Cobertura parcial del escritorio Live

Fecha: 2026-10-17. PR #14.

El criterio global de píxeles no oscuros aceptaba capturas 1920x1080 con escritorio dibujado en 1280x800 y grandes zonas negras. Se añade un criterio de aceptación por 48 regiones: rechazar al menos cuatro con menos de 0.5 % de píxeles cuyo canal máximo supere 8. Se conserva el criterio previo y el requisito de seis capturas.

Validación local sobre evidencia real descargada:
- Artefacto 12104700554, run 39041654332, nexus-iso-desktop.png: 14 regiones casi negras, rechazado.
- Artefacto 12104755351, run 39041856873, native-xfce-session.png: ninguna región casi negra, aceptado. Esta imagen es sesión XFCE/Xvfb, no ISO.

Comando: python3 image/check-desktop-coverage.py RUTA_PNG [OTRAS_RUTAS]. Código de salida 1 al rechazar, 0 al aceptar. Dependencia Pillow, ya presente en workflow.

Es una heurística para la aceptación visual de Horizon con aurora; no identifica aplicaciones, no prueba interacción y rechaza fondos intencionalmente negros. La revisión visual sigue siendo obligatoria. No trata el defecto gráfico: impide declararlo aprobado por tener contenido en solo parte de la pantalla.

Estado: propuesta en borrador sin integrar; CI pendiente. ISO Gate 39042198220 de la corrección #13 seguía en smoke UEFI al registrar esta nota. Próximo: obtener candidato nuevo, revisar captura automática y ejecutar esta comprobación sobre los PNG exactos, manteniendo SHA y checksum de la ISO.
