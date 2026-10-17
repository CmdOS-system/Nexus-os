# Horizon: visual foundation, 2026-10-16

## Recovered design intent

The conversation “Nexus Horizon” asked for an original identity informed by Apple/macOS, GNOME, Material and KDE: quiet dark surfaces, restrained ambient light, clear hierarchy, a floating dock, useful contextual AI, readable type, and precise finishes. The existing Live screenshot is the XFCE baseline, not delivery of that full vision. Earlier Chromium concepts and Xvfb component previews do not establish what the ISO displays.

## Implemented in this change

- Original 3840×2160 SVG aurora wallpaper, resolution-independent source without a branded stock background.
- Arc-Dark GTK/window defaults, Papirus-Dark icons, Inter typography and font antialiasing. The Debian package manifest includes the assets rather than relying on a developer workstation.
- One-time wallpaper initialization discovers XFCE's actual monitor properties instead of assuming a QEMU monitor name. Later logins preserve user wallpaper choices.
- Native Horizon launcher: shared surface palette, original line icons, two-column application cards, a separate search surface, visible keyboard focus, hover feedback, keyboard selection and vertical scrolling on small displays. No decorative animation or blur is claimed by this Tk implementation.
- Full HD component captures, plus regression coverage for reaching the last application in a small window and launching the focused card with Enter.

## Validation boundaries

Component captures are screenshots of running Tk windows in Xvfb. They must be labeled as such. Native desktop theme, wallpaper rendering, the fixed shortcut and the final composition require a rebuilt ISO and a new guest capture. The dock, translucent compositor surfaces, graphical Agent, screen-reader integration, light/high-contrast variants and complete HiDPI acceptance remain separate work. A bigger screenshot alone is not improved design or verified scaling.

## References reviewed

- https://developer.apple.com/design/human-interface-guidelines/materials — design reference; page content was not retrievable in the current tooling, so no new Apple guidance is claimed.
- https://developer.gnome.org/hig/guidelines/typography.html — readable hierarchy, restrained variants, system font and scaling.
- https://packages.debian.org/trixie/arc-theme
- https://packages.debian.org/trixie/papirus-icon-theme
- https://packages.debian.org/trixie/fonts-inter
