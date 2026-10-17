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


## Recuperación de topología integrada — 2026-10-17

PR #16 integrada a6997fb5356e71e70242fe71e545ab1c8d510b78 tras Native Desktop Smoke 39048640275 y Fast Checks 39048640373 success para ae883c4. Esperar el nuevo ISO Gate de a6997fb y posterior captura; la sesión nativa no sustituye aceptación Live. PR #14 incorpora criterio de regiones casi negras: el fallo sobre el candidato viejo es esperado porque contiene cobertura parcial observada. Consultar estado de integración de #14 en GitHub. No debilitar umbral para volver verde un defecto real.

Siguiente acción: identificar run ISO de a6997fb, verificar candidato y SHA256, inspeccionar captura automática con criterio de cobertura completo. La recuperación crea claves por workspace si EWMH/GDK son válidos, pero fondo/repintado siguen sin acreditarse en nueva ISO. Progreso Live/Horizon/atajo sin cambios; instalación persistente, IA en ISO/voz y Windows pendientes.


## Cambio del método de trabajo solicitado por el usuario — 2026-10-17

Evitar el ciclo de corregir/reconstruir sin reproducir causa. PR #17 propone reemplazar preflight Ubuntu por Debian Trixie (como ISO), incluir desktop-base, registrar versiones y comparar píxeles con SVG aurora, además de probar conservación de ruta workspace. ISO Gate dependerá de ese preflight antes de construir. Documentado en docs/desktop-validation-strategy.md de la rama test/debian-desktop-before-iso. Es solución al vacío de validación entre entornos, no reparación gráfica demostrada. CI objetivo 39049597928 en curso; no integrar hasta inspeccionar resultado.

ISO Gate 39048872619 de #16 todavía en build al corte. PR #14 ya detectó la cobertura parcial en el candidato viejo mediante fallo esperado 39048894867. Siguiente: resolver primero el resultado del preflight Debian, después usar una sola ISO con criterio de aurora/cobertura real. No anunciar el fondo arreglado por aprobar sintaxis, mocks o configuración xfconf.


## Preflight Debian con prueba de píxeles aprobado — 2026-10-17

Native Desktop Smoke 39049627191 y Fast Checks 39049627176 success en 0f3667. Artefacto 12107346535 descargado: xfdesktop4 4.20.1-1, xfce4-session 4.20.2-2, xfwm4 4.20.0-1; Aurora pixel match=1.000 en región muestreada. Screenshot nativo 1920x1080 inspeccionado: aurora y Horizon, sin la zona negra anterior. Es contenedor Debian/Xvfb como root, NO ISO/LightDM; no extrapolar aceptación Live.

PR #17 integrada b720aba890e6527f7c81aaaa1ccc4b9523f39f84. ISO Gate exige ahora preflight Debian y comparación de aurora antes del build. Cambios exclusivos de workflow no disparan reconstrucción automática del runtime sin cambios; se conserva dispatch y triggers de runtime. Último ajuste antes de merge solo cambió esa selección de triggers.

ISO Gate 39048872619 de a6997fb ya success; captura automática 39049935491 todavía pendiente de inspección. Usar ese candidato existente y su checksum; no reconstruir otra imagen para comprobar un cambio exclusivo de tests. Próximo: revisar la captura QEMU con criterio de cobertura y aurora; si falla, aislar diferencia Live/LightDM/QEMU usando el preflight Debian ya verde.


## Aurora confirmada en ISO; repintado sigue bloqueado — 2026-10-17

Captura 39049935491 finalizó failure en criterio visual, como corresponde al defecto restante. Artefacto 12107931180 descargado e inspeccionado: PNG inicial muestra aurora real en 1280x800 dentro de framebuffer 1920x1080, con negro a derecha/abajo. #16 sí consiguió crear rutas monitorVirtual-1/workspace0..3/last-image y renderizar aurora; esto sustituye el pendiente genérico de fondo que no aparecía. Cobertura completa y comportamiento tras RandR todavía NO aprobados.

