//! Linux userspace dispatcher for Nexus. Kernel binfmt_misc passes the path to
//! this program; all compatibility work is delegated to installed runtimes.

use std::env;
use std::ffi::{OsStr, OsString};
use std::fs::{self, File, OpenOptions};
use std::io::{self, IsTerminal, Read, Seek, SeekFrom, Write};
use std::os::unix::fs::OpenOptionsExt;
use std::sync::atomic::{AtomicU64, Ordering};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};

const BINFMT_REGISTER: &str = "/proc/sys/fs/binfmt_misc/register";
const BINFMT_STATUS: &str = "/proc/sys/fs/binfmt_misc/status";
const LOADER: &str = "/usr/bin/nexus-omniloader";
const WAYDROID_PREFLIGHT: &str = "/usr/lib/nexus/nexus-waydroid-preflight";
const MAX_ZIP_LISTING: usize = 8 * 1024 * 1024;
const MAX_MANIFEST_SIZE: usize = 4 * 1024 * 1024;
const MAX_CRX_SIZE: u64 = 512 * 1024 * 1024;
const FLATHUB_REPO: &str = "https://dl.flathub.org/repo/flathub.flatpakrepo";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Route {
    Windows,
    WindowsUnsupportedArchitecture(u16),
    WindowsInstaller,
    AndroidApk,
    AndroidDex,
    IosIpa,
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
    BinfmtRule { name: "nexus-ipa", matcher: Matcher::Extension("ipa") },
    BinfmtRule { name: "nexus-ipa-upper", matcher: Matcher::Extension("IPA") },
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
        "ipa" if prefix.starts_with(b"PK\x03\x04") => return Route::IosIpa,
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
        (BinaryFormat::PeCandidate, _) => match pe_machine(prefix) {
            // The staged Wine bridge currently targets the x86 and x86_64
            // Windows ABIs. A DOS MZ header alone is not enough to dispatch.
            Some(0x014c) | Some(0x8664) => Route::Windows,
            Some(machine) => Route::WindowsUnsupportedArchitecture(machine),
            None => Route::Unknown,
        },
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
    if Path::new(program).is_absolute() {
        return Path::new(program).is_file();
    }
    env::split_paths(&env::var_os("PATH").unwrap_or_default())
        .map(|dir| dir.join(program))
        .any(|candidate| candidate.is_file())
}

fn subsystem_helper(name: &str) -> Option<PathBuf> {
    if let Some(path) = env::var_os("NEXUS_SUBSYSTEM_HELPER") {
        let path = PathBuf::from(path).join(name);
        if path.is_file() { return Some(path); }
    }
    let installed = Path::new("/usr/lib/nexus").join(name);
    if installed.is_file() { return Some(installed); }
    env::current_exe().ok()
        .and_then(|binary| binary.parent()?.parent().map(|root| root.join("lib/nexus").join(name)))
        .filter(|path| path.is_file())
}

fn cyber_glass_dialog(
    ecosystem: &str,
    title: &str,
    message: &str,
    path: Option<&Path>,
    question: bool,
) -> io::Result<Option<bool>> {
    if env::var_os("DISPLAY").is_none() && env::var_os("WAYLAND_DISPLAY").is_none() {
        return Ok(None);
    }
    let Some(helper) = subsystem_helper("nexus-omniloader-ui.py") else { return Ok(None); };
    let mut command = Command::new("python3");
    command.arg(helper)
        .args(["--ecosystem", ecosystem, "--title", title, "--message", message]);
    if question { command.arg("--question"); }
    if let Some(path) = path { command.arg("--path").arg(path); }
    let status = command.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null()).status();
    match status {
        Ok(status) if status.success() => Ok(Some(true)),
        Ok(status) if question && status.code() == Some(1) => Ok(Some(false)),
        _ => Ok(None),
    }
}

fn play_system_sound(event: &str) {
    if env::var_os("NEXUS_SOUND_DISABLED").is_some() { return; }
    let Some(helper) = subsystem_helper("nexus-system-sound.py") else { return; };
    let _ = Command::new("python3")
        .arg(helper).arg(event)
        .stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null())
        .spawn();
}

