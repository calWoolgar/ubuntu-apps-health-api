# Ubuntu Apps Health API

**Goal:** Build a small ASP.NET Core Web API, containerize it, deploy it to the user's Ubuntu Apps VM, and push the source to their personal GitHub.

**Architecture:** A .NET 10 Minimal API uses ASP.NET Core's built-in health checks at `GET /health`. A root endpoint identifies the service. Docker Compose runs one non-root container with a health probe and restart policy. Deployment uses SSH and builds on the target VM if appropriate for its existing setup.

**Defaults chosen:** Private repository `woolgarmedia/ubuntu-apps-health-api`; HTTP port 8080 unless the VM already uses it; no database, authentication, or public DNS needed for this health-only service. Inspect the VM before changing it, and preserve its existing workloads.

## Tasks

- [x] API: write HTTP smoke assertions before implementing the routes, observe them fail with the routes absent, implement `GET /health` (200, `Healthy`, no caching) and `GET /` (service metadata), and verify success and unknown-route 404.
- [ ] Container: create a multi-stage Dockerfile, Compose health probe, `.dockerignore`, and `.gitignore`. Build and smoke-test the real container, including its non-root user and Docker health status.
- [ ] Deployment: inspect the confirmed Apps VM, choose a free port, transfer only source files, build and start a dedicated Compose project, and verify health on the VM and from this computer. Record the exact URL and repeatable update instructions.
- [ ] GitHub: review source for credentials, commit the tested implementation, create the private personal repository if absent, push, and verify the remote commit and visibility.

## Review focus

- Missing health route or redirect: assert exact HTTP 200 and body in a real HTTP smoke check.
- Misconfigured container port/user: probe port 8080 and inspect the container's configured user.
- Startup failures: require Docker health status `healthy`, not merely container state `running`.
- Host conflicts: inspect occupied ports and Compose projects before deployment.
- Source leakage: keep credentials and local build artifacts outside the repository and transfer only tracked source.

## Progress

- Workspace initially empty; no existing Git checkout to isolate.
- GitHub CLI authenticated as `woolgarmedia`; its initial network error was caused by sandbox networking.
- System has .NET runtimes but no SDK. Installing an SDK under the task's `work/` directory.
- Apps VM confirmed as `devadmin@ubuntu-apps` on the LAN. Its SSH server accepts the existing key; the passphrase-protected key must be loaded into the local SSH agent to sign authentication requests.
- Release build passed with zero warnings/errors. The smoke checks failed with HTTP 404 before endpoint implementation, then all three passed after implementation.
- Compose configuration passed validation. Local Docker Desktop has an existing startup failure in its inference socket; container verification will use GitHub Actions and the Ubuntu VM instead of changing the workstation's Docker installation.
