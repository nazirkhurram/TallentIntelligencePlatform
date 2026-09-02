# Developer Onboarding

Welcome to the Talent Intelligence Platform. This runbook gets you from a fresh clone to a running local dev stack.

## 1. Prerequisites

Install the following before you start:

- **Docker Desktop** (with the WSL2 backend, if you're on Windows) — [docker.com](https://www.docker.com/products/docker-desktop/)
  - On Windows, make sure WSL2 is installed and updated: `wsl --update`
  - Recommended: allocate at least 4 GB RAM to Docker/WSL2 (see Troubleshooting if builds fail due to low memory)
- **Git** — for cloning and version control
- **Node.js** (LTS) — required for `apps/web`
- **Python 3.11+** and **uv** — required for `apps/api` and `apps/worker` (uv manages dependencies via `pyproject.toml` / `uv.lock`)
- **VS Code** (recommended) — with the Docker and Python extensions

Verify Docker is working before continuing:
```bash
docker --version
docker compose version
```

## 2. Repository Setup

Clone the repository and move into the project root:

```bash
git clone git clone https://github.com/nazirkhurram/TallentIntelligencePlatform.git
cd TallentIntelligencePlatform
```

Project structure overview:

apps/
api/ -> backend service (Python, uv, Dockerfile)
web/ -> frontend (Node/TS, Dockerfile)
worker/ -> background worker (Python, uv, Dockerfile)
infra/
compose/ -> Docker Compose files (compose.yml, compose.override.yml, compose.prod.yml, init-db.sql)
packages/
schema/ -> shared schema package
docs/ -> project documentation (this file lives here)


## 3. Environment Variables

Copy the example environment file and fill in local values:

```bash
cp .env.example .env
```

Open `.env` and set any required values (database credentials, API keys, ports, etc.). Ask a teammate or check `docs/contributing.md` if you're unsure what a variable should be set to. Never commit your filled-in `.env` file.

## 4. Start the Development Stack

Run all commands from the **repository root** (not from inside `infra/compose`), since the compose files reference relative paths from the root.

Build and start all services in the background:

```bash
docker compose -f infra/compose/compose.yml -f infra/compose/compose.override.yml up -d --build
```

Check that everything is running:

```bash
docker compose -f infra/compose/compose.yml ps
```

You should see containers for `api`, `web`, `worker`, and the database, all in an `Up`/`healthy` state.

To stop the stack:

```bash
docker compose -f infra/compose/compose.yml down
```

## 5. Database Setup and Seeding

On first startup, the Postgres container automatically runs `infra/compose/init-db.sql`, which enables the required extensions:

- `uuid-ossp`
- `vector`
- `pg_trgm`
- `unaccent`

If you need to reset the database from scratch (e.g., after a schema change), remove the database volume and restart:

```bash
docker compose -f infra/compose/compose.yml down -v
docker compose -f infra/compose/compose.yml -f infra/compose/compose.override.yml up -d --build
```

> ⚠️ `down -v` deletes local database data. Only use it on your local dev environment.

If the project uses migrations (via Alembic or similar), document the exact command here, e.g.:

```bash
docker compose -f infra/compose/compose.yml exec api uv run alembic upgrade head
```

## 6. Common Development Tasks

**View logs for a specific service:**
```bash
docker compose -f infra/compose/compose.yml logs -f api
```

**Restart a single service after a code change:**
```bash
docker compose -f infra/compose/compose.yml restart api
```

**Rebuild after adding a new dependency:**
```bash
docker compose -f infra/compose/compose.yml -f infra/compose/compose.override.yml up -d --build api
```

**Open a shell inside a running container:**
```bash
docker compose -f infra/compose/compose.yml exec api bash
```

**Run the test suite (example, adjust per service):**
```bash
docker compose -f infra/compose/compose.yml exec api uv run pytest
```

## 7. Troubleshooting

**Docker Desktop fails to start / WSL errors on Windows (`0xc00000fd`, `0x80072746`, etc.)**
- Run `wsl --shutdown`, then `wsl --update`, then relaunch Docker Desktop.
- If the error mentions the `docker-desktop` distro specifically, reset it:

wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

  This wipes local containers/images but not your project files — Docker recreates the distros on next launch.
- "Failed to launch the localhost relay process" / connection errors are usually caused by a VPN, firewall, or antivirus interfering with the WSL virtual network. Disconnect VPN and retry, or run `netsh winsock reset` + `netsh int ip reset all` followed by a full restart.

**Build fails with "The paging file is too small for this operation to complete"**
- This is a Windows virtual memory issue, common on machines with 8 GB RAM or less.
- Increase the Windows paging file size manually (System Properties → Advanced → Performance Settings → Advanced → Virtual Memory), or increase WSL2's memory allocation via a `.wslconfig` file in your user profile.
- If it persists, close other memory-heavy applications before building, or build services one at a time:
```bash
  docker compose -f infra/compose/compose.yml build api
```

**Port already in use**
- Check what's using the port (`netstat -ano | findstr <port>` on Windows) and stop the conflicting process, or change the port mapping in `compose.override.yml`.

**Containers build but exit immediately**
- Check logs for the specific service: `docker compose -f infra/compose/compose.yml logs <service>`
- Confirm your `.env` file has all required variables set.

## 8. Verification

Once the stack is up, confirm your environment is working:

- [ ] `docker compose -f infra/compose/compose.yml ps` shows `api`, `web`, `worker`, and the database as running
- [ ] The API responds at its health endpoint (e.g., `http://localhost:8000/health`)
- [ ] The web app loads in the browser at `http://localhost:3000`
- [ ] Logs for all services are free of repeated errors: `docker compose -f infra/compose/compose.yml logs`
- [ ] You can open a shell into the `api` container and run the test suite successfully

If all boxes are checked, you're fully onboarded. For anything not covered here, check `docs/contributing.md` or ask in the team channel.