fn zip_listing(path: &Path) -> io::Result<Vec<String>> {
    require_program("unzip", "inspeccionar el contenedor sin extraer rutas")?;
    let mut child = Command::new("unzip")
        .args(["-Z1"])
        .arg(path)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()?;
    let mut listing = Vec::new();
    child.stdout.take().ok_or_else(|| io::Error::other("No se pudo leer el directorio ZIP."))?
        .take((MAX_ZIP_LISTING + 1) as u64).read_to_end(&mut listing)?;
    if listing.len() > MAX_ZIP_LISTING {
        let _ = child.kill();
        let _ = child.wait();
        return Err(io::Error::other("El directorio comprimido supera el límite de 8 MiB."));
    }
    if !child.wait()?.success() {
        return Err(io::Error::other("El contenedor no tiene un directorio ZIP válido."));
    }
    let text = String::from_utf8(listing)
        .map_err(|_| io::Error::other("El directorio ZIP contiene nombres que no son UTF-8."))?;
    let entries: Vec<String> = text.lines().map(str::to_owned).collect();
    if entries.iter().any(|entry| entry.starts_with('/') || entry.contains('\\') || entry.split('/').any(|part| part == "..")) {
        return Err(io::Error::other("El contenedor incluye nombres de ruta inseguros."));
    }
    Ok(entries)
}

fn zip_member(path: &Path, member: &str, limit: usize) -> io::Result<Vec<u8>> {
    let mut child = Command::new("unzip")
        .args(["-p"])
        .arg(path)
        .arg(member)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()?;
    let mut bytes = Vec::new();
    child.stdout.take().ok_or_else(|| io::Error::other("No se pudo leer un miembro del ZIP."))?
        .take((limit + 1) as u64).read_to_end(&mut bytes)?;
    if bytes.len() > limit {
        let _ = child.kill();
        let _ = child.wait();
        return Err(io::Error::other(format!("El miembro {member} supera el límite de {} bytes.", limit)));
    }
    if !child.wait()?.success() {
        return Err(io::Error::other(format!("No se pudo leer {member} desde el contenedor.")));
    }
    Ok(bytes)
}

struct TempCrxZip(PathBuf);

impl Drop for TempCrxZip {
    fn drop(&mut self) { let _ = fs::remove_file(&self.0); }
}

static TEMP_CRX_SEQUENCE: AtomicU64 = AtomicU64::new(0);

/// Remove the CRX envelope before invoking Info-ZIP: Info-ZIP warns about the
/// prepended bytes and exits 1 even when it can list the embedded ZIP.
fn materialize_crx_zip(path: &Path, offset: usize) -> io::Result<TempCrxZip> {
    let size = fs::metadata(path)?.len();
    if size > MAX_CRX_SIZE { return Err(io::Error::other("CRX supera el límite de inspección de 512 MiB.")); }
    let offset = u64::try_from(offset).map_err(|_| io::Error::other("Offset ZIP CRX fuera de rango."))?;
    if size <= offset + 4 { return Err(io::Error::other("CRX no contiene datos ZIP completos.")); }
    for _ in 0..32 {
        let sequence = TEMP_CRX_SEQUENCE.fetch_add(1, Ordering::Relaxed);
        let temp_path = env::temp_dir().join(format!("nexus-crx-{}-{sequence}.zip", std::process::id()));
        let mut output = match OpenOptions::new().write(true).create_new(true).mode(0o600).open(&temp_path) {
            Ok(file) => file,
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => continue,
            Err(error) => return Err(error),
        };
        let guard = TempCrxZip(temp_path);
        let mut input = File::open(path)?;
        input.seek(SeekFrom::Start(offset))?;
        let mut signature = [0u8; 4];
        input.read_exact(&mut signature)?;
        if signature != *b"PK\x03\x04" { return Err(io::Error::other("El payload CRX no comienza con una cabecera ZIP local.")); }
        input.seek(SeekFrom::Start(offset))?;
        if io::copy(&mut input, &mut output)? != size - offset { return Err(io::Error::other("Copia incompleta del payload ZIP CRX.")); }
        output.flush()?;
        return Ok(guard);
    }
    Err(io::Error::new(io::ErrorKind::AlreadyExists, "No se pudo crear un archivo temporal seguro para CRX."))
}

fn zip_member_prefix(path: &Path, member: &str, count: usize) -> io::Result<Vec<u8>> {
    let mut child = Command::new("unzip")
        .args(["-p"])
        .arg(path)
        .arg(member)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()?;
    let mut bytes = vec![0; count];
    let mut stdout = child.stdout.take().ok_or_else(|| io::Error::other("No se pudo leer el encabezado DEX."))?;
    let mut read = 0;
    while read < count {
        let n = stdout.read(&mut bytes[read..])?;
        if n == 0 { break; }
        read += n;
    }
    bytes.truncate(read);
    if read == count {
        let _ = child.kill();
        let _ = child.wait();
    } else if !child.wait()?.success() {
        return Err(io::Error::other(format!("No se pudo leer {member} desde el APK.")));
    }
    Ok(bytes)
}

