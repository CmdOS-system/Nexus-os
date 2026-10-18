//! Linux userspace dispatcher for Nexus. Kernel binfmt_misc passes the path to
//! this program; all compatibility work is delegated to installed runtimes.

use std::env;
use std::ffi::{OsStr, OsString};
use std::fs::{self, File};
use std::io::{self, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};

const BINFMT_REGISTER: &str = "/proc/sys/fs/binfmt_misc/register";
const BINFMT_STATUS: &str = "/proc/sys/fs/binfmt_misc/status";
const LOADER: &str = "/usr/bin/nexus-omniloader";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Route {
    Windows,
    WindowsInstaller,
    AndroidApk,
    AndroidDex,
    MacOs,
    Wasm,
    ChromeExtension,
    DebianPackage,
    NativeElf,
    Unknown,
}

#[derive(Clone, Copy)]
struct BinfmtRule {
    name: &'static str,
    matcher: Matcher,
}

#[derive(Clone, Copy)]
enum Matcher {
    Magic(&'static [u8]),
    Extension(&'static str),
}

const RULES: &[BinfmtRule] = &[
    BinfmtRule { name: "nexus-pe", matcher: Matcher::Magic(b"MZ") },
    BinfmtRule { name: "nexus-msi", matcher: Matcher::Extension("msi") },
    BinfmtRule { name: "nexus-msi-upper", matcher: Matcher::Extension("MSI") },
    BinfmtRule { name: "nexus-apk", matcher: Matcher::Extension("apk") },
    BinfmtRule { name: "nexus-apk-upper", matcher: Matcher::Extension("APK") },
    BinfmtRule { name: "nexus-dex", matcher: Matcher::Extension("dex") },
    BinfmtRule { name: "nexus-dex-upper", matcher: Matcher::Extension("DEX") },
    BinfmtRule { name: "nexus-macho-be", matcher: Matcher::Magic(&[0xfe, 0xed, 0xfa, 0xcf]) },
    BinfmtRule { name: "nexus-macho-le", matcher: Matcher::Magic(&[0xcf, 0xfa, 0xed, 0xfe]) },
    BinfmtRule { name: "nexus-wasm", matcher: Matcher::Magic(b"\0asm\x01\0\0\0") },
    BinfmtRule { name: "nexus-crx", matcher: Matcher::Magic(b"Cr24") },
];

fn registration_bytes(rule: &BinfmtRule) -> Vec<u8> {
    let mut bytes = format!(":{}:", rule.name).into_bytes();
    match rule.matcher {
        Matcher::Magic(magic) => {
            bytes.extend_from_slice(b"M::");
            bytes.extend_from_slice(magic);
            bytes.extend_from_slice(b"::");
        }
        Matcher::Extension(extension) => {
            bytes.extend_from_slice(b"E::");
            bytes.extend_from_slice(extension.as_bytes());
            bytes.extend_from_slice(b"::");
        }
    }
    bytes.extend_from_slice(LOADER.as_bytes());
    bytes.push(b':');
    bytes
}

fn route(path: &Path, prefix: &[u8]) -> Route {
    let extension = path.extension().and_then(OsStr::to_str).unwrap_or("").to_ascii_lowercase();
    match extension.as_str() {
        "msi" if prefix.starts_with(&[0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]) => return Route::WindowsInstaller,
        "apk" if prefix.starts_with(b"PK\x03\x04") => return Route::AndroidApk,
        "dex" if omni_loader::magic_detector::detect_magic(prefix).format == omni_loader::magic_detector::BinaryFormat::Dex => return Route::AndroidDex,
        "deb" if prefix.starts_with(b"!<arch>\n") => return Route::DebianPackage,
        "wasm" | "wat" => return Route::Wasm,
        "crx" if prefix.starts_with(b"Cr24") => return Route::ChromeExtension,
        _ => {}
    }
    let detection = omni_loader::magic_detector::detect_magic(prefix);
    use omni_loader::magic_detector::{BinaryFormat, Subsystem};
    match (detection.format, detection.subsystem) {
        (BinaryFormat::Elf, _) => Route::NativeElf,
        (BinaryFormat::PeCandidate, _) => Route::Windows,
        (BinaryFormat::MachO64 | BinaryFormat::MachOFat, _) => Route::MacOs,
        (BinaryFormat::WebAssemblyCandidate, _) => Route::Wasm,
        (BinaryFormat::CrxCandidate, _) => Route::ChromeExtension,
        (BinaryFormat::Dex, _) => Route::AndroidDex,
        (BinaryFormat::ZipContainer, Subsystem::ContainerInspector) => Route::Unknown,
        _ => Route::Unknown,
    }
}

fn read_prefix(path: &Path) -> io::Result<Vec<u8>> {
    let mut file = File::open(path)?;
    let mut bytes = vec![0; 4096];
    let count = file.read(&mut bytes)?;
    bytes.truncate(count);
    Ok(bytes)
}

fn canonical_existing(path: &Path) -> io::Result<PathBuf> {
    fs::canonicalize(path)
}

fn command_exists(program: &str) -> bool {
    env::split_paths(&env::var_os("PATH").unwrap_or_default())
        .map(|dir| dir.join(program))
        .any(|candidate| candidate.is_file())
}

fn confirm(action: &str, path: &Path) -> io::Result<bool> {
    if command_exists("zenity") {
        return Ok(Command::new("zenity")
            .args(["--question", "--width=520", "--title=Nexus OmniSubsystem", "--text"])
            .arg(format!("{action}\n\n{}", path.display()))
            .status()?
            .success());
    }
    if !atty_stdin() {
        return Err(io::Error::other("No hay interfaz de confirmación (zenity) ni terminal interactiva; acción cancelada."));
    }
    eprint!("{action}\n{}\n¿Continuar? [s/N] ", path.display());
    io::stderr().flush()?;
    let mut answer = String::new();
    io::stdin().read_line(&mut answer)?;
    Ok(matches!(answer.trim().to_ascii_lowercase().as_str(), "s" | "si" | "sí" | "y" | "yes"))
}

fn atty_stdin() -> bool {
    io::stdin().is_terminal()
}

fn require_program(program: &str, purpose: &str) -> io::Result<()> {
    if command_exists(program) {
        Ok(())
    } else {
        Err(io::Error::new(io::ErrorKind::NotFound, format!("No está instalado {program}; se necesita para {purpose}.")))
    }
}

fn run(program: &str, args: impl IntoIterator<Item = OsString>) -> io::Result<ExitCode> {
    let status = Command::new(program).args(args).status()?;
    Ok(status.code().map_or(ExitCode::FAILURE, |c| ExitCode::from(c as u8)))
}

fn dispatch(path: &Path, extra: &[OsString]) -> io::Result<ExitCode> {
    let absolute = canonical_existing(path)?;
    let prefix = read_prefix(&absolute)?;
    match route(&absolute, &prefix) {
        Route::Windows => {
            require_program("wine", "ejecutar aplicaciones de Windows mediante Wine")?;
            let mut args = vec![absolute.into_os_string()];
            args.extend_from_slice(extra);
            run("wine", args)
        }
        Route::WindowsInstaller => {
            require_program("wine", "instalar paquetes MSI mediante Windows Installer de Wine")?;
            let mut args = vec![OsString::from("msiexec"), OsString::from("/i"), absolute.into_os_string()];
            args.extend_from_slice(extra);
            run("wine", args)
        }
        Route::AndroidApk => {
            require_program("unzip", "comprobar que el ZIP tiene estructura APK")?;
            let mut child = Command::new("unzip")
                .args(["-Z1"])
                .arg(&absolute)
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .spawn()?;
            let mut listing = Vec::new();
            child.stdout.take().ok_or_else(|| io::Error::other("No se pudo leer el listado ZIP."))?
                .take(8 * 1024 * 1024 + 1).read_to_end(&mut listing)?;
            if listing.len() > 8 * 1024 * 1024 {
                let _ = child.kill();
                let _ = child.wait();
                return Err(io::Error::other("El listado interno del ZIP supera el límite seguro de 8 MiB."));
            }
            if !child.wait()?.success() {
                return Err(io::Error::other("El archivo no es un ZIP/APK válido."));
            }
            let entries = String::from_utf8_lossy(&listing);
            let valid_apk = entries.lines().any(|e| e == "AndroidManifest.xml")
                && entries.lines().any(|e| e == "classes.dex" || (e.starts_with("classes") && e.ends_with(".dex")) || e.starts_with("lib/"));
            if !valid_apk {
                return Err(io::Error::other("El archivo es ZIP, pero no contiene el manifiesto y código esperados de un APK."));
            }
            require_program("waydroid", "instalar aplicaciones Android")?;
            if !confirm("Waydroid instalará esta aplicación Android en el entorno de usuario.", &absolute)? {
                return Ok(ExitCode::SUCCESS);
            }
            let installed = Command::new("waydroid")
                .args(["app", "install"])
                .arg(&absolute)
                .status()?;
            if !installed.success() {
                return Ok(installed.code().map_or(ExitCode::FAILURE, |c| ExitCode::from(c as u8)));
            }
            if command_exists("aapt") {
                let metadata = Command::new("aapt").args(["dump", "badging"]).arg(&absolute).output()?;
                if metadata.status.success() {
                    let output = String::from_utf8_lossy(&metadata.stdout);
                    if let Some(package) = output.lines().find_map(parse_aapt_package) {
                        eprintln!("APK instalado; iniciando {package} en Waydroid.");
                        return run("waydroid", [OsString::from("app"), OsString::from("launch"), OsString::from(package)]);
                    }
                }
            }
            eprintln!("APK instalado. No se pudo determinar el package ID para abrirlo; inicia la app desde el menú Waydroid.");
            Ok(ExitCode::SUCCESS)
        }
        Route::AndroidDex => Err(io::Error::other("Un .dex aislado no es una aplicación Android instalable. Usa el .apk original con manifiesto, recursos y firma.")),
        Route::MacOs => {
            require_program("darling", "intentar ejecutar un binario Mach-O en Darling")?;
            let path_inside_prefix = Path::new("/Volumes/SystemRoot")
                .join(absolute.strip_prefix("/").map_err(|_| io::Error::other("La ruta Mach-O debe ser absoluta."))?);
            let executable = path_inside_prefix.to_str()
                .ok_or_else(|| io::Error::other("Darling solo puede recibir rutas UTF-8 en esta versión."))?;
            let mut command = vec![shell_quote(executable)];
            for argument in extra {
                let argument = argument.to_str()
                    .ok_or_else(|| io::Error::other("Darling solo puede recibir argumentos UTF-8 en esta versión."))?;
                command.push(shell_quote(argument));
            }
            run("darling", [OsString::from("shell"), OsString::from(command.join(" "))])
        }
        Route::Wasm => {
            require_program("wasmtime", "ejecutar un módulo WebAssembly/WASI")?;
            let mut args = vec![OsString::from("run"), absolute.into_os_string()];
            args.extend_from_slice(extra);
            run("wasmtime", args)
        }
        Route::ChromeExtension => {
            require_program("chromium", "mostrar el administrador de extensiones aislado")?;
            let profile = env::var_os("HOME")
                .map(PathBuf::from)
                .unwrap_or_else(|| PathBuf::from("/tmp"))
                .join(".local/share/nexus/chromium-extension-preview");
            fs::create_dir_all(&profile)?;
            let instructions = format!("CRX es una extensión, no una aplicación ejecutable. Se abrirá un perfil Chromium separado. Arrastra el archivo a chrome://extensions y comprueba editor y permisos antes de aceptar la instalación.\n\n{}", absolute.display());
            if command_exists("zenity") {
                let _ = Command::new("zenity")
                    .args(["--info", "--width=560", "--title=Nexus OmniSubsystem", "--text"])
                    .arg(&instructions)
                    .status()?;
            } else {
                eprintln!("{instructions}");
            }
            run("chromium", [
                OsString::from("--no-first-run"),
                OsString::from("--no-default-browser-check"),
                OsString::from(format!("--user-data-dir={}", profile.display())),
                OsString::from("--app=chrome://extensions/"),
            ])
        }
        Route::DebianPackage => {
            require_program("pkexec", "autorizar la instalación del paquete Debian")?;
            require_program("apt-get", "instalar un paquete Debian local")?;
            if !confirm("Se solicitará autorización para instalar este paquete Debian y sus dependencias.", &absolute)? {
                return Ok(ExitCode::SUCCESS);
            }
            run("pkexec", [
                OsString::from("apt-get"), OsString::from("install"),
                OsString::from("--"), absolute.into_os_string(),
            ])
        }
        Route::NativeElf => Err(io::Error::other("ELF pertenece al kernel/loader nativo de Linux y no debe volver a encadenarse por Nexus OmniLoader.")),
        Route::Unknown => Err(io::Error::other("Formato no reconocido o sin ruta compatible configurada; no se ejecutó el archivo.")),
    }
}

fn register_binfmt() -> io::Result<()> {
    if !Path::new(BINFMT_STATUS).exists() {
        let status = Command::new("mount")
            .args(["-t", "binfmt_misc", "binfmt_misc", "/proc/sys/fs/binfmt_misc"])
            .status()?;
        if !status.success() && !Path::new(BINFMT_STATUS).exists() {
            return Err(io::Error::other("El kernel no expone binfmt_misc. Habilita CONFIG_BINFMT_MISC y monta /proc/sys/fs/binfmt_misc."));
        }
    }
    let register = Path::new(BINFMT_REGISTER);
    if !register.exists() {
        return Err(io::Error::new(io::ErrorKind::NotFound, "No existe el nodo binfmt_misc/register."));
    }
    for rule in RULES {
        let entry = Path::new("/proc/sys/fs/binfmt_misc").join(rule.name);
        if entry.exists() {
            let current = fs::read_to_string(&entry)?;
            if !current.contains(LOADER) {
                return Err(io::Error::other(format!("La regla {} ya existe y apunta a otro intérprete; se conserva sin sobrescribir.", rule.name)));
            }
            if current.lines().any(|line| line == "disabled") {
                fs::write(&entry, b"1")?;
            }
            continue;
        }
        let mut node = OpenOptionsWrite::open(register)?;
        node.write_all(&registration_bytes(rule))?;
    }
    Ok(())
}

fn parse_aapt_package(line: &str) -> Option<&str> {
    let value = line.strip_prefix("package: name='")?;
    let end = value.find('\'')?;
    let package = &value[..end];
    (!package.is_empty() && package.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'.' || b == b'_')).then_some(package)
}

fn shell_quote(value: &str) -> String {
    format!("'{}'", value.replace('\'', "'\\''"))
}

struct OpenOptionsWrite;
impl OpenOptionsWrite {
    fn open(path: &Path) -> io::Result<File> {
        fs::OpenOptions::new().write(true).open(path)
    }
}

fn usage() {
    eprintln!("Uso: nexus-omniloader --register-binfmt | ARCHIVO [ARGUMENTOS…]\n       ELF se ejecuta directamente por el kernel de Linux; .deb requiere confirmación.");
}

fn main() -> ExitCode {
    let mut args = env::args_os().skip(1);
    let Some(first) = args.next() else { usage(); return ExitCode::from(2); };
    if first == OsStr::new("--register-binfmt") {
        return match register_binfmt() {
            Ok(()) => { println!("Nexus OmniSubsystem: reglas binfmt_misc registradas."); ExitCode::SUCCESS }
            Err(error) => { eprintln!("nexus-omniloader: {error}"); ExitCode::FAILURE }
        };
    }
    match dispatch(Path::new(&first), &args.collect::<Vec<_>>()) {
        Ok(code) => code,
        Err(error) => { eprintln!("nexus-omniloader: {error}"); ExitCode::FAILURE }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::Path;

    #[test]
    fn routes_supported_magics_and_extensions() {
        assert_eq!(route(Path::new("run.exe"), b"MZ"), Route::Windows);
        assert_eq!(route(Path::new("install.msi"), &[0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]), Route::WindowsInstaller);
        assert_eq!(route(Path::new("app.apk"), b"PK\x03\x04"), Route::AndroidApk);
        assert_eq!(route(Path::new("APP.APK"), b"PK\x03\x04"), Route::AndroidApk);
        assert_eq!(route(Path::new("classes.dex"), b"dex\n035\0"), Route::AndroidDex);
        assert_eq!(route(Path::new("app"), b"\x7fELF\x02"), Route::NativeElf);
        assert_eq!(route(Path::new("app"), &[0xcf, 0xfa, 0xed, 0xfe]), Route::MacOs);
        assert_eq!(route(Path::new("app"), b"\0asm\x01\0\0\0"), Route::Wasm);
        assert_eq!(route(Path::new("addon.crx"), b"Cr24"), Route::ChromeExtension);
        assert_eq!(route(Path::new("package.deb"), b"!<arch>\n"), Route::DebianPackage);
        assert_eq!(route(Path::new("fake.apk"), b"not a zip"), Route::Unknown);
        assert_eq!(route(Path::new("fake.crx"), b"not a crx"), Route::Unknown);
        assert_eq!(route(Path::new("fake.deb"), b"not an ar archive"), Route::Unknown);
    }

    #[test]
    fn zip_files_are_not_automatically_treated_as_apks() {
        assert_eq!(route(Path::new("download.zip"), b"PK\x03\x04"), Route::Unknown);
    }

    #[test]
    fn registered_rules_are_namespaced_and_point_to_this_binary() {
        assert_eq!(RULES.len(), 11);
        assert!(RULES.iter().all(|r| r.name.starts_with("nexus-")));
        assert!(RULES.iter().all(|r| registration_bytes(r).windows(LOADER.len()).any(|w| w == LOADER.as_bytes())));
        assert!(registration_bytes(&RULES[7]).windows(4).any(|w| w == [0xfe, 0xed, 0xfa, 0xcf]));
    }

    #[test]
    fn parses_only_package_ids_from_aapt_badging() {
        assert_eq!(parse_aapt_package("package: name='com.example.reader' versionCode='4'"), Some("com.example.reader"));
        assert_eq!(parse_aapt_package("package: name='; touch /tmp/pwned'"), None);
        assert_eq!(parse_aapt_package("application: label='Sample'"), None);
    }

    #[test]
    fn darling_shell_arguments_are_single_quoted() {
        assert_eq!(shell_quote("/Volumes/SystemRoot/home/My App/run"), "'/Volumes/SystemRoot/home/My App/run'");
        assert_eq!(shell_quote("a'b"), "'a'\\''b'");
    }
}
