# Nexus OS — Windows compatibility engineering study (2026-10)

## Scope and evidence
Source-level architectural analysis of open-source Bottles, Lutris, Wine ecosystem, Proton, DXVK, VKD3D-Proton, and Winetricks. This is **not** a claim of binary reverse engineering or compatibility certification. No third-party code is copied into Nexus OS.

Upstream sources:
- Bottles manager: https://github.com/bottlesdevs/Bottles/blob/main/bottles/backend/managers/manager.py
- Bottles runners: https://docs.usebottles.com/components/runners
- Bottles CLI: https://docs.usebottles.com/advanced/cli
- Bottles environments: https://docs.usebottles.com/getting-started/environments
- Bottles dependency recipes: https://github.com/bottlesdevs/dependencies
- Lutris declarative installers: https://github.com/lutris/lutris/blob/master/docs/installers.rst
- Proton: https://github.com/ValveSoftware/Proton
- DXVK: https://github.com/doitsujin/dxvk
- VKD3D-Proton: https://github.com/HansKristian-Work/vkd3d-proton
- Winetricks: https://github.com/Winetricks/winetricks

## What each project solves
| Project | Primary abstraction | Lesson for Nexus |
|---|---|---|
| Wine | Windows API compatibility, prefix and DLL selection | Use maintained upstream runtime; do not claim full Windows emulation. |
| Bottles | Environment-scoped prefix, runner/dependency/install/version managers | Treat each app as a reproducible environment, with rollback and diagnostics. |
| Lutris | Declarative YAML installer and per-app runner settings | Use reviewable, versioned install manifests rather than hardcoded app guesses. |
| Proton | Wine-derived compatibility bundle, Steam runtime assumptions | Keep game-specific runtime separate; never assume Proton works outside its supported launcher. |
| DXVK | D3D8/9/10/11 to Vulkan | Detect Vulkan/driver capability and offer fallback to WineD3D. |
| VKD3D-Proton | D3D12 to Vulkan | Gate on GPU and driver features; do not enable indiscriminately. |
| Winetricks | Targeted dependencies and Wine workarounds | Install only approved, hashed dependencies with clear licenses. |

## Proposed Nexus Compatibility Manager (NCM)
1. **App intake:** inspect PE headers without execution; determine x86/x64, installer vs portable, signature metadata where available; warn for unsupported ARM/.NET/UWP and kernel drivers.
2. **Hardware readiness:** query Vulkan, Mesa/NVIDIA driver versions, 32-bit userspace, disk, filesystem, sandbox capabilities.
3. **Recipe resolver:** choose signed/versioned manifest and recommended Wine runner; allow user override. Never silently fetch arbitrary scripts.
4. **Isolated prefix:** per-app prefix under user-owned XDG data directory; prevent symlink/path traversal, use separate process environment and file permissions.
5. **Transactional setup:** snapshot or backup prefix before dependencies/runner changes; rollback on failure; preserve user files.
6. **Launch:** Wine for general apps; optional Proton/umu only where supported; DXVK/VKD3D only if supported by graphics stack.
7. **Observability:** capture exit status, Wine log, missing DLL clues, DXVK/VKD3D and Vulkan diagnostics; redact usernames, secrets and tokens before sharing.
8. **User experience:** double-click .exe/.msi opens a preview of actions, required downloads, permission prompts and expected compatibility; never silently execute.
9. **AI agent:** opt-in recommendations based on local diagnostics; **no execution, download, permission elevation or prefix mutation without explicit approval**.
10. **Export:** sanitized recipe, component versions, hashes and reproducible troubleshooting bundle.

## Proposed declarative manifest
```yaml
schema: 1
id: example-editor
title: Example Editor
installer:
  type: exe
  sha256: "<required verified digest>"
runtime:
  family: wine
  version: "<pinned supported release>"
  arch: win64
graphics:
  backend: auto # dxvk | vkd3d-proton | wined3d | auto
dependencies: []
permissions:
  network: ask
  home_files: ask
```

## Threat model and constraints
- Wine is **not** a security sandbox. Windows executables can access user files and network unless separately restricted.
- Flatpak isolation is a separate boundary; filesystem portals and explicit grants must be audited.
- Drivers, anticheat kernel modules, DRM, hardware devices and some Microsoft apps may remain incompatible.
- PE signatures do not imply safety; hash pinning provides integrity, not trust.
- Respect third-party licenses, distribution restrictions, and vendor terms; do not bundle proprietary DLLs without permission.
- Never install Windows dependencies automatically based only on LLM output.

## Implementation gates
G0: research and architecture reviewed (this document).
G1: static PE parser + hostile-file tests; no execution.
G2: runner inventory and GPU capability probe; no downloads.
G3: prefix lifecycle create/list/remove with path traversal and rollback tests.
G4: safe manifest parser and signed/hash-verified dependency installer.
G5: controlled GUI flow for one permitted open-source Windows test app in VM.
G6: performance, regression, rollback, sandbox escape assessment and user usability.
Only then enable double-click Windows launch by default.

## Important distinction
Nexus OS has an ISO boot gate, but **Windows application compatibility has not yet been demonstrated in a Nexus OS guest**. This is an architecture/research deliverable, not a completed feature.
