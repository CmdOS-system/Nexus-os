/* Minimal UEFI boot proof for QEMU isa-debug-exit (x86_64 only).
 * Uses no UEFI libraries; entry uses Microsoft x64 EFI ABI.
 * Boot success is signaled only after firmware transfers control here.
 */
typedef unsigned long long EFI_STATUS;
typedef void *EFI_HANDLE;
typedef struct EFI_SYSTEM_TABLE EFI_SYSTEM_TABLE;

__attribute__((ms_abi))
EFI_STATUS efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *system_table) {
    (void)image;
    (void)system_table;
    __asm__ __volatile__(
        "movw $0x2a, %%ax\n\t"
        "outw %%ax, $0xf4\n\t"
        : : : "ax", "memory");
    for (;;) __asm__ __volatile__("hlt");
}
