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
- ELF no se registra a través del cargador para evitar un ciclo infinito. `.deb` es un archivo de paquete y se abre mediante asociación gráfica, no `binfmt_misc`.
- Las asociaciones MIME de EXE preservan Nexus Install y su catálogo limitado de instaladores aprobados. Ejecutar un EXE de forma directa es una acción distinta y usa Wine.

## Validación y límites técnicos

`cargo test -p omni-loader` prueba clasificación y generación de reglas sin requerir privilegios. El workflow del ISO compila el binario, construye la ISO, verifica su checksum, extrae `filesystem.squashfs`, comprueba binarios/paquetes/activación del servicio y luego ejecuta el smoke test UEFI existente. Estas pruebas validan integración de imagen, no compatibilidad universal ni aceptación sobre hardware físico.

| Ruta | Comportamiento implementado | Requisitos y límites pendientes |
|---|---|---|
| PE `.exe` / MSI | Wine para PE; los MSI válidos se pasan a `wine msiexec /i` vía `binfmt_misc` o asociación MIME | No se redirige automáticamente a Proton: Steam/Proton no es una API genérica para todo instalador. No acredita Office/Word ni periféricos. |
| APK | Comprueba ZIP y entradas Android; pide confirmación, instala en Waydroid e intenta abrir el package ID con `aapt` | Waydroid debe inicializarse, tener imagen Android, Binder y sesión Wayland funcional. La ISO instala componentes; no descarga ni configura imágenes Android durante el build. Aceptación GUI Live pendiente. |
| DEX independiente | Explica por qué no es un APK instalable | Requiere ART/framework Android; no se inventa un paquete alrededor del DEX. |
| Mach-O | Llama a `darling shell` si existe; traduce la ruta del host a `/Volumes/SystemRoot` y cita los argumentos para el shell del prefix | Darling no se distribuye con la ISO por ser externo al archive Debian usado aquí; aplicaciones, GUI, arquitectura y versión no son universalmente compatibles. |
| WASM | Ejecuta Wasmtime sin conceder preopens de filesystem | El comportamiento WASI depende de imports y versión. El usuario sigue siendo responsable de ejecutar el módulo escogido. |
| CRX | Abre gestor de extensiones Chromium en perfil dedicado | No instala a ciegas extensiones de terceros. CRX es extensión del navegador, no una app independiente; verificación de editor/permisos e instalación manual pendiente. |
| `.deb` | Pide confirmación y solicita autenticación de escritorio antes de apt | Requiere red/repositorios válidos y privilegios aceptados. Los paquetes locales no se instalan solo por descargarlos. |

No se descargan binarios de Darling/Proton/Wine fuera de los repositorios configurados ni se eluden licencias, DRM o controles de acceso. No se afirma soporte para macOS, ChromeOS, Office o Android completo sin pruebas por aplicación, versión, arquitectura y entorno.

## Ejecución local reproducible

En Debian x86_64 con Rust nightly, requerido porque el workspace también contiene la base UEFI:

```sh
cargo +nightly fmt --manifest-path omnios/Cargo.toml --package omni-loader -- --check
cargo +nightly test --manifest-path omnios/Cargo.toml -p omni-loader
bash image/stage-omni-subsystem.sh
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
