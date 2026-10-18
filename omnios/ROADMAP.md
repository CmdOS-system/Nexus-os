# OmniOS: estado, fases y pendientes

Este archivo es la fuente de verdad del avance del prototipo. Los porcentajes describen alcance de ingeniería, no compatibilidad certificada. Actualiza este documento en el mismo cambio que complete una tarea.

## Estado general

- **OmniOS (proyecto completo): 5% estimado.** Existe la base experimental x86_64 y CI ya construye y arranca el prototipo UEFI en QEMU. No es un sistema operativo de uso diario.
- **Nexus (repositorio anfitrión): 38% reportado anteriormente.** Es un proyecto distinto y este cambio no modifica su implementación.

## Componentes

| Área | Avance | Hecho | Siguiente | Pendiente / límite |
|---|---:|---|---|---|
| Repositorio y CI | 45% | Estructura inicial, workflow verde, imágenes UEFI/BIOS y artefacto publicado | Añadir caché/lockfile y pruebas repetibles para cambios de kernel | Protección de ramas y matriz ARM64 |
| OmniKernel / arranque | 8% | Entrada `no_std`, arranque UEFI confirmado en QEMU, salida serial y comprobación de tablas | Gestor de memoria física a partir del mapa UEFI | Excepciones, interrupciones, paginación, scheduler, IPC y drivers |
| OmniLoader | 6% | Detección acotada de ELF/MZ/Mach-O/DEX/ZIP/WASM/CRX y pruebas unitarias | Parser ELF y validadores por formato con límites | No verifica firmas CRX, no interpreta secciones WASM ni carga/ejecuta formatos |
| Dispatcher ABI | 2% | Tablas ilustrativas Linux y rutas internas OmniBridge Windows/Darwin | Definir contrato de ABI y entrada de trap | No hay syscalls reales; no prometer compatibilidad NT/XNU |
| OmniLang | 2% | Borrador de sintaxis y objetivos de diseño | Prototipo lexer/parser y decisiones de tipos/ownership | No existe compilador, UIR, LLVM backend ni runtime |
| Puentes y gráficos | 1% | Alcance y límites documentados para Win32, glibc, Cocoa, ART y Vulkan | Priorizar un bridge con pruebas de conformidad | No existen implementaciones; evaluar APIs, licencias y drivers |
| WASI / ChromeOS / PWA | 2% diseño | Magic WASM/CRX y límites de seguridad documentados | Diseñar host WASI aislado de usuario y shell web/PWA | Runtime, verificación CRX, APIs ChromeOS y PWA no implementados; 0% compatibilidad verificada |
| Windows/macOS/Android/Linux/ChromeOS | 0% compatibilidad verificada | Requisitos registrados en la arquitectura | Desglosar por aplicación y servicio | Ningún programa de esos sistemas se ha instalado o ejecutado aquí |

El porcentaje global es una estimación ponderada del plan técnico, no una métrica de líneas de código. La compatibilidad de aplicaciones se reporta por separado y permanece en **0% verificado** hasta ejecutar programas representativos.

## Fases de entrega

1. **Base compilable y arranque UEFI x86_64 — completada en CI.** Run #4 pasó tests, construcción BIOS/UEFI, arranque OVMF/QEMU con `OMNIOS_BOOT_OK`, staging y publicación de artefactos: https://github.com/CmdOS-system/Nexus-os/actions/runs/39099281130 .
2. **Memoria e interrupciones — pendiente.** Mapa UEFI, allocator de frames con pruebas, paginación, IDT/excepciones y temporizador.
3. **Loader Linux — pendiente.** Parser ELF defensivo, espacio de usuario, carga de un binario de prueba y ABI Linux mínima documentada.
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

1. Programar `kernel/src/memory/frame_allocator.rs` con allocator de frames probado sobre mapas UEFI sintéticos.
2. Añadir parsers WASM/CRX acotados, validando versión y longitudes; nunca instalar basándose solo en magic bytes.
3. Después de disponer de memoria e IPC, integrar runtime WASI en usuario con capacidades/cuotas; planear PWA como shell web separada.
4. Añadir caché/lockfile y medir el tiempo de CI para evitar reinstalaciones costosas en cada cambio.

## Registro de validación

- CI #1: falló durante la preparación del bootloader porque faltaba `rust-src`; agregado al toolchain y a la instalación del workflow.
- CI #2: `x86_64 0.15.2` no compila con el nightly actual porque su implementación inestable de `Step` no incluye los métodos nuevos; fijada la dependencia en `0.15.5`, cuya publicación declara compatibilidad con nightlies desde 2026-07-10. Arranque QEMU aún no confirmado.
- CI #3: pruebas del workspace, construcción BIOS/UEFI y arranque UEFI QEMU con `OMNIOS_BOOT_OK` pasaron; falló solo la publicación por una ruta de artefacto que no encontró archivos. Se prepara una carpeta conocida y se comprueba que contenga ambas imágenes antes de subirlas.
- CI #4: https://github.com/CmdOS-system/Nexus-os/actions/runs/39099281130 terminó verde; tests, imágenes, arranque serial y artefactos pasaron.
- CI #5: https://github.com/CmdOS-system/Nexus-os/actions/runs/39099561789 terminó verde sobre el estado actualizado de la hoja de ruta.
- ChromeOS/WASM (este cambio): añadidas firmas candidatas y pruebas; aún falta parser, verificación CRX, runtime WASI, navegador/PWA y pruebas de aplicaciones.