Prueba siguiente en test/live-repaint-reload: mismo candidato a6997fb, cinco imágenes de base intactas, luego xfdesktop --reload documentado y sexta imagen del probe. Busca comprobar recuperación de repintado sin reconstrucción. Un eventual éxito tras intervención no acredita comportamiento automático del sistema. Python/shell local aprobados, ejecución pendiente. Fuente: https://docs.xfce.org/xfce/xfdesktop/command-line . No desactivar la validación por regiones negras para convertir el fallo en éxito.


## Investigación Nexus TV solicitada — 2026-10-17

Ver docs/research/nexus-tv-feasibility-2026-10-17.md: fuentes primarias, propuesta Kodi/IPTV Simple + Tvheadend opcional + broker de IA, alternativa libmpv y servicios DRM por vías oficiales. Investigación documental guardada, sin implementación/reproducción probada. Falta identificar SuperTV exacto; la ficha com.supertv.yapp no permite deducir que sea la aplicación del usuario ni sus derechos de contenido. No se descargó ni analizó un APK. Sin puerta pirata ni evasión de DRM/pagos; interoperabilidad solo con fuentes y accesos autorizados.

Este trabajo no sustituye el bloqueo de cobertura Live ni requiere nueva ISO. Próximo TV: identificar app, elegir fuente propia/autorizada y prototipo aislado antes de empaquetado. Escritorio: revisar prueba test/live-repaint-reload sobre el candidato existente.


## Repintado: reload descartado y prueba EDID preparada — 2026-10-17

Run 39050598708 failure, artefacto 12108125568 inspeccionado. xfdesktop --reload devolvió 0 y sexta captura aún presenta aurora limitada a región antigua; no integrar #18 como reparación. PR #19 configura EDID preferido 1920x1080 desde el arranque y elimina cambio xrandr en la prueba, manteniendo requisito de dimensiones y rechazo de negro. Usa la misma ISO a6997fb; sin reconstrucción. Fuente QEMU v8.2.2 vga-pci.c / edid.h confirma propiedades xres/yres. Si pasa, acredita arranque Full HD, no cambio dinámico de resolución; el defecto RandR sigue separado.

TV: disponibilidad oficial de Kodi y kodi-pvr-iptvsimple en Debian Trixie documentada; Tvheadend aún no confirmado como paquete de esa distribución. Próximo prototipo aislado con clip propio, sin alterar ISO ni incorporar fuentes no autorizadas.


## Radio y formato de progreso global — 2026-10-17

Usuario solicita incluir radio y estudiar documentación antes de integración. Investigación guardada en docs/research/nexus-radio-feasibility-2026-10-17.md: directorio Radio Browser, fuentes oficiales, motor compartido, MPRIS, IA por IDs y FM opcional con hardware V4L2. Radio sigue sin implementación/reproducción comprobada. No prometer perfección sin matriz de pruebas.

En cada respuesta usar barra global por hitos, no porcentaje inventado. Orden estable de ocho hitos: 1 Live/UEFI; 2 escritorio Horizon completo; 3 IA integrada en sistema; 4 instalación/persistencia; 5 compatibilidad Windows; 6 actualización/recuperación instalada; 7 TV/radio; 8 aceptación de release/hardware. Convención: verde=criterio completo, amarillo=en curso/parcial, blanco=pendiente. Al corte: 🟩🟨🟨⬜⬜⬜🟨⬜. Las posiciones no representan esfuerzo equivalente ni porcentaje de producto. Live probado, escritorio con aurora pero cobertura pendiente, IA real solo consola fuera ISO, medios en investigación. Mantener el progreso actualizado con evidencia.

Escritorio: captura Full HD nativa 39051320346 todavía en curso al corte; no reconstruir ISO para esta prueba.


## Porcentajes por módulo solicitados — 2026-10-17

El usuario pide porcentaje global y por cada función, incluyendo nuevas funciones. Sustituye la presentación solo por colores. Leer docs/PROJECT-PROGRESS.md: escala estimada 0/25/50/75/100 y pesos explícitos que suman 100; primer corte 40.75 %, mostrado ≈41 %. Es estimación de gestión que incluye diseño/implementación parcial, no porcentaje de funcionalidades acabadas ni certificación. Los pesos son juicio inicial de planificación, no horas medidas. Mostrar siempre porcentaje global aproximado; añadir/reponderar filas ante nuevo alcance y explicar si baja el total. No subir avances por estados CI sin verificar ni por documentación repetida. Cortes anteriores sin porcentaje siguen siendo registros históricos.


