# Nexus OS — avance global estimado

Corte vigente: 2026-10-17. Método de seguimiento solicitado por el usuario. **Estimación de gestión, no porcentaje de código, certificación ni probabilidad de terminar.** Sustituye el formato solo por colores; no convierte el antiguo 70 % en dato válido.

## Cálculo y criterios

Cada módulo tiene peso según su relevancia/esfuerzo previsto. Los pesos son una decisión de planificación inicial, no mediciones de horas. Suman 100. Avance global = suma(peso × avance del módulo) / 100. Redondear el resultado solo al mostrarlo: 35.75 % -> aproximadamente 36 %.

Escala de cinco etapas para evitar falsa precisión: 0 % = pendiente; 25 % = alcance/investigación/diseño concreto, con posibles piezas preliminares; 50 % = implementación parcial y pruebas de componentes; 75 % = flujo principal validado en el sistema objetivo, faltando aceptación completa; 100 % = criterios del módulo satisfechos con evidencia. Para módulos amplios, no ascender por un único componente aprobado. El porcentaje es aproximado y revisable.

| Módulo | Peso | Avance estimado | Motivo / siguiente requisito |
| --- | ---: | ---: | --- |
| Base Linux y arranque Live | 7 | 100 % | ISO, checksum y UEFI Live comprobados. Hardware e instalación pertenecen a otros módulos. |
| Escritorio Horizon y diseño | 8 | 50 % | Lanzador, atajo y aurora visibles; cobertura, diseño completo y accesibilidad pendientes. |
| IA por texto y proveedores | 6 | 50 % | Proveedor/CLI con modelo real fuera ISO; flujo completo dentro del OS pendiente. |
| Voz | 2 | 0 % | Sin reconocimiento y síntesis E2E probados. |
| Acciones de IA en el sistema | 4 | 25 % | Broker/permisos y piezas preliminares; automatización visible y verificable pendiente. |
| Instalador y persistencia | 12 | 25 % | Plan, preflight y preview; instalación ejecutada y arranque sin ISO pendientes. |
| Aplicaciones Windows | 25 | 50 % | 7-Zip Windows x64 instalado y usado en laboratorio Debian/Wine; asistente Nexus, más apps y persistencia OS pendientes. |
| Aplicaciones Android/APK | 15 | 0 % | Prioridad alta; runtime e integración gráfica todavía no probados. |
| Asistente de instalación con un clic | 8 | 25 % | Prototipo gráfico 7-Zip probado con Wine; asociación Descargas, preparación del motor, desinstalación y otros formatos pendientes. |
| Paquetes y aplicaciones Linux | 3 | 0 % | Integración gráfica .deb/Flatpak/AppImage pendiente de aceptación. |
| Compatibilidad macOS | 1 | 0 % | Alcance futuro independiente de Android. |
| Actualizaciones y recuperación | 4 | 50 % | Modelos y simulaciones probadas; actualización/rollback instalado pendientes. |
| Televisión | 1 | 25 % | Arquitectura y paquetes investigados; sin reproducción real Nexus validada. |
| Radio | 1 | 25 % | Investigación y plan guardados; sin reproducción implementada/probada. |
| Seguridad, hardware y entrega | 3 | 25 % | Endurecimiento preliminar; aceptación conjunta, matriz hardware y release pendientes. |

## Resultado vigente — Windows, Android e instalación gráfica

**Avance global estimado: 35.75 %, mostrado como aproximadamente 36 %.** No afirmar que el 36 % de las funciones está terminado: el cálculo acredita también etapas de diseño e implementación parcial según la escala anterior.

## Actualización

- Consultar PROJECT-CONTINUITY.md y evidencia de cada módulo antes de subir porcentajes. Registrar módulo, valor anterior/nuevo, motivo, SHA/run y fecha.
- Nueva función solicitada: añadir fila con alcance y avance real, asignar/rebalancear pesos y conservar el corte previo. El global puede bajar al ampliar alcance, sin significar pérdida del trabajo realizado.
- Si aparece un fallo que invalida aceptación, bajar la etapa y explicar por qué. No subir el global por abrir una PR, esperar CI o producir documentación repetida.
- En respuestas de estado mostrar barra y porcentaje global aproximado, más los módulos que cambiaron. Mostrar tabla completa cuando el usuario la pida o cambie el alcance.
- No incluir puertas piratas o evasión de DRM en el alcance; TV/radio se refieren a fuentes autorizadas.

Ejemplo de presentación: Avance global estimado ≈36 %; completado para release todavía no. Barra gráfica de diez segmentos es solo representación redondeada del cálculo.


## Reponderación solicitada: Windows primero

El corte inicial del 17/10 daba 40.75 % (≈41 %) con Windows al 10 % del peso. El usuario confirmó que Windows es objetivo central: ahora pesa 30 %, instalación 15 % y medios 4 % combinados. Mismos avances por módulo; resultado 35.75 % (≈36 %). La diferencia es cambio de prioridades/pesos, no pérdida de código ni una regresión. No subir el módulo Windows por esta reorganización: sigue 25 % estimado de diseño, sin aplicaciones reales acreditadas. Plan operativo: [WINDOWS-FIRST-ROADMAP.md](WINDOWS-FIRST-ROADMAP.md).


## Ampliación vigente: Android y abrir/instalar sin terminal

Usuario confirma APK, Windows y Linux con asistente gráfico como prioridad central. Android se separa de macOS y se añaden instalador común y formatos Linux. Nuevos módulos mantienen 0 % conservador hasta integración verificable. Pesos actuales suman 100 y dan 27.50 % -> ≈28 %. Corte previo Windows-first: 35.75 % -> ≈36 %. La baja es ampliación/reponderación de alcance; no hubo pérdida de trabajo ni avance técnico causado por documentación. Plan: ONE-CLICK-APPLICATIONS.md. Windows25+Android15+asistente8+Linux3 suman 51 % del peso; instalación del OS añade 12 %.


## Incremento verificado: primera aplicación Windows real

2026-10-17: Windows25 -> Windows50 en la escala de implementación parcial/laboratorio. Run 39052936193 y artefacto 12107549425 inspeccionados; PR #20 integrada f727d825. 7-Zip Windows 26.04 x64 instala, crea ZIP correcto, reabre tras reinicio Wine y muestra GUI en Debian 13. Pendientes integración Nexus/ISO, reboot instalado y aplicaciones difíciles. Con peso25, contribución aumenta 6.25 puntos: global27.50 ->33.75 (≈34 %). No significa 50 % del catálogo Windows compatible. Ver WINDOWS-COMPATIBILITY-MATRIX.md.


## Incremento verificado: asistente gráfico limitado

2026-10-17: instalador común0->25 por primer prototipo restringido con prueba real de selección sin ejecución, confirmación, instalación y apertura. Run39053538833, artefacto12108338331 revisado; Fast Checks39053586940 aprobado. No equivale al flujo completo APK/EXE/Linux ni integración en ISO. Con peso8 añade2 puntos:33.75->35.75≈36 %. Windows sigue50; Android y paquetes Linux0. No confundir este ≈36 % con un corte antiguo que tenía otros pesos.
