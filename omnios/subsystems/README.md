# OmniOS subsystems

Compatibility bridges stay in user space, isolated per process and version. They translate API semantics; the kernel does not pretend that PE/Mach-O/DEX headers contain their original operating system.

| Directory | Planned scope | Current state |
|---|---|---|
| `win32/` | Win32/NT user-mode bridge, versioned DLL contracts | design only |
| `glibc/` | Linux syscall/libc ABI adaptation | design only |
| `cocoa/` | Darwin/Mach and selected framework compatibility | design only; no Apple code included |
| `android/` | package verification, Bionic and ART integration | design only |
| `graphics/` | Vulkan compositor and API translation adapters | design only |

The Linux kernel interface, Windows NT services, Darwin frameworks and Android ART have different behavior and versioning. Each API family requires its own tests and compatibility matrix.
