# Nexus Horizon — design direction (concept, not implemented)

## Mission
Nexus OS should feel like a coherent, approachable and fast operating system, not a reskinned XFCE or a copy of macOS/Windows. The visual direction is **Horizon**: quiet surfaces, restrained ambient light, strong hierarchy, and AI that appears only when useful.

## Design principles
1. **Clarity before spectacle:** a user should recognize the primary action in three seconds. Use progressive disclosure, predictable navigation and reversible actions.
2. **Material with purpose:** translucent overlays only for floating navigation and ephemeral controls; content remains opaque and readable.
3. **Motion explains:** animations show origin, destination, state change, and focus. Respect reduced-motion preferences and offer instant transitions.
4. **AI is permissioned:** Nexus Agent must explain intended actions, request explicit consent for consequential operations and display a persistent activity trail.
5. **Responsive by default:** design at 1024×600, 1366×768, 1920×1080, 4K fractional scaling and keyboard-only use.
6. **Performance is a design feature:** prioritize low latency, fast first paint and reduced GPU effects on modest hardware.
7. **Accessibility is foundational:** high contrast, readable labels, focus indicators, screen-reader names, large text and color-independent status.

## Visual language (provisional tokens)
- Background: midnight navy #0B1220
- Surface: deep slate #151F31
- Raised surface: #202D43
- Primary text: #F4F7FC
- Secondary text: #B9C5D8
- Accent: horizon cyan #57D6F7
- Secondary accent: aurora violet #9879F7
- Success: #65D6AB; warning: #FFC76A; danger: #FF808D
- Spacing: 4px base grid; 8/12/16/24/32px rhythm
- Corner radius: 12px controls, 18px cards, 22px dialogs
- Minimum comfortable pointer targets: 40–44px; keyboard focus always visible
- Motion target: 120–220ms for simple transitions; reduced-motion alternative

These are proposals, not validated contrast ratios or production tokens. Validate WCAG contrast for every state before shipping.

## Product experiences
- **Horizon Desktop:** clean wallpaper, uncluttered workspace, contextual status rather than permanent clutter.
- **Horizon Dock:** favorites, active windows, drag-and-drop, accessible labels, optional auto-hide.
- **Horizon Search:** one entry point for apps, files, settings and opt-in AI commands; local-first search.
- **Nexus Control Center:** device status, updates, security, network and AI permissions in consistent adaptive cards.
- **Nexus Agent:** optional overlay, transparent action previews, permission prompts, cancellation and audit trail.
- **Nexus Installer:** guided steps with explicit disk identity, no destructive action before independently verified installation gates.
- **Horizon Themes:** light/dark/high-contrast, reduced transparency, reduced motion, scalable typography.

## Engineering strategy
**Phase 0 — Stable foundation:** retain XFCE for validated Live ISO. Do not replace a working desktop before installer/boot/persistence tests pass.
**Phase 1 — Design system prototype:** implement reusable visual tokens and components in a non-destructive Control Center mock, test keyboard navigation and scaling.
**Phase 2 — Shell experiment:** compare KDE Plasma/Qt Quick and GTK4/Libadwaita plus a compositor, with actual performance, Wayland, accessibility and packaging measurements. Choose based on tests, not appearance alone.
**Phase 3 — Native integration:** build launcher, dock, settings and Agent surfaces with shared interaction semantics.
**Phase 4 — Visual polish:** optional blur and depth, animation curves, sound design, responsive layout and theme customization.

## Acceptance criteria
- Test at 1024×600, 1366×768, 1920×1080 and HiDPI.
- Full keyboard navigation, visible focus, readable screen-reader labels, high-contrast and large-text modes.
- Respect reduced-motion and reduced-transparency preferences.
- Confirm legible text and contrast in light and dark themes.
- Benchmark cold start, idle RAM, UI latency and frame pacing on low-end hardware and QEMU.
- No Agent action that modifies user files or system settings without an explicit permission boundary.

## Research references
- GNOME HIG principles: https://developer.gnome.org/hig/principles
- GNOME adaptive design: https://developer.gnome.org/hig/guidelines/adaptive.html
- GNOME accessibility: https://developer.gnome.org/hig/guidelines/accessibility.html
- Apple HIG materials: https://developer.apple.com/design/human-interface-guidelines/materials
- Google Material 3 Expressive research: https://design.google/library/expressive-material-design-google-research
- KDE Plasma Wayland for artists: https://userbase.kde.org/Kde_wayland_for_artists

**Status:** research-backed design proposal only. Not a claim that these visuals or capabilities already exist in the Nexus ISO.