## Prioridad central ratificada: aplicaciones Windows — 2026-10-17

Leer docs/WINDOWS-FIRST-ROADMAP.md antes de elegir la siguiente tarea. El usuario confirma Windows como objetivo central de Nexus; no retrasar el laboratorio Wine esperando acabados estéticos, TV/radio o voz. Trabajar instalación/persistencia como habilitador. Orden: laboratorio Debian/Wine -> aplicación real sencilla -> aplicación difícil del usuario con tarea útil -> asistente Nexus/prefijos -> prueba persistente en VM -> ampliar matriz. Investigación/ingeniería inversa para interoperabilidad con permisos, fuentes primarias y componentes abiertos; no prometer universalidad.

Nueva ponderación PROJECT-PROGRESS.md: Windows 30 %, instalación 15 %; global estimado 35.75 % -> ≈36 %, frente al ≈41 % histórico por distinta ponderación. Avances de módulo no cambiaron. Windows sigue 25 % de diseño/piezas preliminares, sin una aplicación real acreditada. Siguiente incremento exige ejecución comprobada. Captura Full HD sigue como tarea acotada de escritorio; no consumir todo el proyecto en pulido visual.


## Prioridad central ampliada: APK/Windows/Linux sin terminal — 2026-10-17

Usuario exige descargar, abrir archivo y usar asistente gráfico para instalar apps Android APK, Windows exe/msi y Linux, sin introducir comandos. Leer docs/ONE-CLICK-APPLICATIONS.md: router/adaptadores, preparación gráfica de runtimes, progreso, permisos, acceso Horizon y desinstalación. No ejecutar al descargar; clic abre asistente y confirmaciones necesarias. No prometer compatibilidad de cualquier APK/EXE ni todos los formatos Linux.

Android ahora prioridad alta separada de macOS. Waydroid candidato, no integrado: necesita resolver Wayland frente al XFCE/X11 actual, Binder/GPU y ABI ARM/x86_64. Investigar código abierto/interoperabilidad; no copiar emuladores propietarios ni eludir controles. Windows sigue central; TV/radio y pulido avanzado secundarios. Trabajo siguiente: laboratorio Windows real y requisitos Android antes de empaquetado.

PROJECT-PROGRESS.md reponderado por alcance nuevo: ≈28 % global estimado (27.50), frente a ≈36 % del corte anterior. Mismos avances técnicos; Android/asistente/Linux nuevo mantienen 0 % conservador. Explicar reducción por alcance, no regresión. Mostrar porcentaje/barra en cada respuesta de estado.


## Full HD Live aprobado; laboratorio Windows iniciado — 2026-10-17

Captura 39051320346 success en baf5918: artefacto 12107933545 descargado y nexus-iso-desktop-horizon.png inspeccionado, aurora y Horizon cubren 1920x1080 sin el negro anterior. Se valida arranque Full HD con EDID nativo; NO se valida resize dinámico. #19 integrada para conservar esta configuración de laboratorio; comprobar SHA de merge en GitHub. No cambió la ISO a6997fb. Diseño completo/accesibilidad aún pendientes, módulo Horizon mantiene 50 % conservador.

PR #20, test/windows-7zip-real-app: laboratorio Debian Trixie con Wine, instalador Windows 7-Zip 26.04 x64 oficial y SHA256 upstream d54bf805f9f3704d1e8db2fa3498ae7ef2df0312b40b558e7c71c734430a665d. Prueba instalación, ZIP con contenido verificado independientemente, reinicio Wine y ventana GUI con captura, sin privilegios. Shell local correcto; ejecución real pendiente. No equivale a instalador gráfico Nexus ni persistencia tras reboot OS. No subir Windows25/global≈28 hasta evidencias verificadas. Próximo trabajo prioritario: resultados PR #20 y primera aplicación real, después integración gráfica y APK conforme ONE-CLICK-APPLICATIONS.md.


## Primera aplicación Windows validada en laboratorio — 2026-10-17

