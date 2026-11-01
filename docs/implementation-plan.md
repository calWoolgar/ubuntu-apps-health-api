# Ubuntu Apps Health API

**Goal:** Build a small ASP.NET Core Web API, containerize it, deploy it to the user's Ubuntu Apps VM, and push the source to their personal GitHub.

**Architecture:** A .NET 10 Minimal API uses ASP.NET Core's built-in health checks at `GET /health`. A root endpoint identifies the service. Docker Compose runs one non-root container with a health probe and restart policy. Deployment uses SSH and builds on the target VM if appropriate for its existing setup.

**Repository:** Public `calWoolgar/ubuntu-apps-health-api`, as specified by the user.

**Defaults chosen:** HTTP port 8080 unless the VM already uses it; no database, authentication, or public DNS needed for this health-only service. Inspect the VM before changing it, and preserve its existing workloads.

## Tasks

- [x] API: write HTTP smoke assertions before implementing the routes, observe them fail with the routes absent, implement `GET /health` (200, `Healthy`, no caching) and `GET /` (service metadata), and verify success and unknown-route 404.
- [x] Container: create a multi-stage Dockerfile, Compose health probe, `.dockerignore`, and `.gitignore`. Build and smoke-test the real container, including its non-root user and Docker health status.
- [x] Deployment: inspect the confirmed Apps VM, choose a free port, transfer only source files, build and start a dedicated Compose project, and verify health on the VM and from this computer. Record the exact URL and repeatable update instructions.
- [x] GitHub: review source for credentials, commit the tested implementation, create the private personal repository if absent, push, and verify the remote commit and visibility.

## Review focus

- Missing health route or redirect: assert exact HTTP 200 and body in a real HTTP smoke check.
- Misconfigured container port/user: probe port 8080 and inspect the container's configured user.
- Startup failures: require Docker health status `healthy`, not merely container state `running`.
- Host conflicts: inspect occupied ports and Compose projects before deployment.
- Source leakage: keep credentials and local build artifacts outside the repository and transfer only tracked source.

## Progress

- Workspace initially empty; no existing Git checkout to isolate.
- GitHub CLI access is available; the user explicitly identified `calWoolgar` as the personal repository owner.
- System has .NET runtimes but no SDK. Installing an SDK under the task's `work/` directory.
- Apps VM confirmed as `devadmin@ubuntu-apps` on the LAN. Authenticated in a temporary interactive SSH session using the existing key.
- Release build passed with zero warnings/errors. The smoke checks failed with HTTP 404 before endpoint implementation, then all three passed after implementation.
- Compose configuration passed validation. Local Docker Desktop has an existing startup failure in its inference socket; container verification will use GitHub Actions and the Ubuntu VM instead of changing the workstation's Docker installation.
- Independent source review found no blocking defects. Updated deployment instructions to extract clean releases and preserve shared configuration, addressing its one documentation finding.
- VM preflight found port 8080 free and 29 GB disk space available. Installed Docker, Compose, and Buildx from Ubuntu's signed repositories, and enabled Docker startup.
- GitHub Actions run 41272052723 passed container health, all three HTTP smoke checks, and non-root runtime verification. The repository destination is `calWoolgar/ubuntu-apps-health-api`.
- Deployed runtime source revision `26bf6b0` in a clean release directory. Docker reports `healthy`, UID 1654, read-only root filesystem, and `unless-stopped`. Docker is enabled and active.
- All three HTTP smoke checks passed from the workstation against `http://192.168.1.87:8080`. Exact deployment paths and operations are recorded in `docs/deployment.md`.
