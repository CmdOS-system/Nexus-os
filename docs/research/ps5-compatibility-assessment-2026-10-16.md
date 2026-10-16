# PS5 en Nexus OS — evaluación inicial

Fecha: 2026-10-16. Investigación documental; no se compiló ni ejecutó un juego de PS5 en Nexus.

## Objetivo del usuario

Explorar ingeniería inversa e integración para ejecutar juegos PS5 en Nexus con una experiencia sencilla, idealmente insertar disco y jugar.

## Hallazgo principal

Existe una línea concreta que merece evaluación: KytyPS5/KytyPS5 se describe como una capa de traducción PS5 para Windows/Linux y macOS experimental. Su README declara arranque de juegos 2D/3D y remite a resultados comunitarios. Son afirmaciones del proyecto, no pruebas realizadas en Nexus. Su interfaz documentada recibe carpetas de juego, ELF o dumps ZArchive; no documenta ejecución directa desde un disco comercial insertado en un PC.

El Kyty original sólo declara juegos PS4 sencillos y homebrew PS5, con funciones incompletas. No confundir ambos estados ni usar capturas de terceros como validación propia. shadPS4 es PS4, no PS5.

## Qué estudiar y aprovechar

1. Capa de llamadas/servicios del entorno huésped: reproducir comportamiento compatible con el sistema anfitrión requiere más que compartir arquitectura de CPU.
2. Traducción gráfica: KytyPS5 documenta decodificación de instrucciones, representación intermedia, recompilación de shaders y emisión SPIR-V; backend Vulkan y gestión de recursos. Usar su referencia RDNA 2 y documentación Vulkan para análisis de compatibilidad.
3. Memoria y sincronización: revisar pruebas enfocadas antes de introducir cambios, con resultados por juego/build.
4. Integración Nexus: un adaptador que invoque un ejecutable seleccionado con argumentos fijos, biblioteca de juegos y diagnóstico Vulkan. Mantenerlo como componente experimental separado de la base estable.
5. Licencias: KytyPS5 declara GPL-2.0-only; conservar avisos y cumplir condiciones aplicables si se distribuye o modifica. No copiar componentes propietarios de Sony como si fueran código abierto.

## Disco físico

Los discos PS5 no son CDs. La documentación Sony describe soporte Blu-ray y limita su unidad PS5 extraíble a modelos de consola específicos; requiere emparejamiento durante configuración. Leer un medio óptico y ejecutar su juego son problemas distintos. Una lectora PC no aporta por sí sola el entorno de ejecución, gráficos, servicios y autenticación necesarios. No hay evidencia en esta revisión de un flujo general insertar disco PS5 en Nexus y jugar. No comprometer esa función ni vender compatibilidad universal.

## Plan de pruebas concreto

- Fijar commit/release y revisar licencia, dependencias y fuentes del proyecto.
- Comprobar CPU x86-64, GPU/controlador Vulkan 1.3, audio y mando en hardware de prueba.
- Compilar primero el objetivo de pruebas/regresiones sin añadirlo a la ISO estable.
- Ejecutar homebrew redistribuible y pruebas de shaders/memoria con registros y capturas reales.
- Para un título concreto con archivos obtenidos legítimamente: registrar build, hardware, versión del juego, arranque, imagen, audio, mando, estabilidad, FPS y guardado.
- Sólo después integrar un lanzador experimental Nexus y publicar una matriz título por título. El soporte de disco requiere un proyecto independiente y evidencia adicional.

No se ha probado aún ninguno de estos pasos de ejecución. La prueba de IA realizada en esta sesión y la construcción ISO no acreditan emulación PS5.

## Fuentes primarias consultadas

- https://github.com/KytyPS5/KytyPS5 — README, estado, requisitos Linux/Vulkan, ejecución y licencia.
- https://github.com/InoriRus/Kyty — alcance del proyecto original.
- https://github.com/shadps4-emu/shadPS4 — emulación PS4 y alcance distinto.
- https://www.playstation.com/es-co/support/hardware/ps5-disc-drive-set-up/ — compatibilidad y emparejamiento de unidad de disco.

## Captura de Nexus recuperada

Se recuperó nexus-horizon-desktop-preview de Fast Checks 38978527776, SHA 98e23179. Muestra panel y lanzador ejecutados en Xvfb. No es una captura de la ISO arrancada y no muestra juegos PS5.