PR #20 integrada f727d8256ae4bfbe8f0c18dbdd911b16357ec65a. Windows Application Lab 39052936193 y Fast Checks 39052939320 success para 3ce90a2. Artefacto 12107549425 descargado, logs y GUI revisados: instalador 7-Zip 26.04 x64 oficial con hash, creación ZIP por ejecutable Windows y contenido verificado, reapertura tras reiniciar Wine10 en Debian13 y GUI 7zFM visible. NO prueba en ISO, reboot de OS ni compresión mediante clics. Matriz WINDOWS-COMPATIBILITY-MATRIX.md creada.

Windows pasa25->50 como implementación parcial/laboratorio; global33.75≈34 % con mismos pesos, Android/asistente0. Próximo trabajo prioritario: asistente gráfico para una instalación Windows conocida y verificada, luego Nexus instalado y app difícil del usuario. No extrapolar 7-Zip a todo Windows. Mantener APK como prioridad alta con requisitos Wayland/Binder separados.


## Asistente gráfico Windows en desarrollo — 2026-10-17

PR #21 feat/graphical-app-installer-prototype: agent/app_installer.py y pruebas. Selección/verificación del 7-Zip26.04x64 aprobado sin ejecutar; botón de confirmación -> perfil Wine por usuario -> progreso -> Abrir. Cuatro tests locales y sintaxis correctos. WineGUI real se prueba en workflow Nexus Windows Application Lab; consultar head vigente de #21. Aún sin menú/asociación MIME ni ISO, sin preparación automática de Wine, sin APK/Linux/desinstalación/cancelación en este corte.

No anunciar flujo general con un clic terminado. Mantener global≈34, Windows50 (laboratorio), Android0 e instaladorcomún0 hasta ejecución gráfica inspeccionada. Próxima acción: resultado GUI y screenshot nexus-install-7zip.png del head #21; resolver fallos con ese laboratorio antes de empaquetar.


## Prototipo gráfico de instalación verificado — 2026-10-17

PR #21 integrada02d6bdb4672a742b0968ff5b75bdd1d535499941. GUIWineLab39053538833 success para8d3c970; FastChecks39053586940 success para cf04e70 (mismo código más docs). Artefacto12108338331 descargado; gui-assistant-result.txt confirma selección sin ejecución/prefijo, botón Instalar completado y botón Abrir produjo ventana7-Zip. Captura de app revisada, 7-Zip tapa gran parte del asistente; no presentarla como diseño completo del instalador. Es Debian/Wine/Xvfb, no ISO, ni reinicio OS.

Asistente común0->25 como prototipo limitado; global35.75≈36 %. Windows50, Android0, Linux0. Próxima implementación prioritaria: asociación del archivo y acceso gráfico con empaquetado, comprobar importación real en staging y preparar Wine gráficamente; luego desinstalación y expansión de formatos. No prometer APK/Linux soportados ni incluir cualquier EXE en la whitelist de 7-Zip. Releer ONE-CLICK-APPLICATIONS.md y app-installer-prototype.md antes de ampliar.


## Integración de archivos e imagen (2026-10-17)

Se incorpora app_installer.py al runtime preparado por image/build.sh; entrada de menú Nexus Install y asociaciones EXE para perfiles nuevos mediante mimeapps.list. Wine/wine64/fonts-wine se incluyen en la lista de paquetes. Abrir un EXE entrega su ruta al asistente; no autoriza ejecutarlo: se conserva verificación de hash y confirmación. Solo está aprobado 7-Zip26.04 x64. APK, MSI y paquetes Linux siguen pendientes. Esta integración requiere validar apertura desde Thunar y generar/probar una nueva ISO; el E2E anterior demuestra el asistente en Debian/Xvfb, no esta nueva integración en Nexus. Avance global permanece ≈36%, instalador25%, Windows50%, Android0%. Siguiente: comprobar MIME con archivo cuyo nombre tenga espacios, ausencia de ejecución al abrir y confirmación/resultado en ISO; no reconstruir repetidamente sin revisar el fallo concreto.


## Asociación EXE validada en laboratorio — 2026-10-17

