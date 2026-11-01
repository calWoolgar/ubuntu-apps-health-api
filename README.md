# Ubuntu Apps Health API

A small ASP.NET Core Web API on .NET 10, with no external NuGet dependencies.

| Request | Response |
| --- | --- |
| `GET /health` | HTTP 200, plain text `Healthy`; responses cannot be cached |
| `GET /` | HTTP 200, JSON identifying the service and health endpoint |
| Unknown route | HTTP 404 |

The health endpoint uses [ASP.NET Core health checks](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-10.0). It checks that the application can respond; no database or external dependencies are configured.

## Run with .NET

Install the .NET 10 SDK, then run:

```powershell
dotnet run --project src/HealthApi --urls http://localhost:8080
```

In another PowerShell terminal, run the HTTP smoke checks:

```powershell
./scripts/SmokeTest.ps1 -BaseUri http://localhost:8080
```

GitHub Actions runs the deployment-script tests, builds and starts the actual container, waits for Docker health to pass, runs these same HTTP checks, and verifies that the runtime user is non-root on every push and pull request.

## Run in Docker

Install Docker with the Compose plugin, then run:

```sh
docker compose up -d --build --wait --wait-timeout 120
curl --fail http://127.0.0.1:8080/health
docker compose ps
```

The API binds to the host's loopback address by default. To allow LAN access, copy `.env.example` to `.env` and set `API_BIND_ADDRESS` to the host's LAN IPv4 address. Set `API_PORT` to a free host port if 8080 is occupied. Then rerun the Compose command.

The multi-stage image uses Microsoft's .NET 10 Alpine images and runs as the built-in non-root `app` user on container port 8080. Docker probes `/health` every 30 seconds. Compose starts the service after a host reboot unless manually stopped, drops Linux capabilities, uses a read-only root filesystem, and rotates logs. An unhealthy health probe alone does not restart a running process; a process exit does trigger the restart policy.

## Deploy automatically

Push to `main` in [calWoolgar/ubuntu-apps-health-api](https://github.com/calWoolgar/ubuntu-apps-health-api):

```sh
git push origin main
```

The [workflow](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/workflows/ci.yaml) first tests the deployment script and container on GitHub-hosted Linux. After those checks pass, a repository-specific self-hosted runner on `ubuntu-apps` deploys the exact tested commit. Pull requests and other branches run tests without deploying.

Deployments queue without interrupting an active deployment. Superseded commits are skipped. Each release contains only committed source, and its image is tagged with the full commit SHA. Docker and HTTP health checks must pass before `current` switches to the new release. A failed build leaves the running API untouched; failed activation or HTTP verification attempts to restore the previous image and keeps the previous `current` pointer.

The VM's shared `.env` is preserved. Its `IMAGE_TAG` value is overridden with each deployed commit's SHA. The API remains at <http://192.168.1.87:8080/health>. The runner connects outbound to GitHub; deployments do not require public SSH access or a stored personal GitHub token. Container replacement causes a short interruption.

## VM operations and rollback

Useful commands from the deployment root (`~/apps/ubuntu-apps-health-api`):

```sh
sudo docker compose --env-file .env -f current/compose.yaml logs --tail 100 api
sudo docker compose --env-file .env -f current/compose.yaml restart api
sudo docker compose --env-file .env -f current/compose.yaml down
```

To restore a preserved release, choose its directory and run:

```sh
release_dir="$PWD/releases/26bf6b0" # Replace with the release to restore.
revision=$(cat "$release_dir/.deploy-revision" 2>/dev/null || basename "$release_dir")
sudo env IMAGE_TAG="$revision" docker compose --env-file .env -f "$release_dir/compose.yaml" up -d --no-build --wait --wait-timeout 120 && ln -sfn "$release_dir" current
```

The next successful push to `main` resumes automatic deployment. Keep previous release directories and image tags while they are needed for rollback. See [deployment details](docs/deployment.md) for runner-service operations.

The service uses HTTP and has no authentication. Configure HTTPS at an existing reverse proxy before giving it a public internet hostname.
