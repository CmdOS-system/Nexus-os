# Nexus OmniSubsystem: arquitectura híbrida Debian

Estado de esta rama: integración en construcción. Nexus usa el kernel Linux y el espacio de usuario Debian como base de producto. El árbol `omnios/kernel` conserva un prototipo freestanding UEFI de investigación; no forma parte del arranque ni del build del sistema Nexus. El ejecutable que conecta formatos con runtimes es un proceso de usuario Rust, no código de anillo 0.

```text
Gestor de archivos / execve
        │ asociación MIME o regla Linux binfmt_misc
        ▼
/usr/bin/nexus-omniloader (Rust, usuario)
        ├── PE / MSI → Wine (Proton no es un sustituto genérico de Wine)
        ├── APK → validación ZIP + confirmación → Waydroid / ART
        ├── Mach-O → Darling, solo si está instalado y ese binario es compatible
        ├── WASM → Wasmtime sin preabrir archivos del host
        ├── CRX → perfil separado de Chromium y página de extensiones
        ├── .deb → confirmación + pkexec + apt-get
        └── ELF → ejecutado directamente por el kernel Linux
```

## Qué instala y configura la imagen

- Rust compila `omnios/loader` como `nexus-omniloader` para Linux x86_64.
- `image/stage-omni-subsystem.sh` toma el artefacto Linux amd64 de Wasmtime v49.0.2, verifica el `sha256` publicado por la API oficial de releases y prepara los binarios fuera de Git.
- `image/auto/config`, listas de paquetes, el archivo oficial de `trixie-backports` y hooks configuran live-build. Waydroid se instala desde Debian Trixie Backports; Chromium y `aapt` salen de Debian Trixie.
- `nexus-omnios-binfmt.service` registra handlers del kernel al iniciar. El kernel solo despacha por magic/extension a `/usr/bin/nexus-omniloader`; el código del cargador sigue en espacio de usuario.
- `nexus-waydroid-preflight` confirma Binder, propone inicializar la imagen oficial con autorización y arranca el contenedor/sesión Waydroid. El hook del ISO solicita `binder_linux` al inicio sin descargar Android durante el build.
- El perfil Wine de Office es explícito y aislado. El asistente descarga componentes por Winetricks tras confirmación y limita `DllOverrides` a ese prefijo; no altera otros perfiles.
- ELF no se registra a través del cargador para evitar un ciclo infinito. `.deb` es un archivo de paquete y se abre mediante asociación gráfica, no `binfmt_misc`.
- Las asociaciones MIME de EXE preservan Nexus Install y su catálogo limitado de instaladores aprobados. Ejecutar un EXE de forma directa es una acción distinta y usa Wine.

## Validación y límites técnicos

`cargo +nightly -Z bindeps test -p omni-loader` prueba el parser AXML/DEX/CRX y el despacho. `image/runtime-smoke.sh` genera fixtures estructurales, inspecciona un APK, valida el contenedor CRX, ejecuta un módulo WASI con Wasmtime y compila/ejecuta un EXE PE x86_64 por el cargador y Wine. También comprueba el contrato de argumentos de Darling y PWA mediante ejecutables de prueba. El workflow del ISO construye la ISO, verifica checksum/SquashFS y arranca el sistema con QEMU/UEFI.

Estas comprobaciones no son intercambiables: el APK fixture se inspecciona pero no se instala; el CRX de prueba es unsigned y nunca se instala; el CI no dispone de Binder/Waydroid ni Darling y sus scripts se validan sin afirmar ejecución de apps Android/macOS. El smoke de PE es un programa de consola mínimo, no Word/Office. La ISO y la aceptación en hardware dependen del resultado final del gate.