fn inspect_apk(path: &Path) -> io::Result<String> {
    let entries = zip_listing(path)?;
    if entries.iter().filter(|entry| entry.as_str() == "AndroidManifest.xml").count() != 1 {
        return Err(io::Error::other("El ZIP no incluye AndroidManifest.xml."));
    }
    if entries.iter().filter(|entry| entry.as_str() == "classes.dex").count() != 1 {
        return Err(io::Error::other("El APK no incluye classes.dex; no se puede validar el payload Android."));
    }
    let manifest = zip_member(path, "AndroidManifest.xml", MAX_MANIFEST_SIZE)?;
    let package = omni_loader::package_inspector::android_package_id(&manifest)
        .map_err(io::Error::other)?;
    let dex = zip_member_prefix(path, "classes.dex", 112)?;
    if !omni_loader::package_inspector::valid_dex_header(&dex) {
        return Err(io::Error::other("classes.dex no tiene una cabecera DEX válida."));
    }
    Ok(package)
}

fn inspect_crx(path: &Path) -> io::Result<()> {
    let mut file = File::open(path)?;
    let mut header = vec![0; 1024 * 1024 + 13];
    let count = file.read(&mut header)?;
    header.truncate(count);
    let offset = omni_loader::package_inspector::crx_zip_offset(&header)
        .map_err(io::Error::other)?;
    let zip = materialize_crx_zip(path, offset)?;
    let entries = zip_listing(&zip.0)?;
    if entries.iter().filter(|entry| entry.as_str() == "manifest.json").count() != 1 {
        return Err(io::Error::other("CRX estructuralmente incompleto: no contiene manifest.json."));
    }
    let manifest = zip_member(&zip.0, "manifest.json", 1024 * 1024)?;
    let text = std::str::from_utf8(&manifest)
        .map_err(|_| io::Error::other("manifest.json del CRX no es UTF-8."))?;
    if !text.trim_start().starts_with('{')
        || !text.contains("manifest_version")
        || !text.contains("\"name\"")
        || !text.contains("\"version\"")
    {
        return Err(io::Error::other("manifest.json no contiene campos básicos de una extensión."));
    }
    eprintln!("CRX v{} con manifest.json validado estructuralmente (ZIP desde byte {offset}); Chromium verificará firma y permisos.", u32::from_le_bytes(header[4..8].try_into().unwrap_or([0; 4])));
    Ok(())
}

struct IpaInspection {
    bundle_path: String,
    bundle_id: String,
    display_name: String,
    executable: String,
    arm64_macho: bool,
}

impl IpaInspection {
    fn report(&self) -> String {
        format!("iOS IPA estructural válido: app={} ({}); ejecutable={}; Mach-O ARM64 móvil={}",
            self.display_name, self.bundle_id, self.executable, self.arm64_macho)
    }
}

fn is_mobile_arm64_macho(prefix: &[u8]) -> bool {
    if prefix.len() < 8 { return false; }
    let cpu = if prefix.starts_with(&[0xcf, 0xfa, 0xed, 0xfe]) {
        u32::from_le_bytes(prefix[4..8].try_into().unwrap_or([0; 4]))
    } else if prefix.starts_with(&[0xfe, 0xed, 0xfa, 0xcf]) {
        u32::from_be_bytes(prefix[4..8].try_into().unwrap_or([0; 4]))
    } else { return false; };
    cpu == 0x0100_000c
}

