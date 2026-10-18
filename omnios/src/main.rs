use ovmf_prebuilt::{Arch, FileType, Prebuilt, Source};
use std::process::{Command, ExitCode};

const SUCCESS_MARKER: &str = "OMNIOS_BOOT_OK";
const QEMU_SUCCESS_STATUS: i32 = 33; // isa-debug-exit: (0x10 << 1) | 1

fn main() -> ExitCode {
    let mode = std::env::args().nth(1).as_deref().unwrap_or("help").to_owned();
    match mode.as_str() {
        "uefi-smoke" => uefi_smoke(),
        "help" | "--help" | "-h" => {
            println!("Usage: cargo run --release -- uefi-smoke");
            ExitCode::SUCCESS
        }
        other => {
            eprintln!("Modo desconocido: {other}");
            ExitCode::from(2)
        }
    }
}

fn uefi_smoke() -> ExitCode {
    let ovmf = match Prebuilt::fetch(Source::LATEST, "target/ovmf") {
        Ok(files) => files,
        Err(error) => {
            eprintln!("No se pudo preparar OVMF para UEFI: {error}");
            return ExitCode::FAILURE;
        }
    };
    let code = ovmf.get_file(Arch::X64, FileType::Code);
    let vars = ovmf.get_file(Arch::X64, FileType::Vars);
    let image = env!("OMNIOS_UEFI_IMAGE");

    let result = Command::new("qemu-system-x86_64")
        .args(["-machine", "q35", "-m", "512M", "-display", "none"])
        .args(["-serial", "stdio", "-monitor", "none", "-no-reboot", "-no-shutdown"])
        .args(["-device", "isa-debug-exit,iobase=0xf4,iosize=0x04"])
        .arg("-drive")
        .arg(format!("format=raw,file={image}"))
        .arg("-drive")
        .arg(format!(
            "if=pflash,format=raw,unit=0,file={},readonly=on",
            code.display()
        ))
        .arg("-drive")
        .arg(format!(
            "if=pflash,format=raw,unit=1,file={},snapshot=on",
            vars.display()
        ))
        .output();

    let output = match result {
        Ok(output) => output,
        Err(error) => {
            eprintln!("No se pudo ejecutar QEMU: {error}");
            return ExitCode::FAILURE;
        }
    };
    let serial = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    print!("{serial}");
    eprint!("{stderr}");

    if serial.contains("OMNIOS_KERNEL_PANIC") {
        eprintln!("QEMU mostró el marcador de kernel panic.");
        return ExitCode::FAILURE;
    }
    if output.status.code() == Some(QEMU_SUCCESS_STATUS) && serial.contains(SUCCESS_MARKER) {
        println!("QEMU UEFI smoke test: boot marker and debug-exit success verified.");
        ExitCode::SUCCESS
    } else {
        eprintln!(
            "QEMU no confirmó el arranque: status={:?}, marker_present={}",
            output.status.code(),
            serial.contains(SUCCESS_MARKER)
        );
        ExitCode::FAILURE
    }
}