PR #22, código probado5a287001204cd7ae956287874fc769b92e549cde. Windows Application Lab39062209497 aprobado: instalación CLI real, confirmación/instalación/apertura gráfica y asociación instalada mediante desktop-file-validate + xdg-mime + GIO. MIME observado application/vnd.microsoft.portable-executable. Nombre con espacios llega como argumento exacto al asistente; captura muestra paquete verificado esperando confirmación; no se crea prefijo Wine al abrir. Artefacto12111667022 descargado y revisado (file-association-result.txt y file-association.png). Fast Checks39062213140 y Native Desktop Smoke39062212953 aprobados. Primer intento39062066021 falló porque faltaba file en el contenedor mínimo para xdg-mime; se añadió esa dependencia y pasó. No se cambió la ISO para resolver un fallo del laboratorio.

Estado: asistente, entrada de menú, asociaciones para perfiles nuevos y paquetes Wine preparados para imagen. Pendiente generar/verificar la nueva ISO, interacción real con Thunar y confirmar que los paquetes Wine se resuelven en live-build. Este laboratorio NO demuestra un clic dentro de Nexus, persistencia tras reiniciar ni soporte general EXE/MSI/APK/Linux. Mantener global≈36%, Windows50%, instalador25%, Android0%. Próximo trabajo: revisar ISO Gate y validar ruta Descargas→asistente→confirmación en máquina virtual, conservando logs/capturas; después mejorar recuperación/desinstalación y ampliar aplicaciones mediante casos probados.


## Bloqueo de preflight ISO corregido — 2026-10-17

ISO Gate39062372682 no produjo ISO: verify.sh rechazó las llamadas Tk app.confirm.invoke() y app.open_button.invoke() del E2E gráfico como si fueran la API antigua del broker. No fue un fallo de Wine ni de arranque. Se sustituye grep genérico por análisis AST: solo se permiten esas dos llamadas sin argumentos en tests/windows_installer_gui_smoke.py; se siguen rechazando otras llamadas invoke e imports from secrets, incluso con espacios. Dos tests de regresión cubren seis casos. Fast Checks ejecuta ahora el mismo scanner, evitando descubrir este bloqueo recién al construir. verify.sh y los scripts del scanner disparan ISO Gate cuando cambian. Pendiente CI y nueva construcción; porcentaje global permanece≈36%.


## Prueba Windows dentro de ISO preparada — 2026-10-17

Se extiende captura QEMU para comprobar el runtime empaquetado de Nexus Install dentro del Live, con 4GB RAM, hash oficial fijado, nombre EXE con espacios, consulta MIME, selección sin prefijo, confirmación gráfica programática y apertura real7-Zip. Se conservan dos capturas adicionales del framebuffer (preparado y aplicación abierta) y marcadores seriales; se exige PASS. El probe se transfiere únicamente al invitado temporal después de las capturas Horizon; no cambia la ISO ni se instala en el producto. No representa un clic físico en Thunar ni persistencia tras reinicio. Implementación compilada; ejecución E2E pendiente de ISO Gate39064997881. No elevar porcentajes hasta revisar resultado y capturas. Global≈36%, Windows50%, instalador25%, Android0%.


## Reabrir aplicación instalada — 2026-10-17

Nexus Install guarda tras instalación exitosa un registro local mediante reemplazo atómico, con hash del instalador aprobado y del ejecutable instalado. Al abrir de nuevo reconoce ese perfil y habilita Abrir sin elegir/reinstalar EXE; abrir sigue siendo una acción explícita. Revalida el ejecutable antes de lanzarlo; registro ausente/dañado o binario modificado se rechazan. El registro es local y editable por el dueño del perfil: no es firma de proveedor ni sistema antimalware. Instalaciones previas sin registro requieren reinstalar una vez.

Seis unit tests locales aprobados (incluyen reapertura sin ejecución automática y rechazo por alteración). Se amplía Wine GUI Lab para cerrar asistente/Wine, reconstruir el servicio desde el perfil y abrir7-Zip de nuevo. E2E pendiente. No es persistencia tras reiniciar el Live. ISO791625cd sigue siendo una versión anterior a esta mejora; no atribuirle el nuevo comportamiento hasta una futura imagen. Global≈36%, instalador25%, Windows50%, Android0%.


### Resultado confirmado de reapertura

