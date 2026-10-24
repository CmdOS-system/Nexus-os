# OmniOS / Nexus OmniSubsystem: estado, fases y pendientes

Este archivo es la fuente de verdad del avance del prototipo. Los porcentajes describen alcance de ingeniería, no compatibilidad certificada. Actualiza este documento en el mismo cambio que complete una tarea.

## Estado general

- **OmniKernel freestanding: 6% estimado.** Es un prototipo de investigación x86_64 con arranque QEMU; no es el kernel de Nexus ni una meta de producto para ejecutar aplicaciones comerciales.
- **Nexus OmniSubsystem (primera integración): 25% estimado.** Se ha escrito un binario Linux en Rust que despacha a runtimes del sistema, junto con configuración live-build y pruebas unitarias. Falta compilarlo/probarlo en CI, verificar el contenido de la ISO y probar rutas con aplicaciones reales en la sesión gráfica.
- **Nexus OS global: ≈38% reportado en `docs/PROJECT-PROGRESS.md`.** No sube con esta integración hasta que una ISO y un flujo de aplicación representativo pasen validación; reconocer un formato no prueba compatibilidad de apps.

## Componentes

| Área | Avance | Hecho | Siguiente | Pendiente / límite |
|---|---:|---|---|---|
| Repositorio y CI | 45% | Estructura inicial, workflow verde, imágenes UEFI/BIOS y artefacto publicado | Añadir caché/lockfile y pruebas repetibles para cambios de kernel | Protección de ramas y matriz ARM64 |
| OmniKernel / arranque | 17% | Entrada `no_std`, arranque UEFI confirmado en QEMU, allocator fijo basado en mapa UEFI con reserva/liberación, backend de tablas x86_64 de cuatro niveles con aislamiento, scheduler RR/Fair y pruebas unitarias | Ejecutar CI y conectar el allocator a `BootInfo`; configurar direct map para tablas activas | IDT, timer ISR/context restore, activación de CR3 en arranque, IPC y drivers |
| Nexus OmniLoader (usuario Linux) | 25% | CLI Rust con rutas Wine/Waydroid/Darling/Wasmtime/Chromium/apt, registro `binfmt_misc`, pruebas unitarias escritas | Cargo/CI, extracción de ISO y smoke UEFI; sesión gráfica y apps objetivo | CI y contenido de la ISO todavía no verificados en este cambio; no es parser universal ni garantiza ABI |
| OmniKernel freestanding (investigación) | 17% | Entry `no_std`, memoria/scheduler de prototipo y pruebas; arranque anterior en QEMU | Mantener separado del producto Debian | No arranca Nexus ni reemplaza Linux; traps/ABI/drivers incompletos |
| Dispatcher ABI | 2% | Tablas ilustrativas Linux y rutas internas OmniBridge Windows/Darwin | Definir contrato de ABI y entrada de trap | No hay syscalls reales; no prometer compatibilidad NT/XNU |
| OmniLang | 2% | Borrador de sintaxis y objetivos de diseño | Prototipo lexer/parser y decisiones de tipos/ownership | No existe compilador, UIR, LLVM backend ni runtime |
| Puentes y gráficos | 1% | Alcance y límites documentados para Win32, glibc, Cocoa, ART y Vulkan | Priorizar un bridge con pruebas de conformidad | No existen implementaciones; evaluar APIs, licencias y drivers |
| WASI / ChromeOS / PWA | 2% diseño | Magic WASM/CRX y límites de seguridad documentados | Diseñar host WASI aislado de usuario y shell web/PWA | Runtime, verificación CRX, APIs ChromeOS y PWA no implementados; 0% compatibilidad verificada |
| Windows/macOS/Android/Linux/ChromeOS | 0% compatibilidad verificada | Requisitos registrados en la arquitectura | Desglosar por aplicación y servicio | Ningún programa de esos sistemas se ha instalado o ejecutado aquí |

El porcentaje global es una estimación ponderada del plan técnico, no una métrica de líneas de código. La compatibilidad de aplicaciones se reporta por separado y permanece en **0% verificado** hasta ejecutar programas representativos.

## Arquitectura de producto vigente

Nexus se entrega como Debian con el kernel Linux real. OmniLoader se compila como proceso Linux en espacio de usuario y se registra mediante `binfmt_misc`; formatos Linux ELF quedan al kernel. OmniKernel y el futuro OmniLang continúan como investigación separada, sin reclamación de compatibilidad de apps. Detalle: [Nexus OmniSubsystem](../docs/NEXUS-OMNISUBSYSTEM.md).

## Fases de entrega

