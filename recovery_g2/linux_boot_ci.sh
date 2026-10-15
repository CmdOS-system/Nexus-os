#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/linux-boot/rootfs/{bin,dev,proc,sys}
kernel="$(find /boot -maxdepth 1 -type f -name 'vmlinuz-*' | sort -V | tail -1)"
if [[ -z "$kernel" ]]; then echo "No installed Linux kernel" >&2; exit 1; fi
busybox_binary="$(dpkg-query -L busybox-static | grep -E '^/(usr/)?bin/busybox
ln -s busybox build/linux-boot/rootfs/bin/sh
cat > build/linux-boot/rootfs/init <<'EOF'
#!/bin/sh
/bin/busybox mount -t proc proc /proc
echo NEXUS_LINUX_INIT_READY >/dev/console
exec /bin/busybox sh
EOF
chmod +x build/linux-boot/rootfs/init
# busybox-static is required: no dynamic library dependency inside initramfs.
if ! readelf -l build/linux-boot/rootfs/bin/busybox | grep -q 'INTERP'; then
  echo "BusyBox static binary confirmed"
else
  echo "BusyBox is dynamically linked; cannot boot minimal initramfs" >&2
  exit 1
fi
(cd build/linux-boot/rootfs && find . -print0 | cpio --null -ov --format=newc 2>/dev/null | gzip -9) > build/linux-boot/initramfs.cpio.gz
python -m recovery_g2.linux_boot_probe "$kernel" build/linux-boot/initramfs.cpio.gz
 | head -n 1)"
if [[ -z "$busybox_binary" || ! -x "$busybox_binary" ]]; then
  echo "busybox-static package does not provide an executable" >&2; exit 1
fi
cp "$busybox_binary" build/linux-boot/rootfs/bin/busybox
ln -s busybox build/linux-boot/rootfs/bin/sh
cat > build/linux-boot/rootfs/init <<'EOF'
#!/bin/sh
/bin/busybox mount -t proc proc /proc
echo NEXUS_LINUX_INIT_READY >/dev/console
exec /bin/busybox sh
EOF
chmod +x build/linux-boot/rootfs/init
# busybox-static is required: no dynamic library dependency inside initramfs.
if ldd build/linux-boot/rootfs/bin/busybox 2>&1 | grep -q 'not a dynamic executable\|statically linked'; then
  echo "BusyBox static binary confirmed"
else
  echo "BusyBox is dynamically linked; cannot boot minimal initramfs" >&2
  exit 1
fi
(cd build/linux-boot/rootfs && find . -print0 | cpio --null -ov --format=newc 2>/dev/null | gzip -9) > build/linux-boot/initramfs.cpio.gz
python -m recovery_g2.linux_boot_probe "$kernel" build/linux-boot/initramfs.cpio.gz
