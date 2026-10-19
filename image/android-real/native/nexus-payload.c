#include <stdio.h>

int main(void) {
    volatile unsigned long left = 6;
    volatile unsigned long right = 7;
    unsigned long result = left * right;
    printf("ARM64 Android APK payload executed: %lu x %lu = %lu\n", left, right, result);
    return result == 42 ? 0 : 1;
}
