# Win32 bridge

Planned user-mode compatibility service. Do not hard-code undocumented Windows syscall numbers: the bridge must pin/identify its supported Windows ABI version and normalize supported calls into OmniKernel operations. Initial scope is console output and process exit only after loader, handles and memory safety exist.
