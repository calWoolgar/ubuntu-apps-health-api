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

GitHub Actions builds and starts the actual container, waits for Docker health to pass, runs these same HTTP checks, and verifies that the runtime user is non-root on every push and pull request.

## Run in Docker

Install Docker with the Compose plugin, then run:

```sh
docker compose up -d --build --wait --wait-timeout 120
curl --fail http://127.0.0.1:8080/health
docker compose ps
```

The API binds to the host's loopback address by default. To allow LAN access, copy `.env.example` to `.env` and set `API_BIND_ADDRESS` to the host's LAN IPv4 address. Set `API_PORT` to a free host port if 8080 is occupied. Then rerun the Compose command.

The multi-stage image uses Microsoft's .NET 10 Alpine images and runs as the built-in non-root `app` user on container port 8080. Docker probes `/health` every 30 seconds. Compose starts the service after a host reboot unless manually stopped, drops Linux capabilities, uses a read-only root filesystem, and rotates logs. An unhealthy health probe alone does not restart a running process; a process exit does trigger the restart policy.

## Deploy or update Ubuntu Apps

SSH access as `devadmin@ubuntu-apps` and permission to use Docker on the VM are required. No GitHub credential needs to be copied to the VM.

From a local checkout, archive the committed source:

```powershell
git archive --format=tar.gz --output=../health-api-source.tar.gz HEAD
scp ../health-api-source.tar.gz devadmin@ubuntu-apps:~/health-api-source.tar.gz
ssh devadmin@ubuntu-apps
```

On the VM, inspect `docker ps` and `ss -lnt` first to choose an unused host port. Then:

```sh
deploy_root="$HOME/apps/ubuntu-apps-health-api"
mkdir -p "$deploy_root/releases"
release_dir=$(mktemp -d "$deploy_root/releases/release-XXXXXXXX")
tar -xzf ~/health-api-source.tar.gz -C "$release_dir"
test -f "$deploy_root/.env" || cp "$release_dir/.env.example" "$deploy_root/.env"
# Edit "$deploy_root/.env" to choose the VM's LAN address and a free port.
docker compose --env-file "$deploy_root/.env" -f "$release_dir/compose.yaml" up -d --build --wait --wait-timeout 120
# Only switch the current-release pointer after the command succeeds.
ln -sfn "$release_dir" "$deploy_root/current"
docker compose --env-file "$deploy_root/.env" -f "$deploy_root/current/compose.yaml" ps
# Replace the address and port below with the values in .env.
curl --fail http://VM_LAN_IP:HOST_PORT/health
```

Repeat the archive, transfer, and VM commands after pulling source updates. Each update extracts into a clean release directory, so files removed from Git cannot linger. The shared `.env` file is preserved, and the Compose project name stays `ubuntu-apps-health-api`. `--wait` succeeds only when the container is healthy. This deployment has a short interruption during container replacement. Keep previous release directories until you no longer need their source.

Useful commands from the deployment root (`~/apps/ubuntu-apps-health-api`):

```sh
docker compose --env-file .env -f current/compose.yaml logs --tail 100 api
docker compose --env-file .env -f current/compose.yaml restart api
docker compose --env-file .env -f current/compose.yaml down
```

The service uses HTTP and has no authentication. Configure HTTPS at an existing reverse proxy before giving it a public internet hostname.
