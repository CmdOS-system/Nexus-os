#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/linux-boot/rootfs/{bin,dev,proc,sys}
kernel="$(find /boot -maxdepth 1 -type f -name 'vmlinuz-*' | sort -V | tail -1)"
if [[ -z "$kernel" ]]; then echo "No installed Linux kernel" >&2; exit 1; fi
busybox_binary="$(dpkg-query -L busybox-static | grep -E '/bin/busybox$' | head -n 1)"
if [[ -z "$busybox_binary" || ! -x "$busybox_binary" ]]; then
  echo "busybox-static executable missing" >&2; exit 1
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
if readelf -l build/linux-boot/rootfs/bin/busybox | grep -q 'INTERP'; then
  echo "BusyBox must be statically linked" >&2; exit 1
fi
echo "Static BusyBox confirmed"
(cd build/linux-boot/rootfs && find . -print0 | cpio --null -ov --format=newc 2>/dev/null | gzip -9) > build/linux-boot/initramfs.cpio.gz
python -m recovery_g2.linux_boot_probe "$kernel" build/linux-boot/initramfs.cpio.gz
