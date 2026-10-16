# Nexus OS — historial consolidado y mapa de evidencia

Corte: 2026-10-16. Se recorrieron las cinco páginas de historial de main hasta el commit inicial: **445 commits** a partir de `1903a7ac9f619165d0251b9864744aac3390bf71`. Se consultaron cinco ramas y todas las propuestas de cambio (una PR abierta). Esto es un inventario de metadatos de todos esos commits y una revisión selectiva de código, documentación y ejecuciones; no una auditoría línea por línea de 445 diffs.

## Cómo leer la evidencia

Un commit registra un cambio propuesto en código o documentación. Su título no acredita funcionamiento. El estado operativo requiere contenido, pruebas, SHA y entorno específicos. Las ramas no integradas se registran aparte.

## Mapa del trabajo existente

| Componente | Commits representativos | Evidencia / implementación | Límite |
| --- | --- | --- | --- |
| Base Live | 4bf369a2, 5f6e674b, dbd3d257 | Construcción Debian Trixie y configuración GRUB; ISO Gate 38935133161 aprobó build, integridad y smoke UEFI/XFCE en 10270441. | No acredita instalador, BIOS, red o hardware. |
| Nexus Horizon | a685e97f, ab1b4a99, 5f0344cf, 10270441 | Lanzador buscable, atajo configurado, panel opcional, reloj y accesos a archivos/terminal/ajustes; smoke gráfico aprobado en 378a6388. | No acredita todo el diseño final, accesibilidad, Wayland ni atajo ejercitado en ISO. |
| IA y conversación | 3c938c1e, 766ba0a5, 3b995826, 7dcb206e, 7f4f47d2, 590d38e5 | Código para chat Ollama con roles, sesión independiente del proveedor, adaptador compatible HTTPS, configuración persistente, keyring y diagnóstico local. Se leyeron session.py y provider_client.py. | Presencia de código y mocks no confirma una conversación con modelo real en la ISO, voz ni control del ratón. |
| Permisos y herramientas | 36f31c20, a613625c, e3c49ffb, f9c40eca | Broker de permisos de un uso ligado a herramienta y argumentos, lectura autorizada y previsualización de acciones. Se leyó tool_broker.py. | PR #1 de seguridad sigue abierta; no equivale a auditoría completa. |
| Instalador | b1eee20a, a7cf28d1, d783c7f2, 1fb8340a, df18b9be | Planificador, inventario, preflight y GUI de solo lectura; rechazo de discos inseguros y guardia de inventario fresco. Se leyó installer_plan.py. | El módulo no aporta ejecutor privilegiado: no particiona ni instala; persistencia y arranque sin ISO pendientes. |
| Recuperación A/B | ad3decc2, 505bd4b0, e9da38f4, 3b798904 | Máquina de estados, metadatos redundantes/persistidos, reintentos y rollback en laboratorio/simulación. Se leyó nexus_recovery_sim.py. | No equivale a recuperación de sistema instalado ni cadena de Verified/Secure Boot. |
| Laboratorio QEMU | 828f1b68, cc97cfbb, 630b4ae5, a17f6553 | Historial de aislamiento de VARS/discos QCOW2, inspección qemu-img, probes EFI y kernel/initramfs. | No se revalidó cada ejecución histórica de estos probes. |
| Compatibilidad Windows | c91c0f90, 127d90a6, 5c845385 | Arquitectura de integración y módulo para inspección acotada de cabeceras PE. | No demuestra ejecutar aplicaciones Windows con Wine/Proton. |

## Ejecuciones verificadas directamente

