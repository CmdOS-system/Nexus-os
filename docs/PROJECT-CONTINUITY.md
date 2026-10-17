# Punto de entrada actualizado — 2026-10-17

Leer primero [AI-HANDOFF.md](AI-HANDOFF.md): consolida estado, trabajo realizado, backlog priorizado, criterios de aceptación y prompt portátil para cualquier IA. El resto de este archivo conserva el registro cronológico; las notas posteriores sustituyen estados anteriores.

En esta sesión se confirmó directamente que PR #7 está integrada en `c5c05a6392ab543882b1f53ce40d12ac3db06d92`. Su captura usó la ISO antigua, por lo que no valida el rediseño de PR #9. No se confirmó el resultado de ISO Gate 38991943403; esa comprobación y la revisión visual del candidato nuevo siguen como siguiente acción. Este cambio es documental y no añade validaciones de ejecución del sistema.

# Nexus OS — continuidad del proyecto

Actualizado: 2026-10-16. Punto de partida inspeccionado: main, b4592913efafbc83065021ae75e39d330fe4e798.

## Objetivo y uso

Crear una distribución Linux fácil de usar, con escritorio propio, instalación gráfica, IA integrada y compatibilidad práctica con aplicaciones Windows. Este archivo reúne el estado verificado y el siguiente trabajo para continuar entre conversaciones. No sustituye los logs ni certifica el producto.

## Fuentes de verdad

- Código y cambios: https://github.com/CmdOS-system/Nexus-os
- Evidencia de ejecución: GitHub Actions, vinculada al SHA exacto.
- Criterios de entrega: docs/release-gates.md.
- Decisiones previas recuperadas: separar Nexus Update, Nexus Recovery y Nexus Boot Manager; validar primero en máquinas virtuales desechables, sin modificar discos ni EFI físicos.

## Estado verificado en esta revisión

- README: desarrollo temprano; sin certificación ni validación en hardware físico.
- Último cambio inspeccionado: b4592913, pruebas de acciones rápidas y errores del panel Horizon.
- Nexus ISO Gate 38935133161: success, SHA 102704419534f0d6d65dec0764cfc76b833c9423. El éxito corresponde a ese SHA; no acredita por sí solo todos los criterios de instalación o release.
- Nexus Fast Checks 38935146493: failure, SHA b4592913efafbc83065021ae75e39d330fe4e798.
- Fallan compilación Python 3.12/3.13 y smoke del panel. El log Python 3.13 identifica SyntaxError en agent/tests/horizon_panel_gui_smoke.py, línea 39: carácter inesperado tras continuación de línea. Las pruebas unitarias fueron omitidas tras el fallo de compilación.
- Validación estática de imagen y staging del instalador: success en esa ejecución.
- docs/build-and-test.md todavía afirma que no se ha construido una ISO: requiere reconciliación con las evidencias de Actions antes de usarlo como resumen actual.

## Antecedentes recuperados, pendientes de revalidación actual

Conversaciones anteriores describen arranque Live UEFI en QEMU, XFCE/LightDM, Nexus Flow y trabajo de IA. Recuperación A/B persistente, instalador real, proveedor de IA conectado, compatibilidad Wine/Proton y hardware siguen requiriendo evidencia específica. No tratar un relato anterior como prueba actual.

## Próximas acciones por orden

1. Revisar PR #1 de seguridad BYOAI/file grants (abierta y sin integrar al revisar); comprobar regresiones y compatibilidad antes de integrarla.
2. Contrastar artefactos de ISO Gate y pruebas visuales con el SHA y checksum exactos; comprobar la integración panel+lanzador y el atajo real.
3. Continuar instalador y persistencia en VM, luego integración de IA y matriz Wine/Proton, siguiendo release-gates.md.
4. Mantener actualizados los documentos que todavía describen prototipos ya evolucionados, sin convertir propuestas en funciones entregadas.

## Protocolo de continuidad

En cada sesión, leer este archivo, comprobar main y Actions actuales, conservar decisiones vigentes y actualizar: cambio realizado, SHA, pruebas ejecutadas, resultado y siguiente bloqueo. No declarar trabajo terminado por tener código o un workflow exitoso de otro SHA. No reiniciar componentes que ya tengan evidencia suficiente.

