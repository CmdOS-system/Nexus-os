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