- [ISO Gate 38935133161](https://github.com/CmdOS-system/Nexus-os/actions/runs/38935133161): build, checksum, inspección GRUB, smoke UEFI y subida de artefactos aprobados para `102704419534f0d6d65dec0764cfc76b833c9423`. No se inspeccionó el binario descargado en esta revisión.
- [Fast Checks 38977578555](https://github.com/CmdOS-system/Nexus-os/actions/runs/38977578555): cinco jobs aprobados para `378a6388974505059d7b1d3cc6640eda6d431d7e`; corrige el SyntaxError del smoke Horizon.

## Ramas y trabajo sin integrar al corte

- `fix/byoai-consent-20261016`: `46cd5cbc5193ae86f25ca5fe1e3b9ad2a8b892c4`.
- `fix/ci-node24-isogate-20261016`: `46cd5cbc5193ae86f25ca5fe1e3b9ad2a8b892c4`.
- `fix/installer-flags-iso-queue-20261016`: `b024b47bfe80db52f174fe2b09e0476135406a77`.
- `fix/security-byoai-file-grants-20261014`: `eb35e7b879ca849b31e58d630a6f2ad9830ac052`.
- `main`: `1903a7ac9f619165d0251b9864744aac3390bf71`.

[PR #1](https://github.com/CmdOS-system/Nexus-os/pull/1): Security hardening: strict BYOAI consent and safe file grants, abierta, sin integrar. No contar como entregada en main.

## Decisiones recuperadas de conversaciones

- Nexus debe ser un sistema independiente arrancable e instalable desde USB/ISO, con escritorio propio; una preview web es un artefacto diferente y no prueba el OS.
- Experiencia profesional, distintiva y usable sin conocimientos Linux; inspiración macOS/Windows sin copiar. Mantener XFCE como base mientras evoluciona Nexus Desktop.
- IA por voz/texto que convierta intenciones en acciones visibles, autorizadas, cancelables y verificables, con auditoría y elección de proveedor.
- Compatibilidad práctica mediante integración Wine/Proton/Bottles y componentes existentes; ejecutar aplicaciones objetivo en pruebas reales.
- No declarar terminado/publicable sólo por pruebas unitarias: validar ISO, instalación, Wine, accesibilidad y Wayland con evidencia específica.
- Avanzar autónomamente, investigar y comunicar progreso global; investigación de REA, ChromiumOS y PS5 no implica compatibilidad entregada.
- Separar actualización, recuperación y boot manager; proteger datos y probar en discos virtuales desechables.

La recuperación de conversaciones es parcial y no incluye acceso directo a las instrucciones privadas del proyecto ChatGPT. No afirmar que se revisó exhaustivamente todo el proyecto de ChatGPT. Consultar PROJECT-CONTINUITY.md para el punto de reanudación.

## Historial completo de main al corte

De más reciente a más antiguo. Mensajes reproducidos como metadatos históricos, no como certificaciones de funcionalidad.

| Commit | Fecha UTC | Mensaje |
| --- | --- | --- |
| [1903a7ac](https://github.com/CmdOS-system/Nexus-os/commit/1903a7ac9f619165d0251b9864744aac3390bf71) | 2026-10-16T22:47:29Z | docs: consolidate recovered requirements, passing checks and remaining gates |
| [72ae1c5a](https://github.com/CmdOS-system/Nexus-os/commit/72ae1c5a3fe3123d1f678da2e4af66529802ee9c) | 2026-10-16T22:47:08Z | docs: reconcile build status with verified ISO and fast checks evidence |
| [378a6388](https://github.com/CmdOS-system/Nexus-os/commit/378a6388974505059d7b1d3cc6640eda6d431d7e) | 2026-10-16T22:44:55Z | fix(horizon): repair duplicated line continuation in panel smoke test |
| [42b1666b](https://github.com/CmdOS-system/Nexus-os/commit/42b1666b94d1a399580cc18ad82221d0d0aef8b8) | 2026-10-16T22:44:43Z | docs: centralize verified Nexus OS status and next steps |
| [b4592913](https://github.com/CmdOS-system/Nexus-os/commit/b4592913efafbc83065021ae75e39d330fe4e798) | 2026-10-16T16:51:04Z | test(horizon): verify safe panel quick actions and missing app feedback |
| [10270441](https://github.com/CmdOS-system/Nexus-os/commit/102704419534f0d6d65dec0764cfc76b833c9423) | 2026-10-16T16:50:57Z | feat(horizon): add files terminal and settings quick actions to desktop panel |
| [28f5227f](https://github.com/CmdOS-system/Nexus-os/commit/28f5227ffd0e18d6df4cb33cd6f2500380334002) | 2026-10-16T16:48:08Z | ci(horizon): publish real screenshot of combined panel and launcher |
| [4cf527d8](https://github.com/CmdOS-system/Nexus-os/commit/4cf527d8d3f3cab8b0aa18fe0ffebb5a3f1e60f5) | 2026-10-16T16:48:01Z | feat(horizon): capture real combined panel and launcher desktop screenshot |
| [5350a9c7](https://github.com/CmdOS-system/Nexus-os/commit/5350a9c72e2cb9775cca8011f3928047ab6f9093) | 2026-10-16T16:46:30Z | ci(horizon): gate launcher and panel coexistence in shared Xvfb session |
| [67bb7dff](https://github.com/CmdOS-system/Nexus-os/commit/67bb7dff59fe2b095323c5c68173ac7973e234c6) | 2026-10-16T16:46:26Z | test(horizon): run panel and launcher together on one graphical display |
| [6c9a92f1](https://github.com/CmdOS-system/Nexus-os/commit/6c9a92f11013065a2a1a7f3c33bf1becec854a0e) | 2026-10-16T16:43:26Z | test(horizon): ensure preview panel does not obscure normal application windows |
| [36922812](https://github.com/CmdOS-system/Nexus-os/commit/36922812ea91f389e55ae631a4ddb7cbdad8e4f9) | 2026-10-16T16:43:20Z | fix(horizon): keep preview panel below active applications instead of always-on-top |
| [8fc9632a](https://github.com/CmdOS-system/Nexus-os/commit/8fc9632a572f3b903d48cf4ed6261c79f66e3fb4) | 2026-10-16T16:27:13Z | test(image): verify Horizon panel preview is staged in ISO sources |
| [d11a607c](https://github.com/CmdOS-system/Nexus-os/commit/d11a607c5811ba377d1e9979584f0447bd3193bd) | 2026-10-16T16:27:07Z | ci(horizon): test optional panel preview under Xvfb |
| [7a0a763f](https://github.com/CmdOS-system/Nexus-os/commit/7a0a763fbadcc4a6a53af41a54b2ca967e6228ce) | 2026-10-16T16:27:02Z | test(horizon): exercise actual desktop panel, clock and launcher |
| [affb2f6c](https://github.com/CmdOS-system/Nexus-os/commit/affb2f6c1543364c5795ad848e299d0ec42d5acf) | 2026-10-16T16:26:56Z | feat(horizon): make desktop panel preview launchable without forced autostart |
| [5f0344cf](https://github.com/CmdOS-system/Nexus-os/commit/5f0344cf59c993c470cc7c93054c733a764c89a0) | 2026-10-16T16:26:50Z | feat(horizon): introduce optional persistent desktop panel with clock and launcher |
| [78e33b68](https://github.com/CmdOS-system/Nexus-os/commit/78e33b6802983858ac73e8ffd6ffd1b846c5d8c8) | 2026-10-16T16:25:02Z | ci(horizon): publish real Xvfb screenshot for visual inspection |
| [82318c50](https://github.com/CmdOS-system/Nexus-os/commit/82318c5021f091e4e7715277d602597cf04659af) | 2026-10-16T16:24:56Z | feat(horizon): capture actual launcher screenshot from virtual graphical session |
| [0ce9d89d](https://github.com/CmdOS-system/Nexus-os/commit/0ce9d89dc9864bed314288cfd24c2665daa7841f) | 2026-10-16T15:50:06Z | test(image): validate Horizon keyboard shortcut and launcher staging |
| [ab1b4a99](https://github.com/CmdOS-system/Nexus-os/commit/ab1b4a99f35f33c679518cb2459d8657f1833f05) | 2026-10-16T15:50:00Z | feat(horizon): bind Super+Space to launcher for new XFCE user profiles |
| [35329f4b](https://github.com/CmdOS-system/Nexus-os/commit/35329f4b3ab2e8027341dfcddeeeb7cbf52d8338) | 2026-10-16T15:49:54Z | feat(horizon): use dedicated launcher from desktop menu |
| [d6083a83](https://github.com/CmdOS-system/Nexus-os/commit/d6083a835db600b3bf5a7ab740c01c21949a8bf0) | 2026-10-16T15:49:49Z | feat(horizon): add dedicated launcher for keyboard shortcut integration |
| [9de9d647](https://github.com/CmdOS-system/Nexus-os/commit/9de9d647dc776826e15437a4d6f1ba92b459af7e) | 2026-10-16T13:54:42Z | test(horizon): assert interactive AI agent opens in a terminal |
| [49cebae7](https://github.com/CmdOS-system/Nexus-os/commit/49cebae7fb3eebc915c0ccb29a4db96632f9ad11) | 2026-10-16T13:54:37Z | fix(horizon): launch interactive Nexus Agent in a terminal window |
| [46cd5cbc](https://github.com/CmdOS-system/Nexus-os/commit/46cd5cbc5193ae86f25ca5fe1e3b9ad2a8b892c4) | 2026-10-16T13:16:48Z | fix(ci): install tkinter in Debian ISO preflight test environment |
| [a4278090](https://github.com/CmdOS-system/Nexus-os/commit/a42780908710382ad63ff3acf7eadf0d3a9cd0f6) | 2026-10-16T13:15:11Z | test(horizon): verify AI assistant is discoverable from launcher |
| [f7815781](https://github.com/CmdOS-system/Nexus-os/commit/f78157812768ca7971aa963975701e783f26f193) | 2026-10-16T13:15:07Z | feat(horizon): integrate Nexus Agent into searchable application launcher |
| [e27d1963](https://github.com/CmdOS-system/Nexus-os/commit/e27d19632131f8ab628986b2002a5b54eb3bef2d) | 2026-10-16T13:13:34Z | ci(horizon): verify actual launcher rendering and keyboard search under Xvfb |
| [372cee0b](https://github.com/CmdOS-system/Nexus-os/commit/372cee0b93f37680ff90e24d1504c906ed0758b9) | 2026-10-16T13:13:29Z | test(horizon): open real launcher and exercise keyboard search in Xvfb |
| [161964fd](https://github.com/CmdOS-system/Nexus-os/commit/161964fd2b79a4bb30719579b23b06c87a6278a2) | 2026-10-16T06:58:42Z | test(horizon): cover app discovery and shell-free launcher behavior |
| [8482db80](https://github.com/CmdOS-system/Nexus-os/commit/8482db80d116791ae51e1e15e73a79d6472f91d8) | 2026-10-16T06:58:36Z | test(image): require Horizon application and desktop entry in live ISO sources |
| [4a651b51](https://github.com/CmdOS-system/Nexus-os/commit/4a651b515365ffa207231f00967ef67d9e099fab) | 2026-10-16T06:58:31Z | feat(horizon): expose Nexus Horizon launcher in desktop applications menu |
| [a685e97f](https://github.com/CmdOS-system/Nexus-os/commit/a685e97f03fdf999eee927475209c04cf2f4caa6) | 2026-10-16T06:58:26Z | feat(horizon): add keyboard-first searchable desktop launcher prototype |
| [bb84ad8e](https://github.com/CmdOS-system/Nexus-os/commit/bb84ad8e21a24b268e484df6d3a111fb34741eef) | 2026-10-16T06:43:36Z | test(gui): prevent stale model readiness feedback after selection changes |
| [b0b1ed10](https://github.com/CmdOS-system/Nexus-os/commit/b0b1ed101b674845288a8134e0b8444ba88ac443) | 2026-10-16T06:43:29Z | fix(ai-ui): discard stale asynchronous model probe results after settings change |
| [94326c44](https://github.com/CmdOS-system/Nexus-os/commit/94326c44c36aff99d975d20ea65ce1b3aec4f9f3) | 2026-10-16T06:41:27Z | test(image): stage and import real Control Center dependencies alongside installer |
| [32f4f6a2](https://github.com/CmdOS-system/Nexus-os/commit/32f4f6a2e68a91aa41e5a8fe6ef6aa3f81ad04fc) | 2026-10-16T06:39:59Z | test(gui): cover successful installer launch and local model readiness feedback |
| [4c33fbb9](https://github.com/CmdOS-system/Nexus-os/commit/4c33fbb9fbb4afe999e640875be08f2d75fae4ca) | 2026-10-16T06:38:34Z | ci(gui): run actual Nexus Control Center smoke tests in virtual display |
| [58481161](https://github.com/CmdOS-system/Nexus-os/commit/58481161f6439dad33f44ef14acd93d44c65b0a0) | 2026-10-16T06:38:29Z | test(gui): exercise real Control Center widgets and safety behavior under Xvfb |
| [27357f00](https://github.com/CmdOS-system/Nexus-os/commit/27357f002595831b222eeb844bc131bc725e7f07) | 2026-10-16T06:37:10Z | test(security): assert loopback Ollama probe bypasses proxy configuration |
| [79948f0d](https://github.com/CmdOS-system/Nexus-os/commit/79948f0d4f4a9b5120c55eb9aadb6323aa3d789a) | 2026-10-16T06:37:04Z | security(ai): disable environment proxies for loopback Ollama diagnostic |
| [fc3a8025](https://github.com/CmdOS-system/Nexus-os/commit/fc3a8025367a2afcd468dd047cc7c8320ad8448c) | 2026-10-16T06:34:23Z | test(security): verify Ollama probe refuses redirects and uses guarded opener |
| [ba38b692](https://github.com/CmdOS-system/Nexus-os/commit/ba38b6923acaeddf98b11a2de33073f4f8a283b5) | 2026-10-16T06:34:17Z | security(ai): prevent local Ollama readiness probe from following HTTP redirects |
| [edc4ac4f](https://github.com/CmdOS-system/Nexus-os/commit/edc4ac4f5926feba631cd0b5d9d520564aeddd72) | 2026-10-16T06:31:28Z | test(ai): cover Ollama availability, absent models and sanitized failures |
| [037c1242](https://github.com/CmdOS-system/Nexus-os/commit/037c1242f0af190573e0e82de266a748ca54f6f1) | 2026-10-16T06:31:21Z | feat(control-center): add nonblocking local Ollama model readiness button |
| [8e324882](https://github.com/CmdOS-system/Nexus-os/commit/8e3248825746dd3cd5db9c3bea66e9b93055ae49) | 2026-10-16T06:31:13Z | build(ai): include local model diagnostic in Nexus live image |
| [55645f0e](https://github.com/CmdOS-system/Nexus-os/commit/55645f0e52894d5260d6e662f44055d92e494afc) | 2026-10-16T06:31:11Z | build(ai): include local model diagnostic in Nexus live image |
| [590d38e5](https://github.com/CmdOS-system/Nexus-os/commit/590d38e5b5459393057c67a99ac2054d626806c8) | 2026-10-16T06:31:06Z | feat(ai): add bounded read-only loopback Ollama model availability probe |
| [142feee2](https://github.com/CmdOS-system/Nexus-os/commit/142feee2f941836d8d392da00f023fd845978d68) | 2026-10-16T06:29:18Z | test(ci): align AI configuration wording with honest connectivity state |
| [26f4d94a](https://github.com/CmdOS-system/Nexus-os/commit/26f4d94af6a26a5ef3e3fc9845edb588072e38dc) | 2026-10-16T06:29:14Z | ux(ai): distinguish selected AI configuration from verified runtime connectivity |
| [9be4599a](https://github.com/CmdOS-system/Nexus-os/commit/9be4599a614aa75f18334c307b303eaba66631fb) | 2026-10-16T06:24:58Z | test(ci): assert control center exposes AI privacy mode status |
| [e6c585f2](https://github.com/CmdOS-system/Nexus-os/commit/e6c585f269f7007f0c40e71e3d938a3bb7dcf604) | 2026-10-16T06:24:53Z | feat(control-center): show live AI mode and privacy status guidance |
| [395b035f](https://github.com/CmdOS-system/Nexus-os/commit/395b035f3efd939b2ef4d586bdff2bf9f329b4e2) | 2026-10-16T06:22:45Z | test(ci): verify control center exposes safe installation preview launcher |
| [d2b4a3cc](https://github.com/CmdOS-system/Nexus-os/commit/d2b4a3cceb87f363e2690172a26aabbf7684dde1) | 2026-10-16T06:22:40Z | feat(control-center): add integrated read-only installation preview launcher |
| [dfc67da6](https://github.com/CmdOS-system/Nexus-os/commit/dfc67da621d29088fa74a96e29d0c94a40dfd1ae) | 2026-10-16T06:21:01Z | fix(ci): correct Python quoting in staged installer smoke check |
| [3a58c963](https://github.com/CmdOS-system/Nexus-os/commit/3a58c963cbefbc74cdeb09e46805374a61e6c341) | 2026-10-16T06:19:02Z | ci: exercise staged installer module imports in isolated image-like directory |
| [0f54ff39](https://github.com/CmdOS-system/Nexus-os/commit/0f54ff398f628d7d04605a923acd26acbde6eeb9) | 2026-10-16T06:18:55Z | ci(iso): include image validation changes in build trigger coverage |
| [e6fc9d5d](https://github.com/CmdOS-system/Nexus-os/commit/e6fc9d5d8a1fffb3bd510c278828dd0f6af5023c) | 2026-10-16T06:17:19Z | ci(iso): limit automatic ISO builds to runtime and boot-impacting image changes |
| [4f613bd7](https://github.com/CmdOS-system/Nexus-os/commit/4f613bd72f4140fa3ff8bfeac2f8da5d4d7133e2) | 2026-10-16T06:13:39Z | test(installer-ui): malformed inventory fails closed without exposing targets |
| [78d60d17](https://github.com/CmdOS-system/Nexus-os/commit/78d60d1719ac42edc03b92fa78f0423b0b8c03b4) | 2026-10-16T06:13:32Z | fix(installer-ui): fail closed and clear selections for malformed disk inventory |
| [cd724a23](https://github.com/CmdOS-system/Nexus-os/commit/cd724a23d87624313d279125ff0e1b1d69bc5d79) | 2026-10-16T05:32:23Z | ci: add fast installer runtime staging gate without rebuilding ISO |
| [362fe24b](https://github.com/CmdOS-system/Nexus-os/commit/362fe24b531355a6a74b9cb806a207b4a9bef14a) | 2026-10-16T05:14:25Z | test(installer-ui): verify eligibility totals and no-safe-disk message |
| [1f3f0dd6](https://github.com/CmdOS-system/Nexus-os/commit/1f3f0dd66fc55f1d92be048c2d01bc035851e22a) | 2026-10-16T05:14:20Z | feat(installer-ui): show eligibility totals and explicit no-safe-disk state |
| [d0631ad1](https://github.com/CmdOS-system/Nexus-os/commit/d0631ad1bdab5db796511e227c7a85d8287da3d5) | 2026-10-16T05:12:42Z | test(installer-ui): reject mounted disks from dropdown and programmatic target injection |
| [df18b9be](https://github.com/CmdOS-system/Nexus-os/commit/df18b9be180c873c86ab5110a2ea4d4359eef789) | 2026-10-16T05:12:36Z | feat(installer-ui): restrict selectable targets to eligible disks and block injected selections |
| [382fdf96](https://github.com/CmdOS-system/Nexus-os/commit/382fdf96edbae5106d76cfc90d03b8ac3f3215e5) | 2026-10-16T05:08:04Z | test(installer-ui): verify GUI renders eligible and rejected disk diagnostics |
| [194f6c44](https://github.com/CmdOS-system/Nexus-os/commit/194f6c44316eaac3311669be44adb5979e2457fd) | 2026-10-16T05:07:56Z | fix(installer-ui): render readiness lines with real newline escapes |
| [4235a9ef](https://github.com/CmdOS-system/Nexus-os/commit/4235a9ef317a1b590337c557e8e79f3d869554e8) | 2026-10-16T05:07:49Z | feat(installer-ui): display read-only per-disk readiness and rejection reasons |
| [778f3847](https://github.com/CmdOS-system/Nexus-os/commit/778f384775443c25f0e9524b6a9b0ffc49ccfbe6) | 2026-10-16T05:06:52Z | fix(image): validate new preflight module in ISO staging and Python checks |
| [96d9ad77](https://github.com/CmdOS-system/Nexus-os/commit/96d9ad7748ac306f348362bca9cd8478d6b8c9fc) | 2026-10-16T05:06:41Z | fix(test): correctly identify mounted and missing targets by their paths |
| [2e6e9d3e](https://github.com/CmdOS-system/Nexus-os/commit/2e6e9d3ede73026ddd566603d0c59d4e639d941f) | 2026-10-16T05:04:46Z | feat(image): ship read-only installer preflight utility inside Nexus ISO |
| [4b409f21](https://github.com/CmdOS-system/Nexus-os/commit/4b409f21550e44d37c44b3ee0ebcf513dc18bc0f) | 2026-10-16T05:04:42Z | fix(test): locate rejected missing disk by path instead of list position |
| [49ea8af4](https://github.com/CmdOS-system/Nexus-os/commit/49ea8af48b0c172f21e7502d176fa13e986c235e) | 2026-10-16T05:02:26Z | test(installer): assert missing target by path rather than sort index |
| [b9d49ec5](https://github.com/CmdOS-system/Nexus-os/commit/b9d49ec58414d6b49cb04b5063a3ff64897c0939) | 2026-10-16T05:02:22Z | test(installer): validate readiness JSON, mount rejection, missing targets and CLI failure |
| [1fb8340a](https://github.com/CmdOS-system/Nexus-os/commit/1fb8340a146c58136148b56250036d848c466d4f) | 2026-10-16T05:02:14Z | feat(installer): add read-only JSON readiness report for disks and explicit target |
| [dc2e20c1](https://github.com/CmdOS-system/Nexus-os/commit/dc2e20c1985c4d8ec48b5463f6f50dce5c431e51) | 2026-10-16T05:00:26Z | test(installer-ui): assert planner receives freshly captured inventory and exact target |
| [3c50bf26](https://github.com/CmdOS-system/Nexus-os/commit/3c50bf262b6930fb1ad8116afb2d8a42683fc95d) | 2026-10-16T04:57:14Z | fix(gui-test): use parenthesized multi-context syntax |
| [ae8a261d](https://github.com/CmdOS-system/Nexus-os/commit/ae8a261d2e0355cb07b3e0eb3f1f2181a66c6788) | 2026-10-16T04:57:07Z | test(gui): reject unsafe target and clear stale disk selection |
| [aabfa1ec](https://github.com/CmdOS-system/Nexus-os/commit/aabfa1ec8480c7605ba3a9472af54ce585587fb4) | 2026-10-16T04:54:50Z | test(gui): cover disk scan failure and stale target reset in headless installer |
| [2f8f0b3b](https://github.com/CmdOS-system/Nexus-os/commit/2f8f0b3bc3c66f1dd7329ff4a1cbfeaee8f32ee7) | 2026-10-16T04:53:56Z | fix(gui-test): normalize Tk widget state before asserting |
| [f3a7933f](https://github.com/CmdOS-system/Nexus-os/commit/f3a7933fb41e6c10dfb68e79956bc2236c772c58) | 2026-10-16T04:51:57Z | ci(gui): run installer UI smoke in parallel using Xvfb |
| [7b96a688](https://github.com/CmdOS-system/Nexus-os/commit/7b96a688e42c05d681134a51a2b620aa02ce3305) | 2026-10-16T04:51:52Z | test(gui): exercise installer preview in virtual display without disk writes |
| [44b3c79d](https://github.com/CmdOS-system/Nexus-os/commit/44b3c79dee2758a80b40872dce87aecf44ddba3a) | 2026-10-16T04:50:26Z | fix(installer): reuse tested freshness guard and clear stale selection on rejection |
| [1ff05cf7](https://github.com/CmdOS-system/Nexus-os/commit/1ff05cf7fed1005743537dc3804bf196f6864e9a) | 2026-10-16T04:50:21Z | test(installer): verify inventory freshness guard rejects changes |
| [ec80b5a9](https://github.com/CmdOS-system/Nexus-os/commit/ec80b5a91965a8582d4b248e7ba0e8e2ac4f3b78) | 2026-10-16T04:50:16Z | feat(installer): reusable fail-closed inventory freshness guard |
| [23796efb](https://github.com/CmdOS-system/Nexus-os/commit/23796efbdcbd626c29c4aa033c4fe20d85d442d7) | 2026-10-16T04:50:03Z | fix(installer): fail closed when disk inventory changes before preview |
| [28d623d2](https://github.com/CmdOS-system/Nexus-os/commit/28d623d24cfe18736aed2d0b42b7102240b2ee5f) | 2026-10-16T04:47:37Z | ci(iso): publish commit-bound checksum and boot marker evidence in run summary |
| [ad499f6a](https://github.com/CmdOS-system/Nexus-os/commit/ad499f6a6aeb73f203e6bf80f3754e1901b8424c) | 2026-10-16T04:40:54Z | docs(ci): codify parallel workstreams, run evidence and safe concurrency policy |
| [10792061](https://github.com/CmdOS-system/Nexus-os/commit/10792061496723f929b8bfe179b92f8b88dbe764) | 2026-10-16T04:36:06Z | ci: queue ISO builds without dropping pending runs |
| [48609d05](https://github.com/CmdOS-system/Nexus-os/commit/48609d05e2dea83d7a6c8e0eba7dfa192d151799) | 2026-10-16T04:20:51Z | ci: add parallel fast Python matrix and static image checks |
| [d0cc7d2c](https://github.com/CmdOS-system/Nexus-os/commit/d0cc7d2ce15d8145f2eb3ea53550f6f9c8338536) | 2026-10-16T04:20:45Z | ci: decouple expensive ISO builds from agent commits and avoid cancelling active builds |
| [902a3e47](https://github.com/CmdOS-system/Nexus-os/commit/902a3e47236c6cb0b1fcbf84e76ac1a54850b6a6) | 2026-10-16T04:18:00Z | test(image): validate Nexus Flow action preview module in ISO |
| [405b5a15](https://github.com/CmdOS-system/Nexus-os/commit/405b5a15fc5d326012656ee63b1962e0027e6e0a) | 2026-10-16T04:17:57Z | build(agent): ship Nexus Flow action previews in Live ISO |
| [b11d3166](https://github.com/CmdOS-system/Nexus-os/commit/b11d316627978ec28a400d37c963d1bc528e629f) | 2026-10-16T04:17:53Z | test(agent): cover read-only previews and destructive risk labeling |
| [f9c40eca](https://github.com/CmdOS-system/Nexus-os/commit/f9c40ecaa2cbe9029d3cc6f73d9a724fcf2040ec) | 2026-10-16T04:17:46Z | feat(agent): introduce non-executing risk-aware action previews |
| [f797e079](https://github.com/CmdOS-system/Nexus-os/commit/f797e07907226b87b24b991f6556209d964374df) | 2026-10-16T04:15:44Z | docs(ux): define Nexus Flow intent, consent, progress and accessibility gates |
| [ef0b0874](https://github.com/CmdOS-system/Nexus-os/commit/ef0b08745fc522aadc558739199407e0c1e068f8) | 2026-10-16T04:08:37Z | docs(design): establish Nexus Horizon design system vision and measurable UX gates |
| [0677c5ce](https://github.com/CmdOS-system/Nexus-os/commit/0677c5ce73107593934768cae77f0dfc29dc3c0f) | 2026-10-16T03:58:23Z | test(installer): cyclic and unknown device topologies fail closed |
| [18df2bf2](https://github.com/CmdOS-system/Nexus-os/commit/18df2bf2b7fe53e2327503b25eb4bf72503ff1d2) | 2026-10-16T03:58:18Z | security(installer): bound topology traversal and reject cycles or unknown children |
| [5a02e115](https://github.com/CmdOS-system/Nexus-os/commit/5a02e11578d3034204ca86c8ad4d62b5e81cad66) | 2026-10-16T03:56:17Z | test(installer): reject mapped storage under target |
| [d3096019](https://github.com/CmdOS-system/Nexus-os/commit/d30960196d1df6fe58789a61c741523aa6c033b8) | 2026-10-16T03:56:12Z | security(installer): fail closed for stacked and mapped target devices |
| [522ca079](https://github.com/CmdOS-system/Nexus-os/commit/522ca079b4ffb03aa2da56dee79d5ee99280f15d) | 2026-10-16T03:53:54Z | test(image): assert read-only installer launcher and required runtime wiring |
| [c2e15b4b](https://github.com/CmdOS-system/Nexus-os/commit/c2e15b4be90d697dd64dfab7549df95253b26d9e) | 2026-10-16T03:31:03Z | fix(installer): render multiline disk review as actual line breaks |
| [e82ec76d](https://github.com/CmdOS-system/Nexus-os/commit/e82ec76dcbe92d142b5d195c8b77285e088f2357) | 2026-10-16T03:20:38Z | test(image): validate installer preview desktop entry, Python syntax and bundled modules |
| [f2d723b5](https://github.com/CmdOS-system/Nexus-os/commit/f2d723b5314bc432f15df01d42a9faa8f65030c4) | 2026-10-16T03:20:33Z | feat(desktop): expose safe installer preview launcher in XFCE |
| [b6213356](https://github.com/CmdOS-system/Nexus-os/commit/b621335634e7f0dafc0c0f3f59e0ced86eec2b37) | 2026-10-16T03:20:27Z | build(installer): bundle read-only planner and inventory modules into live ISO |
| [a7cf28d1](https://github.com/CmdOS-system/Nexus-os/commit/a7cf28d19f430c0514b94139246d77bcba007faa) | 2026-10-16T03:20:22Z | feat(installer): add read-only Tkinter disk inspection preview |
| [75653619](https://github.com/CmdOS-system/Nexus-os/commit/75653619bd45782cdee71bde3acc1f7c62601c2c) | 2026-10-16T03:20:12Z | ci: avoid expensive ISO rebuilds for documentation-only changes |
| [fecc715d](https://github.com/CmdOS-system/Nexus-os/commit/fecc715dfd67f60cc74576d16fa42a64fb45a89f) | 2026-10-16T03:19:21Z | test(installer): verify read-only lsblk invocation and fail-closed errors |
| [d783c7f2](https://github.com/CmdOS-system/Nexus-os/commit/d783c7f2420461917a22136e7349df14c64711c3) | 2026-10-16T03:19:16Z | feat(installer): capture read-only lsblk JSON with explicit tree and columns |
| [6410ca65](https://github.com/CmdOS-system/Nexus-os/commit/6410ca65b25b96508e276b70022d049694ae0aaf) | 2026-10-16T03:17:57Z | test(installer): malformed children must fail closed |
| [9240c9a1](https://github.com/CmdOS-system/Nexus-os/commit/9240c9a1af7167a5cbb842a1db0d7b73dab8e685) | 2026-10-16T03:17:52Z | security(installer): reject malformed block device child topology |
| [97b23ebe](https://github.com/CmdOS-system/Nexus-os/commit/97b23ebe3baa5f105d3e6e4fd9138031ea4588df) | 2026-10-16T03:16:13Z | test(installer): reject nested path aliases |
| [a36dd195](https://github.com/CmdOS-system/Nexus-os/commit/a36dd1956ae42dd9dda1eb30f0d0c749f0e1e194) | 2026-10-16T03:16:08Z | security(installer): reject nested or noncanonical target paths |
| [0ed3c2cc](https://github.com/CmdOS-system/Nexus-os/commit/0ed3c2ccc54368ba20514eae5e3e89c3dcab9acd) | 2026-10-16T03:14:32Z | test(installer): reject incomplete mount inventory |
| [aba08935](https://github.com/CmdOS-system/Nexus-os/commit/aba089355fba0b2220130d9ab8b6ef113d292a14) | 2026-10-16T03:14:28Z | security(installer): fail closed on unknown mount status throughout disk inventory |
| [53b6a53b](https://github.com/CmdOS-system/Nexus-os/commit/53b6a53b2832dcd133ef6a094c4dd01f3b76b881) | 2026-10-16T02:57:21Z | test(installer): cover duplicate and missing device paths |
| [fc133388](https://github.com/CmdOS-system/Nexus-os/commit/fc1333887f93f5583f20f3dce0f1dc0cff70553b) | 2026-10-16T02:57:16Z | security(installer): reject duplicate or invalid paths across block device inventory |
| [22cb42cc](https://github.com/CmdOS-system/Nexus-os/commit/22cb42ccc80468866c9cbfb7b63fec100c6610ec) | 2026-10-16T02:41:02Z | test(installer): cover dry-run and unsafe disk rejection cases |
| [b1eee20a](https://github.com/CmdOS-system/Nexus-os/commit/b1eee20ae0ac94e51cbbfcbca44a09f626370f83) | 2026-10-16T02:40:54Z | feat(installer): add fail-closed read-only disk installation planner |
| [67dd0dd5](https://github.com/CmdOS-system/Nexus-os/commit/67dd0dd54a44649cf7a399aa24e1c1b5867232e4) | 2026-10-16T02:38:28Z | docs(installer): specify read-only planning, device identity and QCOW2-only integration architecture |
| [0bbfdb43](https://github.com/CmdOS-system/Nexus-os/commit/0bbfdb437ab27cf2297acf12749c0210ffc999ce) | 2026-10-16T02:35:20Z | docs: define fail-closed installer safety and disposable disk verification gates |
| [250c1a37](https://github.com/CmdOS-system/Nexus-os/commit/250c1a3763d602856459c655c368e6d9cc98f848) | 2026-10-16T02:05:37Z | test(recovery): corrupt checksum-protected payload rather than slot padding |
| [f015984e](https://github.com/CmdOS-system/Nexus-os/commit/f015984e5faa984bee5ba6b54f2b1013e23c4b71) | 2026-10-16T02:03:17Z | ci: run Nexus ISO gate on documentation updates for integrated validation |
| [9e5ca2ea](https://github.com/CmdOS-system/Nexus-os/commit/9e5ca2eab654b41fe9578a3706df9fc3aa9fc551) | 2026-10-16T01:58:22Z | boot: include console and null device nodes in Linux initramfs |
| [c06f3e1a](https://github.com/CmdOS-system/Nexus-os/commit/c06f3e1a255cb581bb01a1e450703fe8fb594b6d) | 2026-10-16T01:56:59Z | test: make Linux initramfs smoke build repeatable on reruns |
| [91528cf2](https://github.com/CmdOS-system/Nexus-os/commit/91528cf2396b91fb65a96fed03514ddebaf36d3b) | 2026-10-15T18:04:01Z | fix(ci): copy root-readable Ubuntu test kernel into QEMU workspace |
| [50807156](https://github.com/CmdOS-system/Nexus-os/commit/50807156568d7cc3a92b80fe707553051bd4414a) | 2026-10-15T18:00:07Z | diagnostics: preserve QEMU stderr when Linux boot exits before init marker |
| [7900e33d](https://github.com/CmdOS-system/Nexus-os/commit/7900e33d93e8e5545d9c0e4cf625dbf2912a17e8) | 2026-10-15T18:00:02Z | fix(ci): select installed generic kernel instead of Azure runner host kernel |
| [7a967bfc](https://github.com/CmdOS-system/Nexus-os/commit/7a967bfc2431ca0ecb24b0970b3e427b0d192c8f) | 2026-10-15T14:15:42Z | fix: replace corrupted Linux boot script with clean shell implementation |
| [f06aa287](https://github.com/CmdOS-system/Nexus-os/commit/f06aa287814e5abae6646b3d6fe74f408ce99f83) | 2026-10-15T14:13:24Z | fix: select BusyBox from busybox-static package and verify ELF has no interpreter |
| [a9c792e3](https://github.com/CmdOS-system/Nexus-os/commit/a9c792e3aa04cfbf71a640b70753401ef9261f3a) | 2026-10-15T14:11:29Z | fix(ci): use Ubuntu linux-image-generic instead of Debian-only linux-image-amd64 |
| [794aefad](https://github.com/CmdOS-system/Nexus-os/commit/794aefadf787038aaabb2cdc6dc8ee38f7403792) | 2026-10-15T06:23:27Z | ci: execute real Linux kernel plus BusyBox initramfs in QEMU |
| [a17f6553](https://github.com/CmdOS-system/Nexus-os/commit/a17f6553d6662d3d6564a679bb5d22fab5843c7e) | 2026-10-15T06:23:22Z | ci: build minimal static BusyBox initramfs and boot real Linux kernel under QEMU |
| [247d04d9](https://github.com/CmdOS-system/Nexus-os/commit/247d04d95541edc15247066ebdf70360518a5828) | 2026-10-15T06:17:13Z | feat: add bounded direct Linux kernel boot probe requiring guest init serial marker |
| [5bb98fde](https://github.com/CmdOS-system/Nexus-os/commit/5bb98fdec08cc91d37032492ee0b771748f30e47) | 2026-10-15T06:06:18Z | test(qcow2): align regression with required ImageCheck check-errors schema |
| [e5e42cc1](https://github.com/CmdOS-system/Nexus-os/commit/e5e42cc17a3636481b0602f454b1bd9c865bed20) | 2026-10-15T06:06:13Z | fix(qcow2): require mandatory QAPI check-errors while accepting optional zero counters |
| [1d1d00bb](https://github.com/CmdOS-system/Nexus-os/commit/1d1d00bb651403d9302727984238d3c931d39d89) | 2026-10-15T06:06:08Z | test(qcow2): cover optional QAPI zero corruption/leak fields omitted in real images |
| [bc85d69c](https://github.com/CmdOS-system/Nexus-os/commit/bc85d69cf4353a57f07411fc0732910d75c29335) | 2026-10-15T06:06:00Z | fix(qcow2): handle QAPI optional corruptions and leaks omitted when zero |
| [d7edb480](https://github.com/CmdOS-system/Nexus-os/commit/d7edb4803fcb54519f8903aa07981d69deb00899) | 2026-10-15T06:04:41Z | test: regress real qemu-img JSON omission of optional check-errors field |
| [5ee87aa4](https://github.com/CmdOS-system/Nexus-os/commit/5ee87aa49052ff71c863fe5a6b6c948661eb5cf4) | 2026-10-15T06:04:34Z | fix: accept qemu-img check JSON without optional check-errors when exit status succeeds |
| [33240959](https://github.com/CmdOS-system/Nexus-os/commit/33240959337575811b63e116f360712c2796d632) | 2026-10-15T06:02:37Z | fix(ci): accept actual file(1) PE32+ EFI application output formats |
| [ed7ffebc](https://github.com/CmdOS-system/Nexus-os/commit/ed7ffebc86db5420868ff7e578ebb01b7696ff04) | 2026-10-15T06:00:58Z | fix: compare PE signature against two actual NUL bytes |
| [ea21d7e3](https://github.com/CmdOS-system/Nexus-os/commit/ea21d7e3ab5f06cba79d84eb400fe545f80acc14) | 2026-10-15T06:00:53Z | security: verify PE32+ x86-64 signatures before booting EFI guest |
| [5c4109b2](https://github.com/CmdOS-system/Nexus-os/commit/5c4109b299380f9b72114fbc68e6002b28fdde85) | 2026-10-15T06:00:44Z | build: assert EFI binary is a PE32+ UEFI application after linking |
| [521bb62a](https://github.com/CmdOS-system/Nexus-os/commit/521bb62ae007b380bb2d8f15bc3aecd5b760181f) | 2026-10-15T05:59:13Z | ci: compile UEFI guest and require real OVMF/QEMU execution marker |
| [630b4ae5](https://github.com/CmdOS-system/Nexus-os/commit/630b4ae50a3c14ee58a3669a19ceade750c401b6) | 2026-10-15T05:59:08Z | feat: real OVMF EFI guest execution test requiring debug-exit handshake |
| [96ade5a0](https://github.com/CmdOS-system/Nexus-os/commit/96ade5a05e3f95c33b27b9f0cb94cc6e988e9997) | 2026-10-15T05:58:57Z | build: compile freestanding EFI probe with clang and lld |
| [e9458cd0](https://github.com/CmdOS-system/Nexus-os/commit/e9458cd0dd410050323a2a504ba9d38d3de5f926) | 2026-10-15T05:58:50Z | feat: minimal x86_64 UEFI guest emits QEMU debug-exit success marker |
| [8e05cd4c](https://github.com/CmdOS-system/Nexus-os/commit/8e05cd4c669c9ea2d841fce32e72dc881be3f196) | 2026-10-15T05:57:57Z | test: require exact QEMU guest debug-exit marker to confirm EFI execution |
| [57e8aeed](https://github.com/CmdOS-system/Nexus-os/commit/57e8aeed43db03e50ba9d86200ff5ce87a415e51) | 2026-10-15T05:57:50Z | feat: define explicit guest-to-host QEMU debug-exit success handshake |
| [a716b7bc](https://github.com/CmdOS-system/Nexus-os/commit/a716b7bc859c4ea0fe20382154186b9b1d222be0) | 2026-10-15T05:56:40Z | test: QEMU process timeout must not be misreported as successful OVMF initialization |
| [1b945565](https://github.com/CmdOS-system/Nexus-os/commit/1b9455655f647fc0cacd8beab6b059054647ab27) | 2026-10-15T05:56:37Z | fix: classify QEMU timeout as inconclusive, not proof of firmware boot |
| [a610cbe2](https://github.com/CmdOS-system/Nexus-os/commit/a610cbe280a743841eb6017cab96716f65a204dc) | 2026-10-15T05:55:37Z | feat: capture OVMF firmware debug console on I/O port 0x402 |
| [d436699c](https://github.com/CmdOS-system/Nexus-os/commit/d436699cec398ea17418bf0286ffe20138bcb11e) | 2026-10-15T05:54:05Z | test: verify real-OVMF probe timeout and early-exit semantics |
| [9d4e39db](https://github.com/CmdOS-system/Nexus-os/commit/9d4e39dbe2223a54927bbd63849fadc7636ba080) | 2026-10-15T05:53:07Z | fix: allow differing OVMF CODE and VARS sizes (common firmware layout) |
| [764b2ff4](https://github.com/CmdOS-system/Nexus-os/commit/764b2ff44123441006c8ba6f7a88a587d41acd94) | 2026-10-15T05:53:03Z | fix: reject invalid probe timeouts and mismatched OVMF pflash sizes |
| [51e49d19](https://github.com/CmdOS-system/Nexus-os/commit/51e49d19ec43b183a2e62bb9ed56d635f480bf5e) | 2026-10-15T05:51:41Z | ci: install real OVMF and QEMU and run bounded firmware power-on probe |
| [43c3fef0](https://github.com/CmdOS-system/Nexus-os/commit/43c3fef0025787f126284c3a0e9ed98a734b97b2) | 2026-10-15T05:51:37Z | feat: add bounded real QEMU/OVMF power-on probe with disposable QCOW2 |
| [4996355f](https://github.com/CmdOS-system/Nexus-os/commit/4996355f11c840ed723fd5de18a6f34fab0898bd) | 2026-10-15T05:49:58Z | test: reject malformed declared QCOW2 v3 header length |
| [7f4af51e](https://github.com/CmdOS-system/Nexus-os/commit/7f4af51ef60ec306210ea2f02e6b6bb7a90e87a4) | 2026-10-15T05:49:51Z | test: set QCOW2 v3 header_length to 104 in synthetic fixtures |
| [350716f4](https://github.com/CmdOS-system/Nexus-os/commit/350716f42b0755caaf51ddf5b7b1f70e7491bb0c) | 2026-10-15T05:49:48Z | test: set QCOW2 v3 header_length to 104 in synthetic fixtures |
| [0057e196](https://github.com/CmdOS-system/Nexus-os/commit/0057e196428de50883811276f815c30a5ec4289f) | 2026-10-15T05:49:44Z | fix: validate QCOW2 v3 declared header length against QEMU specification |
| [1dc905a8](https://github.com/CmdOS-system/Nexus-os/commit/1dc905a899d7167c310ef223466dcdff8ff6ddb9) | 2026-10-15T05:48:09Z | test: backing, corrupt and encrypted QCOW2 headers fail closed |
| [6d292380](https://github.com/CmdOS-system/Nexus-os/commit/6d2923803bb2e628e779789cefa383b41eba06f2) | 2026-10-15T05:48:02Z | security: reject backing, encryption, dirty and corrupt QCOW2 header flags before qemu-img |
| [c138457d](https://github.com/CmdOS-system/Nexus-os/commit/c138457de60917ce79f942da210565d53a3687b0) | 2026-10-15T05:46:33Z | test: QCOW2 v2 72-byte headers allowed and truncated v3 rejected |
| [f9a8bdbd](https://github.com/CmdOS-system/Nexus-os/commit/f9a8bdbd72f2b9b7be54e1c430dd26d16e0b178a) | 2026-10-15T05:46:25Z | test: align QCOW2 v3 synthetic fixtures to 104-byte header minimum |
| [91c4821a](https://github.com/CmdOS-system/Nexus-os/commit/91c4821a2bbcbf802a1875d2c39f0afaeb259ba7) | 2026-10-15T05:46:22Z | test: align QCOW2 v3 synthetic fixtures to 104-byte header minimum |
| [04db8c5d](https://github.com/CmdOS-system/Nexus-os/commit/04db8c5d9d1110cfca53e3db760db93c870fcece) | 2026-10-15T05:46:18Z | fix: respect QCOW2 v2 72-byte and v3 104-byte minimum headers |
| [1f817c30](https://github.com/CmdOS-system/Nexus-os/commit/1f817c303191307433521cf0d9aa784c9dbf95d4) | 2026-10-15T05:45:11Z | test: reject truncated QCOW2 headers and external data bit without qemu-img |
| [fa070d49](https://github.com/CmdOS-system/Nexus-os/commit/fa070d49648e39310e17323b98928cdb349091fe) | 2026-10-15T05:45:07Z | test: use complete QCOW2 v3 header fixtures for new header checks |
| [14cf5c3f](https://github.com/CmdOS-system/Nexus-os/commit/14cf5c3fcaa3acf659499528f4992645c43ebbaf) | 2026-10-15T05:45:05Z | test: use complete QCOW2 v3 header fixtures for new header checks |
| [a9aa3f4c](https://github.com/CmdOS-system/Nexus-os/commit/a9aa3f4c8f2e7a245538cfaaa06a95b4039170a3) | 2026-10-15T05:45:00Z | security: reject QCOW2 v3 external-data incompatibility bit in image header |
| [81f2e067](https://github.com/CmdOS-system/Nexus-os/commit/81f2e0675667529cf5f51bb04eb3157bdc070b5d) | 2026-10-15T05:44:55Z | fix: enforce smoke validation even when Python assertions are optimized away |
| [e4af6c26](https://github.com/CmdOS-system/Nexus-os/commit/e4af6c2693dbc6268880cffff32f6f23e85f5ded) | 2026-10-15T05:43:39Z | test: smoke command never reports VM boot and handles missing qemu-img |
| [ce2f87aa](https://github.com/CmdOS-system/Nexus-os/commit/ce2f87aa5177dc14cf940c4e3224ab83d486b012) | 2026-10-15T05:42:33Z | ci: run disposable QCOW2 smoke test with real qemu-img |
| [5a3ee4cc](https://github.com/CmdOS-system/Nexus-os/commit/5a3ee4cce0f79b9a73f44310f45cf5a934aa2edb) | 2026-10-15T05:42:29Z | feat: add reproducible real-qemu-img smoke test command |
| [21692878](https://github.com/CmdOS-system/Nexus-os/commit/216928789fc69e8919ddce8f3f5e091058bc1fb4) | 2026-10-15T05:41:51Z | test: reject empty qemu-img check reports rather than assuming success |
| [aaf2cd8f](https://github.com/CmdOS-system/Nexus-os/commit/aaf2cd8fa4b5613bce0297ffbb64b072a6f48ba3) | 2026-10-15T05:41:45Z | security: fail closed on missing or malformed QCOW2 check fields |
| [6c450121](https://github.com/CmdOS-system/Nexus-os/commit/6c4501219ab962c0a86661ff16b6032dc0a8c59c) | 2026-10-15T05:39:20Z | ci: install qemu-utils so QCOW2 integration tests execute on every push |
| [d4eb6095](https://github.com/CmdOS-system/Nexus-os/commit/d4eb6095899fb044e3c4786eb4475fec87cbe27e) | 2026-10-15T05:39:15Z | test: exercise real qemu-img QCOW2 validation, isolation and backing rejection |
| [25ff58c6](https://github.com/CmdOS-system/Nexus-os/commit/25ff58c61ffcff63e910af9fd6a7d1ab9d36200a) | 2026-10-15T05:38:20Z | test: reject qemu-img check_errors reported with underscore |
| [2d5270c5](https://github.com/CmdOS-system/Nexus-os/commit/2d5270c5678f5192672d230ca56a730492900e3d) | 2026-10-15T05:38:15Z | fix: accept QAPI check_errors naming in qemu-img consistency reports |
| [6518a07b](https://github.com/CmdOS-system/Nexus-os/commit/6518a07bf631d66e095b55567ce1a3ee30cd0a9f) | 2026-10-15T05:37:32Z | test: cover qemu-img check corruption and external data files |
| [6b154500](https://github.com/CmdOS-system/Nexus-os/commit/6b154500edbee97e6a4694dd40c2c0d6b83ecc73) | 2026-10-15T05:37:26Z | security: require qemu-img check and reject external data files |
| [65d3515f](https://github.com/CmdOS-system/Nexus-os/commit/65d3515f0550126a5c6f2a1af6868d1aa8c2ef71) | 2026-10-15T05:35:51Z | style: normalize nested QEMU lab context indentation |
| [3388d825](https://github.com/CmdOS-system/Nexus-os/commit/3388d8257ecaa335b62eee7ad17f70665fc25366) | 2026-10-15T05:35:45Z | fix: fail fast on invalid disk signature before invoking qemu-img |
| [6ee12349](https://github.com/CmdOS-system/Nexus-os/commit/6ee12349adb4455f2c9bb51143bbf2524b78ef00) | 2026-10-15T05:35:41Z | test: assert both OVMF and guest disk are isolated and removed |
| [7ab2bfc5](https://github.com/CmdOS-system/Nexus-os/commit/7ab2bfc5622ebe0f2cdc906c50fb923ad6cd4883) | 2026-10-15T05:35:35Z | feat: use isolated disk copies in QEMU lab launch contexts |
| [cc97cfbb](https://github.com/CmdOS-system/Nexus-os/commit/cc97cfbb07d41583ff8ef2bfea4f901c1115b7e0) | 2026-10-15T05:35:30Z | feat: isolate guest QCOW2 disks using disposable full copies |
| [e8cc3827](https://github.com/CmdOS-system/Nexus-os/commit/e8cc3827aa6e2c7dca1970c158072e3dc690e638) | 2026-10-15T05:35:01Z | test: validate disposable OVMF VARS lifecycle in QEMU launch context |
| [6dd71e2d](https://github.com/CmdOS-system/Nexus-os/commit/6dd71e2d4c1d7b4621b12034ec91ac3c5e2cea26) | 2026-10-15T05:34:56Z | feat: connect isolated OVMF VARS to validated QEMU launch plan |
| [55610d66](https://github.com/CmdOS-system/Nexus-os/commit/55610d66917dd5466b2810c9d772a8c2f1c11ebf) | 2026-10-15T05:34:13Z | test: ensure OVMF variable template survives guest changes |
| [e2bbb1a9](https://github.com/CmdOS-system/Nexus-os/commit/e2bbb1a9e2f0febb77e799faf6634c4cf1bce17d) | 2026-10-15T05:34:08Z | fix: reject OVMF template symlinks before resolving paths |
| [828f1b68](https://github.com/CmdOS-system/Nexus-os/commit/828f1b6832c76b3452bc24cf2464f271b92731f8) | 2026-10-15T05:34:04Z | feat: isolate writable OVMF variables in disposable lab directory |
| [9442d6ee](https://github.com/CmdOS-system/Nexus-os/commit/9442d6ee06d26250817c716830e6c170213e1296) | 2026-10-15T05:32:20Z | test: adapt QEMU launch checks to qemu-img validation dependency |
| [a651accf](https://github.com/CmdOS-system/Nexus-os/commit/a651accf7f756bfcdc6ae5eb410ec6982340a0a0) | 2026-10-15T05:32:16Z | fix: require qemu-img validation before constructing VM launch |
| [c42469ff](https://github.com/CmdOS-system/Nexus-os/commit/c42469ff5a43d6827e508b0cce006405eb873084) | 2026-10-15T05:29:33Z | test: cover QCOW2 qemu-img metadata and backing chain rejection |
| [13d21958](https://github.com/CmdOS-system/Nexus-os/commit/13d21958bf2b33f19aa5ad1d110a149817ff7fb6) | 2026-10-15T05:29:28Z | feat: validate QCOW2 with qemu-img JSON and reject backing chains |
| [46287c73](https://github.com/CmdOS-system/Nexus-os/commit/46287c73c68cbb044ec24a9ac5bd6cae8cbdaba0) | 2026-10-15T05:29:23Z | fix: use unambiguous QCOW2 magic bytes |
| [ea11d141](https://github.com/CmdOS-system/Nexus-os/commit/ea11d1417d7eb659acaa5f0d7fdb21de965183f8) | 2026-10-15T05:28:35Z | test: check QCOW2 signature and reject mislabeled disk files |
| [67921a59](https://github.com/CmdOS-system/Nexus-os/commit/67921a5932f00dc65be1db7b2cf2c901a326f973) | 2026-10-15T05:28:28Z | fix: reject non-QCOW2 disk images before building QEMU launch |
| [534899b8](https://github.com/CmdOS-system/Nexus-os/commit/534899b850efd5bde1c57916997f6806bd7fb500) | 2026-10-15T05:28:04Z | test: verify safe QEMU OVMF command construction |
| [59db6981](https://github.com/CmdOS-system/Nexus-os/commit/59db6981267b1c0916aef911b57e2836424b0951) | 2026-10-15T05:27:59Z | feat: construct non-executing QEMU OVMF launch plans with file safety checks |
| [bab77bee](https://github.com/CmdOS-system/Nexus-os/commit/bab77bee1da11fe54622b6d9c6a1f448f34d7f3e) | 2026-10-15T05:26:43Z | test: cover safe QEMU OVMF environment detection |
| [0e9c775d](https://github.com/CmdOS-system/Nexus-os/commit/0e9c775d6dc483cf5de3199e9843265416f327d1) | 2026-10-15T05:26:38Z | feat: add safe read-only QEMU OVMF prerequisite detector |
| [df86c3a7](https://github.com/CmdOS-system/Nexus-os/commit/df86c3a722f5327e2904f43481be4298c63e16bc) | 2026-10-15T05:24:59Z | docs: define QEMU OVMF validation matrix and single retry authority |
| [2ab3cb70](https://github.com/CmdOS-system/Nexus-os/commit/2ab3cb7037d7c8556f12234d658a4101c1ee86cd) | 2026-10-15T05:24:18Z | ci: run Recovery G2 suite on Python 3.12 and 3.13 |
| [12b01f89](https://github.com/CmdOS-system/Nexus-os/commit/12b01f8959e19410da9ec140bbf3845f698b61a4) | 2026-10-15T05:23:26Z | test: use spawn to avoid unsafe fork in multithreaded runners |
| [5c6878e1](https://github.com/CmdOS-system/Nexus-os/commit/5c6878e1e2fc90cd3f86a548ecda6377705b93dd) | 2026-10-15T05:21:52Z | test: cover systemd boot-count transitions and successful blessing |
| [39cbae6b](https://github.com/CmdOS-system/Nexus-os/commit/39cbae6b3cb43a21a58902b87dbee6d80de37e11) | 2026-10-15T05:21:46Z | feat: model systemd-boot retry rename and blessing transitions |
| [4ac2d1fe](https://github.com/CmdOS-system/Nexus-os/commit/4ac2d1fe16966c33db374e3c18ae0c46077d259b) | 2026-10-15T05:21:16Z | test: validate offline boot-count filename parsing and traversal rejection |
| [73a1be94](https://github.com/CmdOS-system/Nexus-os/commit/73a1be948966295e5ef584252143980ca832e334) | 2026-10-15T05:21:12Z | feat: parse systemd-boot boot-count entry names offline |
| [62e14275](https://github.com/CmdOS-system/Nexus-os/commit/62e14275ed05e80697ef7a1ec1685ca615a25818) | 2026-10-15T05:20:22Z | test: check recovery boot attempts are serialized across processes |
| [3b798904](https://github.com/CmdOS-system/Nexus-os/commit/3b79890425ebf5c8068dce41abcee9135395d5ab) | 2026-10-15T05:20:17Z | fix: serialize recovery state read-modify-write transactions |
| [0dab50e1](https://github.com/CmdOS-system/Nexus-os/commit/0dab50e1ff564f42ce2ca7bc05de5a4ac4d5aec0) | 2026-10-15T05:20:12Z | feat: add Linux advisory transaction lock for Recovery G2 |
| [a7cd09df](https://github.com/CmdOS-system/Nexus-os/commit/a7cd09df15dd364c2f6a11a7a63339dc17357734) | 2026-10-15T05:19:31Z | docs: document Recovery G2 trust boundaries and hardware safety gates |
| [a63d30e8](https://github.com/CmdOS-system/Nexus-os/commit/a63d30e8efe21ac17463d652550c726dc2bbe964) | 2026-10-15T05:19:08Z | test: validate simulated boot fallback and successful confirmation |
| [a7ba96c8](https://github.com/CmdOS-system/Nexus-os/commit/a7ba96c803de559b34f291bfe7eb687405844fed) | 2026-10-15T05:19:02Z | feat: add disposable Recovery G2 boot and rollback simulator |
| [192493cd](https://github.com/CmdOS-system/Nexus-os/commit/192493cd5b42ada6463e5b4e2b8523b1253e0ba3) | 2026-10-15T05:16:56Z | fix: reject boolean and noninteger recovery state counters |
| [acb3fbe2](https://github.com/CmdOS-system/Nexus-os/commit/acb3fbe2da9f34217d4549d296fb551bc080510a) | 2026-10-15T05:16:52Z | test: require strict integer recovery counters and boot budgets |
| [2f1eaf28](https://github.com/CmdOS-system/Nexus-os/commit/2f1eaf285e120f651317b9ef6423ad819e2a1b21) | 2026-10-15T05:14:19Z | test: cover persisted boot controller verification, retry and confirmation |
| [505bd4b0](https://github.com/CmdOS-system/Nexus-os/commit/505bd4b0fadd2e1b0484739307c1b24c4916fd64) | 2026-10-15T05:14:17Z | feat: connect persistent recovery metadata to A/B boot controller |
| [7cef0943](https://github.com/CmdOS-system/Nexus-os/commit/7cef094369cefa65c849f47df4f30a4c68460a01) | 2026-10-15T05:14:08Z | fix: reliably detect metadata tampering in crash window test |
| [a3d8380b](https://github.com/CmdOS-system/Nexus-os/commit/a3d8380b5dad434ab919dc267ae7c106b2a8d748) | 2026-10-15T05:10:28Z | test: cover interrupted redundant writes, checksum corruption and exhausted candidates |
| [e9da38f4](https://github.com/CmdOS-system/Nexus-os/commit/e9da38f45165ac4947ddeccadba26db9994d40ac) | 2026-10-15T05:07:22Z | test: exercise persisted A/B boot retries, confirmation and rollback across restarts |
| [efc4015c](https://github.com/CmdOS-system/Nexus-os/commit/efc4015cac920bccc6181477e8b7ca4f76eceb0f) | 2026-10-15T05:05:16Z | test: reject conflicting metadata and tolerate torn redundant copy |
| [e426b33b](https://github.com/CmdOS-system/Nexus-os/commit/e426b33b78f1107693775bb7f854f173260e62e9) | 2026-10-15T05:05:08Z | ci: run Recovery G2 boot and metadata unit tests on pushes and PRs |
| [6a7a124d](https://github.com/CmdOS-system/Nexus-os/commit/6a7a124d45ddc58eaed5c67d0cc969719407abbf) | 2026-10-15T05:02:42Z | test: cover recovery metadata corruption and generation safety |
| [ad3decc2](https://github.com/CmdOS-system/Nexus-os/commit/ad3decc22f7f5e5a7487e06d4becbe689c3ff287) | 2026-10-15T05:02:40Z | feat: add durable redundant checksummed recovery metadata store |
| [2832e72d](https://github.com/CmdOS-system/Nexus-os/commit/2832e72da70b3ae93451a5034e5df5d0deca1971) | 2026-10-15T05:00:10Z | test: cover tentative boot attempts, confirmation and rollback |
| [3ab4e01a](https://github.com/CmdOS-system/Nexus-os/commit/3ab4e01a50dfca5319036373633c3d282045eab0) | 2026-10-15T05:00:08Z | feat: add pure Recovery G2 A/B boot decision state machine |
| [db224084](https://github.com/CmdOS-system/Nexus-os/commit/db22408484650832c5e00148454f895b61648f66) | 2026-10-15T04:58:09Z | docs: specify Recovery G2 A/B boot confirmation and fault injection contract |
| [ca9ea785](https://github.com/CmdOS-system/Nexus-os/commit/ca9ea7850d671033e8d2c5a55377e45627ef9a56) | 2026-10-15T02:55:15Z | test: verify disposable A/B slot isolation and corruption detection |
| [d921d12d](https://github.com/CmdOS-system/Nexus-os/commit/d921d12dde1176a2e5f8fcf3a21f99e5215cedb3) | 2026-10-15T02:55:05Z | feat: add disposable file-backed A/B recovery storage model |
| [ffbb62db](https://github.com/CmdOS-system/Nexus-os/commit/ffbb62db54ab67b780de0cb5eb3e036dad498cad) | 2026-10-15T02:36:17Z | test: verify redundant recovery metadata failover |
| [6f066f28](https://github.com/CmdOS-system/Nexus-os/commit/6f066f2838af549bdd87a4e7f909975b64372155) | 2026-10-15T02:36:06Z | feat: add redundant recovery metadata selection |
| [6f7e9271](https://github.com/CmdOS-system/Nexus-os/commit/6f7e92713a52890c2916bbcc0c2c91fe7d189bbd) | 2026-10-15T02:21:47Z | test: inject actual invalid UTF-8 bytes into metadata parser |
| [2165ba35](https://github.com/CmdOS-system/Nexus-os/commit/2165ba35143875205dcba09b7f6de419df91c756) | 2026-10-15T02:21:41Z | test: inject metadata write failures and verify recovery invariants |
| [1cd29364](https://github.com/CmdOS-system/Nexus-os/commit/1cd2936476d62f33bc818bcfb560ed2df533b611) | 2026-10-15T02:05:49Z | fix: use hmac.compare_digest for recovery metadata checksums |
| [654a2be8](https://github.com/CmdOS-system/Nexus-os/commit/654a2be8096c2f21cfc94214a61d451f12be78f9) | 2026-10-15T02:04:46Z | test: cover Nexus Recovery metadata corruption and atomic replacement |
| [989acecd](https://github.com/CmdOS-system/Nexus-os/commit/989acecd9928c9787dfe6881a94f7b73255b71c3) | 2026-10-15T02:04:35Z | feat: add crash-safe validated Nexus Recovery metadata |
| [0ecc222f](https://github.com/CmdOS-system/Nexus-os/commit/0ecc222f1b6edd6115b1c6a353bfbd9f2a92be6f) | 2026-10-15T01:45:41Z | test: gate Nexus Recovery rollback invariants in CI |
| [b87ec675](https://github.com/CmdOS-system/Nexus-os/commit/b87ec675172ed661aded373af434e99bfa871703) | 2026-10-15T01:24:21Z | feat: add unprivileged Nexus Recovery A/B state simulator with safety tests |
| [dbc7aaa8](https://github.com/CmdOS-system/Nexus-os/commit/dbc7aaa8e108653d85f0f1f3fcf39d43467f7966) | 2026-10-15T01:18:53Z | docs: design Nexus Recovery with ChromiumOS-inspired safe A/B gates |
| [bf083031](https://github.com/CmdOS-system/Nexus-os/commit/bf083031f0202c456c6a416d472f4c8680a77c62) | 2026-10-15T01:03:53Z | test: require XFCE window manager and panel readiness |
| [22509dd5](https://github.com/CmdOS-system/Nexus-os/commit/22509dd53e588454eed11ccc77f6fa87d258b66b) | 2026-10-15T00:27:21Z | fix: enable XFCE session evidence relay in live image |
| [79628c64](https://github.com/CmdOS-system/Nexus-os/commit/79628c64174ef4c7f31a27a51df73fd019c68b6f) | 2026-10-15T00:27:19Z | fix: record XFCE readiness in user runtime directory |
| [c88b4ad3](https://github.com/CmdOS-system/Nexus-os/commit/c88b4ad3e8ac184eedc27a07bf263b437be8d896) | 2026-10-15T00:27:14Z | fix: configure live LightDM autologin and XFCE evidence relay |
| [0334b108](https://github.com/CmdOS-system/Nexus-os/commit/0334b1082e6f7fd06222aff0954d09c3be9c9725) | 2026-10-15T00:27:11Z | fix: configure live LightDM autologin and XFCE evidence relay |
| [29cdb21f](https://github.com/CmdOS-system/Nexus-os/commit/29cdb21f61a6a37eae1bc25474e3a6d953941ddf) | 2026-10-15T00:27:09Z | fix: configure live LightDM autologin and XFCE evidence relay |
| [55c0e5b0](https://github.com/CmdOS-system/Nexus-os/commit/55c0e5b020bb3028e09e1c6eb7d95e407595b1d8) | 2026-10-15T00:14:09Z | fix: launch XFCE readiness probe through shell from XDG autostart |
| [d2b241c6](https://github.com/CmdOS-system/Nexus-os/commit/d2b241c6ae4b2df9948499d4d250df7170416260) | 2026-10-14T23:57:36Z | fix: explicitly configure Nexus live user and XFCE session |
| [d90bfe38](https://github.com/CmdOS-system/Nexus-os/commit/d90bfe38ee89afcae18b0bb3f5db32e98828b0bc) | 2026-10-14T22:54:21Z | test: require real XFCE user session in UEFI smoke gate |
| [0f7ba5bc](https://github.com/CmdOS-system/Nexus-os/commit/0f7ba5bc941c986988697b1785acfb46ae55349a) | 2026-10-14T22:54:15Z | test: add in-session XFCE readiness evidence |
| [0b52e0d9](https://github.com/CmdOS-system/Nexus-os/commit/0b52e0d91b92c04aa6eaf4dc17b73e84138cc799) | 2026-10-14T22:54:13Z | test: add in-session XFCE readiness evidence |
| [e337021e](https://github.com/CmdOS-system/Nexus-os/commit/e337021ee8e1b263f0e7b305d829b38bab5c357d) | 2026-10-14T13:07:18Z | test: require graphical stack readiness in UEFI smoke gate |
| [80673c35](https://github.com/CmdOS-system/Nexus-os/commit/80673c35d7003aa710683121f2204f0187e0730c) | 2026-10-14T06:59:07Z | test: enable graphical readiness probe in live image |
| [520d6f86](https://github.com/CmdOS-system/Nexus-os/commit/520d6f862dd7d4a1cfff179c6f2c6f905c1f32a5) | 2026-10-14T06:59:02Z | test: add graphical stack readiness probe |
| [b4e35b3e](https://github.com/CmdOS-system/Nexus-os/commit/b4e35b3efe2725124c7581a0f5f8cfa73506e263) | 2026-10-14T06:58:59Z | test: add graphical stack readiness probe |
| [f07dc065](https://github.com/CmdOS-system/Nexus-os/commit/f07dc0656214e7485f1ac412e442d653e0dd0633) | 2026-10-14T06:32:11Z | fix: restore ISO gate workflow after malformed incremental edit |
| [bdb09192](https://github.com/CmdOS-system/Nexus-os/commit/bdb09192e8a455081895c5cca842ef2dcd2af7c4) | 2026-10-14T06:10:10Z | test: validate GRUB template-based unattended boot configuration |
| [64c84ebe](https://github.com/CmdOS-system/Nexus-os/commit/64c84ebeeddfbca78b14b4ccd63cd9dccfb2380c) | 2026-10-14T06:10:06Z | ci: assert final ISO contains GRUB default and three-second timeout |
| [dbd3d257](https://github.com/CmdOS-system/Nexus-os/commit/dbd3d257fbba83062ac0ecf47222e29bb9e7e926) | 2026-10-14T06:10:00Z | fix: configure unattended GRUB using live-build supported bootloader template override |
| [95713e08](https://github.com/CmdOS-system/Nexus-os/commit/95713e0825a17c06a5c2485c10d9d90d3e9093d5) | 2026-10-14T05:51:31Z | ci: extract actual GRUB configuration from built ISO for unattended UEFI diagnosis |
| [03a8bc99](https://github.com/CmdOS-system/Nexus-os/commit/03a8bc9933f9ec55362249524b0162502892f028) | 2026-10-14T05:36:42Z | test: require PE inspector in image runtime module set |
| [5c845385](https://github.com/CmdOS-system/Nexus-os/commit/5c845385c5be289710228e7aa19f22e664fdf01d) | 2026-10-14T05:36:37Z | build: ship PE compatibility inspector in Nexus live image |
| [7cc82402](https://github.com/CmdOS-system/Nexus-os/commit/7cc82402ebe450029fea0b669498a94f8ddeba3c) | 2026-10-14T05:34:47Z | test: cover PE architecture and malformed input boundaries |
| [127d90a6](https://github.com/CmdOS-system/Nexus-os/commit/127d90a698257af54cef18487cad0257db65e61e) | 2026-10-14T05:34:41Z | feat: add bounded read-only Windows PE header inspector |
| [2b3e3ca7](https://github.com/CmdOS-system/Nexus-os/commit/2b3e3ca726f4a5f674f755145881e3f7bbf3fddd) | 2026-10-14T05:34:35Z | test: reject premature GRUB binary hook execution |
| [635ea3fa](https://github.com/CmdOS-system/Nexus-os/commit/635ea3fa5d6ddac1a0b2a83b6f002eea8862c48e) | 2026-10-14T05:34:29Z | fix: stop executing GRUB mutation before live-build generates grub.cfg |
| [c91c0f90](https://github.com/CmdOS-system/Nexus-os/commit/c91c0f90476093a7c9a5783a7e7a55a5c8da1776) | 2026-10-14T05:30:05Z | docs: analyze Bottles Lutris Proton architecture and define safe Windows compatibility gates |
| [0b2ec94d](https://github.com/CmdOS-system/Nexus-os/commit/0b2ec94d438cb545fed69fe63929db926798c7db) | 2026-10-14T05:21:09Z | test: prevent incorrect live-build binary hook staging path |
| [35f59939](https://github.com/CmdOS-system/Nexus-os/commit/35f59939c147e2a025926ea19fbe0f9a26b436d7) | 2026-10-14T05:21:05Z | fix: stage binary GRUB hook in Debian Live documented hooks/live directory |
| [810087b6](https://github.com/CmdOS-system/Nexus-os/commit/810087b677f5bba2e27845fa193daf9c94b2ac4a) | 2026-10-14T05:19:40Z | test: require generated GRUB timeout hook and shell syntax |
| [2b1d63a3](https://github.com/CmdOS-system/Nexus-os/commit/2b1d63a36bb95e19e78157751687ad2a88fd782c) | 2026-10-14T05:19:35Z | build: stage GRUB binary hook before ISO assembly |
| [33ae3382](https://github.com/CmdOS-system/Nexus-os/commit/33ae3382f8518e29e491931ebf11edb62dc9ec7b) | 2026-10-14T05:19:31Z | boot: configure generated GRUB menu for unattended default boot |
| [5b1924a0](https://github.com/CmdOS-system/Nexus-os/commit/5b1924a03844d948d7b04b2946d26201bc218c27) | 2026-10-14T04:58:08Z | test: align image preflight with supported live-build flags |
| [7a30d795](https://github.com/CmdOS-system/Nexus-os/commit/7a30d795b5a8cadd500d9c6d54f5e8e541cf99fb) | 2026-10-14T04:58:05Z | fix: remove unsupported live-build bootloader-timeout option |
| [d38ddb91](https://github.com/CmdOS-system/Nexus-os/commit/d38ddb915fb6ecb372abd37db97aff6e52a2685b) | 2026-10-14T04:56:18Z | test: enforce unattended bootloader configuration in image gate |
| [237f0455](https://github.com/CmdOS-system/Nexus-os/commit/237f0455d782231ec77f00c76cc7849eb6232a3a) | 2026-10-14T04:56:12Z | test: require unattended UEFI live boot without synthetic keypresses |
| [0614068d](https://github.com/CmdOS-system/Nexus-os/commit/0614068d1070229e823200ece23c63a9e83996a5) | 2026-10-14T04:56:07Z | boot: configure unattended GRUB EFI timeout for live image |
| [76c9039e](https://github.com/CmdOS-system/Nexus-os/commit/76c9039edae2ae4172042441d2b8a805d27ac53e) | 2026-10-14T04:32:34Z | test: probe EFI boot menu with automated Enter through QEMU monitor |
| [aad09b31](https://github.com/CmdOS-system/Nexus-os/commit/aad09b319f39159ca7ca434582b3d426fb243933) | 2026-10-14T04:11:54Z | test: require serial console boot arguments for CI observability |
| [05f62896](https://github.com/CmdOS-system/Nexus-os/commit/05f62896fd939010a12b991fbe45d33da6db265c) | 2026-10-14T04:11:50Z | boot: expose live kernel and systemd output on serial console |
| [5317960b](https://github.com/CmdOS-system/Nexus-os/commit/5317960bf842d335a738af86feb3b106f7b3df2c) | 2026-10-14T03:53:29Z | diagnostics: capture QEMU guest errors and serial tail on boot timeout |
| [58729422](https://github.com/CmdOS-system/Nexus-os/commit/58729422a55aa8f725d2a1b6a7aaf39d5fdb0fd8) | 2026-10-14T03:53:24Z | ci: retain QEMU serial and debug diagnostics even when boot gate fails |
| [71ab111c](https://github.com/CmdOS-system/Nexus-os/commit/71ab111c52546dd7e0833582d47519b4da98189a) | 2026-10-14T03:38:00Z | fix: syntax-check live-build hooks independent of filename extension |
| [b75b75f3](https://github.com/CmdOS-system/Nexus-os/commit/b75b75f3ba846ef53ea9e8a071b9bd560975093a) | 2026-10-14T03:34:19Z | test: syntax-check all image shell scripts before expensive ISO build |
| [ef86d1d1](https://github.com/CmdOS-system/Nexus-os/commit/ef86d1d1bbd5c7c5348a1442788a58e6cbefe16c) | 2026-10-14T03:34:15Z | fix: quote ISO 9660 shell case pattern in artifact verification |
| [aaf567f3](https://github.com/CmdOS-system/Nexus-os/commit/aaf567f30c39a57a38c11b20fbce0521fb7b7859) | 2026-10-14T03:22:56Z | fix: reconstruct image validator and self-check shell syntax |
| [537d4f47](https://github.com/CmdOS-system/Nexus-os/commit/537d4f47ddaaf3b099eb7647cfeed855924e4f24) | 2026-10-14T03:20:39Z | test: reject duplicate boot readiness wants entry during preflight |
| [c2a96e76](https://github.com/CmdOS-system/Nexus-os/commit/c2a96e76cc4305e7337a90e808648a91e6830169) | 2026-10-14T03:20:36Z | fix: remove duplicate systemd wants file; let live hook create symlink |
| [5f6e674b](https://github.com/CmdOS-system/Nexus-os/commit/5f6e674bfb9255f1c0c86ca94095dd0a28690cae) | 2026-10-14T03:15:41Z | ci: build Debian Trixie ISO using matching Debian live-build in container |
| [d636b25f](https://github.com/CmdOS-system/Nexus-os/commit/d636b25f4d4b7eb707d7d3417525207b7f5e78c6) | 2026-10-14T03:13:28Z | build: install executable readiness hook in live-build live stage |
| [ba8cac6b](https://github.com/CmdOS-system/Nexus-os/commit/ba8cac6b1b899c8466a98397ce6e2f80263ea11c) | 2026-10-14T03:13:25Z | fix: repair truncated and duplicated image validation script |
| [bb95e3ed](https://github.com/CmdOS-system/Nexus-os/commit/bb95e3ed743a646734f2308680e8354685bf6251) | 2026-10-14T03:13:18Z | fix: replace literal backslash-n with actual newline in system test |
| [5fd73de0](https://github.com/CmdOS-system/Nexus-os/commit/5fd73de0209474524f4bc5e3dd30154e4acc99c4) | 2026-10-14T03:12:10Z | test: syntax-check agent tests before unit discovery |
| [bdcd12a4](https://github.com/CmdOS-system/Nexus-os/commit/bdcd12a4a5e3095da19127afb274216b7d3db295) | 2026-10-14T03:12:08Z | test: fix corrupted system tool broker test syntax |
| [02c16357](https://github.com/CmdOS-system/Nexus-os/commit/02c16357e7fc85c91b223d4953eca4d4f5e6170e) | 2026-10-14T03:10:52Z | ci: verify candidate checksum before boot smoke |
| [331f3955](https://github.com/CmdOS-system/Nexus-os/commit/331f39559d8eb54e1fc1018566dc28724f4401e6) | 2026-10-14T03:10:15Z | ci: add reproducible ISO build and UEFI boot gate |
| [d9c14dc5](https://github.com/CmdOS-system/Nexus-os/commit/d9c14dc570bcd6c5251c2852222ee8bb32e56f5a) | 2026-10-14T03:09:50Z | docs: define exact Nexus guest boot readiness gate |
| [d652996b](https://github.com/CmdOS-system/Nexus-os/commit/d652996b8f53d248fb8a2fdaf40f180f515b5d63) | 2026-10-14T03:09:27Z | test: reject systemd readiness ordering cycles |
| [4c737728](https://github.com/CmdOS-system/Nexus-os/commit/4c737728313309ff9b0a59e6a2a876d2a84db86f) | 2026-10-14T03:09:19Z | boot: remove multi-user ordering cycle from readiness service |
| [47e34dce](https://github.com/CmdOS-system/Nexus-os/commit/47e34dceee02163513976e949ae6c0a2f0799286) | 2026-10-14T03:08:48Z | build: include BYOAI catalog and diagnostics runtime |
| [3af9a4c9](https://github.com/CmdOS-system/Nexus-os/commit/3af9a4c96a61183a9170f5e152f97a7571acf5e9) | 2026-10-14T03:08:46Z | build: include BYOAI catalog and diagnostics runtime |
| [5e5ef32a](https://github.com/CmdOS-system/Nexus-os/commit/5e5ef32aacc8d9b0d2f53b5d621f840131cb590e) | 2026-10-14T03:08:44Z | test: verify provider diagnostics do not leak secrets |
| [e1a89f48](https://github.com/CmdOS-system/Nexus-os/commit/e1a89f48c5db5be40383829eccd4e0b4c35c4310) | 2026-10-14T03:08:38Z | feat: add secret-safe provider connectivity diagnostic |
| [f593d9db](https://github.com/CmdOS-system/Nexus-os/commit/f593d9db283e26a233d2e6971bdadcf122675e6c) | 2026-10-14T03:08:36Z | feat: add credential-free BYOAI provider catalog |
| [c3707d52](https://github.com/CmdOS-system/Nexus-os/commit/c3707d529db8cba679fc08df033e1c3aec6eaa63) | 2026-10-14T03:08:06Z | desktop: require existing or newly supplied cloud credential |
| [5d108992](https://github.com/CmdOS-system/Nexus-os/commit/5d108992c9b85a56d0fa5715cc179b6142e95e1a) | 2026-10-14T03:08:04Z | feat: add keyring presence check for BYOAI setup |
| [1587e6d3](https://github.com/CmdOS-system/Nexus-os/commit/1587e6d3848520401503c665ad455b5d3c3795f5) | 2026-10-14T03:07:56Z | desktop: store BYOAI API keys in Linux keyring from Control Center |
| [a19c793c](https://github.com/CmdOS-system/Nexus-os/commit/a19c793c203824ff15954dcbf3624ea3d6fffe06) | 2026-10-14T03:07:50Z | security: canonicalize BYOAI keyring references per provider |
| [1875d376](https://github.com/CmdOS-system/Nexus-os/commit/1875d376a63815131b60fc0a94f4222364e4b9c9) | 2026-10-14T03:07:14Z | test: require libsecret-tools in Nexus image |
| [a314315c](https://github.com/CmdOS-system/Nexus-os/commit/a314315c3190b58933a0e52d95369482ca4b2f78) | 2026-10-14T03:07:11Z | build: ship libsecret Secret Service CLI for BYOAI keyring |
| [762b6b42](https://github.com/CmdOS-system/Nexus-os/commit/762b6b42bc20eeabda9ea5073aad4a9dc12070b4) | 2026-10-14T03:07:07Z | build: include Linux Secret Service adapter |
| [eefb7e02](https://github.com/CmdOS-system/Nexus-os/commit/eefb7e0244954b110e3bb2a51705e83b3c25326f) | 2026-10-14T03:07:05Z | build: include Linux Secret Service adapter |
| [029600cd](https://github.com/CmdOS-system/Nexus-os/commit/029600cdacc2773a0030a7c69b2d4562ad09924c) | 2026-10-14T03:07:02Z | test: cover Secret Service credential isolation and failure modes |
| [7f4f47d2](https://github.com/CmdOS-system/Nexus-os/commit/7f4f47d2a026a3ba37f73e498a79357062e37036) | 2026-10-14T03:06:56Z | feat: add fail-closed Linux Secret Service keyring adapter |
| [893ab84e](https://github.com/CmdOS-system/Nexus-os/commit/893ab84e126e432f217b5fd2a80ede5cc0c19f03) | 2026-10-14T03:06:27Z | test: scope legacy API security scan to Python sources |
| [a853d8ce](https://github.com/CmdOS-system/Nexus-os/commit/a853d8ce38af4c4b8754b848c7c5da5d1038ea09) | 2026-10-14T03:06:21Z | desktop: connect Control Center to validated shared AI settings |
| [5358af23](https://github.com/CmdOS-system/Nexus-os/commit/5358af2388e3a0f4b3be59614c7f0f8f87eeca81) | 2026-10-14T03:05:49Z | build: include shared AI settings persistence runtime |
| [83ccf770](https://github.com/CmdOS-system/Nexus-os/commit/83ccf7704fe9ba0ad25062ec0e1694893733a3ac) | 2026-10-14T03:05:46Z | build: include shared AI settings persistence runtime |
| [d411d6aa](https://github.com/CmdOS-system/Nexus-os/commit/d411d6aae83c675efde10877754a3aa59eb2213c) | 2026-10-14T03:05:43Z | test: cover private atomic AI settings persistence |
| [7dcb206e](https://github.com/CmdOS-system/Nexus-os/commit/7dcb206e5d85bdfb42ff7fac46fd54dc2858ae04) | 2026-10-14T03:05:37Z | feat: add atomic private persistence for Nexus AI settings |
| [1cef2e61](https://github.com/CmdOS-system/Nexus-os/commit/1cef2e61515e36b009262b52f4a3ffe024e7a7d1) | 2026-10-14T03:05:28Z | fix: replace corrupted image validator with clean fail-closed version |
| [825f0bcf](https://github.com/CmdOS-system/Nexus-os/commit/825f0bcf8a0d215a6a107a778c3aa79d80a86a79) | 2026-10-14T03:04:49Z | test: validate Nexus Control Center image sources |
| [dd38ab67](https://github.com/CmdOS-system/Nexus-os/commit/dd38ab675a16abf9539c0a350418c74b6bad9f7b) | 2026-10-14T03:04:46Z | desktop: include Tk runtime for Control Center prototype |
| [4498725a](https://github.com/CmdOS-system/Nexus-os/commit/4498725a746e5e63080fa6eb105f90a10f5bd40f) | 2026-10-14T03:04:40Z | desktop: add initial Nexus Control Center AI settings UI |
| [d2782fd5](https://github.com/CmdOS-system/Nexus-os/commit/d2782fd5d31c08b4a94205c8244eae0603156e0e) | 2026-10-14T03:04:38Z | desktop: add initial Nexus Control Center AI settings UI |
| [2f630c2d](https://github.com/CmdOS-system/Nexus-os/commit/2f630c2d500a1ee93ec06b6aa0dde5f0771d19e8) | 2026-10-14T03:04:26Z | test: validate boot readiness service activation sources |
| [64682375](https://github.com/CmdOS-system/Nexus-os/commit/64682375756c379569152a487ede93c4189cfcfb) | 2026-10-14T03:04:24Z | build: stage systemd enable hook for live image |
| [7597185a](https://github.com/CmdOS-system/Nexus-os/commit/7597185a164ea270fb56860ed68f9839bc0c3d94) | 2026-10-14T03:04:21Z | build: enable Nexus boot readiness service in chroot |
| [070ddf6c](https://github.com/CmdOS-system/Nexus-os/commit/070ddf6c2afa61c05bdd2406ec8bd45218c8c886) | 2026-10-14T03:03:47Z | test: require guest-emitted marker to pass QEMU smoke test |
| [7fa3a9b1](https://github.com/CmdOS-system/Nexus-os/commit/7fa3a9b151ee504731a9bb2cb1dfebfd19676b4f) | 2026-10-14T03:03:45Z | boot: execute readiness marker via shell independent of file mode |
| [f8765e2e](https://github.com/CmdOS-system/Nexus-os/commit/f8765e2e37d08714d169667143391972df490089) | 2026-10-14T03:03:42Z | boot: execute readiness marker via shell independent of file mode |
| [8cba9b26](https://github.com/CmdOS-system/Nexus-os/commit/8cba9b26d08de8b364b4dd4fee86f3116e991b89) | 2026-10-14T03:03:36Z | boot: add live guest readiness marker service |
| [bdcda0f2](https://github.com/CmdOS-system/Nexus-os/commit/bdcda0f23985dc507c2a2a9291250cd0d9c0d370) | 2026-10-14T03:03:34Z | boot: add live guest readiness marker service |
| [2e51e169](https://github.com/CmdOS-system/Nexus-os/commit/2e51e16999ba1b121663141ff2385574ce6ebf43) | 2026-10-14T03:03:32Z | boot: add live guest readiness marker service |
| [ffaf56bf](https://github.com/CmdOS-system/Nexus-os/commit/ffaf56bf840bd1edaaa0eda326c554137bc3ca39) | 2026-10-14T03:03:06Z | test: harden preflight with dependency and legacy API gates |
| [bb63363f](https://github.com/CmdOS-system/Nexus-os/commit/bb63363fd8cca652e7cea7d09eda95addc1b9c28) | 2026-10-14T03:02:11Z | test: add single Nexus preflight verification command |
| [0974c5f1](https://github.com/CmdOS-system/Nexus-os/commit/0974c5f1d2358559b8238497faafa95fc5a7f4fe) | 2026-10-14T03:02:07Z | build: package secret_store without stdlib namespace collision |
| [40249d2a](https://github.com/CmdOS-system/Nexus-os/commit/40249d2a90ab55508592617681c550eaf1acdacc) | 2026-10-14T03:02:05Z | build: package secret_store without stdlib namespace collision |
| [b48983ca](https://github.com/CmdOS-system/Nexus-os/commit/b48983caa0becc73ad819cae4d90770bb38296d5) | 2026-10-14T03:01:58Z | refactor: use unambiguous secret_store module |
| [68091b94](https://github.com/CmdOS-system/Nexus-os/commit/68091b94a8f2d8a5893aeb2d8f40cdd738f1683f) | 2026-10-14T03:01:54Z | refactor: use unambiguous secret_store module |
| [c15ceefa](https://github.com/CmdOS-system/Nexus-os/commit/c15ceefa88af4ce5ef0c526fd552826113383b2f) | 2026-10-14T03:01:52Z | refactor: use unambiguous secret_store module |
| [f0fd7a80](https://github.com/CmdOS-system/Nexus-os/commit/f0fd7a80f538ce87cd5fcbb513478f7213846d44) | 2026-10-14T03:01:48Z | refactor: move Nexus SecretStore away from stdlib secrets namespace |
| [9d7fc508](https://github.com/CmdOS-system/Nexus-os/commit/9d7fc508e196ab384ee978f0fd1c533bee8d17f1) | 2026-10-14T03:01:22Z | test: migrate system tool regression to permission broker |
| [8d7088fc](https://github.com/CmdOS-system/Nexus-os/commit/8d7088fc0353f2bce5b8d846f37e674a473af2e5) | 2026-10-14T03:01:20Z | fix: avoid stdlib secrets shadowing in authorization tokens |
| [c9b665af](https://github.com/CmdOS-system/Nexus-os/commit/c9b665af7e96248a9735af0f8f8a7f788bc1edd8) | 2026-10-14T03:01:17Z | fix: avoid stdlib secrets shadowing in authorization tokens |
| [de38cdde](https://github.com/CmdOS-system/Nexus-os/commit/de38cdde69bd4b07815504437f7f6f80e547b589) | 2026-10-14T03:00:18Z | build: include PermissionBroker in Nexus image runtime |
| [acdd5f0b](https://github.com/CmdOS-system/Nexus-os/commit/acdd5f0b7d0f12b9788e25a4625863d284dfe25c) | 2026-10-14T03:00:16Z | build: include PermissionBroker in Nexus image runtime |
| [284a063a](https://github.com/CmdOS-system/Nexus-os/commit/284a063a3df75b60a63a7868b6d95e8670f0b3ac) | 2026-10-14T03:00:11Z | test: migrate agent tools to bound permission flow |
| [c8000abd](https://github.com/CmdOS-system/Nexus-os/commit/c8000abd3d92e3016e44bc58036fff5b0de3a47e) | 2026-10-14T03:00:08Z | test: migrate agent tools to bound permission flow |
| [c70eada6](https://github.com/CmdOS-system/Nexus-os/commit/c70eada6b788c05bf9f46e7d94c06bb3d0a491d8) | 2026-10-14T03:00:06Z | test: migrate agent tools to bound permission flow |
| [a613625c](https://github.com/CmdOS-system/Nexus-os/commit/a613625cdc270ba36ef21c669239aefe48c01e81) | 2026-10-14T02:59:07Z | security: require bound PermissionBroker approval for tool execution |
| [01525783](https://github.com/CmdOS-system/Nexus-os/commit/01525783af4955d2d9372d5ccc86be596a06949e) | 2026-10-14T02:57:49Z | fix: bind one-shot permissions to normalized arguments |
| [a1abff6a](https://github.com/CmdOS-system/Nexus-os/commit/a1abff6ac7d07aa0ab2337a603b05fd94faad2c6) | 2026-10-14T02:57:22Z | fix: bind permission decisions to exact tool |
| [36f31c20](https://github.com/CmdOS-system/Nexus-os/commit/36f31c20c646e5608b34ea05744802df498dd9c0) | 2026-10-14T02:57:16Z | feat: add one-shot user permission broker prototype |
| [d9e07b08](https://github.com/CmdOS-system/Nexus-os/commit/d9e07b08a914aeaff4b97e63194290e51892465b) | 2026-10-14T02:57:15Z | feat: add one-shot user permission broker prototype |
| [a8917551](https://github.com/CmdOS-system/Nexus-os/commit/a89175510084fbabe3fee43420d0d916a35d74e1) | 2026-10-14T02:57:13Z | feat: add one-shot user permission broker prototype |
| [0dff4f72](https://github.com/CmdOS-system/Nexus-os/commit/0dff4f72692520310082a3ff76644b2c94a72357) | 2026-10-14T02:56:30Z | test: enforce token-only file reads through broker |
| [af5148b9](https://github.com/CmdOS-system/Nexus-os/commit/af5148b96c835fc39b0ead691bb2c68eadca7332) | 2026-10-14T02:56:25Z | feat: expose one-shot file grants through Tool Broker |
| [7fa8720a](https://github.com/CmdOS-system/Nexus-os/commit/7fa8720aac053583f7d27fb727385190b6c03943) | 2026-10-14T02:55:45Z | build: embed and validate R1 file grants |
| [a8b7d1b2](https://github.com/CmdOS-system/Nexus-os/commit/a8b7d1b22aa6e59b7e18755c49803b6809028c34) | 2026-10-14T02:55:42Z | build: embed and validate R1 file grants |
| [e3c49ffb](https://github.com/CmdOS-system/Nexus-os/commit/e3c49ffbf9c7fd78af22dbc821a1c9c919c50369) | 2026-10-14T02:55:38Z | feat: add one-shot R1 user file grants |
| [0b3f7ecb](https://github.com/CmdOS-system/Nexus-os/commit/0b3f7ecbb59c304569b1220d3a92f8ed919ad05c) | 2026-10-14T02:55:36Z | feat: add one-shot R1 user file grants |
| [29398f6e](https://github.com/CmdOS-system/Nexus-os/commit/29398f6e52ee58db0d41f3fec9b9ed818c751b83) | 2026-10-14T02:55:34Z | feat: add one-shot R1 user file grants |
| [caab3a52](https://github.com/CmdOS-system/Nexus-os/commit/caab3a522b64dfb703b3aba1d31b9d339a067495) | 2026-10-14T02:55:15Z | build: embed and validate fixed-source Nexus system tools |
| [2f5a7ff9](https://github.com/CmdOS-system/Nexus-os/commit/2f5a7ff9d17b93e20cd1b0c94c104662a4d172b2) | 2026-10-14T02:55:12Z | build: embed and validate fixed-source Nexus system tools |
| [97a45e52](https://github.com/CmdOS-system/Nexus-os/commit/97a45e52aaead93211d4e31b685c86f47d7961b5) | 2026-10-14T02:55:09Z | feat: add fixed-source R0 system identity tool |
| [4cd2d231](https://github.com/CmdOS-system/Nexus-os/commit/4cd2d23160fddf720d7c7bc315acdb5eae675549) | 2026-10-14T02:55:07Z | feat: add fixed-source R0 system identity tool |
| [a4feca27](https://github.com/CmdOS-system/Nexus-os/commit/a4feca271c5ed5e6d9e910f63d0266e2405402b7) | 2026-10-14T02:55:05Z | feat: add fixed-source R0 system identity tool |
| [e4f652f3](https://github.com/CmdOS-system/Nexus-os/commit/e4f652f3fbb2f70bf48ed4b0d0f158626ce35042) | 2026-10-14T02:54:29Z | build: embed and validate Nexus Tool Broker |
| [80579507](https://github.com/CmdOS-system/Nexus-os/commit/80579507ee479f5f160cd913ccb6c719f6a0d1a3) | 2026-10-14T02:54:26Z | build: embed and validate Nexus Tool Broker |
| [278941a6](https://github.com/CmdOS-system/Nexus-os/commit/278941a611b24dd68757f58f2c009b0f03e703a7) | 2026-10-14T02:54:23Z | feat: add fail-closed Nexus Agent tool broker |
| [c16edf6d](https://github.com/CmdOS-system/Nexus-os/commit/c16edf6d3d0c6377e64148ebc89bc52f334d0944) | 2026-10-14T02:54:21Z | feat: add fail-closed Nexus Agent tool broker |
| [f3d6897f](https://github.com/CmdOS-system/Nexus-os/commit/f3d6897fdae1c3b4b35df1f9ca9e43a6747b65b5) | 2026-10-14T02:54:19Z | feat: add fail-closed Nexus Agent tool broker |
| [f9082ece](https://github.com/CmdOS-system/Nexus-os/commit/f9082eceb4262edacbd9a146b8a58ca99f462ede) | 2026-10-14T02:53:48Z | test: add privacy regression cases for AI routing modes |
| [68173851](https://github.com/CmdOS-system/Nexus-os/commit/681738516b56d7bfae2917b4d2991776fe870c35) | 2026-10-14T02:53:43Z | feat: enforce AI settings policy in provider routing |
| [2078beca](https://github.com/CmdOS-system/Nexus-os/commit/2078beca87e81947900e950cd6683f067ac7d6b6) | 2026-10-14T02:53:25Z | build: embed and validate Nexus AI settings module |
| [f3dac1a9](https://github.com/CmdOS-system/Nexus-os/commit/f3dac1a96685c9c9bbf712ce5f046a8defccba31) | 2026-10-14T02:53:23Z | build: embed and validate Nexus AI settings module |
| [32539689](https://github.com/CmdOS-system/Nexus-os/commit/325396894139ee49ca8c63509b96147726b26799) | 2026-10-14T02:53:19Z | feat: add secret-free Nexus AI settings policy |
| [ceb9d553](https://github.com/CmdOS-system/Nexus-os/commit/ceb9d55330e8c52591f0ad730a110b617f375ead) | 2026-10-14T02:53:16Z | feat: add secret-free Nexus AI settings policy |
| [f34e2be9](https://github.com/CmdOS-system/Nexus-os/commit/f34e2be97557aeb786df87970c6b68eded72b951) | 2026-10-14T02:53:13Z | feat: add secret-free Nexus AI settings policy |
| [9bdfef08](https://github.com/CmdOS-system/Nexus-os/commit/9bdfef08300b38d0f60b0e20e502b1bbf4a10bb3) | 2026-10-14T02:52:47Z | build: include compatible cloud provider module in image and checks |
| [1a548227](https://github.com/CmdOS-system/Nexus-os/commit/1a54822767794185e7c5c8036c862df540fbe875) | 2026-10-14T02:52:45Z | build: include compatible cloud provider module in image and checks |
| [3b995826](https://github.com/CmdOS-system/Nexus-os/commit/3b995826958c8bbba1472c91c7deb288ab8725a4) | 2026-10-14T02:52:41Z | feat: introduce explicit HTTPS BYOAI compatible chat adapter |
| [d765513b](https://github.com/CmdOS-system/Nexus-os/commit/d765513bc6672c6e5ae4c2b32ea657d5f425edf8) | 2026-10-14T02:52:39Z | feat: introduce explicit HTTPS BYOAI compatible chat adapter |
| [95fc7869](https://github.com/CmdOS-system/Nexus-os/commit/95fc7869c06ac5eb326796e8cb68a013e965cd73) | 2026-10-14T02:52:37Z | feat: introduce explicit HTTPS BYOAI compatible chat adapter |
| [070318c3](https://github.com/CmdOS-system/Nexus-os/commit/070318c37efe09076923d508657e1bdd9e7acba4) | 2026-10-14T02:52:12Z | docs: record Debian Live, QEMU and sandbox research decisions |
| [51db3f50](https://github.com/CmdOS-system/Nexus-os/commit/51db3f50e940f46581759fcedf9ce56648ec9a5d) | 2026-10-14T02:52:06Z | build: add prepare-only staging gate and protect work directory |
| [582db791](https://github.com/CmdOS-system/Nexus-os/commit/582db7913247b5d557561a2f66efaf3d5ec7164b) | 2026-10-14T02:50:14Z | test: validate embedded agent and Nexus desktop identity |
| [09309100](https://github.com/CmdOS-system/Nexus-os/commit/0930910002d00290524ee186bf8f5feaf0822fca) | 2026-10-14T02:49:19Z | fix: repair live build setup and embed Nexus Agent runtime |
| [bc221838](https://github.com/CmdOS-system/Nexus-os/commit/bc22183845802ccaa99fdb30e8caa50d84681ce2) | 2026-10-14T02:48:48Z | feat: add safe desktop entry and launcher for Nexus Agent |
| [7f62d402](https://github.com/CmdOS-system/Nexus-os/commit/7f62d40267e8e653e33c385be24967cbe8cf1e93) | 2026-10-14T02:48:46Z | feat: add safe desktop entry and launcher for Nexus Agent |
| [a373f764](https://github.com/CmdOS-system/Nexus-os/commit/a373f7643bb2a0e1b531814adafccd2cfc937632) | 2026-10-14T02:48:44Z | feat: add safe desktop entry and launcher for Nexus Agent |
| [6e2bb730](https://github.com/CmdOS-system/Nexus-os/commit/6e2bb73021a9124c67486abea03ab4d53a635e98) | 2026-10-14T02:48:02Z | feat: include Nexus OS identity files in live image |
| [076c3922](https://github.com/CmdOS-system/Nexus-os/commit/076c39221e0b3de1094de239ccee2a213a37339b) | 2026-10-14T02:47:58Z | feat: add transparent Nexus OS development identity |
| [451aedc2](https://github.com/CmdOS-system/Nexus-os/commit/451aedc298f579abf6b88e5d9e3a762f53d44ef6) | 2026-10-14T02:47:55Z | feat: add transparent Nexus OS development identity |
| [b3c9ebf9](https://github.com/CmdOS-system/Nexus-os/commit/b3c9ebf9ce9b2fa413601159c195b7900e4ae691) | 2026-10-14T02:47:53Z | feat: add transparent Nexus OS development identity |
| [0708a3d5](https://github.com/CmdOS-system/Nexus-os/commit/0708a3d557ed13a2c8c14fcd2b9260025d396a79) | 2026-10-14T02:47:51Z | feat: add transparent Nexus OS development identity |
| [99eaa356](https://github.com/CmdOS-system/Nexus-os/commit/99eaa3563acd5184f31e17023cec242b091c216b) | 2026-10-14T02:47:35Z | test: add non-destructive QEMU UEFI boot smoke harness |
| [511ea284](https://github.com/CmdOS-system/Nexus-os/commit/511ea28403445eb84eebc0c9d13fb053e73be636) | 2026-10-14T02:47:33Z | test: add non-destructive QEMU UEFI boot smoke harness |
| [ddf7a03f](https://github.com/CmdOS-system/Nexus-os/commit/ddf7a03f37a4657ebf72c873e0242883aa45ab71) | 2026-10-14T02:46:31Z | test: add post-build ISO artifact verification gate |
| [add619ac](https://github.com/CmdOS-system/Nexus-os/commit/add619acde355c3016eed05cf45a67ef9dc56072) | 2026-10-14T02:46:29Z | test: add post-build ISO artifact verification gate |
| [0fe08b42](https://github.com/CmdOS-system/Nexus-os/commit/0fe08b422db0957478c0bb5216b5042b6b32a0e7) | 2026-10-14T02:45:19Z | test: strengthen image source and installer safety checks |
| [b0fa4ac8](https://github.com/CmdOS-system/Nexus-os/commit/b0fa4ac8f6788594d38e112b51162d81d8d0eee3) | 2026-10-14T02:44:40Z | docs: define installer safety and distribution release gates |
| [9d9f9ddb](https://github.com/CmdOS-system/Nexus-os/commit/9d9f9ddbf16072147a3f1306072c3582b4525721) | 2026-10-14T02:44:37Z | docs: define installer safety and distribution release gates |
| [fc98fd99](https://github.com/CmdOS-system/Nexus-os/commit/fc98fd99873faf9ea673ebcc451b41f2d35fd1d5) | 2026-10-14T02:43:12Z | feat: add secret-store abstraction and nonpersistent test backend |
| [8f3cc988](https://github.com/CmdOS-system/Nexus-os/commit/8f3cc98811e91b42a1a85c3821d1ddb3edd827e1) | 2026-10-14T02:43:10Z | feat: add secret-store abstraction and nonpersistent test backend |
| [5ec735f2](https://github.com/CmdOS-system/Nexus-os/commit/5ec735f240f96998aea87f8982091113647f0213) | 2026-10-14T02:43:08Z | feat: add secret-store abstraction and nonpersistent test backend |
| [d4b6686a](https://github.com/CmdOS-system/Nexus-os/commit/d4b6686ad7ec8376c0f158a0328188b9911071f7) | 2026-10-14T02:42:25Z | feat: add safe BYOAI configuration and secret-reference boundary |
| [04ef1bbb](https://github.com/CmdOS-system/Nexus-os/commit/04ef1bbbc57e6f3cf9af2a750c005981a8067b10) | 2026-10-14T02:42:23Z | feat: add safe BYOAI configuration and secret-reference boundary |
| [191ca4b2](https://github.com/CmdOS-system/Nexus-os/commit/191ca4b2971c7df6cf22fc53e0e132ff96460da8) | 2026-10-14T02:42:21Z | feat: add safe BYOAI configuration and secret-reference boundary |
| [d514c418](https://github.com/CmdOS-system/Nexus-os/commit/d514c418c440d35bc83d75b0fbb9155dadda5466) | 2026-10-14T02:41:20Z | feat: add privacy-first AI provider router |
| [f37a5431](https://github.com/CmdOS-system/Nexus-os/commit/f37a5431fcd10767da75016ebfbd1b0684694655) | 2026-10-14T02:41:18Z | feat: add privacy-first AI provider router |
| [68e9d3fd](https://github.com/CmdOS-system/Nexus-os/commit/68e9d3fd68e413c5947bd4529843f50cc15019df) | 2026-10-14T02:40:53Z | feat: add AI capability model and safe routing policy |
| [1895cbef](https://github.com/CmdOS-system/Nexus-os/commit/1895cbefd89f6540facb81f12beaa027eb30c534) | 2026-10-14T02:40:51Z | feat: add AI capability model and safe routing policy |
| [fbc2420c](https://github.com/CmdOS-system/Nexus-os/commit/fbc2420ca0128fedc4e993d62051960e4eace1b6) | 2026-10-14T02:40:49Z | feat: add AI capability model and safe routing policy |
| [502f35d8](https://github.com/CmdOS-system/Nexus-os/commit/502f35d8a4cd5339cd697f4ab1743ef68ba035f4) | 2026-10-14T02:39:46Z | test: verify provider-independent session behavior |
| [766ba0a5](https://github.com/CmdOS-system/Nexus-os/commit/766ba0a50c6ec00fad9f403b2d9e331339d133a0) | 2026-10-14T02:39:39Z | refactor: decouple agent session from Ollama transport |
| [ac618f1e](https://github.com/CmdOS-system/Nexus-os/commit/ac618f1e9f080264d6804556b7d9d1b3c2bed5ac) | 2026-10-14T02:39:08Z | feat: add pluggable AI provider adapter contract and registry |
| [65a2b45a](https://github.com/CmdOS-system/Nexus-os/commit/65a2b45a10565cda727472d58244bec6db011bef) | 2026-10-14T02:39:06Z | feat: add pluggable AI provider adapter contract and registry |
| [7e4b90df](https://github.com/CmdOS-system/Nexus-os/commit/7e4b90dfbfbec25111c1d4a1defb4c76d05e38d8) | 2026-10-14T02:38:39Z | fix: use native role-separated history in agent sessions |
| [3c938c1e](https://github.com/CmdOS-system/Nexus-os/commit/3c938c1e13ed2b20fe805731d8630e2e299ae0e8) | 2026-10-14T02:36:07Z | feat: support native Ollama role-separated chat messages |
| [a1552309](https://github.com/CmdOS-system/Nexus-os/commit/a1552309cb213c4b5cb45965875833de356f74b8) | 2026-10-14T02:35:06Z | test: add local session history and failure isolation tests |
| [0da9a336](https://github.com/CmdOS-system/Nexus-os/commit/0da9a33686e0f52aab49a17c5519677ef4aab43d) | 2026-10-14T02:35:00Z | feat: connect in-memory conversation history to local chat session |
| [f444345d](https://github.com/CmdOS-system/Nexus-os/commit/f444345d54c69f02bf11447ccd04b2ee43544a93) | 2026-10-14T02:34:26Z | feat: add bounded in-memory conversation history with tests |
| [58e987c9](https://github.com/CmdOS-system/Nexus-os/commit/58e987c9656c201db92755eed2e44cc36e1d747f) | 2026-10-14T02:34:24Z | feat: add bounded in-memory conversation history with tests |
| [b69fd4af](https://github.com/CmdOS-system/Nexus-os/commit/b69fd4af5f9ee4cc531ca2d3627b332f20c2efbb) | 2026-10-14T02:33:10Z | feat: add interactive local-only agent CLI and tests |
| [bb22e98a](https://github.com/CmdOS-system/Nexus-os/commit/bb22e98a57a4dfc3e916ba0d0ff7397d31c79e5d) | 2026-10-14T02:33:08Z | feat: add interactive local-only agent CLI and tests |
| [0da99b25](https://github.com/CmdOS-system/Nexus-os/commit/0da99b25eec73eee7ed6ea06d45f48a6d8508067) | 2026-10-14T02:31:38Z | feat: prototype local Ollama chat adapter and mocked tests |
| [4efc161e](https://github.com/CmdOS-system/Nexus-os/commit/4efc161ef8a4502a15c17abec6bb09d691e5cd5d) | 2026-10-14T02:31:36Z | feat: prototype local Ollama chat adapter and mocked tests |
| [bf46a321](https://github.com/CmdOS-system/Nexus-os/commit/bf46a321192a163cd56e6cc54778c8d828e46317) | 2026-10-14T02:29:21Z | feat: add fail-closed Nexus Agent provider and permission prototype |
| [d93aa0d8](https://github.com/CmdOS-system/Nexus-os/commit/d93aa0d893f353420a02705fc4175c851840a351) | 2026-10-14T02:29:19Z | feat: add fail-closed Nexus Agent provider and permission prototype |
| [0d9c045a](https://github.com/CmdOS-system/Nexus-os/commit/0d9c045aeaebe2ad452d0a534461eed50516a9ba) | 2026-10-14T02:29:17Z | feat: add fail-closed Nexus Agent provider and permission prototype |
| [ca5e766e](https://github.com/CmdOS-system/Nexus-os/commit/ca5e766e40ac55e326a529412e7bce474ef9d145) | 2026-10-14T02:27:29Z | test: add source validation and VM verification plan |
| [038bd8ac](https://github.com/CmdOS-system/Nexus-os/commit/038bd8ace67af82fe7f7226c81f0e21f6f62790b) | 2026-10-14T02:27:26Z | test: add source validation and VM verification plan |
| [4bf369a2](https://github.com/CmdOS-system/Nexus-os/commit/4bf369a23459b492e13cc909d83fd732dcab8b61) | 2026-10-14T02:24:39Z | build: add experimental Debian live ISO pipeline |
| [cbb1a010](https://github.com/CmdOS-system/Nexus-os/commit/cbb1a010df80a5d6c79822a86a62ab08c85c88d8) | 2026-10-14T02:24:36Z | build: add experimental Debian live ISO pipeline |
| [5a3c52c9](https://github.com/CmdOS-system/Nexus-os/commit/5a3c52c9e7ec77ebd18d294d626eef5b7205f543) | 2026-10-14T02:21:47Z | docs: add Linux desktop and AI security research review |
| [a360f9d7](https://github.com/CmdOS-system/Nexus-os/commit/a360f9d76c616eabc68652c74e8b5a2d76401ccd) | 2026-10-14T02:20:24Z | docs: specify bring-your-own-AI Nexus Agent architecture |
| [7d38b5d9](https://github.com/CmdOS-system/Nexus-os/commit/7d38b5d9e34557ea99972e17928f0df64bb1c686) | 2026-10-14T02:15:28Z | docs: initialize Nexus OS engineering roadmap |
