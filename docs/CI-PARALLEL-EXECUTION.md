# Nexus OS — parallel engineering and CI execution

## Confirmed baseline (2026-10-15)
- Fast checks completed successfully: https://github.com/CmdOS-system/Nexus-os/actions/runs/38850148567
- Previous ISO gate completed successfully: https://github.com/CmdOS-system/Nexus-os/actions/runs/38849908938
- Later ISO run #38850140904 was still running at last inspection; #38851467523 was pending. Do not label them successful until verified.

## Execution lanes
1. **Fast CI (every relevant agent/image change):** Python 3.12 and 3.13 test matrix plus image static checks. These jobs run independently; no ISO compilation.
2. **ISO gate (image/ or ISO workflow change, or manual dispatch):** Debian Trixie image build, artifact integrity and QEMU UEFI boot smoke. Serialize ISO builds to avoid duplicate heavy work.
3. **Recovery gate:** run Recovery G2 checks independently.
4. **Visual prototype gate (future):** headless GUI launch and accessibility checks; never substitute concept art for actual GUI evidence.

## Parallel development model
- Use one branch or git worktree per bounded feature: agent, desktop, installer, recovery.
- Declare changed paths, expected tests and acceptance evidence for each pull request.
- Merge only after fast CI and security review; reserve full ISO verification for release candidates or image-affecting changes.
- Never let a passing Python test imply a passing installer or physical hardware boot.

## Concurrency policy
- Fast checks: cancel outdated runs on the same branch to save runner time.
- ISO: `cancel-in-progress: false` and `queue: max` to avoid losing builds. GitHub permits up to 100 pending runs per concurrency group; this is a maximum, **not a goal**. Avoid excessive pushes to the image tree.
- GitHub concurrency queue ordering is based on when jobs begin waiting, and may not match commit order. Always tie release evidence to the exact commit SHA.
- Matrix jobs are parallel subject to account runner availability. Set `max-parallel` only when there is a measured resource bottleneck.

## Efficiency measurements to add
Record per run: commit SHA, trigger, total elapsed time, queue wait, build duration, QEMU boot duration, tests executed, outcome and artifact SHA256. Track median and p95 duration and number of cancelled or redundant runs. Optimize after collecting a baseline, not on intuition.

## Security and reliability
- Pin third-party Actions by immutable commit SHA after review.
- Keep workflow permissions minimal (`contents: read` for CI).
- Avoid running privileged image builds on untrusted pull request code or exposing secrets to forks.
- Do not reuse privileged build caches across trust boundaries.
- Path-filtered workflows can remain Pending as required checks on PRs; configure required checks accordingly or use an always-running lightweight gate.
- Use workflow timeouts and artifact retention limits to bound cost.

## Official references
- GitHub concurrency: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- GitHub matrix parallelism: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations
- GitHub Actions limits: https://docs.github.com/en/actions/reference/limits
- GitHub workflow syntax and path filters: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Git worktree: https://git-scm.com/docs/git-worktree
