# Nexus OS — relevo para cualquier IA

Actualizado: 2026-10-17 (Bogotá).

## Corte prioritario — 2026-10-17, 20:35 Bogotá

Esta sección sustituye los estados antiguos que aparecen más abajo. Global ponderado37.75≈38%; Windows50%, asistente50%, APK0%. No elevar por CI o documentación.

- Prioridad central: aplicaciones Windows y después APK/Linux, instalación gráfica sin terminal; no reabrir el diagnóstico Horizon ya acreditado salvo regresión.
- Main incluye PR #29 (fad9f10e): dos EXE oficiales por hash, perfiles separados, selección sin ejecución, confirmación, recibo/verificación, menú y retirada recuperable. Laboratorio Debian/Wine acredita ambos programas, edición/guardado Notepad++, MIME y ciclo de retirada. No confundir con instalación persistente del OS.
- ISO Gate39076397453 aprobó build y arranque UEFI de fad9f10e. Captura39077637721 acredita7-Zip; Notepad++ instaló pero la prueba de apertura fija12s fue insuficiente.
- PR #30 abierta: https://github.com/CmdOS-system/Nexus-os/pull/30 . Run39078885829 con espera de ventana acredita apertura y menú de ambos, pero falla visualmente: editorNotepad++ negro. Artefacto12118387302 inspeccionado.
- Ensayo GDI en perfil descartable39079632096 salió verde; revisión del artefacto12118184503 detectó que notepad-open.png NO muestra la aplicación. NO considerar arreglado el editor ni incorporar ese ajuste al instalador aún.
- Siguiente ejecución concreta39087177796 usa la misma ISO e incorpora sincronización por ACK: no cerrar escena hasta que QMP guardePNG. Revisar resultado, serial y capturaNotepad++ de esta ejecución antes de repetir, modificar runtime o reconstruir.
- Si la imagen demuestra GDI correcto, implementar ajuste automático en adaptadorNotepad++ con pruebas que preserven configuración y perfil7-Zip; validar laboratorio, integrar y construir una solaISO para probar adaptador empaquetado sin parche del probe. Si sigue negra, investigar dibujo antes de aceptar.
- Pendientes principales después de Windows básico: instalaciónUEFI en QCOW2 y arranque sinISO/persistencia; Androidruntime+APK (Wayland/binder/GPU); Linuxformatos; IAenISO. TV/radio solo fuentesautorizadas, investigación25% sinreproductoraceptado.

## Prioridad funcional vigente — 2026-10-17, 21:44 Bogotá

El usuario exige demostrar instalación y uso de **Microsoft Word/Office de escritorio**.7-Zip/Notepad++ solo son pruebas básicas; no dar por aceptada compatibilidadWindows con esos dos programas. Leer [OFFICE-DESKTOP-ACCEPTANCE.md](OFFICE-DESKTOP-ACCEPTANCE.md): siete requisitos aún pendientes enNexus. Primer intento real de instalación/tareaWord en DebianWine: https://github.com/CmdOS-system/Nexus-os/actions/runs/39091083886 (consultar resultado, no asumir éxito). Código en PR #32, https://github.com/CmdOS-system/Nexus-os/pull/32 ; instalador oficialODT16.0.20326.20112 fijado porhash. No añadirOffice al catálogo aprobado hasta aceptación. SiWinefalla, registrarcausa y evaluarCrossOverporversión oWindowsVM/RemoteApp sin confundirbackends.

BloqueoNotepad++: captura sincronizada39087177796 y artefacto12121412527 inspeccionados; editor visiblecorrecto con ensayoGDI0, apertura/menú de ambos programas. PR #30 integrada7c804462. PR #31 implementa GDI automático en instalador;19unitarias, Fast Checks39090854682 y WineLab39090852630 aprobados; artefacto12122523119 inspeccionado. Falta nuevaISO con adaptador empaquetado; capturaPR39090854665 todavía usa fixtureantigua. No confundir ensayoGDI delprobe conISOactualizada. Global37.75≈38%, Windows50/asistente50/APK0.

## Entrada única y alcance

Repositorio: https://github.com/CmdOS-system/Nexus-os

Leer primero este documento y docs/PROJECT-CONTINUITY.md. El segundo conserva el registro cronológico: sus estados antiguos pueden estar sustituidos por notas posteriores. docs/PROJECT-HISTORY.md conserva el inventario histórico de 445 commits al corte indicado; no representa el total actual ni una auditoría completa. Usar git log para cambios posteriores. Este relevo consolida el contenido disponible del repositorio y los chats recuperados; no garantiza que se hayan recuperado todas las conversaciones o instrucciones privadas de ChatGPT.

## Visión y decisiones vigentes