| Ruta | Comportamiento implementado | Requisitos y límites pendientes |
|---|---|---|
| PE `.exe` / MSI | El cargador comprueba firma PE, cabecera COFF, número acotado de secciones y tamaño/magic del encabezado opcional antes de despachar; acepta x86 y x86_64 hacia Wine y rechaza arquitecturas no soportadas con su código de máquina. MSI válido usa `wine msiexec /i`. Perfil Office aislado con Winetricks y overrides por prefijo. CI compila y ejecuta un PE que devuelve 0. | La comprobación de cabeceras no valida todas las secciones, imports ni firmas Authenticode. El smoke prueba el dispatcher, no una suite de oficina. Word/Office, versiones, periféricos y GUI aún requieren aceptación real. Proton no es un destino genérico. |
| APK | Valida ZIP/rutas, lee package ID desde AXML, verifica cabecera DEX, pide confirmación y preflight Binder/Waydroid; después instala y abre por package ID. CI inspecciona un APK fixture. | El fixture no se instala ni tiene actividad. Ejecución de APK real requiere imagen Waydroid, Binder, ABI compatible y sesión gráfica/hardware. |
| DEX independiente | Explica por qué no es un APK instalable | Requiere ART/framework Android; no se inventa un paquete alrededor del DEX. |
| Mach-O | Llama a `darling shell` si existe; traduce rutas y cita argumentos. CI verifica ese contrato con un ejecutable de prueba. | No se ejecuta una app Mach-O real en CI. Darling es externo y requiere pruebas de apps/arquitecturas en un host compatible. |
| WASM / PWA | Ejecuta un módulo WASI con Wasmtime sin preabrir el filesystem; `--webapp` abre Chromium con `--app` usando HTTPS o localhost. | El fixture verifica salida cero, no todas las APIs WASI ni ChromeOS como sistema. |
| CRX | Valida versión/longitudes y manifest en perfil Chromium separado, para revisión manual. | CI usa paquete unsigned solo para inspección. Chromium debe verificar firma/editor y permisos antes de instalar. CRX no es una app independiente. |
| `.deb` | Pide confirmación y solicita autenticación de escritorio antes de apt | Requiere red/repositorios válidos y privilegios aceptados. Los paquetes locales no se instalan solo por descargarlos. |

No se descargan binarios de Darling/Proton/Wine fuera de los repositorios configurados ni se eluden licencias, DRM o controles de acceso. No se afirma soporte para macOS, ChromeOS, Office o Android completo sin pruebas por aplicación, versión, arquitectura y entorno.

## Ejecución local reproducible

En Debian x86_64 con Rust nightly, requerido porque el workspace también contiene la base UEFI:

```sh
cargo +nightly fmt --manifest-path omnios/Cargo.toml --package omni-loader -- --check
cargo +nightly -Z bindeps test --manifest-path omnios/Cargo.toml -p omni-loader
bash image/stage-omni-subsystem.sh
sudo apt install gcc-mingw-w64-x86-64 wine64 xvfb
bash image/runtime-smoke.sh
docker run --rm --privileged --mount type=bind,source="$PWD",target=/src --workdir /src debian:trixie bash image/build.sh
```

La compilación requiere red para paquetes Debian y descargar el artefacto fijado de Wasmtime. No se necesita ni se recomienda usar `sudo` en el disco real para generar la ISO: el contenedor construye el chroot desechable.

## Documentación primaria revisada

- [Kernel Linux: binfmt_misc](https://docs.kernel.org/admin-guide/binfmt-misc.html): sintaxis de registro, magic/extension y despacho al intérprete.
- [systemd-binfmt](https://manpages.debian.org/trixie/systemd/systemd-binfmt.8.en.html): registro de formatos durante el inicio.
- [Manual Debian Live: personalizar instalación de paquetes](https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-package-installation.en.html) y [hooks de contenido](https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-contents.en.html).
- [Debian Trixie Backports: Waydroid](https://packages.debian.org/trixie-backports/utils/waydroid).
- [Waydroid: instalar y ejecutar aplicaciones](https://docs.waydro.id/usage/install-and-run-android-applications).
- [Wasmtime releases](https://github.com/bytecodealliance/wasmtime/releases): release inmutable y digest de artefactos.
- [Darling shell](https://docs.darlinghq.org/darling-shell.html) y [límites de instalación de software](https://docs.darlinghq.org/installing-software.html).
