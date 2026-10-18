#![no_std]
#![no_main]

use bootloader_api::{BootInfo, entry_point};
use core::fmt::Write;
use uart_16550::backend::PioBackend;
use uart_16550::{Config, Uart16550Tty};

mod syscall {
    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    #[repr(u8)]
    pub enum Personality {
        LinuxX86_64 = 1,
        WindowsNtX64 = 2,
        DarwinX64 = 3,
    }

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    pub enum Primitive {
        ConsoleWrite,
        ProcessExit,
    }

    #[derive(Clone, Copy)]
    pub struct Route {
        pub number: u64,
        pub primitive: Primitive,
    }

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    pub enum DispatchError {
        UnknownPersonality,
        UnsupportedCall,
    }

    // Linux x86_64 raw syscall numbers from its ABI. This table describes a
    // route; it does not yet implement copy_from_user, file descriptors, or exit.
    const LINUX_X64: &[Route] = &[
        Route { number: 1, primitive: Primitive::ConsoleWrite },
        Route { number: 60, primitive: Primitive::ProcessExit },
    ];

    // These are OmniBridge thunk IDs, deliberately not undocumented raw NT or
    // XNU syscall numbers. A future versioned user-mode bridge normalizes APIs.
    const WINDOWS_NT_X64: &[Route] = &[
        Route { number: 0xF000_0001, primitive: Primitive::ConsoleWrite },
        Route { number: 0xF000_0002, primitive: Primitive::ProcessExit },
    ];
    const DARWIN_X64: &[Route] = &[
        Route { number: 0xE000_0001, primitive: Primitive::ConsoleWrite },
        Route { number: 0xE000_0002, primitive: Primitive::ProcessExit },
    ];

    fn table(personality: Personality) -> &'static [Route] {
        match personality {
            Personality::LinuxX86_64 => LINUX_X64,
            Personality::WindowsNtX64 => WINDOWS_NT_X64,
            Personality::DarwinX64 => DARWIN_X64,
        }
    }

    /// Selects the immutable route table from the personality assigned at exec.
    /// The real trap entry and argument translation are future kernel work.
    pub fn dispatch(personality: Personality, number: u64) -> Result<Primitive, DispatchError> {
        let entries = table(personality);
        entries
            .binary_search_by_key(&number, |route| route.number)
            .map(|index| entries[index].primitive)
            .map_err(|_| DispatchError::UnsupportedCall)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u32)]
enum QemuExitCode {
    Success = 0x10,
    Failure = 0x11,
}

fn serial() -> Uart16550Tty<PioBackend> {
    // The first target is QEMU's x86_64 16550-compatible COM1 at 0x3f8.
    unsafe { Uart16550Tty::new_port(0x3F8, Config::default()) }
        .expect("initialize QEMU serial port")
}

fn exit_qemu(code: QemuExitCode) -> ! {
    use x86_64::instructions::port::Port;
    unsafe {
        let mut port = Port::new(0xf4);
        port.write(code as u32);
    }
    loop {
        core::hint::spin_loop();
    }
}

entry_point!(kernel_main);

fn kernel_main(_boot_info: &'static mut BootInfo) -> ! {
    let mut uart = serial();
    let linux_write = syscall::dispatch(syscall::Personality::LinuxX86_64, 1);
    let windows_write = syscall::dispatch(syscall::Personality::WindowsNtX64, 0xF000_0001);
    let darwin_write = syscall::dispatch(syscall::Personality::DarwinX64, 0xE000_0001);
    if linux_write != Ok(syscall::Primitive::ConsoleWrite)
        || windows_write != Ok(syscall::Primitive::ConsoleWrite)
        || darwin_write != Ok(syscall::Primitive::ConsoleWrite)
        || syscall::dispatch(syscall::Personality::LinuxX86_64, u64::MAX).is_ok()
    {
        let _ = writeln!(uart, "OMNIOS_KERNEL_PANIC: dispatcher self-check failed");
        exit_qemu(QemuExitCode::Failure);
    }

    let _ = writeln!(uart, "OmniKernel: UEFI/BIOS entry reached");
    let _ = writeln!(uart, "OmniKernel: personality dispatcher self-check passed");
    let _ = writeln!(uart, "OMNIOS_BOOT_OK");
    exit_qemu(QemuExitCode::Success);
}

#[panic_handler]
fn panic(info: &core::panic::PanicInfo<'_>) -> ! {
    let _ = writeln!(serial(), "OMNIOS_KERNEL_PANIC: {info}");
    exit_qemu(QemuExitCode::Failure)
}