PR #25 integrada1ba09e059fb9f3492bd17fd90d4239c2be6f8082. Fast Checks39066414257 y Windows Lab39066411933 aprobados. Artefacto12113303078 descargado, resultado y captura nexus-install-reopened.png revisados: cerrar asistente y Wine, reconstruir desde registro local y abrir7-Zip sin seleccionar instalador funciona en Debian/Xvfb. Sustituye el estado E2E pendiente de la nota anterior. No demuestra reinicio del OS ni aparece en ISO791625cd. ISO Gate39064997881 sí aprobó construcción y arranque UEFI de esa imagen anterior; su captura39066298801 continúa pendiente de resultado. Global≈36%.


## Flujo Windows confirmado dentro de Nexus Live — 2026-10-17

ISO Gate39064997881 aprobado (fuente791625cd119717fa5195a51477a70c00e6a90e65). Captura39066298801 aprobada; artefacto12113313508 descargado y revisado. SHA256 ISO: eb480efef282fa109f1f5eb35d609aa77656f8b0269bff7485c444d02b544520. El asistente empaquetado verifica el instalador oficial7-Zip26.04 x64, no crea prefijo antes de confirmar, instala mediante su botón y abre ventana7-Zip real. Marcadores NEXUS_WINDOWS_ISO_PREPARED/OPEN/PASS presentes. Ocho capturas1920x1080 pasan controles de cobertura; dos capturas clave guardadas en docs/evidence/2026-10-17/.

Alcance exacto: máquina QEMU/UEFI Live descartable, confirmación del botón programática, un paquete Windows; consulta MIME aprobada. No afirmar clic físico en Thunar, persistencia tras reinicio, compatibilidad general o certificación. La reapertura del asistente implementada en PR #25 se probó aparte en Debian/Wine y es posterior a esta ISO.

Avance: instalador común25→50 por componentes integrados y flujo parcial validado en ISO, junto con MIME y reapertura probados en laboratorio. Sigue sin APK/Linux, desinstalación o aceptación completa; no corresponde75%. Windows permanece50 por amplitud del módulo. Peso8 añade2 puntos:35.75→37.75≈38% global. Siguiente entrega funcional: acceso a la aplicación instalada desde el menú, manejo de desinstalación y ampliar matriz Windows; priorizar Android y Linux después de estabilizar este flujo.


## Acceso a 7-Zip desde el menú — 2026-10-17

Tras instalar correctamente, Nexus Install registra atómicamente nexus-7zip.desktop en el directorio de aplicaciones del usuario (XDG_DATA_HOME absoluto o ~/.local/share). Exec fijo llama al runtime empaquetado con --open-installed: vuelve a verificar instalación y lanza7-Zip directamente. Si no puede abrir, muestra el error en el asistente; no se añaden nombres de archivos descargados al comando. El registro no ejecuta nada. Ocho unit tests locales aprobados; se amplía Wine Lab para validar .desktop, cerrar asistente/Wine y abrir desde GIO con ventana7-Zip real. CI pendiente; no equivale a clic físico en el menú de XFCE ni está incluido en ISO791625cd. Global≈38%, instalador50%, Windows50%, APK0%. Siguiente: revisar laboratorio, integrar y agrupar próxima ISO con cambios funcionales para evitar reconstrucciones por cada ajuste.


### Resultado confirmado del acceso de aplicación

PR #26 integrada652059f6c14eae6b52c72f9817a6b834a6ba6030. Fast Checks39067681676 y Windows Lab39067679141 aprobados. Artefacto12113773411 descargado, menu-launch-result.txt y 7zip-menu-launch.png revisados: acceso .desktop válido abre7-Zip directamente después de cerrar asistente/Wine, sin ventana del instalador. Sustituye el estado CI pendiente anterior. Verificación en Debian/Xvfb mediante GIO; sigue pendiente el clic físico en menúXFCE y nueva ISO con PR #25/#26. No reconstruir la imagen por documentación: agrupar próxima entrega funcional. Global≈38%, Windows50%, instalador50%, Android0%.


## Segunda aplicación Windows: Notepad++ — 2026-10-17