1. **Base compilable y arranque UEFI x86_64 — completada en CI.** Run #4 pasó tests, construcción BIOS/UEFI, arranque OVMF/QEMU con `OMNIOS_BOOT_OK`, staging y publicación de artefactos: https://github.com/CmdOS-system/Nexus-os/actions/runs/39099281130 .
2. **Base de memoria — 45% de fase.** Ya hay allocator de frames 4 KiB, gestor 4 niveles, backend direct-map opt-in y scheduler RR/Fair con contexto guardado; pruebas unitarias añadidas. Falta pasar el mapa real de `BootInfo` a un allocator persistente, habilitar/configurar direct map/NX, e integrar IDT, timer y restauración hardware del contexto.
3. **Nexus OmniSubsystem — en integración.** Compilar el cargador para Linux, registrar runtimes de usuario, construir ISO y comprobar sus contenidos; después validar APK/Wine/Wasmtime en la imagen real. ELF sigue nativo y no debe redirigirse al cargador.
4. **Compatibilidad Windows y formatos adicionales — pendiente.** Parser PE, puente Win32 incremental y pruebas con aplicaciones Windows legales/de muestra; Mach-O, Android/APK, ChromeOS y ARM64 requieren proyectos separados y revisión técnica/legal.
5. **OmniLang — pendiente.** Lexer, parser, AST, verificador de tipos/seguridad, UIR versionada y backend LLVM; primero compilar y ejecutar ejemplos en host.
6. **WASI, ChromeOS y PWA — diseño/firmas en curso.** El loader reconoce candidatos WASM y CRX; implementar parsers seguros, host WASI en usuario y shell web PWA con manifiestos, permisos y APIs web.
7. **Gráficos, instaladores y producto multiplataforma — pendiente.** Servicio de usuario, Vulkan, instalación con interfaz, drivers, seguridad, telemetría opcional, empaquetado y pruebas en hardware real.

## Criterios para marcar una tarea como hecha

- Código y documentación están en GitHub.
- El CI correspondiente termina en verde y se enlaza su ejecución en el PR.
- Para compatibilidad, registrar aplicación/versión, arquitectura, hardware o emulador, resultado y limitaciones. Una prueba de parser o un arranque del kernel no cuenta como prueba de compatibilidad de aplicaciones.
- Actualizar porcentajes solo con evidencia nueva y describir qué cambió.

## Pendiente inmediato

1. Ejecutar CI del cambio y resolver cualquier fallo de compilación o test antes de dar por cerrados los tres módulos.
2. Instanciar allocator persistente desde `BootInfo.memory_regions`; configurar en el bootloader el mapeo físico, probarlo en QEMU y activar CR3 de forma controlada.
3. Añadir IDT de x86_64, timer ISR y epílogo que consuma `SwitchDecision` para alternar el marco de registros real.
4. Añadir parsers WASM/CRX acotados, validando versión y longitudes; nunca instalar basándose solo en magic bytes.
5. Después de disponer de memoria e IPC, integrar runtime WASI en usuario con capacidades/cuotas; planear PWA como shell web separada.
6. Añadir caché/lockfile y medir el tiempo de CI para evitar reinstalaciones costosas en cada cambio.

## Registro de validación

- CI #1: falló durante la preparación del bootloader porque faltaba `rust-src`; agregado al toolchain y a la instalación del workflow.
- CI #2: `x86_64 0.15.2` no compila con el nightly actual porque su implementación inestable de `Step` no incluye los métodos nuevos; fijada la dependencia en `0.15.5`, cuya publicación declara compatibilidad con nightlies desde 2026-07-10. Arranque QEMU aún no confirmado.
- CI #3: pruebas del workspace, construcción BIOS/UEFI y arranque UEFI QEMU con `OMNIOS_BOOT_OK` pasaron; falló solo la publicación por una ruta de artefacto que no encontró archivos. Se prepara una carpeta conocida y se comprueba que contenga ambas imágenes antes de subirlas.
- CI #4: https://github.com/CmdOS-system/Nexus-os/actions/runs/39099281130 terminó verde; tests, imágenes, arranque serial y artefactos pasaron.
- CI #5: https://github.com/CmdOS-system/Nexus-os/actions/runs/39099561789 terminó verde sobre el estado actualizado de la hoja de ruta.
- ChromeOS/WASM (este cambio): añadidas firmas candidatas y pruebas; aún falta parser, verificación CRX, runtime WASI, navegador/PWA y pruebas de aplicaciones.
- Memoria/scheduler: implementación `no_std` de rangos de frames 4 KiB inicializados desde regiones UEFI, reserva/liberación con detección de doble liberación, mapeo/desmapeo y traducción de páginas 4 niveles con permisos R/W/X/User y W^X, y selección RR/Fair guardando contexto/personality. Se añadieron tests simulados para los tres módulos y smoke checks de allocator/scheduler al arranque; pendiente CI y conexión a IDT/timer/CR3 activo.
