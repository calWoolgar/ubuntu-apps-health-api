# Ubuntu Apps deployment

Deployed and verified on 1 November 2026.

| Setting | Value |
| --- | --- |
| SSH target | `devadmin@ubuntu-apps` |
| Health endpoint | <http://192.168.1.87:8080/health> |
| Service metadata | <http://192.168.1.87:8080/> |
| Deployment root | `/home/devadmin/apps/ubuntu-apps-health-api` |
| Active source release | `current` symlink to the latest successful release under `releases/` |
| Runtime source commit | Recorded in `current/.deploy-revision` |
| Image tag | `ubuntu-apps-health-api:<full commit SHA>` |
| Compose project | `ubuntu-apps-health-api` |
| Container | `ubuntu-apps-health-api-api-1` |
| Shared configuration | `/home/devadmin/apps/ubuntu-apps-health-api/.env` |
| Network exposure | VM LAN IPv4 address, HTTP port 8080 |
| Deployment trigger | Successful container CI for a push to `main` |
| Repository runner | `ubuntu-apps-health-api` |
| Runner directory | `/home/devadmin/actions-runner-health-api` |
| Runner service user | `devadmin`, with Docker group access |

Installed `docker.io`, `docker-compose-v2`, and `docker-buildx` from Ubuntu's package repositories. Docker is active and enabled at host startup. The container uses the `unless-stopped` restart policy; no VM reboot was performed.

Verification:

- Release build: zero warnings and zero errors.
- [GitHub Actions container checks](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/runs/41272052723): passed.
- Docker health status on the VM: `healthy`.
- Container user: `app`, UID 1654; root filesystem is read-only.
- All three HTTP smoke checks passed from the Windows workstation against the VM's LAN address: health body/status/cache headers, root metadata, and unknown-route 404.
- [Automatic deployment verification](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/runs/41273066930): a push to `main` passed hosted CI and deployed the same commit through the VM runner. The running image tag and release metadata matched the pushed SHA, and workstation HTTP smoke checks passed afterward.

To inspect the deployment:

```sh
ssh devadmin@ubuntu-apps
cd ~/apps/ubuntu-apps-health-api
sudo docker compose --env-file .env -f current/compose.yaml ps
sudo docker compose --env-file .env -f current/compose.yaml logs --tail 100 api
```

Push updates to `main`; no manual source transfer is needed. The runner uses its repository-scoped registration credentials and short-lived per-job tokens. No personal GitHub token or SSH private key is stored on the VM. The original `releases/26bf6b0` and matching image remain available for rollback.

To inspect or restart the runner:

```sh
cd ~/actions-runner-health-api
sudo ./svc.sh status
sudo ./svc.sh stop
sudo ./svc.sh start
```

Its systemd unit is `actions.runner.calWoolgar-ubuntu-apps-health-api.ubuntu-apps-health-api.service`, enabled at host startup. Runner updates are managed by GitHub's runner application. If the VM or runner is offline, deployment jobs queue until it is available. Inspect [workflow runs](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/workflows/ci.yaml) for CI, deployment, and rollback logs.

To rebuild this setup on a replacement Ubuntu VM, install `docker.io`, `docker-compose-v2`, `docker-buildx`, Git, Python 3, and curl. Restore the deployment root and shared `.env`, enable Docker, grant the runner's service account Docker access, then register and install a repository-specific runner following [GitHub's runner setup instructions](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners). Use the runner label `ubuntu-apps-health-api` to match the workflow.
