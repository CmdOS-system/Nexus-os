use std::{env, path::PathBuf};

fn main() {
    let out = PathBuf::from(env::var_os("OUT_DIR").expect("Cargo must set OUT_DIR"));
    let kernel = PathBuf::from(
        env::var_os("CARGO_BIN_FILE_KERNEL_kernel")
            .expect("nightly artifact dependency must provide the kernel binary"),
    );

    let uefi_image = out.join("omnios-uefi.img");
    bootloader::UefiBoot::new(&kernel)
        .create_disk_image(&uefi_image)
        .expect("create UEFI boot image");

    let bios_image = out.join("omnios-bios.img");
    bootloader::BiosBoot::new(&kernel)
        .create_disk_image(&bios_image)
        .expect("create BIOS boot image");

    println!("cargo:rustc-env=OMNIOS_UEFI_IMAGE={}", uefi_image.display());
    println!("cargo:rustc-env=OMNIOS_BIOS_IMAGE={}", bios_image.display());
    println!("cargo:rerun-if-changed=kernel/src/main.rs");
}