Se añade laboratorio real para Notepad++8.9.8.1 x64, instalador de https://github.com/notepad-plus-plus/notepad-plus-plus/releases/tag/v8.9.8.1 con SHA25626f3bcced788fadbac4e7e577b430ea2ce6060cf3bcad993ef4612ecd7d743da (digest del asset oficial). Manual primario https://github.com/notepad-plus-plus/npp-usermanual/blob/master/content/docs/command-prompt.md: /S y /noUpdater documentados. El probe instala sin root en prefijo descartable, abre un archivo cuyo nombre tiene espacios, enfoca la ventana real, escribe con teclado y guarda; verifica bytes del archivo y conserva captura/logs. CI pendiente. No añadir Notepad++ al catálogo gráfico aprobado ni afirmar soporte dentro de ISO hasta validar e implementar su adaptador. Global≈38%, Windows50%.


### Notepad++ confirmado en laboratorio

PR #27 integrada170cfd9e2515cd388c50efa72b2782b5b56f2de1. Windows Lab39068787928 y Fast Checks39068790547 aprobados. Artefacto12114811229 descargado y revisado: Notepad++8.9.8.1 x64 instalado, archivo Nexus sample.txt abierto, texto escrito por teclado y guardado con Ctrl+S; contenido exacto verificado. Captura y muestra guardadas en docs/evidence/2026-10-17/notepad-edit-save.png y notepad-saved-sample.txt.

Primer intento39068603099 falló con syswow64/ntdll.dll ausentes: el laboratorio solo tenía Wine64. Se habilitó i386 y wine32:i386 junto a Wine64 según README Debian Wine10; se repitieron7-Zip/asistente/reapertura/menú/MIME y también aprobaron. La configuración mixta está probada en laboratorio, aún no en imagen. Manual primario: https://sources.debian.org/src/wine/10.0~repack-6/debian/README.debian .

Siguiente prioridad concreta: integrar segundo paquete en Nexus Install (identificación por hash y perfil separado) y preparar motor mixto automáticamente en próxima ISO, con prueba de ambos. No marcar Notepad++ como instalable desde asistente actual: solo7-Zip está integrado. No demuestra plugins, impresión, actualizaciones, hardware o persistencia. Global≈38%, Windows50%, instalador50%, APK0%.


## Catálogo gráfico de dos aplicaciones y siguiente ISO — 2026-10-17

Nexus Install reconoce por hash7-Zip26.04 x64 y Notepad++8.9.8.1 x64 sin confiar en el nombre del archivo. Elige perfil, binario, argumentos y entrada de menú propios; --application permite abrir el programa correcto. Registro local de instalación y nueva verificación del binario siguen activos. El selector bloquea Abrir mientras se identifica el paquete, y cancelar/cerrar el asistente limpia su temporizador Tk. Diez unit tests locales aprobados, incluidos perfiles separados, selección sin ejecución y acceso específico Notepad++.

Se amplía Wine GUI Lab para instalar Notepad++ desde el propio asistente y abrirlo desde su acceso sin alterar registro7-Zip. CI pendiente. Se prepara hook chroot030 para habilitar i386 y wine32:i386 al construir la ISO (sin comandos del usuario). Se amplía prueba Live a ambos programas y acciones de menú, con10 capturas y6GBRAM de laboratorio. Captura automática solo después de ISO Gate exitoso; ejecución manual exige id/SHA del candidato exacto para evitar intentar una imagen antigua.

Fuentes: manual Debian Live de hooks https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-contents.en y README Debian Wine10 https://sources.debian.org/src/wine/10.0~repack-6/debian/README.debian . Pendiente revisar GUI lab, integrar, construir una sola nueva ISO y revisar capturas/markers. ISO791625cd anterior solo acredita7-Zip y no incluye este catálogo ni runtime mixto. Global≈38%, Windows50%, instalador50%, APK0%; no elevar por código pendiente de validación.


### Integración gráfica de Notepad++ validada

PR #28 integrada4b3565acff56842f1f51f369125507b858379d47. Fast Checks39073201045 aprobó6jobs; Wine Lab39073199395 aprobó instalación gráfica, Abrir y acceso de menú para ambos programas, registro7-Zip sin cambios, MIME y edición/guardadoNotepad++. Artefacto12115259388 descargado, notepad-assistant-result.txt y captura nexus-notepad-install.png revisados. Sustituye CI pendiente de la nota anterior. Nueva ISO Gate39073455863 iniciada con runtime mixto y catálogo de ambos programas; aún pendiente construcción/captura Live. La ISO anterior no acredita estos cambios. Global≈38%.


