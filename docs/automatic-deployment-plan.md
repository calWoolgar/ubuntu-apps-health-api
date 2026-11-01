# Automatic deployment plan

**Goal:** A push to `main` in `calWoolgar/ubuntu-apps-health-api` automatically deploys the API to `ubuntu-apps` after container CI passes.

**Architecture:** Keep tests on GitHub-hosted Linux. Add a repository-specific Linux runner service on the private Apps VM. A dependent job runs only for this repository's `main` pushes, serializes deployments, and skips a commit if it is no longer the main branch head. No inbound SSH access or stored GitHub personal token is needed for deployments.

**Deployment contract:** Build the exact tested Git revision into a new release directory and image tag. Preserve the VM's shared `.env`. Only update `current` after Docker and HTTP health checks pass. If activation or HTTP verification fails, restore the previous image and leave `current` unchanged. Build failures leave the running release untouched.

## Tasks

- [x] Write and run deployment-script tests covering success, failed build, failed activation, failed HTTP health, missing configuration, and invalid revision input.
- [x] Implement the script and prove all tests pass against controlled Docker/HTTP substitutes.
- [x] Add the guarded deploy job after the existing real-container CI checks, and review the workflow and script.
- [x] Install and register the official checksum-verified runner as a service on `ubuntu-apps`; verify it is online and can access Docker.
- [x] Push to `main` and verify the workflow deploys that exact commit without a manual deployment command.
- [x] Verify the API across the LAN, record the runner/service operations, and confirm the Git working tree and remote agree.

## Verification

- All seven deployment-script tests passed on Ubuntu, including build failures and activation/HTTP rollback paths.
- Independent review found a pending-job replacement race; `queue: max` now preserves pending deployments while the main-head check skips stale commits.
- [Push-triggered integration run 41273066930](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/runs/41273066930) passed hosted container CI and the self-hosted deployment job.
- That run deployed exact source revision `7c943bae5cb863d1bf0f2c5b30e1b0fdd3a2ab64`, confirmed by both the running image tag and `current/.deploy-revision` on the VM.
- Docker reported `healthy`, and all three HTTP smoke checks passed from the workstation over the LAN after deployment.
