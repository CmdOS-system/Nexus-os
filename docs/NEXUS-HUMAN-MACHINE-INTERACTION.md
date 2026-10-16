# Nexus Flow — Human–machine interaction specification

**Status:** product/engineering specification; not implemented functionality.

## North star
Technology adapts to the person. Nexus should make tasks easier, understandable, reversible and satisfying without using dark patterns or addictive engagement loops.

## Five interaction promises
1. **Intent over commands:** natural language, search, keyboard and pointer reach the same capabilities.
2. **Explain before acting:** every consequential operation has a human-readable preview and affected-resource summary.
3. **Progress without mystery:** show step, remaining work when measurable, ability to pause/cancel, and a clear success/failure result.
4. **Learn only with permission:** preferences remain local by default; cloud use and retention are explicit, revocable choices.
5. **Never trap the user:** no manipulative streaks, nagging, hidden settings, forced AI, or nonessential notifications.

## Nexus Flow interaction states
- **Idle:** unobtrusive launcher; no background microphone access.
- **Listening / typing:** visible input and microphone indicator; explicit activation.
- **Understanding:** paraphrase user goal when ambiguity or risk is high.
- **Planning:** concise list of actions, expected outputs, risks and requested permissions.
- **Awaiting consent:** explicit approval for file changes, purchases, account actions, terminal commands, software installation or destructive changes.
- **Executing:** step-by-step activity feed, stop button, tool provenance and failure feedback.
- **Review:** result preview, undo where supported, links to affected files.

## Permission tiers
- **Tier 0 — read-only:** search local apps, answer general questions, view allowed settings.
- **Tier 1 — reversible local:** create draft, rearrange windows, edit explicitly selected files with undo or versioned backup.
- **Tier 2 — consequential:** install software, change system settings, delete files, send messages, cloud upload; request specific, time-limited consent.
- **Tier 3 — destructive/privileged:** partition disks, alter boot, erase data. Nexus Agent must never silently authorize these actions. A separate, audited, privileged workflow with independent human confirmation is required.

## Example: 'Prepare a presentation from my vacation photos'
1. Ask for folder access via native file picker; do not crawl private folders.
2. Preview detected photos, estimated slides and suggested structure.
3. Let the user choose theme, output folder and whether cloud AI is allowed.
4. Generate draft locally where feasible; show progress and cancellation.
5. Display final preview, allow edits, save a copy, preserve originals.

## Accessibility and ease-of-use acceptance gates
- Every workflow must work without voice, and all critical actions must be keyboard accessible.
- UI must explain errors in plain language and suggest recovery actions.
- A first-time user should complete three representative tasks without reading a manual (usability study target, not measured yet).
- Display visible permission history and an obvious revocation path.
- Support reduced motion, high contrast, large text and screen-reader labels.
- Measure task completion rate, median steps, time-to-first-result, error recovery and subjective usability. Do not optimize time spent in the app.

## Implementation roadmap
1. Add structured intent representation and read-only action previews to the existing agent broker.
2. Introduce an explicit permission decision boundary, with tests that deny absent or expired grants.
3. Create a shared progress/cancellation event schema for UI and CLI.
4. Prototype Horizon Search and an accessible activity panel in the Live desktop.
5. Run moderated usability tests on 3–5 representative tasks before expanding scope.

## Sources to study
- GNOME Human Interface Guidelines: https://developer.gnome.org/hig/
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- W3C WAI-ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
- Nielsen Norman Group usability heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
