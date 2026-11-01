#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 || ! $1 =~ ^[0-9a-f]{40}$ ]]; then
    echo 'Expected one full, lowercase Git commit revision.' >&2
    exit 2
fi
revision=$1
deploy_root=${DEPLOY_ROOT:-"$HOME/apps/ubuntu-apps-health-api"}
health_url=${DEPLOY_HEALTH_URL:-http://192.168.1.87:8080/health}
config="$deploy_root/.env"
if [[ ! -f $config ]]; then
    echo "Missing shared deployment configuration: $config" >&2
    exit 2
fi
git cat-file -e "$revision^{commit}"
mkdir -p "$deploy_root/releases"

previous_release=''
previous_revision=''
if [[ -e $deploy_root/current ]]; then
    previous_release=$(readlink -f "$deploy_root/current")
    if [[ $previous_release != "$deploy_root/releases/"* || ! -f $previous_release/compose.yaml ]]; then
        echo 'Current release is outside the deployment releases directory or is invalid.' >&2
        exit 2
    fi
    if [[ -f $previous_release/.deploy-revision ]]; then
        previous_revision=$(cat "$previous_release/.deploy-revision")
    else
        # The initial manual deployment used its short commit as the image tag.
        previous_revision=$(basename "$previous_release")
    fi
    if [[ ! $previous_revision =~ ^[0-9a-f]{7,40}$ ]]; then
        echo 'Previous release has an invalid image revision.' >&2
        exit 2
    fi
fi

compose() {
    local directory=$1
    shift
    docker compose --project-name ubuntu-apps-health-api --env-file "$config" \
        -f "$directory/compose.yaml" "$@"
}

activation_started=0
finish() {
    local status=$?
    trap - EXIT
    if (( status != 0 && activation_started == 1 )) && [[ -n $previous_release ]]; then
        echo "Deployment failed; restoring $previous_revision." >&2
        if IMAGE_TAG="$previous_revision" compose "$previous_release" up -d --no-build --wait --wait-timeout 120; then
            echo "Previous release restored: $previous_revision" >&2
        else
            echo 'Rollback failed. Inspect the Compose logs on ubuntu-apps.' >&2
        fi
    fi
    exit "$status"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

release_dir=$(mktemp -d "$deploy_root/releases/$revision.XXXXXXXX")
git archive "$revision" | tar -x -C "$release_dir"
printf '%s\n' "$revision" > "$release_dir/.deploy-revision"
export IMAGE_TAG="$revision"
export COMMIT_SHA="$revision"
compose "$release_dir" config --quiet
# Finish building before touching the currently running container.
compose "$release_dir" build
activation_started=1
compose "$release_dir" up -d --no-build --wait --wait-timeout 120
health_body=$(curl --fail --silent --show-error --max-time 10 \
    --retry 3 --retry-delay 1 --retry-connrefused "$health_url")
if [[ $health_body != Healthy ]]; then
    echo 'The deployed health endpoint did not return Healthy.' >&2
    exit 1
fi
version_url=${DEPLOY_VERSION_URL:-"${health_url%/health}/version"}
deployed_revision=$(curl --fail --silent --show-error --max-time 10 "$version_url" \
    | python3 -c 'import json, sys; print(json.load(sys.stdin).get("commitSha", ""))')
if [[ $deployed_revision != "$revision" ]]; then
    echo "Version mismatch: expected $revision, received $deployed_revision." >&2
    exit 1
fi
ln -sfn "$release_dir" "$deploy_root/current"
printf 'Deployed %s; health endpoint: %s\n' "$revision" "$health_url"
