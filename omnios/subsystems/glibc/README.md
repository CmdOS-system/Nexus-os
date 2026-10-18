# Linux / glibc bridge

Planned Linux ABI adapter. First target is documented Linux x86_64 syscall ABI. Mapping errno, signals, file descriptors, TLS, futex and libc symbol versions requires separate compatibility tests; no glibc implementation is present yet.
