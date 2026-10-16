# PS5 — trazado de implementación para Nexus

Fecha: 2026-10-16. Se clonó KytyPS5/KytyPS5 y se inspeccionó código del commit `42bb0da520992e35f062f44e6762484c356b9ded`. Análisis estático de implementación abierta; no ingeniería inversa de firmware/binarios Sony, no ejecución de juegos, no pruebas de GPU. No había compilador C++ ni CMake disponibles en el entorno de edición al comprobarlos. No se modificó ni se envió código al proyecto externo.

## Flujo reconstruido

1. `src/main.cpp`, ParseArgs: `--game` recibe directorio, archivo ELF o archivo soportado. Un directorio se asocia a `/app0/eboot.bin`; un archivo de juego se monta en un espacio virtual. La presencia de este parser no demuestra soporte de disco físico ni compatibilidad de cualquier ejecutable.
2. `src/emulator.cpp`: Run prepara la ejecución, llama LoadProgram y Execute. Es el punto de entrada a inspeccionar al separar fallos de montaje, carga y ejecución.
3. `src/loader/elf.cpp`: lectura de cabeceras ELF/SELF y segmentos. Reconocer un contenedor no demuestra descifrado ni autorización de contenido de discos comerciales.
4. `src/loader/runtimeLinker.cpp`: RuntimeLinker aporta LoadProgram, LoadProgramToMemory, RelocateAll/Relocate, Resolve, CreateSymbolDatabase y Execute; esto muestra que mapear instrucciones requiere además memoria, relocalizaciones, símbolos y servicios.
5. `src/kernel/fileSystem.cpp`: MountPoints::Mount conserva ruta anfitriona, punto de montaje y lector de archivo; ResolvePath transforma rutas virtuales. Es un subsistema de compatibilidad, no una prueba de sandbox seguro. Nexus tendría que evaluar permisos y aislamiento por separado.
6. `src/graphics/shader/recompiler/ShaderRecompiler.cpp`: DecodeFrontProgram/DecodeProgram alimentan CFG::BuildGraph y Frontend::TranslateProgram; TrackResources registra recursos; CompileProgram especializa recursos, elimina código muerto y llama Spirv::EmitProgram. La salida SPIR-V se destina al backend Vulkan.
7. `src/graphics/guest_gpu/command_processor`: despacho de comandos huésped; `src/graphics/host_gpu`: recursos, memoria y renderizado anfitrión. La separación orienta diagnóstico de comandos frente a errores de traducción de shaders.

## Implicaciones concretas para Nexus

- Integrar un motor externo versionado mediante adaptador, en lugar de copiar fragmentos aislados sin sus dependencias.
- Preflight de arquitectura y Vulkan 1.3 antes de habilitar una ruta experimental. Todavía no se comprobó GPU física.
- Importar una carpeta/archivo elegido por el usuario y construir argv sin shell. El comando de integración documentado es `kyty_emulator --game RUTA`; no se ha añadido aún al producto.
- Separar estados: archivo reconocido, motor disponible, juego cargado, primer frame, audio/mando, estabilidad y guardado. Un log de arranque no es una prueba de juego utilizable.
- Registrar por prueba commit del motor, hardware/controlador, juego/versión, log y captura propios. Empezar con homebrew redistribuible o pruebas autorizadas.
- Preservar licencia GPL-2.0-only y avisos de terceros al reutilizar/distribuir componentes. No se incorpora código del proyecto externo en esta revisión.
- Insertar un disco y jugar continúa sin demostrar: ni el parser de archivos ni la traducción gráfica resuelven por sí solos lectura/autenticación y entorno completo del juego.

## Qué se realizó y qué falta

Realizado: clonación, identificación de SHA, lectura selectiva de cargador, argumentos, enlazador, sistema de archivos y compilador de shaders; trazado de llamadas y puntos de integración. Pendiente: compilación reproducible del motor, tests upstream, prueba de homebrew, GPU/controladores, integración Nexus y matriz de títulos. No afirmar compatibilidad PS5 entregada.

## Referencias exactas

- https://github.com/KytyPS5/KytyPS5/tree/42bb0da520992e35f062f44e6762484c356b9ded
- https://github.com/KytyPS5/KytyPS5/blob/42bb0da520992e35f062f44e6762484c356b9ded/src/main.cpp
- https://github.com/KytyPS5/KytyPS5/blob/42bb0da520992e35f062f44e6762484c356b9ded/src/emulator.cpp
- https://github.com/KytyPS5/KytyPS5/blob/42bb0da520992e35f062f44e6762484c356b9ded/src/loader/runtimeLinker.cpp
- https://github.com/KytyPS5/KytyPS5/blob/42bb0da520992e35f062f44e6762484c356b9ded/src/graphics/shader/recompiler/ShaderRecompiler.cpp
