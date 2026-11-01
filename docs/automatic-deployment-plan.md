# Public automatic deployment and version reporting

**Goal:** Pushes to the public `calWoolgar/ubuntu-apps-health-api` repository deploy successful `main` revisions to `ubuntu-apps`; `/version` reports the exact compiled commit SHA.

**Architecture:** All CI runs on GitHub-hosted Linux. A VM systemd timer checks the public main branch every two minutes. The installed Python dispatcher requires a successful push CI run for the exact SHA, branch, workflow, and repository before executing that commit's deployment script. A file lock serializes deployment checks. The previous private-repository self-hosted runner is stopped and unregistered before changing visibility.

**Deployment contract:** Build the tested Git revision into a clean release and SHA-tagged image. Embed `COMMIT_SHA` in the compiled assembly and OCI image label. Preserve the VM's shared `.env`. Promote `current` only after Docker health, HTTP health, and the `/version` SHA all pass. Failed activation or verification attempts to restore the previous image; failed builds leave the running API untouched.

## Validation and rollout

- Verify the `/version` smoke check fails before endpoint implementation, then passes against a Release build stamped with a known SHA.
- Verify failed CI, PR/fork runs, other branches, different workflows, and wrong SHAs cannot pass the dispatcher's gate.
- Verify version mismatch rolls back alongside the existing deployment failure tests.
- Inspect all repository history for committed credentials before making it public.
- Install the dispatcher and units, allowing three minutes for shutdown so a 120-second rollback health wait can finish.
- Push the reviewed changes to main, remove the old runner, make the repository public, and enable the timer.
- Confirm hosted container CI passes and the timer deploys the pushed SHA; compare `/version`, release metadata, image label/tag, and GitHub main.

## Pre-rollout evidence

- Release build passed with zero warnings/errors; all four HTTP checks passed with the exact stamped SHA.
- All nine Ubuntu deployment and public-CI gate tests passed after observing the new mismatch/gate tests fail before implementation.
- All six existing Git commits and their tracked file lists were checked for private-key/access-token patterns; none were found.
