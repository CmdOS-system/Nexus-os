#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: runner payload.bin\n"); return 2; }
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) { perror("open payload"); return 2; }
    struct stat st;
    if (fstat(fd, &st) || st.st_size < 8) { perror("invalid payload"); return 2; }
    void *code = mmap(NULL, (size_t)st.st_size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE, fd, 0);
    close(fd);
    if (code == MAP_FAILED) { perror("mmap payload"); return 2; }
    __builtin___clear_cache(code, (char *)code + st.st_size);
    long (*payload)(void) = (long (*)(void))code;
    long value = payload();
    printf("IPA ARM64 __text payload executed by qemu-aarch64-static: result=%ld\n", value);
    return value == 42 ? 0 : 1;
}
