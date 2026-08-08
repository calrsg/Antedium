# Deployment

Antedium ships as a Docker image. A GitHub Actions workflow
([.github/workflows/deploy.yml](../.github/workflows/deploy.yml)) lints and
compiles every push/PR, and on a successful push to `master` builds the image,
pushes it to GHCR, and deploys it straight to the Debian server via a
self-hosted runner.

```
push to master ─▶ checks (ruff + compileall) ─▶ build & push image to GHCR ─▶ deploy (self-hosted runner on the server)
```

Deploys only fire after checks pass, and PRs run checks without deploying.

## One-time server setup (Debian 12)

Run as a user with sudo access.

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
# log out/in (or `newgrp docker`) for the group change to take effect
```

### 2. Create the persistent data directory

The bot persists two files: `config.json` (bot token/settings) and
`linklogging/log.json` (usage stats). These live **outside** the repo
checkout at `/opt/antedium/data` — see the comment in
[docker-compose.yml](../docker-compose.yml) for why.

```bash
sudo mkdir -p /opt/antedium/data
sudo chown "$USER":"$USER" /opt/antedium/data
```

If Antedium is already running on this box outside Docker, copy its existing
state over instead of starting fresh:

```bash
cp /path/to/existing/config.json /opt/antedium/data/config.json
cp /path/to/existing/linklogging/log.json /opt/antedium/data/log.json
```

Otherwise, create `config.json` by hand (the bot won't write a valid one for
you over a bind mount — an empty mounted file isn't the same as a missing
one). Use the template from the main [README](../README.md#installation) and
fill in a real `bot_token`. `linklogging/log.json` can start as `{}`.

### 3. Install a self-hosted GitHub Actions runner

On the repo's GitHub page: **Settings → Actions → Runners → New self-hosted
runner**, choose Linux/x64, and follow the generated commands — they'll look
like:

```bash
sudo mkdir -p /opt/actions-runner && cd /opt/actions-runner
curl -o actions-runner.tar.gz -L <url from GitHub>
tar xzf actions-runner.tar.gz
./config.sh --url https://github.com/calrsg/Antedium --token <token from GitHub>
```

Then install it as a service so it survives reboots, and make sure it can run
`docker` commands:

```bash
sudo ./svc.sh install
sudo usermod -aG docker $(whoami)   # or whichever user the service runs as
sudo ./svc.sh start
```

Confirm it shows as "Idle" under the repo's Runners page.

### 4. Place the compose file where the runner's job will find it

The deploy job in the workflow runs `docker compose pull && docker compose up
-d` from the checked-out repo, so `docker-compose.yml` at the repo root
(already committed) is picked up automatically — no manual copying needed.

## First deploy

Push to `master` (or merge a PR into it). Watch the run under the repo's
**Actions** tab. Once the `deploy` job finishes, check the bot is up:

```bash
docker compose -f /opt/actions-runner/_work/Antedium/Antedium/docker-compose.yml ps
docker logs -f antedium
```

(the exact path depends on the runner's configured work folder — `docker ps`
will show the running `antedium` container regardless of where compose was
invoked from.)

## Notes

- **GHCR visibility**: the image is pushed as a private GitHub Container
  Registry package under this repo. The deploy job logs in with the
  workflow's own `GITHUB_TOKEN` before pulling, so no extra credentials need
  to be set up on the server.
- **Rollback**: `docker compose pull` always takes `:latest`. To roll back,
  `docker pull ghcr.io/calrsg/antedium:<old commit sha>` and `docker run`/edit
  the compose file's tag temporarily — every build is also tagged with its
  commit SHA.
- **Checks**: `ruff` is pinned to a conservative rule set in
  [ruff.toml](../ruff.toml) (real bugs only — unused imports, undefined
  names, syntax errors) rather than style/formatting, since the codebase
  wasn't previously linted. Tighten it whenever you're ready to take on a
  broader cleanup.
