# OmniOS / Nexus OmniSubsystem

La decisión de arquitectura del proyecto de producto es usar el kernel Linux real de Debian en Nexus. El código Rust de `omnios/loader` se integra como el **Nexus OmniSubsystem**, un ejecutable Linux de usuario conectado a `binfmt_misc` y a runtimes instalados. Ver [arquitectura y límites del subsistema](../docs/NEXUS-OMNISUBSYSTEM.md).

`omnios/kernel` permanece como prototipo experimental UEFI/BIOS freestanding para investigación. No arranca Nexus, no implementa una ABI de Windows/macOS/Android y no se usa como alternativa al kernel Linux del sistema.

## Arquitectura inicial

```text
Aplicaciones / formatos
PE + Win32 │ ELF + POSIX │ Mach-O + Darwin │ APK + ART │ WASM/WASI │ CRX/PWA
                         │ runtimes/bridges de usuario
OmniLoader (detección segura; loaders incrementales)
                         │ proceso + personalidad ABI fija
OmniKernel: syscall dispatcher │ memoria │ scheduler │ IPC
                         │ HAL
               x86_64 (primera fase) → ARM64
```

El dispatcher guarda una personalidad por proceso y selecciona una tabla de rutas inmutable. Los bridges y runtimes de usuario convierten contratos de Win32, POSIX, Darwin, Android y WASI a primitivas internas. El kernel inicial solo muestra la estructura del dispatcher: todavía no instala una entrada de syscall de CPU ni implementa esos servicios. Las llamadas Windows NT varían por versión; no se inventan números estables. Las rutas Windows/Darwin iniciales son identificadores internos producidos por el bridge. WASI se implementará en un proceso sandbox de usuario con capacidades; el kernel solo ofrecerá sus primitivas seguras de memoria, IPC y archivos.

OmniLang tendrá sintaxis estática, ownership/borrowing, memoria segura por defecto y FFI marcado. El compilador previsto usa LLVM y una UIR verificada con backends AOT/JIT. Aún no existe compilador. La UIR sirve para programas OmniLang portables; no convierte mágicamente binarios PE, Mach-O o DEX.

## Compilar y probar localmente

Instala Rust nightly, QEMU x86_64 y OVMF. Desde `omnios/`:

```sh
cargo test --workspace
cargo run --release -- uefi-smoke
```

GitHub Actions instala también GCC cross-compilers y LLVM como base para los módulos C/ASM futuros. El primer kernel se compila con Rust para `x86_64-unknown-none`. QEMU debe devolver el código de salida de éxito y la marca serial `OMNIOS_BOOT_OK`; un panic escribe `OMNIOS_KERNEL_PANIC` y hace fallar la prueba.

## Estructura

```text
omnios/
├── Cargo.toml, build.rs, rust-toolchain.toml
├── kernel/       # OmniKernel no_std, ABI y syscall routes
├── loader/       # detector de formatos con pruebas
├── omnilang/     # especificación; compiler aún no implementado
└── subsystems/   # contratos y backlog por bridge/gráficos
```

La detección de magic bytes no autentica ni valida una imagen ejecutable. PE/ELF/Mach-O requieren parsing con límites y validación de segmentos; APK es un ZIP que debe verificarse por sus entradas `AndroidManifest.xml` y DEX/recursos antes de elegir ART. DEX independiente comienza con `dex\n`. WebAssembly empieza con `\0asm`; CRX con `Cr24`, pero reconocer el encabezado no verifica firma, publicador ni permisos. Una PWA es una aplicación web descrita por un manifiesto y recursos web, no un formato binario detectado por magic bytes; requiere un navegador o shell web compatible. La capa correcta depende también de API, arquitectura, servicios, drivers y licencia.

## Fuentes de diseño

- Bootloader x86_64 UEFI/BIOS: https://github.com/rust-osdev/bootloader
- ELF: https://gabi.xinuos.com/
- PE/COFF: https://learn.microsoft.com/windows/win32/debug/pe-format
- Android ART: https://source.android.com/docs/core/runtime
- Wine y traducción de ABI: https://www.winehq.org/about/

## Alcance no validado

El primer CI valida el arranque UEFI de un kernel x86_64 mínimo en QEMU y pruebas unitarias de firmas. No valida una shell, drivers, syscall real, parsers completos, firma CRX, runtime WASI, PWA, Windows/macOS/Android/ChromeOS ABI, aplicaciones gráficas ni ARM64. Emulación/traducción de ISA y compatibilidad de ABI tienen costes y límites; no se promete “latencia cero” ni compatibilidad total.