## Ciclo de instalación y retirada recuperable — 2026-10-17

La ISO Gate39073455863 construyó y arrancó fuente4b3565ac, pero la captura39074859209 falló: primer7-Zip no terminó dentro de180s. Artefacto12116758671 y serial revisados: NEXUS_WINDOWS_ISO_PREPARED presente; excepción de tiempo al ejecutar Wine/setup /S; no se alcanzó OPEN ni Notepad++. No declarar ambos programas validados en esa imagen. La causa exacta no quedó aislada porque el primer arranque de Wine se mezclaba con instalación y no se exportaba install.log.

Se separa wineboot --init (300s, después de confirmar) de ejecución del paquete (180s), con registro por fases y marca wine-ready solo tras inicialización exitosa; perfiles incompletos vuelven a inicializarse. Probe Live espera presupuesto combinado, exporta install.log y captura fallo al detectar salida no cero sin esperar marcadores ausentes. Nueva imagen agrupa estos cambios y dependencia explícita libglib2.0-bin; no atribuir aún solución probada al Live.

Se añade Desinstalar con confirmación (No predeterminado). Espera cierre del wineserver del perfil y rechaza si sigue activo; no mata la aplicación. Retira acceso Nexus y mueve perfil completo a papelera GIO. Conserva acceso dentro del perfil movido; restaura el acceso original si falla el traslado. Bloqueo de operación fuera del perfil evita dejar un lock al restaurarlo de papelera. No borra permanentemente ni purga cachés de otras aplicaciones. Se desactiva winemenubuilder para que nuevas instalaciones no creen accesos paralelos fuera de Nexus. Restaurar archivos desde papelera no implica restablecer automáticamente todos los accesos.

Quince pruebas locales aprobadas: preparación previa, fallo de inicialización no ejecuta paquete, cancelación/rechazo de operación activa cubiertos en GUI lab propuesto, fallo papelera restaura menú y otro perfil intacto. E2E de retirada y nueva ISO pendientes. Global≈38%, Windows50%, instalador50%, APK0%.


### Retirada a papelera confirmada en laboratorio

PR #29 integradafad9f10eafc99d531b72bd656bf48b1b5d97424d. Fast Checks39076129040, Native Desktop39076128989 y Wine Lab39076124206 aprobados. Artefacto12117470710 descargado, notepad-remove-result.txt y notepad-removed.png revisados: No conserva instalación; aplicación activa rechaza retirada; tras cerrar, perfil verificable aparece en papelera real y acceso Nexus desaparece; registro7-Zip sin cambios. También pasan instalación, menú, MIME y edición/guardado. Nueva preparación explícita Wine validada en laboratorio; comportamiento lento Live aún pendiente.

Nueva ISO Gate39076397453 iniciada (fuente fad9f10e). Captura posterior debe demostrar ambos programas dentro del Live; si falla, revisar NEXUS_WINE_INIT_BEGIN/END, NEXUS_PACKAGE_INSTALL_BEGIN y log exportado antes de proponer otra corrección. No declarar arreglada la captura39074859209 solo por aumentar presupuestos. Global≈38%.


## Live de dos aplicaciones: diagnóstico del 17/10

Captura39077637721 (ISO Gate39076397453, fuente fad9f10e) falló, artefacto12118320662 descargado e inspeccionado.7-Zip alcanza PREPARED, OPEN y MENU_PASS en esta ISO mixta. Notepad++ completa wineboot y setup sin error, registra instalación, pero no aparece su título en xwininfo12s después de abrir. No es el timeout de instalación anterior ni demuestra todavía fallo permanente del programa.

Se propone esperar ventana real hasta120s en lugar de dormir12s: error temprano si proceso sale no cero, y diagnóstico de procesos/ventanas si vence el límite. Se conserva el clic del botón y la misma ruta launch del asistente. Misma comprobación para apertura desde menú. Tres verificaciones locales del helper aprobadas (ventana tardía, salida7, timeout con diagnóstico). Falta ejecutar de nuevo en la misma ISO; no reconstruir imagen solo por cambio del probe. Global≈38% sin incremento.