fn inspect_ipa(path: &Path) -> io::Result<IpaInspection> {
    let prefix = read_prefix(path)?;
    if !prefix.starts_with(b"PK\x03\x04") {
        return Err(io::Error::other("El archivo .ipa no comienza con una firma ZIP local válida."));
    }
    if fs::metadata(path)?.len() > 2 * 1024 * 1024 * 1024 {
        return Err(io::Error::other("IPA supera el límite de inspección de 2 GiB."));
    }
    if !Command::new("unzip").args(["-tqq"]).arg(path).status()?.success() {
        return Err(io::Error::other("La comprobación de integridad ZIP del IPA falló."));
    }
    let entries = zip_listing(path)?;
    let info_plists: Vec<&str> = entries.iter().map(String::as_str).filter(|entry| {
        let parts: Vec<&str> = entry.split('/').collect();
        parts.len() == 3 && parts[0] == "Payload" && parts[1].ends_with(".app") && parts[2] == "Info.plist"
    }).collect();
    if info_plists.len() != 1 {
        return Err(io::Error::other("El IPA debe contener exactamente Payload/<app>.app/Info.plist."));
    }
    let info_path = info_plists[0];
    let bundle_path = info_path.strip_suffix("/Info.plist").unwrap_or(info_path);
    let plist = zip_member(path, info_path, MAX_MANIFEST_SIZE)?;
    let parser = "import plistlib,sys\np=plistlib.loads(sys.stdin.buffer.read())\ndef clean(v): return str(v or '').replace('\\t',' ').replace('\\r',' ').replace('\\n',' ')[:256]\nsys.stdout.write('\\t'.join((clean(p.get('CFBundleIdentifier')), clean(p.get('CFBundleDisplayName') or p.get('CFBundleName')), clean(p.get('CFBundleExecutable')))))";
    let mut child = Command::new("python3").args(["-c", parser])
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null()).spawn()?;
    child.stdin.take().ok_or_else(|| io::Error::other("No se pudo enviar Info.plist al parser."))?.write_all(&plist)?;
    let parsed = child.wait_with_output()?;
    if !parsed.status.success() {
        return Err(io::Error::other("Payload/<app>.app/Info.plist no se pudo interpretar."));
    }
    let values = String::from_utf8(parsed.stdout).map_err(|_| io::Error::other("Los metadatos Info.plist no son UTF-8."))?;
    let mut fields = values.splitn(3, '\t');
    let bundle_id = fields.next().unwrap_or("").trim().to_owned();
    let display_name = fields.next().unwrap_or("").trim().to_owned();
    let executable = fields.next().unwrap_or("").trim().to_owned();
    if bundle_id.is_empty() || executable.is_empty() || executable.contains('/') || executable == "." || executable == ".." {
        return Err(io::Error::other("Info.plist no declara un CFBundleIdentifier y CFBundleExecutable seguros."));
    }
    let executable_path = format!("{bundle_path}/{executable}");
    let arm64_macho = entries.iter().any(|entry| entry == &executable_path)
        && is_mobile_arm64_macho(&zip_member_prefix(path, &executable_path, 32)?);
    Ok(IpaInspection {
        bundle_path: bundle_path.to_owned(), bundle_id,
        display_name: if display_name.is_empty() { bundle_path.rsplit('/').next().unwrap_or("iOS app").trim_end_matches(".app").to_owned() } else { display_name },
        executable, arm64_macho,
    })
}

fn pe_machine(prefix: &[u8]) -> Option<u16> {
    if !prefix.starts_with(b"MZ") || prefix.len() < 64 { return None; }
    let offset = u32::from_le_bytes(prefix.get(0x3c..0x40)?.try_into().ok()?) as usize;
    // e_lfanew is attacker-controlled. Keep the read within the bounded
    // prefix supplied by the dispatcher and require a complete COFF header.
    let signature_end = offset.checked_add(4)?;
    if prefix.get(offset..signature_end)? != b"PE\0\0" { return None; }
    let machine_at = signature_end;
    let machine_end = machine_at.checked_add(2)?;
    let section_at = machine_end;
    let section_end = section_at.checked_add(2)?;
    let optional_size_at = offset.checked_add(20)?;
    let optional_size_end = optional_size_at.checked_add(2)?;
    let machine = u16::from_le_bytes(prefix.get(machine_at..machine_end)?.try_into().ok()?);
    let section_count = u16::from_le_bytes(prefix.get(section_at..section_end)?.try_into().ok()?);
    let optional_header_size = u16::from_le_bytes(prefix.get(optional_size_at..optional_size_end)?.try_into().ok()?);
    if section_count == 0 || section_count > 96 || optional_header_size < 2 {
        return None;
    }
    let optional_at = offset.checked_add(24)?;
    let optional_end = optional_at.checked_add(optional_header_size as usize)?;
    let optional_magic_end = optional_at.checked_add(2)?;
    let optional_magic = u16::from_le_bytes(prefix.get(optional_at..optional_magic_end)?.try_into().ok()?);
    if optional_end > prefix.len()
        || !matches!(optional_magic, 0x010b | 0x020b)
        || (machine == 0x014c && optional_magic != 0x010b)
        || (matches!(machine, 0x8664 | 0xaa64) && optional_magic != 0x020b)
    {
        return None;
    }
    Some(machine)
}