## Progreso global

Sin porcentaje recalculado: no existe en esta revisión una matriz ponderada que respalde un porcentaje global. El 70% citado en conversaciones anteriores es una estimación histórica, no una medición actual. Comunicar avance por hitos de release y evidencia verificable.

## Consolidación adicional — 2026-10-16

### Trabajo concluido en esta sesión

- Corrección de sintaxis guardada en `378a6388974505059d7b1d3cc6640eda6d431d7e`.
- [Fast Checks 38977578555](https://github.com/CmdOS-system/Nexus-os/actions/runs/38977578555): los cinco jobs finalizaron con success (Python 3.12, Python 3.13, smoke gráfico, validación estática y staging de instalador).
- ISO Gate 38935133161: se inspeccionaron los pasos; build, checksum, GRUB, smoke UEFI y cargas de artefactos finalizaron con success. No se descargaron ni inspeccionaron los binarios en esta consolidación. El script actual exige marcadores Live, pila gráfica y sesión XFCE; no prueba calidad visual ni instalación.
- `docs/build-and-test.md` actualizado con estas evidencias en `72ae1c5a3fe3123d1f678da2e4af66529802ee9c`.
- PR #1 `Security hardening: strict BYOAI consent and safe file grants`: abierta, no integrada, head observado `eb35e7b879ca849b31e58d630a6f2ad9830ac052`.

### Requisitos recuperados de los chats y contraste con el proyecto

Se recuperó contexto de Acceso a GitHub, Nexus OS desarrollo autónomo y Avanzar Nexus OS hasta las 8. No se realizó una lectura exhaustiva de cada mensaje ni se obtuvo acceso directo a la configuración/instrucciones privadas del proyecto ChatGPT. La documentación del repositorio sí se leyó directamente.

- Prioridad del usuario: avanzar autónomamente, investigar y resolver fallos con pruebas reales; comunicar progreso global y facilitar enlaces de ejecución.
- Experiencia deseada: escritorio pulido, instalación sencilla, IA con voz y acciones del sistema, elección de proveedor y compatibilidad práctica Windows/macOS/Android. Esta visión no equivale a compatibilidad universal demostrada.
- Compatibilidad Windows: aprovechar Wine/Proton/Bottles/Lutris/Winetricks/DXVK/VKD3D mediante integración Nexus; no reimplementar Wine. Exigir ejecución real de aplicaciones objetivo.
- Investigación solicitada: Bottles, REA (github.com/morluto/rea), Chromium/ChromiumOS y compatibilidad PS5. Son líneas de investigación; no capacidades entregadas o certificadas.
- Base de trabajo recuperada: Debian 13/live-build y XFCE; separar validación Live del instalador, IA, actualizaciones/recuperación y hardware.
- `docs/INSTALLER-ARCHITECTURE.md` mantiene instalación bloqueada: planning de solo lectura, autorización por dispositivo y pruebas destructivas exclusivamente QCOW2 desechables.
- `docs/NEXUS-HORIZON-DESIGN.md` contiene dirección visual y criterios de accesibilidad aún propuestos. El lanzador/panel existente y sus smoke tests no prueban que se cumpla toda esa propuesta.
- Validar UEFI con firmware de solo lectura, estado de variables separado cuando aplique y segundo arranque del sistema instalado sin ISO. No confundir boot Live con persistencia instalada.
- A/B, Secure Boot y dm-verity requieren pruebas de su cadena de confianza y recuperación; un marcador serial no certifica integridad.

### Progreso por hitos a este corte

| Hito | Evidencia y límite |
| --- | --- |
| ISO Live y readiness UEFI/XFCE | ISO Gate verde en 1027044; instalación no acreditada |
| Regresión rápida del arreglo Horizon | Cinco jobs verdes en 378a638 |
| Diseño visual completo y accesibilidad | Propuesta; aceptación completa pendiente |
| Instalador persistente | Bloqueado por pruebas E2E de disco virtual y reinicio |
| IA de extremo a extremo | Prototipos presentes; integración conectada pendiente de evidencia |
| Compatibilidad Windows/hardware | Matriz de aplicaciones y equipos pendiente |
| Actualización/recuperación y release | Gates independientes pendientes; sin certificación |

## Avances siguientes — seguridad y arranque de Agent

- [PR #2](https://github.com/CmdOS-system/Nexus-os/pull/2), `08c66bcbee51bcb04d5cdb85f91c1f568ee03ba4`: consentimiento booleano y lectura acotada ligada a identidad del archivo. Se reprodujeron fallos previos. 177 unit tests y validación de imagen locales aprobados; los cinco jobs de [Fast Checks 38978238994](https://github.com/CmdOS-system/Nexus-os/actions/runs/38978238994) también finalizaron con success. Continúa en borrador, sin integrar ni reconstruir ISO.
- [PR #3](https://github.com/CmdOS-system/Nexus-os/pull/3), `0aef476a4def78051c487044826d894a78535869`: Agent toma el modelo local Ollama guardado en Control Center si no hay override explícito; rechaza configuración off/cloud/hybrid/inválida. 180 unit tests locales aprobados, sintaxis Python/shell y image/validate.sh correctos. Borrador independiente basado en main; CI y ejecución con modelo real/ISO pendientes.
- Ambas propuestas recuperan partes concretas de PR #1 sin incorporar sus cambios históricos conflictivos. Revisar compatibilidad conjunta antes de integrar; no cerrar #1 mientras falten sus otros cambios.

## Integración confirmada — 2026-10-16

PR #2 integrada mediante `342024e07163d9b0016579e9868cee76f712fa9f`; PR #3 integrada mediante `98e23179b2feddbb4fc8e4ec6abb26c675f24c81`. Sustituye el estado anterior de borrador de ambas propuestas.

- PR #3 Fast Checks [38978387910](https://github.com/CmdOS-system/Nexus-os/actions/runs/38978387910): success; PR #2 también verde según registro anterior.
- Combinación de ambos cambios sobre main actualizada: 184 pruebas unitarias locales aprobadas, compilación Python y image/validate.sh aprobados.
- [ISO Gate integrado 38978527786](https://github.com/CmdOS-system/Nexus-os/actions/runs/38978527786): ejecución iniciada y observada in_progress para `98e23179b2feddbb4fc8e4ec6abb26c675f24c81`; aún no atribuir éxito ni nueva ISO verificada.
- [Fast Checks integrado 38978527776](https://github.com/CmdOS-system/Nexus-os/actions/runs/38978527776): observado pending al corte.
- Siguiente paso: inspeccionar ambas ejecuciones integradas y sus artefactos; probar Agent con un modelo Ollama real. La prueba de modelo real no ha ocurrido en esta sesión.

## Modelo real verificado — 2026-10-16

- [Nexus Real AI Smoke 38978824081](https://github.com/CmdOS-system/Nexus-os/actions/runs/38978824081): success para `53132df7ae4581cdb16f40c74625cd63b9e74b0d`. Se inspeccionaron los logs y se confirmó artefacto `nexus-real-ai-evidence` (ID 12080530920).
- Ollama CPU con `qwen2.5:0.5b`, digest `a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67`; respuesta real del cliente: `READY`. CLI sin --model ni NEXUS_AI_MODEL, usando configuración local temporal guardada: `READY.`. Dos rutas completadas en 1.262 s dentro de la fase de inferencia; no es un benchmark ni incluye descarga/arranque.
- Fast Checks [38978837017](https://github.com/CmdOS-system/Nexus-os/actions/runs/38978837017): success.
- PR #4 integrada en `65de0b72a7078674588de35470cd2b5ea699c89c`. Workflow/probe quedan disponibles para repetir la prueba y registrar digests de modelo/runtime.
- Este resultado reemplaza el pendiente genérico de conexión con modelo real para proveedor+CLI. Siguen pendientes empaquetado/ejecución en ISO, interfaz gráfica de conversación, voz y automatización del escritorio.
- Main integrado Fast Checks 38978527776: los cinco jobs aprobados. ISO Gate 38978527786 todavía observado in_progress durante la construcción; no atribuirle éxito antes de consultar su resultado.

## ISO integrada aprobada y captura solicitada — 2026-10-16

ISO Gate 38978527786 finalizó con success en `98e23179b2feddbb4fc8e4ec6abb26c675f24c81`: build, checksum, GRUB, smoke UEFI/XFCE y artefactos aprobados. Sustituye los registros anteriores in_progress. Artefacto candidato 12080396980, `nexus-os-candidate-98e23179b2feddbb4fc8e4ec6abb26c675f24c81`, y diagnósticos 12080841033.

El usuario solicitó captura del sistema de pruebas arrancado, no sólo el render Xvfb de Horizon. PR #5 añade captura QMP PNG tras marcadores Live/gráficos/XFCE, usando esa ISO exacta y verificando SHA256SUMS. Fast Checks 38979744178 aprobó sus cinco jobs. Ejecución de captura 38979740620 observada en recuperación del candidato; todavía no se ha validado una imagen. No confundir captura de framebuffer con pruebas de instalación o calidad visual.

## Bloqueo visual Live descubierto — 2026-10-16

Se generaron e inspeccionaron tres capturas REALES de la ISO en QEMU en run 38980101821, artefacto 12080767543: todas muestran pantalla negra (apenas puntero). La captura se ejecutó, pero el escritorio visual NO está validado. Los marcadores XFCE/services no bastan para acreditar UI utilizable. Priorizar diagnóstico de pantalla/VT, inicio de XFCE, DPMS y compositor antes de pulido visual o declarar escritorio listo. Ver `docs/bugs/live-iso-black-framebuffer-2026-10-16.md`. PR #5 sigue sin integrar. Primera ejecución de captura falló antes de QEMU; el segundo intento sí produjo los PNG.

## Escritorio Live visible confirmado — 2026-10-16

El run 38980833818 terminó con success. Se inspeccionaron imágenes reales de la misma ISO (checksum sin cambios): escritorio XFCE y menú Applications visibles. La captura ahora espera 45 s tras readiness y rechaza PNG casi negros. PR #5 integrada en 6ac50336d246903606b89c4c5a706ea88f6e48c0; Fast Checks 38980839173 aprobó. Las imágenes anteriores negras apuntan a captura demasiado temprana; causa exacta de la demora pendiente. No afirmar reparación de la ISO, ya que no fue modificada. Alt-F2 no mostró el diálogo en la tercera imagen; esa acción no está validada.

Estado: arranque Live, sesión y salida visual básica comprobados; diseño Horizon completo, interacción de todas las apps, IA dentro de ISO, instalación/persistencia y compatibilidad Windows/PS5 siguen pendientes. Próximo paso: capturar y ejercitar Nexus Control Center/Horizon dentro de la ISO y mejorar la condición de readiness basada en UI visible.


## Diagnóstico gráfico repetido y siguiente interacción — 2026-10-16

- PR #6: https://github.com/CmdOS-system/Nexus-os/pull/6. Sigue en borrador; no integrada.
- Captura Live 38982257876: success en `23e2412bed066906214a7a77f10a853d4fde131a`, artefacto `12082011087`, ZIP SHA256 `d69244e3abcff6c08595537c3c3934e3c7a38aa9f8ba1dccf6813a5453773cca`. Descargado e inspeccionado el registro y la captura tras Alt-F2; se ve XFCE, sin diálogo Alt-F2 visible.
- Esperar al marcador XFCE antes del diagnóstico eliminó los anteriores errores de autorización/display en este registro: xrandr devuelve Virtual-1 conectado a 1280x800; xwininfo devuelve panel, escritorio y ventanas XFCE. No atribuir este resultado a una modificación de la ISO ni a una solución de todas las interacciones.
- Fast Checks 38982260992: cinco jobs success para el ajuste de diagnóstico. Fast Checks 38982642570: success para `e3d58916cda6982c4ca22bae3b367fb3435ed021`, que también añade un intento Super+Espacio y cuarta captura de Horizon.
- Captura extendida 38982639554: observada in_progress al registrar esta nota. Falta inspeccionar `nexus-iso-desktop-horizon.png`; un PNG no negro no demuestra por sí solo que se abrió Horizon.
- Siguiente paso concreto: inspeccionar el artefacto de 38982639554, confirmar visualmente el lanzador o diagnosticar el atajo; integrar PR #6 cuando termine la validación del head vigente.


## Resultado de la captura extendida — 2026-10-16

- Run 38982639554 terminó con success para `e3d58916cda6982c4ca22bae3b367fb3435ed021`; todas sus etapas fueron inspeccionadas. Artefacto `12081613752`, ZIP SHA256 `9c190d1ac7db00b28521e83ca92616cf19ebc770981776f341634b8cdc8e6865`, descargado localmente.
- Se inspeccionó `nexus-iso-desktop-horizon.png`: muestra Application Finder de XFCE con lista de comandos, NO Nexus Horizon. El éxito del workflow acredita captura y rechazo básico de imágenes negras, no la interacción Horizon.
- PR #6 integrada en `b5a7ac744855dc414e67d43b60e53dd1bc89c080`, tras Fast Checks 38982642570 y captura extendida aprobados. Sustituye su estado de borrador registrado arriba.
- Próximo bloqueo: distinguir latencia de Alt-F2/Escape/Super+Espacio frente a configuración efectiva del atajo en el huésped. Consultar xfconf y archivos/ejecutables Horizon dentro de la ISO; separar cada interacción con esperas verificables. No declarar el lanzador validado hasta verlo y comprobar su respuesta.
- Progreso global: Live visible y diagnósticos de sesión útiles; proveedor+CLI de IA real ya verificados fuera de ISO. Persisten gates independientes de Horizon Live, instalación/persistencia, IA dentro de ISO/voz y compatibilidad Windows.


## Horizon: recuperación del diseño y cambios concretos — 2026-10-16 (Bogotá)

Se recuperó la conversación «Nexus Horizon»: el usuario pidió estudiar Apple/macOS, GNOME, Material y KDE para crear identidad propia, superficies oscuras, luz ambiental, dock flotante, IA contextual, nitidez y acabados. La captura XFCE anterior no cumplía esa dirección. No tratar conceptos Chromium o capturas Xvfb como escritorio ISO final.

- PR #8 integrada en `55b310012021ac60883c0b76d21e7c87fd4b0fcd`: el atajo se siembra en commands/default. La prueba real de xfsettingsd reprodujo pérdida con la configuración antigua y conservación con la nueva, manteniendo Alt-F2. Seis checks success en 38991434581. El primer intento de prueba falló porque el daemon activado por D-Bus no recibía el XDG_CONFIG_HOME temporal; se corrigió el aislamiento antes de interpretar el resultado.
- Captura diagnóstica 38991201713, artefacto 12085591583, success: el registro de la ISO antigua muestra `/usr/local/bin/nexus-horizon` sin permiso de ejecución (0644), y la quinta captura queda en App Finder con nexus-horizon escrito. No era solo una cuestión de latencia.
- PR #9 integrada en `a2582a2c05d826a15e4c7a4f71503889d0b4eb69`: fondo SVG aurora 3840×2160, tema Arc-Dark, iconos Papirus-Dark, Inter, defaults nativos de GTK/XFWM y fondo inicial por monitor; lanzador nativo con tarjetas adaptables, iconos vectoriales, búsqueda y foco visibles, scroll y selección por teclado. Se corrigen modos ejecutables de Nexus Horizon y Agent y se validan en image/validate.sh.
- Seis checks success en 38991844855 para head `d380fc4705f86b9eead473fc6c4a810325d8ef18`; captura del lanzador descargada e inspeccionada. Es una ventana Tk real en Xvfb, recortada a 1040×820 sobre una sesión 1920×1080; NO es captura de la ISO nueva.
- ISO Gate 38991943403 para el merge visual: observado pending/en cola. No afirmar que el diseño nuevo ya se vio en una ISO arrancada.
- PR #7 mantiene diagnóstico ampliado y captura automática al completar ISO Gate, con intento temporal de 1920×1080 en el huésped. Último head `2a5f92caffce8a60614b1d4427cee3e4fb3021aa`: Fast Checks 38991901656 success; captura 38991897998 todavía en curso al registrar esta nota. Integrar tras revisar esa ejecución.
- Próximo paso: comprobar ISO Gate 38991943403, usar su artefacto exacto para captura nueva, verificar fondo/tema/ejecutables y atajo Horizon. Dock flotante, blur/translucidez, IA gráfica, temas accesibles completos y validación HiDPI siguen pendientes.


## Revalidación directa — 2026-10-17 (Bogotá)

- ISO Gate 38991943403 confirmado success: construcción, checksum, GRUB y smoke UEFI. Candidato a2582a2c05d826a15e4c7a4f71503889d0b4eb69, artefacto 12086460150. Sustituye su estado pendiente anterior.
- Captura automática de ese candidato 38993534964 terminó failure en Reject blank visual evidence. La descarga verificó checksum; QEMU produjo cinco capturas. La primera tuvo fracción no oscura 0.000045814 y las otras entre 0.070 y 0.509. No omitir esta comprobación para volver verde el workflow.
- Se descargó artefacto 12085274775 y se inspeccionó nexus-iso-desktop-horizon-direct.png: muestra Application Finder, fondo XFCE en región 1280x800 y negro en el resto del framebuffer 1920x1080. NO muestra Horizon ni aurora. Los logs confirman wrapper 0755 y atajo Super+Espacio configurado; los arreglos anteriores existen, pero la apertura no queda validada. No atribuir todavía causa a latencia, composición o configuración.
- PR #10 confirmada integrada en e95def969b8a9897b00624e7888a19e478d5ad93. Native Desktop Smoke 38993555945 y Fast Checks 38993555911: success en ese SHA. Es sesión XFCE/Xvfb aislada, no ISO.
- Siguiente trabajo: instrumentar la sesión Live con estado de autostart/appearance y preferencias xfconf; ejecutar el wrapper desde la sesión gráfica con stdout/stderr y código de salida, identificar ventana Horizon, esperar repintado tras xrandr antes de captura. Conservar capturas iniciales fallidas y criterios de rechazo. Repetir con el mismo candidato exacto; no reconstruir sin una causa que requiera cambiar imagen.
- Progreso global: nueva ISO construida y UEFI aprobado; apariencia y lanzamiento Horizon Live bloqueados. Instalación persistente, IA en ISO/voz, Windows y recuperación instalada siguen pendientes.


## Hito confirmado: Horizon visible mediante atajo en ISO — 2026-10-17

Se descargó artefacto 12104561411 de captura QEMU 39041523768 (success, harness f5d257f85cb3a80938b27ec121368f393e7ff653, candidato ISO a2582a2). Inspección visual: nexus-iso-desktop-horizon.png muestra el lanzador Horizon tras Super+Espacio; horizon-probe.png lo muestra también por ejecución directa. Esto sustituye el pendiente de apertura y atajo para ese candidato, sin acreditar todavía todas sus interacciones.

El fondo sigue siendo XFCE en área 1280x800 y hay negro en parte del framebuffer 1920x1080. Aurora/cobertura completa no aprobadas; un run verde solo confirma los criterios implementados. PR #11 conserva diagnóstico y sincronización de captura; PR #13 propone esperar claves de backdrop por workspace en vez de finalizar sobre claves heredadas, con CI nativo y validación ISO pendientes. Ambas propuestas siguen sin integrar al corte.

Evidencia real: https://github.com/CmdOS-system/Nexus-os/actions/runs/39041523768/artifacts/12104561411 . Fast Checks 39041669629 success para 4de73ae. Próximo paso: inspeccionar captura sincronizada 39041654332 y resultado nativo 39041856873, resolver fondo/repintado y después reconstruir y validar candidato que incluya la corrección. Progreso: Live UEFI + Horizon visible y atajo confirmados; instalación persistente, IA en ISO/voz, Windows y recuperación instalada pendientes.


## Cambios preparados para integración — 2026-10-17

PR #11: probe acotado de 20 segundos posterior a cinco capturas, salida/código y ventanas; sexta captura separada, señal de sincronización y espera NEXUS_DIAG_END antes de imagen inicial. Captura 39041654332 success en 9779277; PNG inicial inspeccionado: aún fondo XFCE parcial con negro, por lo que la sincronización no arregló el render. Artefacto 12104700554. Fast Checks 39042032070 success en 1d246e6. Es mejora de diagnóstico, no aceptación visual completa.

PR #13: aceptar únicamente backdrop por workspace y esperar hasta 60 s; evitar marcar éxito sobre propiedades heredadas. Prueba controlada local pasó con listado heredado seguido de workspace, sin escrituras prematuras y conservando preferencias posteriores. Native Desktop Smoke 39041856873 y Fast Checks 39041856816 success en e04c2fb. Falta nueva ISO y prueba Live: no declarar fondo reparado en el candidato anterior.

Ambos cambios listos para revisión/integración; comprobar estado actual de PR. Próximo: construir candidato con #13 y capturar con #11; revisar aurora y cobertura 1920x1080. Mantener fallo visual documentado incluso si los workflows pasan. Documentación primaria: https://github.com/xfce-mirror/xfdesktop/blob/xfce-4.20/common/xfdesktop-common.c y https://docs.xfce.org/xfce/xfconf/xfconf-query .


## Integración de diagnóstico y fondo — 2026-10-17

PR #11 integrada 03b0fb63e3e936908d8efe12e714a3a34510984c; PR #13 integrada 9ad6b052da6957c0bdda3a0c2065f04447774ff5. Sustituye estados pendientes de integración anteriores. Los cambios de código tenían CI/captura o sesión nativa aprobadas; últimas actualizaciones previas a merge reconciliaban documentación únicamente. Consultar CI combinado del SHA 9ad6b05 y el nuevo ISO Gate. No afirmar que la ISO anterior incluya la corrección de wallpaper ni que la cobertura negra esté resuelta. Próximo hito: nueva ISO con #13, captura automática usando #11, inspección del fondo aurora y área completa; luego interacción Control Center/Agent en Live.


## Nueva ISO probada: fondo aún incorrecto — 2026-10-17

ISO Gate 39042198220 success en 9ad6b052da6957c0bdda3a0c2065f04447774ff5. Captura automática 39043287407 success según criterio básico; artefacto 12105111678 descargado, horizon-probe.png inspeccionado: Horizon visible, fondo XFCE limitado a 1280x800 con negro restante en 1920x1080. ISO SHA256 8935009d92e26e8a6ce308cab9168b029764ff0dd7e34b4c3593dbe555e06a4a. Este resultado demuestra que #13 no resolvió el aspecto Live; no repetir éxito de sesión Xvfb como aceptación ISO.

Probe sigue mostrando únicamente monitor0/monitor1 last-image heredados; no hay rutas workspace. Siguiente diagnóstico en rama test/live-backdrop-migration: versión xfdesktop, EWMH escritorios, modelos GDK reales, marcador de inicialización y errores tardíos. La ausencia de workspace al migrar es hipótesis, no causa confirmada. Se usa el candidato nuevo exacto sin reconstruirlo.

PR #14 propone rechazar cobertura parcial; prueba local rechazó baseline defectuoso con 14/48 regiones negras y aceptó captura nativa aurora con 0/48. Sigue en borrador. Progreso: Live UEFI y Horizon confirmados; fondo/cobertura bloqueados, instalación persistente, IA en ISO/voz y Windows pendientes.


## Topología Live confirmada y recuperación propuesta — 2026-10-17

Diagnóstico 39044057903 success y Fast Checks 39044076378 success para 2c1da29. Artefacto 12105745314 descargado: xfdesktop 4.20.1, GDK Virtual-1 y cuatro workspaces EWMH; solo claves heredadas y migración=1, inicializador diferido. PR #16 propone crear claves modernas desde topología real cuando falten, con dependencias explícitas. Shell/Python y regresión controlada de topología pasaron; CI nativo y nueva ISO pendientes. No se ha resuelto aún el fondo Live ni la cobertura negra. PR #15 sigue como diagnóstico no integrado; #14 sigue como criterio de cobertura no integrado. Próximo: validar #16 en sesión nativa, luego candidato ISO y capturas; conservar preferencia posterior del usuario.
