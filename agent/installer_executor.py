#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
import time
from installer_plan import UnsafeTarget, plan_install
from installer_inventory import capture_inventory

def run_cmd(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def install(target_path):
    print(f"Installing Nexus OS to {target_path}...")
    run_cmd(["sgdisk", "--zap-all", target_path])
    run_cmd(["sgdisk", "-n", "1:0:+512M", "-t", "1:ef00", "-c", "1:EFI", target_path])
    run_cmd(["sgdisk", "-n", "2:0:0", "-t", "2:8300", "-c", "2:NexusRoot", target_path])
    run_cmd(["partprobe", target_path])
    time.sleep(2)

    import re
    if re.search(r'\d$', target_path):
        part_efi = f"{target_path}p1"
        part_root = f"{target_path}p2"
    else:
        part_efi = f"{target_path}1"
        part_root = f"{target_path}2"

    run_cmd(["mkfs.fat", "-F32", part_efi])
    run_cmd(["mkfs.ext4", "-F", part_root])

    mnt = Path("/mnt/nexus-install")
    mnt.mkdir(parents=True, exist_ok=True)
    run_cmd(["mount", part_root, str(mnt)])

    efi_mnt = mnt / "boot" / "efi"
    efi_mnt.mkdir(parents=True, exist_ok=True)
    run_cmd(["mount", part_efi, str(efi_mnt)])

    try:
        # Copy squashfs contents from /run/live/medium/live/filesystem.squashfs
        # Actually, in live-build, /lib/live/mount/rootfs/filesystem.squashfs or /run/live/rootfs/filesystem.squashfs
        print("Copying system...")
        run_cmd(["rsync", "-aHAX", "--exclude", "/dev/*", "--exclude", "/proc/*", "--exclude", "/sys/*", "--exclude", "/tmp/*", "--exclude", "/run/*", "--exclude", "/mnt/*", "--exclude", "/media/*", "/", str(mnt)])

        for d in ["dev", "proc", "sys", "run"]:
            run_cmd(["mount", "--bind", f"/{d}", str(mnt / d)])

        print("Installing bootloader...")
        run_cmd(["chroot", str(mnt), "grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", "--bootloader-id=Nexus", "--recheck", target_path])
        run_cmd(["chroot", str(mnt), "update-grub"])

        print("Writing fstab...")
        root_uuid = subprocess.run(["blkid", "-s", "UUID", "-o", "value", part_root], capture_output=True, text=True).stdout.strip()
        efi_uuid = subprocess.run(["blkid", "-s", "UUID", "-o", "value", part_efi], capture_output=True, text=True).stdout.strip()

        with open(mnt / "etc" / "fstab", "w") as f:
            f.write(f"UUID={root_uuid} / ext4 defaults 0 1\n")
            f.write(f"UUID={efi_uuid} /boot/efi vfat defaults 0 2\n")

    finally:
        for d in ["dev", "proc", "sys", "run"]:
            subprocess.run(["umount", "-l", str(mnt / d)], check=False)
        subprocess.run(["umount", "-R", str(mnt)], check=False)

    print("Installation complete.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: installer_executor.py <target_disk>")
        sys.exit(1)
    target = sys.argv[1]
    inv = capture_inventory()
    try:
        plan = plan_install(inv, target)
        install(target)
    except UnsafeTarget as e:
        print(f"Refusing to install: {e}")
        sys.exit(1)