Distribución Linux propia, fácil de instalar y usar, escritorio Horizon cuidado, IA integrada por texto/voz y acciones visibles, compatibilidad práctica con aplicaciones Windows. Base documentada: Debian 13/live-build, XFCE y LightDM. Inspiración en Apple/macOS y otras interfaces con identidad propia: aurora, profundidad moderada, dock flotante, nitidez, fluidez e IA discreta. Integrar Wine/Proton/Bottles y componentes existentes. Separar Nexus Update, Recovery y Boot Manager. Compatibilidad universal y juegos PS5 desde disco no están demostrados.

## Trabajo realizado y alcance de la evidencia

| Área | Realizado / referencia | Límite pendiente |
| --- | --- | --- |
| Historial y continuidad | PROJECT-HISTORY.md, PROJECT-CONTINUITY.md y build-and-test.md | Revalidar main y Actions en cada sesión |
| Live | ISO 98e23179, ISO Gate 38978527786 aprobado; escritorio XFCE visible en captura 38980833818 | No prueba instalación persistente ni hardware |
| IA real | PR #4 integrada; run 38978824081, Ollama qwen2.5:0.5b respondió por proveedor y CLI con modelo guardado | Fuera de la ISO; voz/acciones y GUI E2E pendientes |
| Seguridad | PR #2 consentimiento booleano y lectura acotada ligada al archivo; PR #3 selección guardada integradas | Auditoría completa y revisión residual PR #1 pendientes |
| Diagnóstico gráfico | PR #5 y #6 integradas; capturas QMP, esperas y diagnóstico tras XFCE | Captura no negra no demuestra interacción correcta |
| Atajo Horizon | PR #8 integrada 55b3100; prueba con xfsettingsd reprodujo fallo y validó corrección | Probar en la nueva ISO |
| Rediseño Horizon | PR #9 integrada a2582a2: SVG aurora 4K, Arc-Dark, Papirus-Dark, Inter, tarjetas, búsqueda, teclado y permisos ejecutables | Captura Xvfb del componente; conjunto Live nuevo pendiente |
| Captura ampliada | PR #7 confirmada integrada c5c05a6 en consulta de este relevo: cinco imágenes, 1920x1080 y captura tras ISO Gate main exitoso | Run anterior usó ISO antigua con wrapper 0644; no valida rediseño |
| Instalador | Inventario, preflight, planificador e interfaz de solo lectura | Ejecutor e instalación real no acreditados |
| Recuperación | Modelos A/B, metadatos y simulaciones | Rollback instalado y cadena de confianza pendientes |
| Compatibilidad | Inspección PE y arquitectura; investigación Bottles, REA, Chromium y PS5 | No hay ejecución Windows ni juego PS5 demostrados |

## Estado vigente — 2026-10-17, 11:37 Bogotá

