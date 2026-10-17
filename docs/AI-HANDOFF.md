# Nexus OS — relevo para cualquier IA

Actualizado: 2026-10-17 (Bogotá).

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
