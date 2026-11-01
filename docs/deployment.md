# Ubuntu Apps deployment

Deployed and verified on 1 November 2026.

| Setting | Value |
| --- | --- |
| SSH target | `devadmin@ubuntu-apps` |
| Health endpoint | <http://192.168.1.87:8080/health> |
| Deployed version | <http://192.168.1.87:8080/version> |
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
| Deployment mechanism | VM checks successful public `main` push builds every two minutes |
| Deployer service | `ubuntu-apps-health-api-deploy.service` |
| Deployer timer | `ubuntu-apps-health-api-deploy.timer` |
| Deployer service user | `devadmin`, with Docker group access |
| Public source checkout | `/home/devadmin/apps/ubuntu-apps-health-api/source` |
| Installed dispatcher | `/home/devadmin/apps/ubuntu-apps-health-api/deployer/PollDeploy.py` |

Installed `docker.io`, `docker-compose-v2`, and `docker-buildx` from Ubuntu's package repositories. Docker is active and enabled at host startup. The container uses the `unless-stopped` restart policy; no VM reboot was performed.

Verification:

- Release build: zero warnings and zero errors.
- [GitHub Actions container checks](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/runs/41272052723): passed.
- Docker health status on the VM: `healthy`.
- Container user: `app`, UID 1654; root filesystem is read-only.
- HTTP smoke checks cover health status/body/cache headers, root metadata, exact `/version` SHA, and unknown-route 404. Pass `-ExpectedCommitSha <SHA>` to `scripts/SmokeTest.ps1` when checking a deployed revision.
- The initial private-repository runner deployment was verified by [run 41273066930](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/runs/41273066930). Public deployment uses the timer described below instead.

To inspect the deployment:

```sh
ssh devadmin@ubuntu-apps
cd ~/apps/ubuntu-apps-health-api
sudo docker compose --env-file .env -f current/compose.yaml ps
sudo docker compose --env-file .env -f current/compose.yaml logs --tail 100 api
```

Push updates to `main`; no manual source transfer is needed. The VM reads GitHub's public Git and workflow APIs without credentials and checks the exact repository, branch, SHA, workflow, event, status, and conclusion before executing deployment code. Fork and PR runs cannot pass this gate. No personal GitHub token or SSH private key is stored on the VM. The original `releases/26bf6b0` and matching image remain available for rollback.

To inspect the timer and its deployment logs:

```sh
systemctl status ubuntu-apps-health-api-deploy.timer --no-pager
sudo journalctl -u ubuntu-apps-health-api-deploy.service -n 100 --no-pager
sudo systemctl stop ubuntu-apps-health-api-deploy.timer
sudo systemctl start ubuntu-apps-health-api-deploy.timer
```

The timer starts after boot and checks again two minutes after the previous check finishes. The file lock serializes checks. Failed CI, unavailable GitHub, or an offline VM leaves the current API in place; the next check retries. CI uses GitHub-hosted runners, and the old repository-specific VM runner is removed before making the repository public.

To rebuild this setup on a replacement Ubuntu VM, install `docker.io`, `docker-compose-v2`, `docker-buildx`, Git, Python 3, and curl. Restore the deployment root and shared `.env`, enable Docker, and grant `devadmin` Docker group access. From a reviewed checkout, install the dispatcher and units:

```sh
mkdir -p ~/apps/ubuntu-apps-health-api/deployer
install -m 755 scripts/PollDeploy.py ~/apps/ubuntu-apps-health-api/deployer/PollDeploy.py
sudo install -m 644 deploy/ubuntu-apps-health-api-deploy.service /etc/systemd/system/
sudo install -m 644 deploy/ubuntu-apps-health-api-deploy.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ubuntu-apps-health-api-deploy.timer
```

The installed dispatcher lives outside the source checkout. Changes to `PollDeploy.py` or the systemd units require repeating these installation commands; application and `Deploy.sh` changes are pulled automatically after CI passes.
