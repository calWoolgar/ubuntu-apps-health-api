# Ubuntu Apps deployment

Deployed and verified on 1 November 2026.

| Setting | Value |
| --- | --- |
| SSH target | `devadmin@ubuntu-apps` |
| Health endpoint | <http://192.168.1.87:8080/health> |
| Service metadata | <http://192.168.1.87:8080/> |
| Deployment root | `/home/devadmin/apps/ubuntu-apps-health-api` |
| Active source release | `current` symlink to `releases/26bf6b0` |
| Runtime source commit | `26bf6b0dbfc4eda2fd89a9246722e3301e68e57d` |
| Image tag | `ubuntu-apps-health-api:26bf6b0` |
| Compose project | `ubuntu-apps-health-api` |
| Container | `ubuntu-apps-health-api-api-1` |
| Shared configuration | `/home/devadmin/apps/ubuntu-apps-health-api/.env` |
| Network exposure | VM LAN IPv4 address, HTTP port 8080 |

Installed `docker.io`, `docker-compose-v2`, and `docker-buildx` from Ubuntu's package repositories. Docker is active and enabled at host startup. The container uses the `unless-stopped` restart policy; no VM reboot was performed.

Verification:

- Release build: zero warnings and zero errors.
- [GitHub Actions container checks](https://github.com/calWoolgar/ubuntu-apps-health-api/actions/runs/41272052723): passed.
- Docker health status on the VM: `healthy`.
- Container user: `app`, UID 1654; root filesystem is read-only.
- All three HTTP smoke checks passed from the Windows workstation against the VM's LAN address: health body/status/cache headers, root metadata, and unknown-route 404.

To inspect the deployment:

```sh
ssh devadmin@ubuntu-apps
cd ~/apps/ubuntu-apps-health-api
sudo docker compose --env-file .env -f current/compose.yaml ps
sudo docker compose --env-file .env -f current/compose.yaml logs --tail 100 api
```

See the README for the clean-release update procedure. No GitHub token or SSH private key was transferred to the VM.