fn valid_web_url(url: &str) -> bool {
    if url.bytes().any(|byte| byte.is_ascii_control() || byte.is_ascii_whitespace()) { return false; }
    if let Some(authority) = url.strip_prefix("https://") {
        return !authority.split(|c| c == '/' || c == '?' || c == '#').next().unwrap_or("").is_empty();
    }
    if let Some(authority) = url.strip_prefix("http://") {
        let host = authority.split(|c| c == '/' || c == '?' || c == '#').next().unwrap_or("");
        return host == "localhost" || host.starts_with("localhost:") || host.starts_with("127.0.0.1") || host.starts_with("[::1]");
    }
    false
}

fn valid_flatpak_id(app_id: &str) -> bool {
    let parts: Vec<&str> = app_id.split('.').collect();
    app_id.len() <= 255 && parts.len() >= 2 && parts.iter().all(|part| {
        !part.is_empty()
            && part.len() <= 63
            && part.as_bytes()[0].is_ascii_alphanumeric()
            && part.bytes().all(|byte| byte.is_ascii_alphanumeric() || byte == b'-' || byte == b'_')
    })
}

fn flatpak_install(app_id: &str) -> io::Result<ExitCode> {
    if !valid_flatpak_id(app_id) {
        return Err(io::Error::other("ID Flatpak inválido; usa un ID inverso de aplicación como org.example.App."));
    }
    require_program("flatpak", "instalar y ejecutar aplicaciones Linux Flatpak")?;
    let message = format!(
        "Nexus OmniLoader añadirá Flathub como remoto de usuario si hace falta y descargará {app_id} y sus dependencias. La aplicación se instalará en el perfil de este usuario."
    );
    if !confirm_flatpak(&message, app_id)? { return Ok(ExitCode::from(1)); }

    let remote = Command::new("flatpak")
        .args(["--user", "remote-add", "--if-not-exists", "--noninteractive", "--assumeyes", "flathub", FLATHUB_REPO])
        .status()?;
    if !remote.success() {
        return Ok(remote.code().map_or(ExitCode::FAILURE, |code| ExitCode::from(code as u8)));
    }
    run("flatpak", [
        OsString::from("install"), OsString::from("--user"), OsString::from("--noninteractive"),
        OsString::from("--assumeyes"), OsString::from("flathub"), OsString::from(app_id),
    ])
}

fn flatpak_run(app_id: &str) -> io::Result<ExitCode> {
    if !valid_flatpak_id(app_id) {
        return Err(io::Error::other("ID Flatpak inválido; usa un ID inverso de aplicación como org.example.App."));
    }
    require_program("flatpak", "ejecutar aplicaciones Linux Flatpak")?;
    run("flatpak", [OsString::from("run"), OsString::from(app_id)])
}

fn chromium_app(url: &str) -> io::Result<ExitCode> {
    if !valid_web_url(url) {
        return Err(io::Error::other("La URL de PWA debe usar HTTPS; HTTP solo se permite en localhost."));
    }
    require_program("chromium", "abrir una PWA en ventana aislada")?;
    let profile = env::var_os("NEXUS_CHROMIUM_PROFILE").map(PathBuf::from)
        .unwrap_or_else(|| env::var_os("HOME").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("/tmp"))
            .join(".local/share/nexus/chromium-pwa"));
    fs::create_dir_all(&profile)?;
    run("chromium", [
        OsString::from("--no-sandbox"),
        OsString::from("--disable-gpu"),
        OsString::from("--disable-dev-shm-usage"),
        OsString::from("--window-size=1000,660"),
        OsString::from("--password-store=basic"),
        OsString::from("--no-first-run"),
        OsString::from("--no-default-browser-check"),
        OsString::from("--window-position=260,40"),
        OsString::from(format!("--user-data-dir={}", profile.display())),
        OsString::from(format!("--app={url}")),
    ])
}

