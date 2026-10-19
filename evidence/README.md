# Nexus visual evidence

This directory stores PNG evidence from live runtime smoke tests. CI also uploads one combined artifact, `nexus-real-runtime-evidence-*`.

- `boot/desktop-boot.png` — freshly started XFCE desktop before application tests.
- `windows/wine-gui-running.png` — a MinGW-built Win32 GUI PE with a live timer, launched through `nexus-omniloader` and Wine.
- `android/apk-running.png` — the Java/Dex Android app installed through `nexus-omniloader` and running in Android Emulator.
- `web/crx-pwa-running.png` — the real PWA in Chromium, with a live Canvas animation driven by a WebAssembly counter.
- `ios/ipa-running.png` — a native ARM64 UIKit app running in the iOS Simulator from the app bundled into the generated IPA.

The Linux job captures the Windows and Chromium apps. Separate Android Emulator and Apple Silicon iOS Simulator jobs run the mobile apps. The combined workflow artifact is assembled only after all five PNGs pass presence and format checks.