Este corte sustituye los pendientes antiguos de la tabla anterior:
- Live Horizon y Super+Espacio confirmados visualmente en captura QEMU 39041523768; no repetir diagnóstico de permisos/atajo ya resuelto sin nueva regresión.
- ISO Gate 39048872619 success para a6997fb5356e71e70242fe71e545ab1c8d510b78, con recuperación de rutas del fondo (#16). Captura automática 39049935491 todavía en ejecución al corte; consultar su resultado y artefacto antes de cambiar runtime o reconstruir.
- Captura anterior 39043287407 mostraba XFCE parcial/negro, por lo que #13 no bastó. #16 crea claves por workspace desde GDK/EWMH si faltan. No declarar el fondo Live arreglado sin nuevas imágenes.
- #11 y #14 integradas: seis imágenes, probe de ejecución independiente, sincronización con diagnóstico y rechazo de regiones negras. Un fallo del control de cobertura sobre el candidato viejo es esperado.
- #17 integrada b720aba: preflight Debian Trixie/xfdesktop 4.20.1 antes del build, no Ubuntu. Run 39049627191 y Fast Checks 39049627176 success; artefacto 12107346535 inspeccionado. Aurora coincide en 100 % de muestras y se ve completa en sesión Debian/Xvfb. Es contenedor como root, no LightDM/ISO.
- Consultar docs/desktop-validation-strategy.md. Antes de reconstruir, reproducir causa en la capa correspondiente y usar el mismo candidato cuando no cambie runtime. No sustituir calidad visual con claves xfconf, mocks o marcadores de servicios.

## Pendientes ordenados y criterios de aceptación

1. **P0: escritorio nuevo dentro de ISO.** Consultar primero captura 39049935491 del candidato aprobado en ISO Gate 39048872619; si ya terminó, inspeccionar sus artefactos antes de otras acciones; identificar SHA candidato, checksum y artefacto exactos. Descargar y revisar capturas automáticas. Confirmar fondo, tema, iconos, Inter, permisos ejecutables, Super+Espacio y lanzamiento directo. Probar búsqueda, selección, apertura/cierre y Control Center. Guardar imágenes y logs asociados al SHA. Si falla, reproducir y corregir la causa antes de ampliar diseño.
2. **P1: pulido Horizon.** Dock flotante y superficies/translucidez moderadas compatibles con la pila elegida; escalas 100/150/200 %, pantallas pequeñas, teclado, contraste, rendimiento y reducción de movimiento. Aceptar mediante capturas del sistema real y pruebas de interacción, no solo mockups.
3. **P1: instalación y persistencia.** Revisar INSTALLER-ARCHITECTURE.md y release-gates.md; implementar y probar exclusivamente con QCOW2 desechable. Instalar, apagar, retirar ISO, arrancar por UEFI desde disco, crear datos, reiniciar y demostrar persistencia. Registrar particiones, logs y checksum. No tocar discos físicos o EFI del host.
4. **P1: IA en sistema.** Repetir proveedor/CLI real dentro de ISO o sistema instalado; configurar modelo guardado, verificar privacidad y errores. Después conversación gráfica, voz, cancelación y acciones autorizadas con auditoría. No guardar claves en git/logs.
5. **P2: Windows.** Elegir aplicaciones objetivo y registrar versión, Wine/Proton, arquitectura, dependencias, instalación, apertura, función útil y resultado reproducible. No confundir lectura de PE con ejecución.
6. **P2: actualización y recuperación.** Ensayar actualización fallida, pérdida de energía simulada, rollback y recuperación persistente; validar Secure Boot/dm-verity por separado si se incorporan.
7. **P2: hardware y release.** Red, audio, gráficos, suspensión, accesibilidad, instalador y matriz de hardware según release-gates.md. No afirmar certificación antes de cumplir sus criterios.
8. **Investigación sin promesa de entrega.** REA, Chromium y PS5: revisar fuentes, licencias y viabilidad. Análisis estático KytyPS5 está en docs/research/ps5-source-trace-2026-10-16.md; no se ha compilado ni ejecutado un juego según el registro disponible.

## Protocolo de cada sesión

- Leer AGENTS.md si existe; inspeccionar git status, main, ramas/PR abiertas y Actions actuales. No sobrescribir cambios ajenos ni reiniciar trabajo ya validado.
- Leer docs/build-and-test.md, docs/release-gates.md, docs/INSTALLER-ARCHITECTURE.md y docs/NEXUS-HORIZON-DESIGN.md antes de modificar su área. Usar comandos reales del repo, sin inventarlos.
- Trabajar autónomamente en el siguiente bloqueo verificable; pedir al usuario solo datos o acceso imprescindibles. Si no hay herramientas/acceso, explicar el límite y entregar parche o instrucciones comprobables.
- Diferenciar diseñado, implementado, integrado, probado en componente, probado en Live e instalado. Registrar SHA, entorno, comando, resultado y enlace/artefacto por validación.
- Conservar evidencia duradera en git/Actions; los artefactos Actions pueden expirar. No depender de rutas scratch de chats antiguos. Guardar capturas útiles de tamaño razonable o una referencia durable con hash; no subir ISOs enormes al historial git.
- Actualizar PROJECT-CONTINUITY.md y este relevo cuando cambie el estado, con siguiente acción concreta. Conservar antecedentes y señalar qué resultado sustituye a cuál.
- Comunicar en español cambios, pruebas, bloqueos y progreso global por hitos. No reutilizar el 70 % histórico ni inventar porcentajes. No prometer trabajo en segundo plano sin una ejecución real.

## Prompt portátil

Copia este bloque en la IA que vaya a continuar:

```text
Actúa como responsable técnico de Nexus OS y continúa su desarrollo de forma autónoma.

1. CONÉCTATE al repositorio https://github.com/CmdOS-system/Nexus-os usando la integración GitHub disponible o git. Comprueba acceso de lectura y permisos de escritura. Si no tienes acceso, solicita únicamente la conexión necesaria; no afirmes haberte conectado. Nunca pidas que pegue tokens o contraseñas en el chat.

2. ANALIZA el proyecto antes de modificarlo. Lee las instrucciones AGENTS.md aplicables, docs/AI-HANDOFF.md, docs/PROJECT-CONTINUITY.md, docs/PROJECT-HISTORY.md, docs/build-and-test.md y docs/release-gates.md. Inspecciona la estructura y el código relevante, git status, main remoto, historial de commits, ramas, PR abiertas y ejecuciones de GitHub Actions. Identifica cambios locales ajenos antes de actualizar el checkout y consérvalos. Contrasta los documentos con el código y la evidencia actual; las notas antiguas pueden estar sustituidas por posteriores. No declares una auditoría completa si solo hiciste una revisión selectiva.

3. Determina qué está implementado, integrado, probado y pendiente. Resume brevemente el diagnóstico, el bloqueo principal y la siguiente acción; después EJECUTA el trabajo, sin detenerte en un plan ni pedir confirmaciones rutinarias.

4. Continúa desde el avance existente. El objetivo es una distribución Linux fácil de instalar y usar, con escritorio Horizon pulido e identidad propia, IA integrada y compatibilidad práctica Windows. Sigue el backlog y las decisiones documentadas. Primero comprueba si la nueva ISO del rediseño y Horizon ya están validados; si lo están, pasa al siguiente pendiente. No reinicies componentes ni repitas pruebas sin motivo.

5. IMPLEMENTA, PRUEBA Y GUARDA los cambios. Usa ramas y commits claros, publica los avances en el repositorio y crea o actualiza la PR correspondiente siguiendo sus reglas. Comprueba los resultados de CI del SHA exacto. No confundas crear una PR con integrarla ni un workflow iniciado con una prueba aprobada. Respeta las protecciones de ramas y los permisos disponibles.

6. Registra evidencias: SHA, entorno, comando o procedimiento, resultado y enlace a logs/capturas/artefactos. Distingue propuestas, pruebas de componentes, ISO Live e instalación persistente. Usa discos virtuales desechables para instalaciones; protege datos y secretos. No prometas compatibilidad universal, juegos PS5 desde disco ni certificación sin pruebas.

7. Antes de terminar cada sesión, ACTUALIZA docs/PROJECT-CONTINUITY.md y docs/AI-HANDOFF.md con lo realizado, pruebas, fallos, pendientes, bloqueos y siguiente acción exacta. Conserva el historial y señala qué estados quedan sustituidos. Si falta acceso, continúa lo que sea independiente y explica con precisión qué no pudiste verificar o guardar.

Comunícate en español. Muestra avances reales y progreso global por hitos verificables, sin porcentajes inventados. No afirmes que seguirás trabajando en segundo plano si no existe una ejecución real.
```


## Prioridad central ratificada: aplicaciones Windows — 2026-10-17

Leer docs/WINDOWS-FIRST-ROADMAP.md antes de elegir la siguiente tarea. El usuario confirma Windows como objetivo central de Nexus; no retrasar el laboratorio Wine esperando acabados estéticos, TV/radio o voz. Trabajar instalación/persistencia como habilitador. Orden: laboratorio Debian/Wine -> aplicación real sencilla -> aplicación difícil del usuario con tarea útil -> asistente Nexus/prefijos -> prueba persistente en VM -> ampliar matriz. Investigación/ingeniería inversa para interoperabilidad con permisos, fuentes primarias y componentes abiertos; no prometer universalidad.

Nueva ponderación PROJECT-PROGRESS.md: Windows 30 %, instalación 15 %; global estimado 35.75 % -> ≈36 %, frente al ≈41 % histórico por distinta ponderación. Avances de módulo no cambiaron. Windows sigue 25 % de diseño/piezas preliminares, sin una aplicación real acreditada. Siguiente incremento exige ejecución comprobada. Captura Full HD sigue como tarea acotada de escritorio; no consumir todo el proyecto en pulido visual.


## Prioridad central ampliada: APK/Windows/Linux sin terminal — 2026-10-17

Usuario exige descargar, abrir archivo y usar asistente gráfico para instalar apps Android APK, Windows exe/msi y Linux, sin introducir comandos. Leer docs/ONE-CLICK-APPLICATIONS.md: router/adaptadores, preparación gráfica de runtimes, progreso, permisos, acceso Horizon y desinstalación. No ejecutar al descargar; clic abre asistente y confirmaciones necesarias. No prometer compatibilidad de cualquier APK/EXE ni todos los formatos Linux.

Android ahora prioridad alta separada de macOS. Waydroid candidato, no integrado: necesita resolver Wayland frente al XFCE/X11 actual, Binder/GPU y ABI ARM/x86_64. Investigar código abierto/interoperabilidad; no copiar emuladores propietarios ni eludir controles. Windows sigue central; TV/radio y pulido avanzado secundarios. Trabajo siguiente: laboratorio Windows real y requisitos Android antes de empaquetado.

PROJECT-PROGRESS.md reponderado por alcance nuevo: ≈28 % global estimado (27.50), frente a ≈36 % del corte anterior. Mismos avances técnicos; Android/asistente/Linux nuevo mantienen 0 % conservador. Explicar reducción por alcance, no regresión. Mostrar porcentaje/barra en cada respuesta de estado.


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