fn confirm(action: &str, path: &Path) -> io::Result<bool> {
    if let Some(accepted) = cyber_glass_dialog(
        "Android", "Nexus Android APK response", action, Some(path), true,
    )? {
        return Ok(accepted);
    }
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

fn confirm_flatpak(action: &str, app_id: &str) -> io::Result<bool> {
    // CI evidence installs a known Flathub package through OmniStore in a
    // disposable user profile; allow that non-interactive smoke path to accept
    // the same explicit user consent required by the interactive UI.
    if env::var("NEXUS_SMOKE_AUTOCONFIRM").as_deref() == Ok("1") {
        return Ok(true);
    }
    if let Some(accepted) = cyber_glass_dialog(
        "Linux", "Nexus OmniLoader · Flatpak", action, None, true,
    )? {
        return Ok(accepted);
    }
    if command_exists("zenity") {
        return Ok(Command::new("zenity")
            .args(["--question", "--width=520", "--title=Nexus OmniLoader", "--text"])
            .arg(format!("{action}\n\nID: {app_id}"))
            .status()?
            .success());
    }
    if !atty_stdin() {
        return Err(io::Error::other("No hay interfaz de confirmación (zenity) ni terminal interactiva; acción cancelada."));
    }
    eprint!("{action}\nID: {app_id}\n¿Continuar? [s/N] ");
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
    let selected_route = route(&absolute, &prefix);
    if selected_route != Route::Unknown {
        play_system_sound("invoke");
    }
    match selected_route {
        Route::Windows => {
            let runtime = if pe_machine(&prefix) == Some(0x8664) {
                if command_exists("wine64") { "wine64" }
                else if Path::new("/usr/lib/wine/wine64").is_file() { "/usr/lib/wine/wine64" }
                else { "wine" }
            } else { "wine" };
            require_program(runtime, "ejecutar aplicaciones de Windows mediante Wine")?;
            let mut args = vec![absolute.into_os_string()];
            args.extend_from_slice(extra);
            run(runtime, args)
        }
        Route::WindowsInstaller => {
            require_program("wine", "instalar paquetes MSI mediante Windows Installer de Wine")?;
            let mut args = vec![OsString::from("msiexec"), OsString::from("/i"), absolute.into_os_string()];
            args.extend_from_slice(extra);
            run("wine", args)
        }
        Route::WindowsUnsupportedArchitecture(machine) => Err(io::Error::other(format!(
            "El PE declara arquitectura 0x{machine:04x}; la ruta Wine de Nexus solo admite PE x86 (0x014c) y x86_64 (0x8664)."
        ))),
        Route::AndroidApk => {
            let package = inspect_apk(&absolute)?;
            if env::var("NEXUS_ANDROID_TARGET").as_deref() == Ok("adb") {
                require_program("adb", "instalar la aplicación Android en el dispositivo o emulador ADB")?;
                if env::var("NEXUS_SMOKE_AUTOCONFIRM").as_deref() != Ok("1")
                    && !confirm("Se instalará esta aplicación en el dispositivo Android activo.", &absolute)?
                {
                    return Ok(ExitCode::SUCCESS);
                }
                let installed = Command::new("adb")
                    .args([OsString::from("install"), OsString::from("-r")])
                    .arg(&absolute)
                    .status()?;
                if !installed.success() {
                    return Ok(installed.code().map_or(ExitCode::FAILURE, |c| ExitCode::from(c as u8)));
                }
                eprintln!("APK {package} instalado en el dispositivo Android activo; solicitando la actividad de inicio.");
                return run("adb", [
                    OsString::from("shell"), OsString::from("monkey"),
                    OsString::from("-p"), OsString::from(package), OsString::from("1"),
                ]);
            }
            require_program("waydroid", "instalar aplicaciones Android")?;
            if !confirm("Waydroid instalará esta aplicación Android en el entorno de usuario.", &absolute)? {
                return Ok(ExitCode::SUCCESS);
            }
            require_program(WAYDROID_PREFLIGHT, "comprobar el dispositivo Binder y el contenedor Waydroid")?;
            let preflight = Command::new(WAYDROID_PREFLIGHT).status()?;
            if !preflight.success() {
                return Err(io::Error::other("Waydroid no está listo. Revisa Binder, inicializa la imagen Android desde el asistente y vuelve a intentar."));
            }
            let installed = Command::new("waydroid")
                .args(["app", "install"])
                .arg(&absolute)
                .status()?;
            if !installed.success() {
                return Ok(installed.code().map_or(ExitCode::FAILURE, |c| ExitCode::from(c as u8)));
            }
            eprintln!("APK {package} instalado; abriendo en Waydroid.");
            run("waydroid", [OsString::from("app"), OsString::from("launch"), OsString::from(package)])
        }
        Route::AndroidDex => Err(io::Error::other("Un .dex aislado no es una aplicación Android instalable. Usa el .apk original con manifiesto, recursos y firma.")),
        Route::IosIpa => {
            let inspection = inspect_ipa(&absolute)?;
            Err(io::Error::other(format!(
                "{}; this Linux build cannot execute iOS Mach-O code. Run the signed app in the Apple Silicon iOS Simulator workflow.",
                inspection.report()
            )))
        }
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
            inspect_crx(&absolute)?;
            require_program("chromium", "mostrar el administrador de extensiones aislado")?;
            let profile = env::var_os("HOME")
                .map(PathBuf::from)
                .unwrap_or_else(|| PathBuf::from("/tmp"))
                .join(".local/share/nexus/chromium-extension-preview");
            fs::create_dir_all(&profile)?;
            let instructions = format!("CRX es una extensión, no una aplicación ejecutable. Se abrirá un perfil Chromium separado. Arrastra el archivo a chrome://extensions y comprueba editor y permisos antes de aceptar la instalación.\n\n{}", absolute.display());
            let response = cyber_glass_dialog(
                "ChromeOS / CRX", "Nexus ChromeOS CRX response", &instructions, Some(&absolute), false,
            )?;
            if response.is_none() {
                if command_exists("zenity") {
                    let _ = Command::new("zenity")
                        .args(["--info", "--width=560", "--title=Nexus OmniSubsystem", "--text"])
                        .arg(&instructions)
                        .status()?;
                } else {
                    eprintln!("{instructions}");
                }
            }
            run("chromium", [
                OsString::from("--no-sandbox"),
                OsString::from("--disable-gpu"),
                OsString::from("--disable-dev-shm-usage"),
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
        // ELF is not registered with binfmt_misc; this route is only reached
        // when a user explicitly opens a native Linux executable with Omni.
        Route::NativeElf => {
            let status = Command::new(&absolute).args(extra).status()?;
            Ok(status.code().map_or(ExitCode::FAILURE, |code| ExitCode::from(code as u8)))
        }
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

#[cfg(test)]
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
    eprintln!("Uso: nexus-omniloader --register-binfmt | --inspect-apk ARCHIVO | --inspect-crx ARCHIVO | --inspect-ipa ARCHIVO | --webapp HTTPS_URL | --install-flatpak APP_ID | --run-flatpak APP_ID | ARCHIVO [ARGUMENTOS…]\n       Flatpak/.deb/APK requieren confirmación; ELF se ejecuta de forma nativa en Linux.");
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
    if first == OsStr::new("--inspect-apk") || first == OsStr::new("--inspect-crx") || first == OsStr::new("--inspect-ipa") {
        let Some(path) = args.next() else { usage(); return ExitCode::from(2); };
        let path = Path::new(&path);
        let result = if first == OsStr::new("--inspect-apk") {
            inspect_apk(path).map(|package| { println!("APK válido: package={package}; classes.dex=valid"); })
        } else if first == OsStr::new("--inspect-crx") {
            inspect_crx(path).map(|()| println!("CRX válido estructuralmente; la firma queda a cargo de Chromium."))
        } else {
            inspect_ipa(path).map(|inspection| println!("{}; bundle={}", inspection.report(), inspection.bundle_path))
        };
        return match result { Ok(()) => ExitCode::SUCCESS, Err(error) => { eprintln!("nexus-omniloader: {error}"); ExitCode::FAILURE } };
    }
    if first == OsStr::new("--webapp") {
        let Some(url) = args.next() else { usage(); return ExitCode::from(2); };
        return match url.to_str().ok_or_else(|| io::Error::other("La URL no es UTF-8.")).and_then(chromium_app) {
            Ok(code) => code,
            Err(error) => { eprintln!("nexus-omniloader: {error}"); ExitCode::FAILURE }
        };
    }
    if first == OsStr::new("--install-flatpak") || first == OsStr::new("--run-flatpak") {
        let Some(app_id) = args.next().and_then(|value| value.into_string().ok()) else { usage(); return ExitCode::from(2); };
        let result = if first == OsStr::new("--install-flatpak") {
            flatpak_install(&app_id)
        } else {
            flatpak_run(&app_id)
        };
        return match result { Ok(code) => code, Err(error) => { eprintln!("nexus-omniloader: {error}"); ExitCode::FAILURE } };
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
        let mut pe = valid_pe(0x8664, 0x020b);
        assert_eq!(route(Path::new("run.exe"), &pe), Route::Windows);
        pe = valid_pe(0x014c, 0x010b);
        assert_eq!(route(Path::new("run.exe"), &pe), Route::Windows);
        assert_eq!(route(Path::new("install.msi"), &[0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]), Route::WindowsInstaller);
        assert_eq!(route(Path::new("app.apk"), b"PK\x03\x04"), Route::AndroidApk);
        assert_eq!(route(Path::new("app.ipa"), b"PK\x03\x04"), Route::IosIpa);
        assert_eq!(route(Path::new("APP.IPA"), b"PK\x03\x04"), Route::IosIpa);
        assert_eq!(route(Path::new("fake.ipa"), b"not a zip"), Route::Unknown);
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

    fn valid_pe(machine: u16, optional_magic: u16) -> Vec<u8> {
        let mut pe = vec![0u8; 256];
        pe[..2].copy_from_slice(b"MZ");
        pe[0x3c..0x40].copy_from_slice(&64u32.to_le_bytes());
        pe[64..68].copy_from_slice(b"PE\0\0");
        pe[68..70].copy_from_slice(&machine.to_le_bytes());
        pe[70..72].copy_from_slice(&1u16.to_le_bytes());
        pe[84..86].copy_from_slice(&112u16.to_le_bytes());
        pe[88..90].copy_from_slice(&optional_magic.to_le_bytes());
        pe
    }

    #[test]
    fn rejects_mz_stubs_and_routes_unsupported_pe_architectures_explicitly() {
        assert_eq!(route(Path::new("not-pe.exe"), b"MZ"), Route::Unknown);
        assert_eq!(
            route(Path::new("arm.exe"), &valid_pe(0xaa64, 0x020b)),
            Route::WindowsUnsupportedArchitecture(0xaa64)
        );
        assert_eq!(route(Path::new("bad-magic.exe"), &valid_pe(0x8664, 0x010b)), Route::Unknown);
    }

    #[test]
    fn zip_files_are_not_automatically_treated_as_apks() {
        assert_eq!(route(Path::new("download.zip"), b"PK\x03\x04"), Route::Unknown);
    }

    #[test]
    fn accepts_safe_reverse_dns_flatpak_ids_only() {
        assert!(valid_flatpak_id("org.gimp.GIMP"));
        assert!(valid_flatpak_id("com.example.app_2"));
        assert!(!valid_flatpak_id(""));
        assert!(!valid_flatpak_id("org"));
        assert!(!valid_flatpak_id("org..App"));
        assert!(!valid_flatpak_id("-org.example.App"));
        assert!(!valid_flatpak_id("org.example.App;rm"));
        assert!(!valid_flatpak_id("--help"));
    }

    #[test]
    fn registered_rules_are_namespaced_and_point_to_this_binary() {
        assert_eq!(RULES.len(), 13);
        assert!(RULES.iter().all(|r| r.name.starts_with("nexus-")));
        assert!(RULES.iter().all(|r| registration_bytes(r).windows(LOADER.len()).any(|w| w == LOADER.as_bytes())));
        assert!(registration_bytes(&RULES[7]).windows(4).any(|w| w == [0xfe, 0xed, 0xfa, 0xcf]));
        assert_eq!(RULES[11].name, "nexus-ipa");
        assert_eq!(RULES[12].name, "nexus-ipa-upper");
    }

    #[test]
    fn identifies_only_mobile_arm64_macho_headers() {
        let mut macho = vec![0xcf, 0xfa, 0xed, 0xfe];
        macho.extend_from_slice(&0x0100_000cu32.to_le_bytes());
        assert!(is_mobile_arm64_macho(&macho));
        macho[4..8].copy_from_slice(&0x0100_0007u32.to_le_bytes());
        assert!(!is_mobile_arm64_macho(&macho));
        assert!(!is_mobile_arm64_macho(b"not macho"));
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

    #[test]
    fn pe_machine_is_read_only_after_valid_dos_and_pe_headers() {
        let mut pe = valid_pe(0x8664, 0x020b);
        assert_eq!(pe_machine(&pe), Some(0x8664));
        pe[64] = 0;
        assert_eq!(pe_machine(&pe), None);
        pe = valid_pe(0x8664, 0x020b);
        pe[0x3c..0x40].copy_from_slice(&u32::MAX.to_le_bytes());
        assert_eq!(pe_machine(&pe), None);
        assert_eq!(pe_machine(&valid_pe(0x014c, 0x020b)), None);
    }

    #[test]
    fn web_app_urls_reject_non_web_schemes_and_insecure_hosts() {
        assert!(valid_web_url("https://example.com/app"));
        assert!(valid_web_url("http://localhost:3000/app"));
        assert!(!valid_web_url("http://example.com/app"));
        assert!(!valid_web_url("file:///etc/passwd"));
        assert!(!valid_web_url("https://example.com/\n--no-sandbox"));
    }
}
