# Section 7: Deployment and Operations — Complete Study Guide

Up to now your Work Organizer only runs while your laptop is open and a terminal window is running it. This
section turns it into a service that runs **24/7 in the cloud**: packaged with Docker, deployed automatically when
you merge to `main`, served over HTTPS on your own domain, watched by health checks and error tracking, and
kept on a strict AI budget so a bug can't run up a surprise bill.

Work through it in order. Each lesson has:

- **Concepts**: what to understand
- **Code**: configs and code to type out yourself (don't copy-paste; typing builds memory)
- **Common mistakes**: errors beginners hit
- **Exercises**: do them before moving on
- **Check yourself**: you should be able to answer these without looking

Total time: roughly **3–5 weeks at 1–2 hours a day**. Expect to spend a few dollars a month on hosting once you
deploy for real; every lesson can also be practised locally for free with Docker.

---

## Table of Contents

- [Part 0: Before You Start](#part-0-before-you-start)
- [Part A: Packaging Your App](#part-a-packaging-your-app)
  - [Lesson 1: What Deployment Means](#lesson-1-what-deployment-means)
  - [Lesson 2: Linux Server Basics](#lesson-2-linux-server-basics)
  - [Lesson 3: Docker Fundamentals](#lesson-3-docker-fundamentals)
  - [Lesson 4: Writing a Production Dockerfile](#lesson-4-writing-a-production-dockerfile)
  - [Lesson 5: Docker Compose — API, Bot, Worker and Postgres](#lesson-5-docker-compose--api-bot-worker-and-postgres)
  - [Lesson 6: Configuration Management with pydantic-settings](#lesson-6-configuration-management-with-pydantic-settings)
- [Part B: Hosting](#part-b-hosting)
  - [Lesson 7: Choosing a Host](#lesson-7-choosing-a-host)
  - [Lesson 8: Deploying to Render (PaaS Walkthrough)](#lesson-8-deploying-to-render-paas-walkthrough)
  - [Lesson 9: Deploying to a VPS with Docker and Caddy](#lesson-9-deploying-to-a-vps-with-docker-and-caddy)
  - [Lesson 10: Domains, DNS and HTTPS](#lesson-10-domains-dns-and-https)
- [Part C: Running It Properly](#part-c-running-it-properly)
  - [Lesson 11: Background Jobs and Schedulers in Production](#lesson-11-background-jobs-and-schedulers-in-production)
  - [Lesson 12: Databases in Production](#lesson-12-databases-in-production)
  - [Lesson 13: CI/CD with GitHub Actions](#lesson-13-cicd-with-github-actions)
- [Part D: Observability and Operations](#part-d-observability-and-operations)
  - [Lesson 14: Structured Logging](#lesson-14-structured-logging)
  - [Lesson 15: Error Tracking, Health Checks and Uptime Monitoring](#lesson-15-error-tracking-health-checks-and-uptime-monitoring)
  - [Lesson 16: Metrics Basics](#lesson-16-metrics-basics)
  - [Lesson 17: LLM Tracing — Logging Every Prompt, Tool Call and Token](#lesson-17-llm-tracing--logging-every-prompt-tool-call-and-token)
  - [Lesson 18: Controlling AI Costs](#lesson-18-controlling-ai-costs)
  - [Lesson 19: Updates, Rollbacks and Backups](#lesson-19-updates-rollbacks-and-backups)
  - [Lesson 20: The Production Checklist](#lesson-20-the-production-checklist)
- [Capstone Project: Work Organizer in Production](#capstone-project-work-organizer-in-production)
- [Weekly Schedule](#weekly-schedule)
- [Final Checklist](#final-checklist)
- [Exercise Solutions](#exercise-solutions)
- [Recommended Resources](#recommended-resources)

---

## Part 0: Before You Start

### 0.1 What you should already have

After Sections 1–6 your project probably looks something like this. Your names may differ; that's fine — just
map each piece to the role it plays.

```
work_organizer/
├── pyproject.toml / requirements.txt
├── .env                       # secrets (gitignored)
├── .env.example               # fake values (committed)
├── organizer/
│   ├── config.py              # settings (you'll rewrite this in Lesson 6)
│   ├── db.py                  # SQLAlchemy engine + SessionLocal
│   ├── models.py              # Task, Conversation, Message ...
│   ├── agent/                 # the LLM agent loop and tools
│   ├── integrations/          # Gmail, Calendar, Slack clients
│   ├── memory/                # Chroma vector store
│   ├── api/main.py            # FastAPI app: app = FastAPI(), POST /chat streams
│   ├── bot/main.py            # Telegram bot (python-telegram-bot)
│   └── scheduler.py           # APScheduler daily briefing
├── data/                      # SQLite file + Chroma folder (gitignored)
└── tests/
```

By the end of this section it will have three clearly separated **processes**:

| Process | Command | Job |
|---|---|---|
| `api` | `uvicorn organizer.api.main:app` | Serves HTTP: `/chat`, `/healthz`, webhooks |
| `bot` | `python -m organizer.bot.main` | Long-polls Telegram and forwards messages to the agent |
| `worker` | `python -m organizer.worker.main` | Runs scheduled jobs: daily briefing, cost report, cleanup |

…plus a **Postgres** database, a reverse proxy (**Caddy**) for HTTPS, and a CI/CD pipeline.

### 0.2 Tools to install on your own computer

| Tool | Why | Check it works |
|---|---|---|
| **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux) | Build and run containers | `docker version` |
| **Docker Compose v2** (bundled with Docker Desktop) | Run several containers together | `docker compose version` |
| **An SSH client** (built into macOS, Linux, Windows 10+) | Log in to servers | `ssh -V` |
| **GitHub account** with your project pushed | CI/CD | `git remote -v` |
| **`curl`** | Poke at HTTP endpoints | `curl --version` |

Check Docker:

```bash
docker version
```

```bash
docker run --rm hello-world
```

If the second command prints "Hello from Docker!", you're ready.

### 0.3 Accounts you'll create during this section

You don't need them all at once. Each lesson says when.

- A host: **Render** (Lesson 8) and/or a **VPS** at Hetzner or DigitalOcean (Lesson 9)
- A **domain name** from any registrar (Lesson 10) — optional but recommended, roughly the price of a coffee per year for many endings
- **Sentry** (free tier) for error tracking (Lesson 15)
- **Healthchecks.io** or **UptimeRobot** / **Better Stack** (free tiers) for uptime monitoring (Lesson 15)
- **Langfuse** Cloud (free tier) or self-hosted, for LLM tracing (Lesson 17, optional)
- An **S3-compatible bucket** (Backblaze B2, Cloudflare R2, Hetzner Object Storage, AWS S3) for backups (Lesson 19)

**Golden rule of this whole section:** secrets (API keys, bot tokens, database passwords) never go in Git, never
go in a Docker image, and never appear in logs. They live in `.env` on your laptop, in the host's secret store in
production, and in GitHub Actions secrets for CI.

---

## Part A: Packaging Your App

### Lesson 1: What Deployment Means

**Concepts**

**Deployment** = getting your code running on a computer that isn't yours, that stays on, that other things
(Telegram, your phone, a browser) can reach, and doing it in a repeatable way.

| On your laptop ("local") | On a server ("production") |
|---|---|
| Runs while you're watching | Runs 24/7, restarts itself after crashes and reboots |
| `localhost:8000`, only you can reach it | A public address: `https://organizer.example.com` |
| Secrets in `.env` | Secrets in the host's secret manager or a locked-down file |
| SQLite file in `data/` | Usually a managed Postgres database with backups |
| You read errors in the terminal | You read logs, error tracker and dashboards |
| `pip install` whenever | The exact same packages, every time, built by CI |

**Processes.** A process is one running program. Your laptop runs hundreds. When you type
`uvicorn organizer.api.main:app`, you start one process. In production a **process manager** (systemd, Docker, or
the hosting platform) starts your processes, restarts them when they crash, and stops them cleanly.

**Ports.** A port is a numbered "door" on a computer that a process listens on. Only one process can listen on a
given port at a time.

| Port | Usually used for |
|---|---|
| 22 | SSH (remote login) |
| 80 | HTTP |
| 443 | HTTPS |
| 5432 | Postgres |
| 8000 | Your app during development (any free number above 1024 works) |

**Listening address** matters as much as the port:

| Address | Who can connect |
|---|---|
| `127.0.0.1` (localhost) | Only programs on the same machine (or the same container!) |
| `0.0.0.0` | Anyone who can reach any network interface of the machine |

In production you put a **reverse proxy** (Caddy, Nginx, or the platform's load balancer) on ports 80/443. It
handles HTTPS and forwards requests to your app on an internal port. Your app itself is never directly exposed.

```
Internet ──HTTPS:443──▶ Caddy ──HTTP:8000──▶ api (uvicorn)
                                              │
Telegram ◀──long polling── bot ───────────────┤──▶ Postgres
                                              │
                         worker (scheduler) ──┘──▶ LLM API, Gmail, Slack
```

**Environments.** You'll usually have three copies of the app:

| Environment | Purpose | Data | Secrets |
|---|---|---|---|
| **dev** | Your laptop. Break things freely. | Fake / your own test data | Test keys, a **separate dev Telegram bot** |
| **staging** | A production-like copy to try a release before real users see it | Copy of prod schema, fake data | Separate keys and bot |
| **prod** | The real thing | Real data, backed up | Real keys, tightly controlled |

As a solo builder you can skip staging at first, but **never share a database or a Telegram bot token between
dev and prod**. Telegram only allows one process to long-poll a bot token at a time, so running your laptop bot
against the production token silently steals messages from the server (you'll see `Conflict: terminated by other
getUpdates request` errors).

**The twelve-factor ideas that matter most here**

1. **One codebase, many deploys.** The same Git commit runs in dev, staging and prod.
2. **Config in the environment.** Anything that differs between environments (URLs, keys, flags) comes from
   environment variables, not from code.
3. **Explicit dependencies.** Pinned in a lock file and installed during the build.
4. **Stateless processes.** Don't keep important data in memory or on the container's own disk; keep it in a
   database or a mounted volume.
5. **Logs are a stream.** Write logs to stdout; let the platform collect them.
6. **Build, release, run are separate stages.** Build an image once, then run that exact image everywhere.
7. **Disposability.** Processes start fast and shut down cleanly when told to (SIGTERM).

**Common mistakes**
- Thinking "it works on my machine" means it will work in production. The server has a different OS, no `.env`,
  no `data/` folder and no GPU. Containers (Lesson 3) remove most of these surprises.
- Starting the scheduler inside the web process and then running two web processes — you get two daily briefings.
  (Lesson 11 fixes this.)
- Exposing the database port to the internet "just for a minute".

**Exercises**
1. Draw your own architecture diagram for the Work Organizer: every process, every external service it calls,
   every data store, and which port each one listens on.
2. Make a table of every setting your app reads (API keys, model name, database path, timezone, Telegram token…)
   and mark which ones are secret and which differ between dev and prod.
3. Run `ss -tlnp` (Linux) or `lsof -iTCP -sTCP:LISTEN -n -P` (macOS) while your API is running. Find your app's
   port and its listening address.

**Check yourself**
- Why can't two processes listen on port 8000 at the same time?
- What's the difference between binding to `127.0.0.1` and `0.0.0.0`?
- Why should dev and prod use different Telegram bot tokens?

---

### Lesson 2: Linux Server Basics

Even if you end up on a platform like Render, you need enough Linux to read logs, run one-off commands and
understand what the platform is doing for you. On a VPS you need all of this.

**Concepts**

- A **VPS** (virtual private server) is a Linux computer you rent. You get an IP address and root access.
- **SSH** lets you log in securely with a **key pair**: a private key that stays on your laptop and a public key
  you copy to the server.
- **Users**: never run your app as `root`. Create a normal user with `sudo` rights for yourself, and let the app
  run as an unprivileged user.
- **systemd** is the Linux service manager. It starts services at boot, restarts them if they crash, and collects
  their logs (read them with `journalctl`).
- **ufw** ("uncomplicated firewall") decides which ports the outside world can reach.

**Code — SSH keys (on your laptop)**

Create a key (press Enter to accept the default path; set a passphrase):

```bash
ssh-keygen -t ed25519 -C "you@example.com"
```

This creates `~/.ssh/id_ed25519` (private — never share) and `~/.ssh/id_ed25519.pub` (public — safe to share).
Most VPS providers let you paste the public key when you create the server. Then log in:

```bash
ssh root@203.0.113.10
```

(`203.0.113.10` is a documentation example address; use your server's IP.)

**Code — first-time server setup (on the server, as root)**

Update the system:

```bash
apt update
```

```bash
apt upgrade -y
```

Create your own user and give it sudo:

```bash
adduser deploy
```

```bash
usermod -aG sudo deploy
```

Copy your SSH key to the new user:

```bash
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Open a **second** terminal and check you can log in as `deploy` before going further:

```bash
ssh deploy@203.0.113.10
```

**Code — harden SSH**

Turn off password logins and root logins. On Ubuntu, files in `/etc/ssh/sshd_config.d/` are read first and the
**first** value found for a setting wins, so name your file so it sorts before the cloud provider's file
(often `50-cloud-init.conf`):

```bash
sudo nano /etc/ssh/sshd_config.d/00-hardening.conf
```

```text
PasswordAuthentication no
PermitRootLogin no
KbdInteractiveAuthentication no
```

Check the effective settings, then restart SSH:

```bash
sudo sshd -T | grep -Ei 'passwordauthentication|permitrootlogin'
```

```bash
sudo systemctl restart ssh
```

Keep your existing session open and test a new login in another terminal. If it fails, you still have a way in to
fix it.

**Code — firewall with ufw**

```bash
sudo ufw allow OpenSSH
```

```bash
sudo ufw allow 80/tcp
```

```bash
sudo ufw allow 443/tcp
```

```bash
sudo ufw enable
```

```bash
sudo ufw status verbose
```

Always allow SSH **before** enabling the firewall, or you'll lock yourself out.

> **Docker and ufw warning:** ports published by Docker (`ports: - "5432:5432"`) are opened with iptables rules
> that **bypass ufw**. A ufw rule will *not* protect a Docker-published port. The fix: don't publish ports you
> don't need to be public (services in one Compose project reach each other on an internal network), or bind them
> to localhost: `"127.0.0.1:5432:5432"`.

**Code — automatic security updates**

```bash
sudo apt install -y unattended-upgrades
```

```bash
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

**File permissions**

`ls -l` shows something like `-rw-r----- 1 deploy deploy 512 Nov 4 10:00 .env`.

| Part | Meaning |
|---|---|
| `-` | Regular file (`d` = directory) |
| `rw-` | Owner (deploy) can read and write |
| `r--` | Group (deploy) can read |
| `---` | Everyone else: nothing |

Each triple is a number: read = 4, write = 2, execute = 1. So `rw-r-----` = 640, `rw-------` = 600,
`rwxr-xr-x` = 755.

```bash
chmod 600 /srv/organizer/.env
```

```bash
chmod +x /srv/organizer/deploy.sh
```

```bash
sudo chown -R deploy:deploy /srv/organizer
```

Secrets files should be `600` (only the owner can read them). Scripts need the execute bit.

**Code — a systemd service (running without Docker)**

You'll use Docker for the capstone, but you should know how to run a Python process directly under systemd. Say
you've cloned the app into `/srv/organizer` and created a venv there. Create a system user for the app:

```bash
sudo useradd --system --home /srv/organizer --shell /usr/sbin/nologin organizer
```

Then create the unit file:

```bash
sudo nano /etc/systemd/system/organizer-api.service
```

```ini
[Unit]
Description=Work Organizer API
After=network-online.target
Wants=network-online.target

[Service]
User=organizer
Group=organizer
WorkingDirectory=/srv/organizer
EnvironmentFile=/srv/organizer/.env
ExecStart=/srv/organizer/.venv/bin/uvicorn organizer.api.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
# Basic sandboxing
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/srv/organizer/data
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Load it, start it now, and enable it at boot:

```bash
sudo systemctl daemon-reload
```

```bash
sudo systemctl enable --now organizer-api
```

```bash
systemctl status organizer-api
```

Follow its logs:

```bash
journalctl -u organizer-api -f
```

**Useful server commands**

| Command | What it does |
|---|---|
| `htop` | Live CPU/memory per process (`q` quits) |
| `free -h` | Memory usage |
| `df -h` | Disk usage — a full disk is the #1 cause of mysterious outages |
| `du -sh /srv/*` | What's taking the space |
| `ss -tlnp` | Which processes listen on which ports |
| `journalctl -u NAME --since "1 hour ago"` | Recent logs for a service |
| `systemctl restart NAME` | Restart a service |
| `uptime` | How long since reboot, load average |
| `sudo reboot` | Reboot (your services must come back on their own!) |

**Common mistakes**
- Enabling ufw without allowing SSH first.
- Editing `/etc/ssh/sshd_config` while a cloud-init file in `sshd_config.d/` silently overrides your change.
- Forgetting `sudo systemctl daemon-reload` after editing a unit file.
- Making `.env` world-readable (`644`).
- Running everything as root "because it's easier".

**Exercises**
1. Create a cheap VPS (or a local Ubuntu VM with Multipass/UTM/VirtualBox). Create a `deploy` user, log in with
   an SSH key, disable password and root login, and enable ufw with only SSH, 80 and 443 open.
2. Write a systemd unit that runs `python -m http.server 9000 --bind 127.0.0.1` as a service. Prove it restarts
   after you `kill` it.
3. Reboot the server and confirm the service came back by itself.

**Check yourself**
- What does `chmod 640` mean in words?
- Why must you test a new SSH login before closing your current session?
- Why doesn't ufw protect a port published by Docker?

---

### Lesson 3: Docker Fundamentals

**Concepts**

**The problem Docker solves:** your app needs Python 3.12, about forty packages at exact versions, some system
libraries, and a particular folder layout. Docker packages all of that into one **image** that runs the same on
your laptop, in CI, and on any server.

| Term | Meaning | Analogy |
|---|---|---|
| **Image** | A read-only template: OS files + Python + your code + dependencies | A class / a recipe |
| **Container** | A running instance of an image, with its own process and filesystem | An object / a cooked dish |
| **Dockerfile** | Text instructions for building an image | The recipe card |
| **Layer** | Each instruction in a Dockerfile creates a cached layer | Steps you don't redo if nothing changed |
| **Registry** | A server that stores images (Docker Hub, GitHub Container Registry `ghcr.io`) | A package index for images |
| **Tag** | A label for one version of an image: `organizer:sha-3f2a1c9` | A Git tag |
| **Volume** | Storage that lives outside the container and survives restarts/rebuilds | An external hard drive |
| **Port mapping** | `-p 8000:8000` connects a host port to a container port | Call forwarding |

A container is **not** a virtual machine. It shares the host's Linux kernel and is just an isolated process —
which is why it starts in under a second.

**Containers are disposable.** Anything written inside a container's filesystem is lost when the container is
removed (and you'll remove them every deploy). Your SQLite file, Chroma folder and uploaded files must live in a
**volume**.

**Code — your first container**

```bash
docker run --rm -it python:3.12-slim python
```

You're now in a Python REPL inside a container. `exit()` leaves and `--rm` deletes the container.

Run a web server in the background, mapping host port 8080 to container port 80:

```bash
docker run -d --name web -p 8080:80 nginx:stable
```

```bash
curl http://localhost:8080
```

```bash
docker ps
```

```bash
docker logs web
```

```bash
docker stop web
```

(Then `docker rm web` deletes the stopped container.)

**Code — the command cheat sheet**

| Command | What it does |
|---|---|
| `docker build -t organizer:dev .` | Build an image from the Dockerfile in `.` and tag it |
| `docker images` | List images |
| `docker run --rm -p 8000:8000 --env-file .env organizer:dev` | Run a container from an image |
| `docker run -d ...` | Run in the background ("detached") |
| `docker ps` / `docker ps -a` | Running / all containers |
| `docker logs -f NAME` | Follow a container's output |
| `docker exec -it NAME sh` | Open a shell inside a running container |
| `docker stop NAME` / `docker rm NAME` | Stop / delete a container |
| `docker volume ls` / `docker volume inspect NAME` | List / inspect volumes |
| `docker system df` | How much disk Docker is using |
| `docker image prune -a` | Delete unused images (frees a lot of space) |

**Volumes**

```bash
docker volume create organizer_data
```

```bash
docker run --rm -v organizer_data:/data python:3.12-slim sh -c "echo hello > /data/note.txt"
```

```bash
docker run --rm -v organizer_data:/data python:3.12-slim cat /data/note.txt
```

The second container sees the file the first one wrote, even though the first container is gone.

| Kind | Syntax | Use for |
|---|---|---|
| **Named volume** | `-v organizer_data:/app/data` | Production data (Docker manages where it lives) |
| **Bind mount** | `-v "$(pwd)/data:/app/data"` | Development: see/edit files from your laptop |

**Environment variables**

```bash
docker run --rm -e ENVIRONMENT=dev python:3.12-slim python -c "import os; print(os.environ['ENVIRONMENT'])"
```

`--env-file .env` loads many at once. The `.env` file stays on the host; it is **not** copied into the image.

**Common mistakes**
- Writing the database into the container filesystem and losing it on the next deploy.
- Running `uvicorn --host 127.0.0.1` inside a container. Inside a container, 127.0.0.1 is the container itself, so
  port mapping can't reach it. Bind to `0.0.0.0` inside containers.
- Confusing the two sides of `-p HOST:CONTAINER`.
- Filling the server's disk with old images. Run `docker image prune -a` occasionally (or automate it).

**Exercises**
1. Run `python:3.12-slim` with a named volume, write a JSON file into it from Python, delete the container, and
   read the file back from a new container.
2. Start `nginx:stable` on host port 8081, open a shell in it with `docker exec`, and find its config file.
3. Use `docker system df` to see how much space Docker uses on your machine, then prune unused images.

**Check yourself**
- What's the difference between an image and a container?
- Where should a SQLite database file live when the app runs in a container, and why?
- What does `-p 8080:80` do?

---

### Lesson 4: Writing a Production Dockerfile

**Concepts**

A good production Dockerfile for a Python app:

1. Starts from a **slim** official base image (`python:3.12-slim`) — small, but uses normal glibc so wheels work.
   Avoid `alpine` for Python: many packages have no prebuilt wheels for it and you end up compiling for minutes.
2. Uses a **multi-stage build**: a "builder" stage installs dependencies (with compilers if needed), and a small
   "runtime" stage copies only the finished virtual environment. Compilers never reach production.
3. Copies `requirements.txt` **before** the code, so the slow dependency layer is cached and only rebuilt when
   dependencies change.
4. Runs as a **non-root user**.
5. Sets `PYTHONUNBUFFERED=1` so logs appear immediately.
6. Has a `.dockerignore` so secrets, `.git` and your local data never enter the image.

**Code — pin your dependencies first**

Production builds must be reproducible. If you use plain pip, generate a fully pinned file from a short list of
top-level dependencies. Create `requirements.in`:

```text
fastapi
uvicorn[standard]
sqlalchemy>=2
psycopg[binary]
alembic
pydantic-settings
anthropic
python-telegram-bot
apscheduler>=3.10,<4
chromadb
httpx
sentry-sdk[fastapi]
prometheus-client
```

Then compile it to exact versions (with `uv`, or `pip-tools`' `pip-compile`):

```bash
uv pip compile requirements.in -o requirements.txt
```

Keep dev-only tools separate in `requirements-dev.txt`:

```text
pytest
pytest-asyncio
ruff
```

If you already manage the project with `uv` and a `uv.lock`, use that instead — see the uv variant below.

> **Note:** APScheduler 4 has a completely different API from 3.x. The `<4` pin keeps the code in this course
> working.

**Code — `.dockerignore`**

```text
.git
.github
.venv
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/
.env
.env.*
!.env.example
data/
backups/
*.log
*.db
*.sqlite3
.DS_Store
```

**Code — `Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1

############################
# Stage 1: build the venv  #
############################
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Compilers are only needed if a dependency has no prebuilt wheel.
# They stay in this stage and never reach the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

############################
# Stage 2: runtime image   #
############################
FROM python:3.12-slim AS runtime

# Set at build time by CI: docker build --build-arg RELEASE=$GITHUB_SHA
ARG RELEASE=dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    RELEASE=${RELEASE}

# An unprivileged user to run the app
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations/ ./migrations/
COPY --chown=app:app organizer/ ./organizer/

# The data folder must exist and belong to "app" so a named volume
# mounted here inherits the right owner.
RUN mkdir -p /app/data && chown app:app /app/data

USER app
EXPOSE 8000

# Default command = the API. Compose / the host overrides it for bot and worker.
CMD ["uvicorn", "organizer.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--no-access-log"]
```

Why each detail:

| Line | Why |
|---|---|
| `# syntax=docker/dockerfile:1` | Use the latest stable Dockerfile syntax features |
| `AS builder` / `AS runtime` | Names the stages; `COPY --from=builder` pulls files across |
| `COPY requirements.txt .` before code | Code changes don't invalidate the dependency cache |
| `rm -rf /var/lib/apt/lists/*` | Removes package index files you don't need (smaller image) |
| `useradd --system` + `USER app` | A bug in your app can't modify system files |
| `mkdir /app/data && chown` | Named volumes copy ownership from the image's directory the first time |
| `--forwarded-allow-ips "*"` | Trust `X-Forwarded-*` headers from the proxy. Safe **only** because the container port isn't published to the internet |
| `--no-access-log` | You'll write your own JSON access log in Lesson 14 |
| Exec-form `CMD [...]` | Your process becomes PID 1 and receives stop signals directly |

**Code — the uv variant**

If your project uses `pyproject.toml` + `uv.lock`, replace the builder stage with this (pin the uv image to a
specific version you've tested; `0.8.0` below is an example):

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
```

`--frozen` refuses to build if the lock file is out of date, and `--no-install-project` installs only the
dependencies (your code is copied in the runtime stage).

**Code — build and run**

```bash
docker build -t organizer:dev .
```

```bash
docker images organizer
```

```bash
docker run --rm -p 8000:8000 --env-file .env -v organizer_data:/app/data organizer:dev
```

In another terminal:

```bash
curl http://localhost:8000/healthz
```

Run the bot from the **same image** by overriding the command:

```bash
docker run --rm --env-file .env -v organizer_data:/app/data organizer:dev python -m organizer.bot.main
```

One image, three processes. That's the pattern for the rest of the section.

**Shrinking and inspecting**

```bash
docker history organizer:dev
```

shows each layer's size. Typical sizes: `python:3.12-slim` ≈ 130 MB; with FastAPI + Anthropic + Telegram ≈
250 MB; Chroma pulls in `onnxruntime` and friends and can add several hundred MB. That's acceptable, but it's
why you shouldn't install Jupyter, pandas or torch "just in case".

**Common mistakes**
- `COPY . .` before `pip install` — every code change reinstalls every dependency (slow builds).
- Forgetting `.dockerignore` and baking `.env` into the image. **Anyone who can pull the image can read it.**
  Check with `docker run --rm organizer:dev ls -la /app`.
- Using `latest` tags for base images in production, so builds change under you. `python:3.12-slim` is a fair
  compromise (it moves only within 3.12 patch releases); pin a digest if you need full reproducibility.
- Shell-form `CMD uvicorn ...`: the shell becomes PID 1 and doesn't forward SIGTERM, so stops take 10 seconds and
  then kill your app mid-request.

**Exercises**
1. Build your image, then run `docker run --rm organizer:dev ls -la /app` and confirm no `.env`, `.git` or `data/`
   contents are inside.
2. Change one line of code and rebuild. Which layers were cached? Now change `requirements.txt` and rebuild. What
   changed?
3. Build a single-stage version (no builder stage, compilers installed) and compare its size with the multi-stage
   one using `docker images`.
4. Run `docker run --rm organizer:dev whoami` — it should print `app`, not `root`.

**Check yourself**
- Why does the order of `COPY` lines matter?
- What does a multi-stage build save you?
- Why should the container run as a non-root user?

---

### Lesson 5: Docker Compose — API, Bot, Worker and Postgres

**Concepts**

Typing long `docker run` commands for four containers gets old fast. **Docker Compose** describes the whole system
in one YAML file — services, volumes, networks, environment — and starts it with one command.

- Every service in a Compose project is on a private network and can reach the others **by service name**:
  the API connects to Postgres at host `db`, port 5432.
- Only ports listed under `ports:` are reachable from outside.
- `depends_on` with `condition: service_healthy` waits for Postgres to be ready before starting the app.
- The modern file name is `compose.yaml`, and the command is `docker compose` (with a space). The old top-level
  `version:` key is obsolete — leave it out.

**Code — `compose.yaml` (development)**

```yaml
name: organizer

x-app: &app
  build: .
  image: organizer:dev
  env_file: .env
  init: true                 # tiny init process: forwards signals, reaps zombies
  restart: unless-stopped
  volumes:
    - app_data:/app/data
  depends_on:
    db:
      condition: service_healthy

services:
  db:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_USER: organizer
      POSTGRES_DB: organizer
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"  # dev only: lets tools on your laptop connect
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U organizer -d organizer"]
      interval: 5s
      timeout: 5s
      retries: 10

  api:
    <<: *app
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3

  bot:
    <<: *app
    command: ["python", "-m", "organizer.bot.main"]

  worker:
    <<: *app
    command: ["python", "-m", "organizer.worker.main"]

volumes:
  pg_data:
  app_data:
```

And the matching lines in your `.env`:

```text
POSTGRES_PASSWORD=change-me-to-a-long-random-string
DATABASE_URL=postgresql+psycopg://organizer:change-me-to-a-long-random-string@db:5432/organizer
```

Generate a strong password with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Notes:
- `x-app: &app` defines a reusable block (a YAML **anchor**); `<<: *app` merges it into each service. Top-level
  keys starting with `x-` are ignored by Compose, so they're the standard place for shared config.
- The merge is **shallow**: if a service defines its own `environment:` or `volumes:`, it *replaces* the anchor's
  list rather than adding to it.
- The Postgres image is pinned to a major version. Postgres 18+ images changed the recommended volume path to
  `/var/lib/postgresql`; if you choose 18, follow the image's documentation for the mount point.
- The healthcheck uses Python, because `slim` images don't include `curl`.

**Code — everyday Compose commands**

```bash
docker compose up -d --build
```

```bash
docker compose ps
```

```bash
docker compose logs -f api
```

```bash
docker compose exec db psql -U organizer -d organizer
```

```bash
docker compose run --rm api alembic upgrade head
```

```bash
docker compose down
```

`down` stops and removes containers but **keeps volumes**. `docker compose down -v` also deletes volumes — i.e.
your database. Never type `-v` on a server unless you mean it.

**Signals and `init: true`**

When Docker stops a container it sends SIGTERM, waits 10 seconds, then sends SIGKILL. The Linux kernel ignores
SIGTERM for PID 1 unless the program installed a handler. Uvicorn and python-telegram-bot install handlers; a
plain Python script (like a scheduler) often doesn't, so it gets killed hard after 10 seconds. `init: true` runs a
tiny init process as PID 1 that forwards signals properly. Use it for every Python service.

**Common mistakes**
- Connecting to `localhost:5432` from inside the `api` container. Inside a container, `localhost` is that
  container. Use the service name: `db:5432`.
- Starting the app before Postgres is ready and crashing on the first connection — use the healthcheck +
  `condition: service_healthy`.
- Publishing Postgres with `"5432:5432"` on a server. That's on the whole internet, and ufw won't stop it
  (Lesson 2). Use `127.0.0.1:` or no `ports:` at all.
- Changing `POSTGRES_PASSWORD` after the volume already exists. The image only uses it the **first** time it
  initialises an empty data directory.

**Exercises**
1. Bring up the full stack with `docker compose up -d --build`, send a chat message through `/chat`, and watch the
   logs of all three app services at once.
2. Temporarily add `raise RuntimeError("boom")` at the top of the worker's `main()`, rebuild, and watch Docker
   restart it again and again with `docker compose logs -f worker`. (Note: `docker stop` / `docker kill` count as
   *you* stopping it, so the `unless-stopped` policy does not restart it.) Remove the line afterwards.
3. Connect to Postgres with `docker compose exec db psql -U organizer -d organizer` and list the tables with `\dt`.
4. Time `docker compose stop worker` with and without `init: true`. Explain the difference.

**Check yourself**
- How does the `api` container find the database?
- What's the difference between `docker compose down` and `docker compose down -v`?
- Why is the Postgres healthcheck needed?

---

### Lesson 6: Configuration Management with pydantic-settings

**Concepts**

Scattered `os.getenv("SOMETHING")` calls fail late (the first time that code runs, maybe at 7:30am during the
daily briefing) and silently (a typo gives you `None`). **pydantic-settings** reads every setting once, at
startup, from environment variables and an optional `.env` file, converts types, validates them, and **crashes
immediately** with a clear message if something required is missing. Crashing at startup is good: the deploy
fails, the old version keeps running, and you see why.

Priority order (highest wins): arguments passed to `Settings(...)` → real environment variables → `.env` file →
default values in the class. So in production, the platform's environment variables override anything else.

**Code — `organizer/config.py`**

```python
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",            # read if present; ignored if missing (as in production)
        env_file_encoding="utf-8",
        extra="ignore",             # don't crash on unrelated variables like PATH
    )

    # --- general ---
    environment: Literal["dev", "staging", "prod"] = "dev"
    release: str = Field(
        default="dev",
        validation_alias=AliasChoices("RELEASE", "RENDER_GIT_COMMIT"),
    )
    log_level: str = "INFO"
    log_json: bool = True
    timezone: str = "Europe/London"

    # --- storage ---
    database_url: str = "sqlite:///./data/organizer.db"
    chroma_path: str = "./data/chroma"

    # --- AI ---
    anthropic_api_key: SecretStr
    llm_model: str = "claude-sonnet-4-5"   # use a current model id from your provider's docs
    llm_max_tokens: int = Field(default=1024, ge=1, le=8192)
    llm_max_tool_iterations: int = Field(default=8, ge=1, le=25)

    # --- Telegram ---
    telegram_bot_token: SecretStr
    telegram_admin_chat_id: int | None = None

    # --- observability ---
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0, le=1)
    healthcheck_ping_url: str = ""          # e.g. https://hc-ping.com/<uuid>

    # --- cost control ---
    daily_budget_usd: float = Field(default=3.0, gt=0)
    per_user_daily_budget_usd: float = Field(default=1.0, gt=0)

    @field_validator("database_url")
    @classmethod
    def use_psycopg3_driver(cls, value: str) -> str:
        """Hosts hand out postgres:// URLs; SQLAlchemy + psycopg 3 needs postgresql+psycopg://."""
        if value.startswith("postgres://"):
            value = "postgresql://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    """Build settings once and reuse them everywhere."""
    return Settings()
```

Use it:

```python
from organizer.config import get_settings

settings = get_settings()
client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())
```

Things to notice:

| Feature | Why it matters |
|---|---|
| Field names map to env vars case-insensitively | `anthropic_api_key` ← `ANTHROPIC_API_KEY` |
| `SecretStr` | `print(settings)` shows `**********`, so secrets don't leak into logs or tracebacks. Call `.get_secret_value()` only where you need the real value |
| `Literal["dev", "staging", "prod"]` | `ENVIRONMENT=production` (a typo) fails at startup instead of silently acting like dev |
| `Field(ge=..., le=...)` | Rejects nonsense like `LLM_MAX_TOKENS=1000000` |
| `validation_alias=AliasChoices(...)` | Reads `RELEASE`, or falls back to Render's automatic `RENDER_GIT_COMMIT` |
| `@lru_cache` | Settings are read once, not on every request |
| The validator | Fixes the classic "postgres:// vs postgresql+psycopg://" driver mismatch |

**Code — `.env.example` (commit this)**

```text
ENVIRONMENT=dev
LOG_JSON=false
TIMEZONE=Europe/London
DATABASE_URL=postgresql+psycopg://organizer:change-me@db:5432/organizer
POSTGRES_PASSWORD=change-me
ANTHROPIC_API_KEY=your-anthropic-key
LLM_MODEL=claude-sonnet-4-5
TELEGRAM_BOT_TOKEN=your-dev-bot-token
TELEGRAM_ADMIN_CHAT_ID=
SENTRY_DSN=
HEALTHCHECK_PING_URL=
DAILY_BUDGET_USD=3
PER_USER_DAILY_BUDGET_USD=1
```

**Code — settings in tests**

```python
# tests/conftest.py
import pytest
from organizer.config import get_settings


@pytest.fixture(autouse=True)
def test_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-not-a-real-token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    get_settings.cache_clear()     # forget settings cached by a previous test
    yield
    get_settings.cache_clear()
```

**Where config lives in each environment**

| Environment | Where values come from |
|---|---|
| dev | `.env` on your laptop |
| CI | `env:` in the workflow (fake values) + GitHub Actions secrets for anything real |
| Render | Environment tab of each service / Blueprint `envVars` |
| VPS | `/srv/organizer/.env`, mode `600`, owned by `deploy` |

**Common mistakes**
- Calling `Settings()` at import time in many modules: tests can't override values and every module builds its own
  copy. Use `get_settings()`.
- Logging `settings.model_dump()` — fine for `SecretStr` fields, but any secret you typed as plain `str` leaks.
  Type every secret as `SecretStr`.
- Booleans: `LOG_JSON=0`, `false`, `no` and `off` are all `False`. An empty string is an error, not `False`.
- Committing `.env` "just once". If a key ever reaches Git history, rotate it.

**Exercises**
1. Replace every `os.getenv` in your project with `get_settings()`. Start the app with `ANTHROPIC_API_KEY` missing
   and read the error message.
2. Add a `briefing_hour: int` setting (0–23, default 7) and use it in the scheduler. Try `BRIEFING_HOUR=25`.
3. Write a test proving `postgres://u:p@h/db` is turned into `postgresql+psycopg://u:p@h/db`.

**Check yourself**
- Which wins: a real environment variable or a value in `.env`?
- What does `SecretStr` protect you from, and what doesn't it protect you from?
- Why is crashing at startup better than failing later?

---

## Part B: Hosting

### Lesson 7: Choosing a Host

**Concepts**

There are three broad kinds of hosting:

| Kind | You manage | They manage | Examples |
|---|---|---|---|
| **PaaS** (Platform as a Service) | Your code / Dockerfile, env vars | Servers, OS, HTTPS, deploys, logs, scaling | Render, Railway, Fly.io, Heroku |
| **VPS** (Virtual Private Server) | Everything above the hardware: OS updates, firewall, Docker, proxy, backups | Hardware, network | Hetzner, DigitalOcean, Linode/Akamai, Vultr, AWS Lightsail |
| **Cloud (IaaS + managed services)** | Architecture, IAM, networking, many services | Pretty much any building block you want | AWS, Google Cloud, Azure |

**Comparison for this project** (an API + a Telegram bot + a scheduler worker + Postgres, low traffic)

Prices are rough, change often, and depend on region — always check the provider's pricing page before deciding.

| Option | Rough monthly cost for this project | Pros | Cons | Pick it when |
|---|---|---|---|---|
| **Render** | ~$7 per always-on service + database from ~$6; ≈ $25–35 for api + bot + worker + Postgres | Git-push deploys, free HTTPS, managed Postgres with backups, Blueprints (infra as YAML), preview environments | Free web services sleep after ~15 min idle; background workers and disks are paid; per-service pricing adds up; 512 MB on the smallest plan can be tight with Chroma | You want the least ops work and don't mind paying per service |
| **Railway** | Usage-based; small always-on apps often ~$5–20 | Very fast setup, nice UI, Postgres in one click, pay for what you use | Usage billing is less predictable; fewer knobs | Prototypes and small always-on projects |
| **Fly.io** | Pay-as-you-go; small machines a few dollars each, plus volumes | Runs your Docker image close to users, process groups (api/bot/worker from one app), volumes, good CLI | More concepts (machines, volumes, regions); you manage more yourself; no permanent free tier for new accounts | You like CLIs and want multi-region later |
| **VPS** (Hetzner, DigitalOcean) | ~€4–15 for a 2–4 GB machine running everything | Cheapest by far, full control, everything on one box, predictable bill | You are the ops team: updates, firewall, backups, monitoring, disk space | You want to learn, keep costs tiny, and are OK being on call for yourself |
| **AWS / GCP / Azure** | Anywhere from a few dollars (Lightsail, Cloud Run with low traffic) to a lot (ECS + RDS + load balancer ≈ $50+) | Every service imaginable, enterprise features, credits for startups | Steep learning curve, easy to misconfigure, surprise bills | Your job uses it, you need specific services, or you have credits |

**How to decide**

- **Learning + cheapest:** VPS with Docker Compose + Caddy (Lesson 9). One machine runs everything for the price of
  a sandwich.
- **Least maintenance:** Render (Lesson 8). You never SSH into anything.
- **Either way:** the app is the same Docker image. Switching hosts later is mostly config.

**Things that matter for an AI assistant specifically**

| Requirement | Why | Watch out for |
|---|---|---|
| **Always-on processes** | The Telegram bot long-polls and the scheduler must be awake at 7:30 | Free tiers that sleep when idle |
| **Long-lived HTTP responses** | `/chat` streams tokens for 10–60 s | Proxies/platforms with short request timeouts or response buffering |
| **Persistent disk** (if you keep Chroma embedded) | The vector store is files on disk | Platforms with ephemeral disks; disks often limit you to one instance |
| **Outbound internet** | LLM API, Gmail, Slack, Telegram | Very locked-down corporate clouds |
| **Memory** | Chroma's default embedding model + three Python processes | 512 MB plans can OOM; 1–2 GB per service or a 4 GB VPS is comfortable |

**Common mistakes**
- Choosing a free tier that sleeps and wondering why the morning briefing never arrived.
- Picking AWS for a first deployment and spending a week on IAM and VPCs instead of shipping.
- Forgetting to add the database and backup storage to the cost estimate.

**Exercises**
1. Fill in the comparison table with **today's** prices for the region nearest you, for exactly this project.
2. Estimate your monthly LLM spend (messages per day × average tokens × price) and compare it with hosting cost.
   Which one dominates?

**Check yourself**
- What do you trade when you move from a PaaS to a VPS?
- Why is a sleeping free tier a problem for a Telegram bot and a scheduler?

---

### Lesson 8: Deploying to Render (PaaS Walkthrough)

**Concepts**

Render builds your Dockerfile, runs the container, gives it an HTTPS URL, and redeploys on every push to your
chosen branch (or when CI calls a **deploy hook**). A **Blueprint** (`render.yaml` in your repo) describes all
services and the database as code, so you can recreate everything with one click.

The mapping for the Work Organizer:

| Your process | Render service type | Notes |
|---|---|---|
| `api` | **Web Service** (Docker) | Gets a public URL and HTTPS; health check path |
| `bot` | **Background Worker** (Docker) | No public URL; runs `python -m organizer.bot.main` |
| `worker` | **Background Worker** (Docker) | Runs the scheduler; **exactly one instance** |
| Postgres | **Render Postgres** | Managed, with automatic backups on paid plans |

To save money you can merge `bot` and `worker` into one Background Worker process later. Start separate; it's
easier to debug.

**Code — `render.yaml`**

```yaml
envVarGroups:
  - name: organizer-shared
    envVars:
      - key: ENVIRONMENT
        value: prod
      - key: LOG_JSON
        value: "true"
      - key: TIMEZONE
        value: Europe/London
      - key: LLM_MODEL
        value: claude-sonnet-4-5

services:
  - type: web
    name: organizer-api
    runtime: docker
    plan: starter
    region: frankfurt
    dockerfilePath: ./Dockerfile
    healthCheckPath: /readyz
    preDeployCommand: alembic upgrade head
    autoDeploy: false            # CI triggers deploys after tests pass (Lesson 13)
    disk:
      name: organizer-data
      mountPath: /app/data
      sizeGB: 1
    envVars:
      - key: PORT
        value: "8000"
      - key: DATABASE_URL
        fromDatabase:
          name: organizer-db
          property: connectionString
      - fromGroup: organizer-shared
      - key: ANTHROPIC_API_KEY
        sync: false              # Render asks you for the value; it's never stored in Git
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: SENTRY_DSN
        sync: false

  - type: worker
    name: organizer-bot
    runtime: docker
    plan: starter
    region: frankfurt
    dockerfilePath: ./Dockerfile
    dockerCommand: python -m organizer.bot.main
    autoDeploy: false
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: organizer-db
          property: connectionString
      - fromGroup: organizer-shared
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: SENTRY_DSN
        sync: false

  - type: worker
    name: organizer-scheduler
    runtime: docker
    plan: starter
    region: frankfurt
    dockerfilePath: ./Dockerfile
    dockerCommand: python -m organizer.worker.main
    autoDeploy: false
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: organizer-db
          property: connectionString
      - fromGroup: organizer-shared
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: TELEGRAM_ADMIN_CHAT_ID
        sync: false
      - key: SENTRY_DSN
        sync: false
      - key: HEALTHCHECK_PING_URL
        sync: false

databases:
  - name: organizer-db
    databaseName: organizer
    user: organizer
    plan: basic-256mb
    region: frankfurt
```

Plan names, regions and limits change; check Render's Blueprint reference if a field is rejected.

Key points:

| Field | What it does |
|---|---|
| `runtime: docker` | Build from your Dockerfile (Render runs the image's `CMD`, or `dockerCommand` if set) |
| `PORT=8000` | Render routes traffic to the port in `PORT`; ours matches the Dockerfile's `--port 8000` |
| `healthCheckPath` | Render won't switch traffic to a new deploy until this returns 2xx |
| `preDeployCommand` | Runs once per deploy, after the build and before the new version starts — perfect for migrations |
| `fromDatabase` | Injects the connection string; the settings validator converts it for psycopg 3 |
| `sync: false` | You type the secret in the dashboard during setup; it never goes in the repo |
| `disk` | Persistent storage for Chroma. A service with a disk can only run **one instance**, and deploys have a brief gap because the old instance must stop before the new one mounts the disk |
| `RENDER_GIT_COMMIT` | Set automatically; our `release` setting picks it up for Sentry |

**Code — step by step**

1. Commit `render.yaml`, `Dockerfile` and `.dockerignore` and push to GitHub.
2. In the Render dashboard: **New → Blueprint**, connect your GitHub repo, pick the branch.
3. Render shows the resources it will create and asks for every `sync: false` value. Paste them. Use your
   **production** Telegram bot token here, and stop any local bot using that token.
4. Click **Apply**. Watch the build logs of `organizer-api`. The first build takes a few minutes.
5. When it's live, test it:

```bash
curl https://organizer-api.onrender.com/healthz
```

6. Send your Telegram bot a message. Check the `organizer-bot` logs in the dashboard.
7. In **Settings → Deploy Hook** of each service, copy the deploy hook URL. You'll store these as GitHub secrets
   in Lesson 13. A deploy hook URL is a secret: anyone with it can trigger deploys.

**Run a one-off command** (e.g. inspect the database) from the service's **Shell** tab in the dashboard, or
connect with `psql` using the external connection string from the database's page (restrict access with its IP
allow list).

**Rollbacks on Render:** the **Events** tab lists previous deploys; **Rollback** redeploys an older build in
seconds. Remember that the database doesn't roll back with it (Lesson 19).

**A quick look at Fly.io** (same idea, CLI-driven): `fly launch --no-deploy` creates a `fly.toml`,
`fly secrets set NAME=value` stores secrets, and `fly deploy` builds and ships the image. In `fly.toml` you define `[processes]` (e.g. `app`, `bot`, `worker`) that all run from the same image, mount a
volume with `[mounts]`, and add an `[http_service]` with checks for the API.

**Common mistakes**
- Leaving `autoDeploy` on *and* deploying from CI — every merge deploys twice, and sometimes before tests finish.
- Running the bot on a free web service: it isn't a web server, so Render marks it unhealthy (and free web services
  sleep anyway). Bots and schedulers are Background Workers.
- Scaling the scheduler service to 2 instances → two briefings.
- Forgetting the database's region must match the services' region (cross-region latency on every query).

**Exercises**
1. Deploy the Work Organizer to Render with the Blueprint. Send a Telegram message and find it in the logs.
2. Break the health check on purpose (make `/readyz` return 500), push, and watch Render refuse to switch to the
   new deploy. Fix it.
3. Use the **Rollback** button to go back one deploy. Then roll forward again.

**Check yourself**
- Why is the bot a Background Worker and not a Web Service?
- What runs in `preDeployCommand` and when?
- What's the trade-off of attaching a disk to a service?

---

### Lesson 9: Deploying to a VPS with Docker and Caddy

**Concepts**

On a VPS you run the same Compose stack you ran locally, plus **Caddy**, a web server that automatically obtains
and renews free HTTPS certificates from Let's Encrypt. Your images are built by CI and stored in **GitHub Container
Registry** (`ghcr.io`); the server only pulls and runs them. Nothing is built on the server.

```
GitHub Actions ──build & push──▶ ghcr.io/you/work-organizer:sha-abc123
                                          │ docker compose pull
                                          ▼
┌──────────────────────── VPS (Ubuntu 24.04) ────────────────────────┐
│ caddy :80/:443 ──▶ api :8000        bot        worker              │
│                       └──────────┬────┴─────────┘                  │
│                                  ▼                                 │
│                              db (Postgres, no public port)         │
│ volumes: pg_data, app_data (Chroma), caddy_data (certificates)     │
└────────────────────────────────────────────────────────────────────┘
```

**Step 1 — create and harden the server**

Create an Ubuntu 24.04 LTS server with **2 vCPU / 4 GB RAM** (Chroma and three Python processes fit comfortably),
add your SSH public key, then follow Lesson 2: `deploy` user, SSH hardening, ufw allowing only SSH, 80 and 443,
unattended upgrades.

**Step 2 — install Docker**

The official convenience script installs Docker Engine and the Compose plugin:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
```

```bash
sudo sh get-docker.sh
```

Let `deploy` run Docker without sudo, then log out and back in:

```bash
sudo usermod -aG docker deploy
```

```bash
docker compose version
```

> Membership of the `docker` group is effectively root access. Only give it to accounts you'd trust with root.

**Step 3 — point your domain at the server**

Create an `A` record `organizer.example.com → <server IP>` (Lesson 10) and wait until it resolves:

```bash
dig +short organizer.example.com
```

Caddy needs this **before** it starts, or the certificate request fails.

**Step 4 — create the app folder**

```bash
sudo mkdir -p /srv/organizer/backups
```

```bash
sudo chown -R deploy:deploy /srv/organizer
```

**Step 5 — `/srv/organizer/compose.prod.yaml`**

```yaml
name: organizer

x-logging: &logging
  driver: json-file
  options:
    max-size: "10m"          # rotate logs so they can't fill the disk
    max-file: "5"

x-app: &app
  image: ${IMAGE:?set IMAGE in .env}:${IMAGE_TAG:?set IMAGE_TAG in .env}
  env_file: .env
  init: true
  restart: unless-stopped
  logging: *logging
  depends_on:
    db:
      condition: service_healthy

services:
  db:
    image: postgres:17
    restart: unless-stopped
    logging: *logging
    environment:
      POSTGRES_USER: organizer
      POSTGRES_DB: organizer
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
    volumes:
      - pg_data:/var/lib/postgresql/data
    # No "ports:" — only containers in this project can reach the database.
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U organizer -d organizer"]
      interval: 5s
      timeout: 5s
      retries: 10

  api:
    <<: *app
    volumes:
      - app_data:/app/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3

  bot:
    <<: *app
    command: ["python", "-m", "organizer.bot.main"]

  worker:
    <<: *app
    command: ["python", "-m", "organizer.worker.main"]

  caddy:
    image: caddy:2
    restart: unless-stopped
    logging: *logging
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"        # HTTP/3
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data     # certificates live here — never delete this volume
      - caddy_config:/config
    depends_on:
      - api

volumes:
  pg_data:
  app_data:
  caddy_data:
  caddy_config:
```

Only Caddy publishes ports. The API is reachable only through Caddy; Postgres only from other containers.

**Step 6 — `/srv/organizer/Caddyfile`**

```caddyfile
{
	email you@example.com
}

organizer.example.com {
	@internal path /metrics*
	respond @internal 404

	reverse_proxy api:8000
}
```

That's the whole HTTPS setup. Caddy sees a domain name, gets a certificate for it, redirects HTTP to HTTPS, renews
the certificate before it expires, and forwards requests to the `api` service. It also passes streamed responses
(like `/chat`'s server-sent events) through without buffering. The `@internal` matcher hides the metrics endpoint
from the internet (Lesson 16).

**Step 7 — `/srv/organizer/.env`**

```text
IMAGE=ghcr.io/your-github-username/work-organizer
IMAGE_TAG=manual-1
ENVIRONMENT=prod
LOG_JSON=true
POSTGRES_PASSWORD=<long random string>
DATABASE_URL=postgresql+psycopg://organizer:<same long random string>@db:5432/organizer
ANTHROPIC_API_KEY=<production key>
TELEGRAM_BOT_TOKEN=<production bot token>
TELEGRAM_ADMIN_CHAT_ID=<your chat id>
SENTRY_DSN=<from Sentry>
HEALTHCHECK_PING_URL=<from Healthchecks.io>
```

```bash
chmod 600 /srv/organizer/.env
```

`IMAGE` must match what CI pushes in Lesson 13: `ghcr.io/<owner>/<repo>`, all **lowercase** (GHCR rejects
capitals, so `Work-Organizer-` becomes `work-organizer-`).

**Step 8 — let the server pull private images**

Create a GitHub **personal access token (classic)** with only the `read:packages` scope, then on the server:

```bash
docker login ghcr.io -u your-github-username
```

Paste the token as the password. (If you make the package public, you can skip this.)

**Step 9 — the deploy script `/srv/organizer/deploy.sh`**

```bash
#!/usr/bin/env bash
# Usage: ./deploy.sh <image-tag>        e.g. ./deploy.sh sha-3f2a1c9e...
# Rollback: SKIP_MIGRATIONS=1 ./deploy.sh "$(cat .previous_tag)"
set -euo pipefail

cd /srv/organizer
COMPOSE="docker compose -f compose.prod.yaml"
HEALTH_URL="https://organizer.example.com/healthz"

NEW_TAG="${1:?usage: deploy.sh <image-tag>}"
PREV_TAG="$(grep -E '^IMAGE_TAG=' .env | cut -d= -f2-)"
echo "Deploying ${NEW_TAG} (currently ${PREV_TAG})"

# A shell variable overrides .env for Compose interpolation, so .env is only
# changed once we know the new version is healthy.
export IMAGE_TAG="${NEW_TAG}"

$COMPOSE pull api bot worker

if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
  $COMPOSE run --rm api alembic upgrade head
fi

$COMPOSE up -d --remove-orphans

for attempt in $(seq 1 30); do
  if curl -fsS --max-time 3 "${HEALTH_URL}" > /dev/null; then
    sed -i "s|^IMAGE_TAG=.*|IMAGE_TAG=${NEW_TAG}|" .env
    echo "${PREV_TAG}" > .previous_tag
    docker image prune -f > /dev/null
    echo "Deploy OK: ${NEW_TAG}"
    exit 0
  fi
  sleep 2
done

echo "Health check failed after 60s; rolling back to ${PREV_TAG}" >&2
export IMAGE_TAG="${PREV_TAG}"
$COMPOSE up -d --remove-orphans
exit 1
```

```bash
chmod +x /srv/organizer/deploy.sh
```

**Step 10 — the first deploy (by hand)**

Until CI exists (Lesson 13), build and push from your laptop. If your laptop is an Apple Silicon Mac, you **must**
build for the server's CPU architecture:

```bash
docker buildx build --platform linux/amd64 -t ghcr.io/your-github-username/work-organizer:manual-1 --push .
```

(Log in to GHCR on your laptop first with `docker login ghcr.io` and a token that has `write:packages`.) Then on
the server:

```bash
cd /srv/organizer
```

```bash
./deploy.sh manual-1
```

```bash
docker compose -f compose.prod.yaml ps
```

```bash
docker compose -f compose.prod.yaml logs -f caddy
```

You should see Caddy obtaining a certificate. Then:

```bash
curl -i https://organizer.example.com/healthz
```

**Step 11 — survive a reboot**

```bash
sudo reboot
```

After a minute, SSH back in and run `docker compose -f compose.prod.yaml ps`. Everything with
`restart: unless-stopped` should be running again, because the Docker service starts at boot.

**Common mistakes**
- Starting Caddy before DNS points at the server; Let's Encrypt can't verify the domain. Fix DNS, then
  `docker compose -f compose.prod.yaml restart caddy`.
- Repeatedly deleting `caddy_data` while debugging and hitting Let's Encrypt's rate limits. Keep the volume.
- Building on an M-series Mac without `--platform linux/amd64`: the container fails with `exec format error`.
- No log rotation: Docker's default JSON logs grow forever and fill the disk in a few months.
- Forgetting that `.env` on the server is the source of truth for production secrets — back it up somewhere safe
  (a password manager), not in Git.

**Exercises**
1. Deploy the full stack to a VPS and reach `https://<your-domain>/healthz` from your phone on mobile data.
2. Deploy a broken image (e.g. one whose `/healthz` returns 500) and watch `deploy.sh` roll back automatically.
3. Run `sudo ss -tlnp` on the server. Confirm that only 22, 80 and 443 are listening on public addresses.
4. Reboot the server and confirm the bot answers within two minutes without you touching anything.

**Check yourself**
- Why doesn't the server build images itself?
- What would happen if you added `ports: ["5432:5432"]` to the `db` service on this server?
- What does Caddy do for you that you'd otherwise have to do by hand?

---

### Lesson 10: Domains, DNS and HTTPS

**Concepts**

**DNS** is the internet's phone book: it turns `organizer.example.com` into an IP address. You buy a domain from a
**registrar**, and edit its records at a **DNS provider** (often the registrar itself, or Cloudflare).

| Record | Points a name at… | Example |
|---|---|---|
| `A` | An IPv4 address | `organizer → 203.0.113.10` |
| `AAAA` | An IPv6 address | `organizer → 2001:db8::10` |
| `CNAME` | Another name (an alias) | `organizer → organizer-api.onrender.com` |
| `TXT` | Arbitrary text — used for verification, SPF, DKIM | `"google-site-verification=..."` |
| `MX` | A mail server | For email on your domain |
| `CAA` | Which certificate authorities may issue certs | `0 issue "letsencrypt.org"` |

- **TTL** (time to live) is how long resolvers cache a record. Set it to 300 seconds (5 min) while you're setting
  things up; raise it later.
- The **apex** (bare) domain `example.com` can't be a `CNAME` at most DNS providers. Use a subdomain like
  `organizer.example.com` for your app, or a provider that supports `ALIAS`/`ANAME`/CNAME flattening.
- Changes usually appear within minutes but can take up to the old TTL to reach everyone ("propagation").

**HTTPS and certificates**

HTTPS encrypts traffic between the client and your server and proves the server really owns the domain, using a
**TLS certificate** signed by a trusted certificate authority. **Let's Encrypt** issues free 90-day certificates
through the **ACME** protocol; Caddy, Render and Fly all speak ACME and renew automatically.

For the common **HTTP-01** challenge, the CA connects to `http://your-domain/.well-known/acme-challenge/...` on
**port 80**. So for automatic certificates you need:
1. DNS pointing at your server.
2. Port 80 open (in the firewall and the provider's cloud firewall, if it has one).
3. Port 443 open for the HTTPS traffic itself.

Why HTTPS is not optional for this project:
- Your `/chat` requests carry personal data and (often) an auth token.
- Telegram **webhooks** only accept HTTPS URLs.
- Google OAuth redirect URIs must be HTTPS in production.
- Browsers mark plain HTTP sites as "Not secure".

**Code — check DNS and certificates**

```bash
dig +short organizer.example.com
```

```bash
dig organizer.example.com CNAME +short
```

```bash
curl -I https://organizer.example.com/healthz
```

```bash
curl -vI https://organizer.example.com 2>&1 | grep -Ei 'subject|issuer|expire'
```

**Code — custom domain on Render**

1. Service → **Settings → Custom Domains → Add** `organizer.example.com`.
2. At your DNS provider, add `CNAME organizer → organizer-api.onrender.com`.
3. Click **Verify**. Render issues the certificate automatically.

**Code — Cloudflare in front (optional)**

If your DNS is on Cloudflare with the orange-cloud **proxy** enabled, Cloudflare terminates HTTPS first and then
connects to your server. Set SSL/TLS mode to **Full (strict)** so the Cloudflare → server hop is also verified.
While you first set up Caddy, use **DNS only** (grey cloud) so Caddy can complete its challenge directly.

**Code — after HTTPS works: HSTS**

Add this inside your site block in the Caddyfile to tell browsers to always use HTTPS:

```caddyfile
header Strict-Transport-Security "max-age=31536000; includeSubDomains"
```

Only add it once you're sure HTTPS works for every subdomain covered — browsers will refuse plain HTTP for a year.

**Common mistakes**
- Typos like an `A` record for `organiser` when the Caddyfile says `organizer`.
- A cloud firewall at the provider (separate from ufw) blocking port 80, so certificate issuance fails.
- Setting a 24-hour TTL before you're sure the IP is right.
- Pointing the apex domain at a CNAME and breaking email (MX) records.

**Exercises**
1. Buy (or reuse) a domain, create `organizer.<yourdomain>` and point it at your VPS or Render service.
2. Use `dig` to watch the record appear, then confirm the certificate issuer is Let's Encrypt (or Google Trust
   Services, which Render and others also use).
3. Switch your Telegram bot from polling to a webhook at `https://organizer.<yourdomain>/telegram/webhook` with a
   `secret_token`, and verify the header in your FastAPI route. (Optional — polling is fine for one user.)

**Check yourself**
- When would you use a `CNAME` instead of an `A` record?
- Why must port 80 be open even though your app only serves HTTPS?
- What does a TTL of 300 mean?

---

## Part C: Running It Properly

### Lesson 11: Background Jobs and Schedulers in Production

**Concepts**

In Section 5 you probably started APScheduler inside the FastAPI app. That works on a laptop and breaks in
production, because the number of web processes is not always one:

| Situation | Result if the scheduler lives in the web process |
|---|---|
| `uvicorn --workers 4` | 4 schedulers → 4 briefings every morning |
| Host scales the API to 2 instances | 2 briefings |
| Rolling deploy: old and new versions overlap for a minute at 7:30 | Briefing sent twice (or zero times) |
| Your laptop runs the app against the prod database | Your laptop sends briefings too |

**The fix has three layers:**

1. **A separate worker process** that only runs scheduled jobs, deployed with exactly **one** replica. The API can
   then scale freely.
2. **A distributed lock** so that even if two workers start by accident, only one runs jobs. With Postgres, an
   **advisory lock** is perfect: `pg_try_advisory_lock(id)` returns `true` for exactly one connection.
3. **Idempotent jobs**: before sending today's briefing to a user, record `(user_id, date)` in a table with a
   unique constraint. A second attempt hits the constraint and skips.

**Other production rules for jobs**

- **Time zones:** give the scheduler an explicit timezone. Servers run in UTC.
- **Misfires:** if the worker was down at 7:30 (e.g. a deploy), `misfire_grace_time=3600` still runs the job if it
  restarts within an hour; `coalesce=True` runs it once, not once per missed slot.
- **`max_instances=1`:** a slow job doesn't overlap with its next run.
- **Errors:** a job that raises must be logged and sent to Sentry, not swallowed.
- **Heartbeats:** after each successful run, ping a monitor (Lesson 15) so you get an alert when the briefing
  *didn't* happen — silent failures are the dangerous ones.
- **Slow work doesn't belong in a request.** If a user asks "summarise my last 200 emails", reply "working on it"
  and do it in the background. For a single user, `asyncio.create_task` or the worker is fine; at larger scale use
  a queue:

| Tool | Broker | Notes |
|---|---|---|
| **arq** | Redis | Async-native, small, fits FastAPI well |
| **RQ** | Redis | Simple, sync |
| **Dramatiq** | Redis / RabbitMQ | Reliable, simple API |
| **Celery** | Redis / RabbitMQ | The heavyweight standard; many features, more config |

**Code — `organizer/worker/locks.py`**

```python
import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, text

log = logging.getLogger(__name__)


@contextmanager
def singleton_lock(engine: Engine, lock_id: int) -> Iterator[bool]:
    """Yield True if this process holds the Postgres advisory lock `lock_id`.

    The lock belongs to one database session, so we keep a dedicated connection
    open for as long as we hold it. On SQLite (dev) we always "get" the lock.
    """
    if engine.dialect.name != "postgresql":
        yield True
        return

    conn = engine.connect()
    got = False
    try:
        got = bool(conn.execute(text("SELECT pg_try_advisory_lock(:id)"), {"id": lock_id}).scalar())
        conn.commit()          # don't sit "idle in transaction" for days
        yield got
    finally:
        if got:
            conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": lock_id})
            conn.commit()
        conn.close()           # pooled connections keep session locks, so unlock explicitly first
```

**Code — `organizer/worker/main.py`**

```python
import logging
import signal
import sys
import time

import httpx
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from organizer.config import get_settings
from organizer.db import engine
from organizer.observability import setup_logging, setup_sentry
from organizer.worker.jobs import send_cost_report, send_daily_briefings
from organizer.worker.locks import singleton_lock

log = logging.getLogger("organizer.worker")
SCHEDULER_LOCK_ID = 74_200_001     # any constant 64-bit integer, unique to this job runner


def ping_healthcheck(suffix: str = "") -> None:
    url = get_settings().healthcheck_ping_url
    if url:
        try:
            httpx.get(url + suffix, timeout=10)
        except httpx.HTTPError:
            log.warning("healthcheck_ping_failed")


def run_briefings() -> None:
    try:
        send_daily_briefings()
        ping_healthcheck()
    except Exception:
        log.exception("daily_briefing_failed")    # Sentry captures logged exceptions
        ping_healthcheck("/fail")
        raise


def main() -> None:
    settings = get_settings()
    setup_logging(settings)
    setup_sentry(settings, component="worker")
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

    while True:
        with singleton_lock(engine, SCHEDULER_LOCK_ID) as got_lock:
            if not got_lock:
                log.warning("scheduler_lock_held_elsewhere; standing by")
                time.sleep(30)
                continue

            log.info("scheduler_starting", extra={"timezone": settings.timezone})
            scheduler = BlockingScheduler(timezone=settings.timezone)
            common = {"max_instances": 1, "coalesce": True, "misfire_grace_time": 3600}
            scheduler.add_job(run_briefings, CronTrigger(hour=7, minute=30),
                              id="daily_briefing", **common)
            scheduler.add_job(send_cost_report, CronTrigger(hour=8, minute=0),
                              id="daily_cost_report", **common)
            scheduler.start()          # blocks until shutdown / SIGTERM
            return


if __name__ == "__main__":
    main()
```

**Code — idempotent briefing (in `organizer/worker/jobs.py`)**

```python
from datetime import date

from sqlalchemy import Date, Integer, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from organizer.db import SessionLocal
from organizer.models import Base


class BriefingSent(Base):
    __tablename__ = "briefings_sent"
    __table_args__ = (UniqueConstraint("user_id", "day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    day: Mapped[date] = mapped_column(Date)


def claim_briefing(user_id: int, day: date) -> bool:
    """Return True if we are the first to claim today's briefing for this user."""
    with SessionLocal() as session:
        session.add(BriefingSent(user_id=user_id, day=day))
        try:
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False
```

In `send_daily_briefings()`, call `claim_briefing(user.id, today)` before generating each briefing and skip the
user if it returns `False`. (Put the model in `organizer/models.py` in your real project so Alembic sees it.)

**Common mistakes**
- `scheduler.start()` inside FastAPI's lifespan *and* in the worker — two schedulers.
- Releasing an advisory lock by closing a pooled connection. The connection goes back to the pool still holding
  the lock. Unlock explicitly (as above) or use a non-pooled connection.
- Cron times in UTC when you meant local time — the briefing arrives at 6:30 or 8:30 after a daylight-saving change.
- Swallowing exceptions inside jobs, so a broken Gmail token fails silently for two weeks.

**Exercises**
1. Move the scheduler out of the API into `organizer/worker/main.py`. Confirm the API has no APScheduler import left.
2. Run two worker containers at once (`docker compose up -d --scale worker=2`) and show from the logs that only one
   runs jobs. Stop that one and watch the standby take over within 30 seconds.
3. Call `send_daily_briefings()` twice in a row by hand and confirm users only get one message.

**Check yourself**
- Name three ways a scheduler can end up running twice.
- What do `coalesce` and `misfire_grace_time` do?
- Why is idempotency still needed when you already have a lock?

---

### Lesson 12: Databases in Production

**Concepts**

**SQLite vs Postgres.** SQLite is excellent for one process on one machine. Once you have three processes (api,
bot, worker), possibly on different machines, you want a database **server**: Postgres. Chroma can stay embedded
in the API process on a volume (only the API should open it), or move to a Chroma server or `pgvector` later.

**Managed vs self-hosted Postgres**

| | Managed (Render Postgres, Neon, Supabase, AWS RDS, DigitalOcean) | Self-hosted (the `db` container on your VPS) |
|---|---|---|
| Cost | ~$6–25+/month for small instances | Free (uses your VPS) |
| Backups | Automatic, point-in-time restore on many plans | **You** set them up (Lesson 19) |
| Upgrades, patches | Done for you | You do them |
| Failover | Available on higher plans | None |
| Best for | Anything you can't afford to lose | Learning, small personal projects with good backups |

**Migrations.** The database schema must change in step with the code. **Alembic** stores each change as a
numbered migration file in Git and records in the database which ones have run.

**Migrations on deploy.** Run `alembic upgrade head` **once per deploy, before the new code starts** — as Render's
`preDeployCommand`, or a step in `deploy.sh`. Never in the app's startup code: with three processes starting at
once, three migrations would race each other.

**Safe migrations: expand, then contract.** During a deploy (and after a rollback), old code runs against the new
schema. Make every migration backward-compatible:

| Change | Safe way |
|---|---|
| Add a column | Add it **nullable** (or with a default). Deploy code that uses it. |
| Rename a column | Add the new column → write to both → backfill → switch reads → drop the old column in a **later** release |
| Drop a column | First deploy code that no longer uses it; drop it in the next release |
| Add an index on a big table | `CREATE INDEX CONCURRENTLY` (in Alembic: `op.create_index(..., postgresql_concurrently=True)` inside an `autocommit_block()`) |

**Code — set up Alembic**

```bash
alembic init migrations
```

Edit `migrations/env.py` so it uses your settings and models:

```python
# migrations/env.py (near the top, after "config = context.config")
from organizer.config import get_settings
from organizer.models import Base

# "%" must be escaped for Alembic's config parser
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
target_metadata = Base.metadata
```

Create and apply a migration:

```bash
alembic revision --autogenerate -m "add briefings_sent and llm_calls"
```

```bash
alembic upgrade head
```

```bash
alembic current
```

**Always read the generated file** before committing it. Autogenerate misses some things (renames look like a drop
plus an add — which deletes data) and sometimes adds things you didn't intend.

**Code — engine settings for production (`organizer/db.py`)**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from organizer.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,     # detect connections the server closed (restarts, idle timeouts)
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,      # recycle connections every 30 minutes
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
```

Watch the connection count: (processes × (pool_size + max_overflow)) must stay below the database's
`max_connections` — small managed plans often allow only 50–100.

**Code — moving your SQLite data to Postgres (one time)**

The simplest path for a personal project: create the schema in Postgres with `alembic upgrade head`, then copy rows
table by table with a small script:

```python
# scripts/sqlite_to_postgres.py
from sqlalchemy import create_engine, select

from organizer.models import Base

src = create_engine("sqlite:///./data/organizer.db")
dst = create_engine("postgresql+psycopg://organizer:change-me@localhost:5432/organizer")

with src.connect() as s, dst.begin() as d:
    for table in Base.metadata.sorted_tables:      # parents before children
        rows = [dict(r._mapping) for r in s.execute(select(table))]
        if rows:
            d.execute(table.insert(), rows)
        print(f"{table.name}: {len(rows)} rows")
```

Afterwards, reset each table's ID sequence (otherwise the next insert collides with copied IDs), for example:
`SELECT setval(pg_get_serial_sequence('tasks', 'id'), (SELECT MAX(id) FROM tasks));`

**Common mistakes**
- Running migrations from the app's startup code in several processes at once.
- Renaming a column in one step and breaking the still-running old version (and any rollback).
- Forgetting `pool_pre_ping` and getting `server closed the connection unexpectedly` after the DB restarts.
- Using a free managed database that's deleted after its trial period — read the fine print.

**Exercises**
1. Add Alembic to your project and generate the initial migration from your models. Run it against the Compose
   Postgres.
2. Add a nullable `timezone` column to your users table with a migration, deploy it, then write a second migration
   that backfills a default value.
3. Copy your existing SQLite data into Postgres with the script above and verify row counts match.

**Check yourself**
- Why must migrations be backward-compatible with the previous release?
- When exactly should `alembic upgrade head` run during a deploy?
- What does `pool_pre_ping` protect against?

---

### Lesson 13: CI/CD with GitHub Actions

**Concepts**

- **CI (continuous integration):** on every push, a fresh machine installs your project and runs the linters and
  tests. Broken code is caught before it's merged.
- **CD (continuous deployment):** when code lands on `main` and CI passes, build the image once, tag it with the
  commit SHA, push it to a registry, and deploy exactly that image.
- **GitHub Actions** runs **workflows** (YAML in `.github/workflows/`), made of **jobs** (each on a fresh VM), made
  of **steps** (shell commands or reusable **actions**).
- **Secrets** (Settings → Secrets and variables → Actions) are encrypted, injected only into the steps that
  reference them, and masked as `***` in logs. Secrets are **not** passed to workflows triggered by pull requests
  from forks.
- **Environments** (Settings → Environments) group secrets for e.g. `production` and can require a manual approval
  before a deploy job runs.

**The pipeline**

```
push (any branch) ──▶ test: ruff check, ruff format --check, pytest
                          │ (only on main, only if tests pass)
                          ▼
                       build: docker build → ghcr.io/<owner>/<repo>:sha-<commit>
                          │
                          ▼
                       deploy: ssh to VPS → ./deploy.sh sha-<commit>   (or call Render deploy hooks)
```

**Code — `.github/workflows/ci-cd.yml`**

```yaml
name: CI/CD

on:
  push:
    branches: ["**"]
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}   # never cancel a deploy halfway

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: |
            requirements.txt
            requirements-dev.txt

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Lint
        run: ruff check .

      - name: Check formatting
        run: ruff format --check .

      - name: Test
        run: pytest -q
        env:
          ENVIRONMENT: dev
          ANTHROPIC_API_KEY: test-not-a-real-key
          TELEGRAM_BOT_TOKEN: test-not-a-real-token
          DATABASE_URL: sqlite:///./test.db

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write          # push to ghcr.io with the built-in GITHUB_TOKEN
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}    # lowercased automatically
          tags: |
            type=sha,format=long
            type=raw,value=latest

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          platforms: linux/amd64
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          build-args: RELEASE=${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Configure SSH
        env:
          SSH_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
          KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}
        run: |
          mkdir -p ~/.ssh
          printf '%s\n' "$SSH_KEY" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          printf '%s\n' "$KNOWN_HOSTS" > ~/.ssh/known_hosts

      - name: Deploy
        run: ssh deploy@${{ secrets.DEPLOY_HOST }} "/srv/organizer/deploy.sh sha-${{ github.sha }}"
```

`type=sha,format=long` produces the tag `sha-<full commit hash>`, which is exactly what the deploy step passes to
`deploy.sh`. The `RELEASE` build argument ends up in the image as an environment variable, so Sentry knows which
commit an error came from.

**Code — secrets to create**

| Secret | Value | Where |
|---|---|---|
| `DEPLOY_HOST` | Your server's IP or hostname | `production` environment |
| `DEPLOY_SSH_KEY` | A **new** private key used only for deploys | `production` environment |
| `DEPLOY_KNOWN_HOSTS` | Output of `ssh-keyscan -t ed25519 <server>` (verify the fingerprint!) | `production` environment |
| `RENDER_DEPLOY_HOOK_API` etc. | Render deploy hook URLs (Render variant only) | `production` environment |

Create the deploy key on your laptop (no passphrase, since CI can't type one):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/organizer_deploy -N "" -C "github-actions-deploy"
```

Append `~/.ssh/organizer_deploy.pub` to `/home/deploy/.ssh/authorized_keys` on the server, and paste the private key
`~/.ssh/organizer_deploy` into the `DEPLOY_SSH_KEY` secret. Get the host key line for `DEPLOY_KNOWN_HOSTS`:

```bash
ssh-keyscan -t ed25519 203.0.113.10
```

Compare its fingerprint with `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` run **on the server**, so you know
you didn't record an impostor's key.

**Code — the Render variant of the deploy job**

With `autoDeploy: false` in `render.yaml`, replace the `deploy` job's steps with:

```yaml
      - name: Trigger Render deploys
        env:
          HOOK_API: ${{ secrets.RENDER_DEPLOY_HOOK_API }}
          HOOK_BOT: ${{ secrets.RENDER_DEPLOY_HOOK_BOT }}
          HOOK_WORKER: ${{ secrets.RENDER_DEPLOY_HOOK_WORKER }}
        run: |
          for hook in "$HOOK_API" "$HOOK_BOT" "$HOOK_WORKER"; do
            curl -fsS -X POST "$hook"
          done
```

(Render builds from the repo itself, so the `build` job is optional in this variant. Render can also deploy a
prebuilt image from a registry if you prefer "build once" there too.)

**Code — protect `main` and keep dependencies fresh**

In Settings → Branches, add a rule for `main`: require a pull request and require the `test` job to pass. Then add
`.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
  - package-ecosystem: docker
    directory: "/"
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: monthly
```

Dependabot opens PRs; CI tests them; you merge the green ones.

**Common mistakes**
- Echoing secrets in a `run:` step for "debugging". Masking is best-effort; don't rely on it.
- Using your personal SSH key for CI. Use a dedicated key you can revoke on its own.
- Deploying the `latest` tag. Two deploys a minute apart might both pull "latest" and get different images; a
  rollback has nothing to point at. Deploy immutable SHA tags.
- Tests that call the real LLM API in CI: slow, flaky and costly. Mock the client (Section 3).
- Forgetting `permissions: packages: write`, so the push to ghcr.io fails with `denied`.

**Exercises**
1. Add the `test` job only. Push a commit with a lint error and watch CI fail; fix it and watch it pass.
2. Add the `build` job and find your image under your GitHub profile → Packages.
3. Add the `deploy` job, merge a small visible change (e.g. a new field in `/healthz`), and watch it go live
   without touching the server.
4. Turn on "Required reviewers" for the `production` environment so every deploy waits for your approval.

**Check yourself**
- Why tag images with the commit SHA instead of `latest`?
- What's the difference between a repository secret and an environment secret?
- Why does the deploy job `need` the build job, and the build job `need` the test job?

---

## Part D: Observability and Operations

**Observability** answers "what is my app doing right now, and why did it do that?" without SSHing in and adding
print statements. It has four tools, each covered below:

| Tool | Answers | Lesson |
|---|---|---|
| **Logs** | What happened, step by step? | 14 |
| **Errors + health checks** | Is something broken? Am I told when it is? | 15 |
| **Metrics** | How much, how fast, how often — over time? | 16 |
| **Traces** (LLM-specific) | What did the model see, which tools did it call, what did it cost? | 17 |

### Lesson 14: Structured Logging

**Concepts**

`log.info(f"User {uid} called {tool} in {ms}ms")` is fine to read but painful to search across thousands of lines.
**Structured logs** write one JSON object per line, so a log tool (Render's log search, Better Stack, Grafana Loki,
`jq` on the server) can filter by field: "all `tool_call` events for user 42 that took over 2 seconds".

```json
{"ts": "2026-11-04T07:30:02.114+00:00", "level": "INFO", "logger": "organizer.agent", "msg": "tool_call", "request_id": "a1b2c3d4e5f6", "tool": "list_tasks", "duration_ms": 41.2, "ok": true}
```

Rules:
- Log to **stdout**. Docker/the platform collects it; don't write log files inside containers.
- Use a fixed **event name** as the message (`"tool_call"`) and put the variable parts in fields.
- Attach a **request ID** to every line produced while handling one request, so you can follow one conversation
  through the API, agent and tools.
- **Never log secrets.** Be deliberate about personal data (email bodies, message text): log IDs and lengths by
  default; keep full prompts in the LLM trace store with a retention limit (Lesson 17).

**Code — `organizer/observability.py` (logging part)**

```python
import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

from organizer.config import Settings

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Attributes every LogRecord has; anything else came from `extra=` and should be output.
_STANDARD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if (request_id := request_id_var.get()) is not None:
            payload["request_id"] = request_id
        for key, value in vars(record).items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(settings: Settings) -> None:
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(settings.log_level)

    # Route uvicorn's own loggers through our handler instead of theirs
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
    # Quiet chatty libraries
    for name in ("httpx", "httpcore", "apscheduler"):
        logging.getLogger(name).setLevel(logging.WARNING)
```

**Code — request ID + access log middleware (in `organizer/api/main.py`)**

```python
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request

from organizer.config import get_settings
from organizer.observability import request_id_var, setup_logging, setup_sentry

settings = get_settings()
setup_logging(settings)
setup_sentry(settings, component="api")
log = logging.getLogger("organizer.api")

app = FastAPI()


@app.middleware("http")
async def access_log(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid4().hex[:12]
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        log.info("http_request", extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        })
        return response
    finally:
        request_id_var.reset(token)
```

For streaming responses, `duration_ms` is the time until the response *started*; log the full duration at the end
of your stream generator if you need it.

**Code — reading JSON logs on a server**

```bash
docker compose -f compose.prod.yaml logs --no-log-prefix api | jq -c 'select(.level == "ERROR")'
```

```bash
docker compose -f compose.prod.yaml logs --no-log-prefix --since 1h api | jq -c 'select(.msg == "tool_call" and .duration_ms > 2000)'
```

(`jq` is installed with `sudo apt install -y jq`. Non-JSON lines will make `jq` complain; that's fine.)

**Common mistakes**
- `log.info(f"... {api_key} ...")` — or logging a whole request object that contains an `Authorization` header.
- Logging full email bodies and chat messages at INFO in production.
- Using `print()` in production code: no level, no timestamp, no fields.
- Setting `DEBUG` in prod and drowning in httpx noise (and paying for log storage).

**Exercises**
1. Add `setup_logging` to all three processes. Run the stack with `LOG_JSON=true` and filter the logs with `jq`.
2. In your agent loop, log one `tool_call` event per tool execution with `tool`, `duration_ms`, `ok` and the
   `request_id`. Follow one Telegram message through every log line it produced.
3. Write a test that captures a log record with `caplog` and asserts the JSON output contains your extra fields.

**Check yourself**
- Why put variable data in fields instead of in the message string?
- What is a request ID for?

---

### Lesson 15: Error Tracking, Health Checks and Uptime Monitoring

**Concepts**

- **Error tracking (Sentry):** every unhandled exception — and every `log.exception(...)` — is sent to Sentry with
  the stack trace, the release, the environment, and the breadcrumbs (recent log lines) that led to it. Identical
  errors are grouped, and you get an email the first time a new one appears.
- **Health checks:** endpoints the platform and monitors call to ask "are you OK?"
  - **Liveness** `/healthz`: the process is up and can answer HTTP. Cheap, no dependencies. If it fails, restart me.
  - **Readiness** `/readyz`: I can do real work — the database answers. If it fails, don't send me traffic yet.
  - Never call the LLM API in a health check: it costs money and an LLM outage would make your app look "down".
- **Uptime monitoring:** an outside service that calls `https://organizer.example.com/healthz` every minute or so
  and alerts you (email, Telegram, phone push) when it fails. It catches what Sentry can't: the server is off, DNS
  broke, the certificate expired.
- **Heartbeat (dead man's switch) monitoring:** for jobs. The *job* pings the monitor after each successful run; if
  no ping arrives within the expected window, you get alerted. This is how you find out the 7:30 briefing didn't run.

| Service | Good for | Free tier |
|---|---|---|
| **Sentry** | Exceptions, performance traces | Yes (one user, limited events) |
| **Healthchecks.io** | Heartbeats for cron jobs and the worker | Yes |
| **UptimeRobot**, **Better Stack** | HTTP uptime checks + status pages | Yes |
| Render / Fly built-in | Health-check-based restarts and deploy gating | Included |

**Code — Sentry (`organizer/observability.py`, continued)**

```python
import sentry_sdk


def setup_sentry(settings: Settings, component: str) -> None:
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.release,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,          # don't attach IPs, cookies, user data automatically
    )
    sentry_sdk.set_tag("component", component)   # api / bot / worker
```

With `sentry-sdk[fastapi]` installed, the FastAPI and logging integrations switch on automatically. Prove it works
with a temporary route:

```python
@app.get("/debug-sentry")
def debug_sentry():
    raise RuntimeError("Sentry test from the Work Organizer")
```

Hit it once, see the issue in Sentry, then delete the route. Sentry also offers AI-monitoring integrations for LLM
SDKs; if you enable one, check whether it records prompt text and turn that off unless you've decided you want it.

**Code — health endpoints (`organizer/api/main.py`)**

```python
from fastapi import Response
from sqlalchemy import text

from organizer.db import engine


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "release": settings.release}


@app.get("/readyz")
def readyz(response: Response) -> dict:
    checks: dict[str, str] = {}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"
    ok = all(value == "ok" for value in checks.values())
    if not ok:
        response.status_code = 503
    return {"status": "ok" if ok else "unavailable", "checks": checks}
```

**Code — heartbeats**

1. On healthchecks.io create a check named "daily-briefing" with period 1 day and grace 1 hour. Copy its ping URL
   into `HEALTHCHECK_PING_URL`.
2. The worker's `run_briefings()` (Lesson 11) already pings it on success and pings `/fail` on error.
3. Create a second check for backups (Lesson 19).

**Code — uptime monitor**

In UptimeRobot or Better Stack, add an HTTPS monitor for `https://organizer.example.com/readyz`, every 1–5
minutes, alerting you by email and/or Telegram. Turn on certificate-expiry alerts too.

**Common mistakes**
- A health check that only tests the process and never the database — "healthy" while every request fails.
- A health check that calls the LLM or Gmail — slow, costly, and fails when *they* do.
- Sentry with `send_default_pii=True` and prompts in breadcrumbs — personal data in a third-party tool you didn't
  intend to share it with.
- No monitoring on the worker at all; it can crash-loop for days unnoticed because nothing calls it.
- Alerts that fire so often you start ignoring them. Fewer, meaningful alerts.

**Exercises**
1. Connect Sentry to all three processes with the `component` tag. Trigger one error from each and filter by tag.
2. Stop the database container and watch `/readyz` return 503 while `/healthz` still returns 200.
3. Set up a heartbeat check, then stop the worker for longer than the grace period and confirm you get alerted.

**Check yourself**
- What's the difference between liveness and readiness?
- Which failure would a heartbeat monitor catch that an uptime monitor wouldn't?

---

### Lesson 16: Metrics Basics

**Concepts**

Logs describe single events; **metrics** are numbers aggregated over time, cheap to store and graph: requests per
minute, p95 latency, tokens per hour, dollars per day.

| Type | Behaves like | Example |
|---|---|---|
| **Counter** | Only goes up | `llm_tokens_total`, `http_requests_total` |
| **Gauge** | Goes up and down | `active_conversations`, `queue_length` |
| **Histogram** | Distribution of values in buckets | `http_request_duration_seconds` → p50/p95/p99 |

The **four golden signals** to watch for any service: **latency**, **traffic**, **errors**, **saturation** (CPU,
memory, disk, DB connections). For an AI assistant, add **tokens**, **cost** and **tool-call failure rate**.

**Labels** split a metric (e.g. by `model` or `tool`). Keep label values to a small, fixed set — never put user IDs,
message text or request IDs in labels; every unique value creates a new time series.

**Code — Prometheus metrics (`organizer/metrics.py`)**

```python
from prometheus_client import Counter, Histogram

HTTP_LATENCY = Histogram("http_request_duration_seconds", "HTTP latency", ["method", "path"])
LLM_TOKENS = Counter("llm_tokens_total", "LLM tokens used", ["model", "kind"])   # kind: input/output
LLM_COST = Counter("llm_cost_usd_total", "Estimated LLM spend in USD", ["model"])
TOOL_CALLS = Counter("tool_calls_total", "Agent tool calls", ["tool", "ok"])
```

Expose them from the API:

```python
from prometheus_client import make_asgi_app

app.mount("/metrics", make_asgi_app())
```

In the access-log middleware, use the **route template** (not the raw path, which may contain IDs) as the label:

```python
route = request.scope.get("route")
HTTP_LATENCY.labels(request.method, getattr(route, "path", "unmatched")).observe(time.perf_counter() - start)
```

The Caddyfile from Lesson 9 already hides `/metrics` from the internet. A Prometheus server (or Grafana Cloud's
agent, or Better Stack) on the private network scrapes it.

> **Caveats:** metrics live in each process's memory. With `uvicorn --workers N`, use the client's multiprocess
> mode; the bot and worker processes need their own endpoint (`prometheus_client.start_http_server(9100)`). For a
> single-user assistant, the `llm_calls` table from Lesson 17 plus a daily SQL report covers most needs — don't
> build a monitoring stack bigger than the app.

**Common mistakes**
- High-cardinality labels (`user_id`, full URL path) that explode memory.
- Publishing `/metrics` publicly — it leaks internal details.
- Averages instead of percentiles: an average latency of 2 s can hide a p99 of 40 s.

**Exercises**
1. Add the four metrics above and view `http://localhost:8000/metrics` locally.
2. Run Prometheus and Grafana locally with Compose (both have official images) and graph `rate(llm_tokens_total[5m])`.

**Check yourself**
- When do you use a histogram instead of a counter?
- Why is `user_id` a bad label?

---

### Lesson 17: LLM Tracing — Logging Every Prompt, Tool Call and Token

**Concepts**

A normal web app fails loudly. An AI agent fails **quietly**: it calls the wrong tool, loops eight times, or gives
a confident wrong answer — all with HTTP 200. To debug and to control cost you need a record of **every model call**:

| Field | Why |
|---|---|
| `trace_id` | Groups all calls and tool runs for one user message (one agent loop) |
| `user_id`, `conversation_id`, `purpose` | Who, in what chat, for what (`chat`, `briefing`, `summarise`) |
| `model` | Costs and behaviour differ per model |
| `input_tokens`, `output_tokens`, cache tokens | Usage — the basis of cost |
| `cost_usd` | Computed from your price table at the time of the call |
| `latency_ms`, `stop_reason`, `status`, `error` | Speed, why it stopped (`end_turn`, `tool_use`, `max_tokens`), failures |
| `tool_uses` | Which tools the model asked for, with arguments |
| `request_messages`, `response_content` | The full prompt and answer — **sensitive**, so keep them for a limited time |

Tool *executions* are recorded too (name, arguments, duration, success, a short result preview) with the same
`trace_id`.

**Code — the table (`organizer/models.py`)**

```python
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


class LlmCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    latency_ms: Mapped[int] = mapped_column(Integer)
    stop_reason: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))           # ok / error
    error: Mapped[str | None] = mapped_column(Text)
    tool_uses: Mapped[list | None] = mapped_column(JSON)
    request_messages: Mapped[list | None] = mapped_column(JSON)  # purge after N days
    response_content: Mapped[list | None] = mapped_column(JSON)
```

**Code — cost calculation (`organizer/llm/pricing.py`)**

```python
from decimal import Decimal

# USD per million tokens: (input, output, cache write, cache read).
# Copy these from your provider's pricing page and update them when prices change.
# The numbers below are placeholders for illustration — check before relying on them.
PRICES_PER_MTOK: dict[str, tuple[str, str, str, str]] = {
    "claude-sonnet-4-5": ("3.00", "15.00", "3.75", "0.30"),
}


def estimate_cost(model: str, usage) -> Decimal:
    prices = PRICES_PER_MTOK.get(model)
    if prices is None:
        return Decimal("0")       # and log a warning: unknown model = untracked spend!
    p_in, p_out, p_cw, p_cr = (Decimal(p) for p in prices)
    total = (
        usage.input_tokens * p_in
        + usage.output_tokens * p_out
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * p_cw
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * p_cr
    )
    return total / Decimal(1_000_000)
```

Use `Decimal` for money — floats accumulate rounding errors.

**Code — a traced wrapper (`organizer/llm/tracing.py`)**

Every model call in the project goes through this one function — the agent loop, the briefing, summaries.

```python
import asyncio
import logging
import time

import anthropic

from organizer.db import SessionLocal
from organizer.llm.pricing import estimate_cost
from organizer.metrics import LLM_COST, LLM_TOKENS
from organizer.models import LlmCall

log = logging.getLogger("organizer.llm")


def _save(row: LlmCall) -> None:
    try:
        with SessionLocal() as session:
            session.add(row)
            session.commit()
    except Exception:
        # Never let logging break the user's request (or hide the real error)
        log.exception("llm_call_save_failed")


async def traced_create(
    client: anthropic.AsyncAnthropic,
    *,
    trace_id: str,
    purpose: str,
    user_id: int | None = None,
    conversation_id: str | None = None,
    **kwargs,
):
    start = time.perf_counter()
    response, error = None, None
    try:
        response = await client.messages.create(**kwargs)
        return response
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        model = kwargs.get("model", "unknown")
        row = LlmCall(
            trace_id=trace_id, user_id=user_id, conversation_id=conversation_id,
            purpose=purpose, model=model,
            latency_ms=int((time.perf_counter() - start) * 1000),
            status="error" if error else "ok", error=error,
            request_messages=kwargs.get("messages"),
        )
        if response is not None:
            usage = response.usage
            row.input_tokens = usage.input_tokens
            row.output_tokens = usage.output_tokens
            row.cache_write_tokens = usage.cache_creation_input_tokens or 0
            row.cache_read_tokens = usage.cache_read_input_tokens or 0
            row.cost_usd = estimate_cost(model, usage)
            row.stop_reason = response.stop_reason
            row.response_content = [block.model_dump() for block in response.content]
            row.tool_uses = [
                {"name": b.name, "input": b.input} for b in response.content if b.type == "tool_use"
            ]
            LLM_TOKENS.labels(model, "input").inc(usage.input_tokens)
            LLM_TOKENS.labels(model, "output").inc(usage.output_tokens)
            LLM_COST.labels(model).inc(float(row.cost_usd))
        log.info("llm_call", extra={
            "trace_id": trace_id, "purpose": purpose, "model": model, "status": row.status,
            "input_tokens": row.input_tokens, "output_tokens": row.output_tokens,
            "cost_usd": str(row.cost_usd), "latency_ms": row.latency_ms,
        })
        await asyncio.to_thread(_save, row)   # don't block the event loop on the DB write
```

If `messages` contains non-JSON values (e.g. SDK objects from a previous response), convert them with
`model_dump()` before storing. For **streaming** calls, use `async with client.messages.stream(**kwargs) as stream:`
and read usage from `await stream.get_final_message()` at the end, then record the same row.

**Privacy and retention.** Prompts contain emails, calendar entries and messages. Decide a retention period (say 14
days for full text), and run a daily worker job that clears it while keeping the numbers:

```python
from datetime import UTC, datetime, timedelta

from sqlalchemy import update


def purge_old_prompt_text(days: int = 14) -> None:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    with SessionLocal() as session:
        session.execute(
            update(LlmCall)
            .where(LlmCall.created_at < cutoff)
            .values(request_messages=None, response_content=None)
        )
        session.commit()
```

**Dedicated LLM observability tools**

Your own table is enough to start and keeps data in your database. Dedicated tools add a UI for browsing traces as
trees (agent → LLM call → tool call → LLM call), prompt versioning, evaluations and cost dashboards:

| Tool | Notes |
|---|---|
| **Langfuse** | Open source, self-hostable or cloud; Python SDK with an `@observe()` decorator; OpenTelemetry-based |
| **LangSmith** | From the LangChain team; works without LangChain too |
| **Arize Phoenix** | Open source, OpenTelemetry-native, strong on evaluations |
| **Helicone** | Proxy-based: change the API base URL and every call is logged |
| **OpenTelemetry GenAI conventions** | Vendor-neutral span attributes for LLM calls; send to any backend |

A taste of Langfuse (SDK v3 style; set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_HOST` in the
environment — check the docs for the version you install, as the API changed between major versions):

```python
from langfuse import observe


@observe()                       # creates a trace for each user message
async def handle_message(user_id: int, text: str) -> str:
    return await run_agent_loop(user_id, text)


@observe(name="tool")            # nested spans for each tool execution
def run_tool(name: str, arguments: dict):
    return TOOLS[name](**arguments)
```

**Common mistakes**
- Logging some calls (chat) but not others (briefing, summaries, embeddings) — your cost numbers are then wrong.
- Storing full prompts forever.
- A price table that's never updated, or missing a model you switched to (cost silently becomes $0).
- Losing the trace on errors — record failed calls too; they're often what you need to debug.

**Exercises**
1. Route every model call through `traced_create`. Send five Telegram messages and query
   `SELECT purpose, model, input_tokens, output_tokens, cost_usd FROM llm_calls ORDER BY id DESC LIMIT 10;`
2. Record tool executions (name, arguments, duration, ok, first 200 characters of the result) with the same
   `trace_id`, and write a query that shows one full agent run in order.
3. Add the purge job to the worker and test it by temporarily setting `days=0`.
4. (Optional) Send the same traces to Langfuse Cloud and compare its view with your table.

**Check yourself**
- Why does each agent run need a `trace_id`?
- Which fields make it possible to compute cost later if prices change?

---

### Lesson 18: Controlling AI Costs

**Concepts**

With LLMs, a bug costs money directly. An agent stuck in a tool loop, a user pasting a 300-page PDF, or a retry
storm can spend more in an hour than your hosting costs in a year. Defend in layers:

| Layer | What it does | How |
|---|---|---|
| **Provider limits** | Hard monthly cap and email alerts at the provider | Set spend limits/alerts in your provider's console; use a separate API key (or workspace) per environment |
| **Global daily budget** | App refuses non-essential LLM work once today's spend ≥ budget | Sum `cost_usd` for today before each call |
| **Per-user budget** | One user (or one leaked bot link) can't burn everything | Sum by `user_id` for today |
| **Rate limits** | Max N messages per minute per user | Token bucket in memory (one process) or in Redis/Postgres (several) |
| **Loop limits** | Agent stops after `llm_max_tool_iterations` | Counter in the agent loop |
| **Size limits** | `max_tokens` on every call; truncate long inputs; cap history length | Settings + summarise old turns |
| **Model choice** | Cheaper model for simple jobs (classification, routing, briefings) | `purpose` → model mapping |
| **Prompt caching** | Re-used system prompt + tool definitions cost much less | Mark stable prefixes as cacheable (Section 3) |
| **Alerts + reports** | You hear about spend daily, and immediately when it spikes | Worker job → Telegram message to admin |

**Code — budget checks (`organizer/llm/budget.py`)**

```python
from datetime import UTC, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from organizer.config import get_settings
from organizer.db import SessionLocal
from organizer.models import LlmCall


class BudgetExceeded(Exception):
    def __init__(self, scope: str, spent: Decimal, limit: float):
        super().__init__(f"{scope} budget exceeded: ${spent:.2f} of ${limit:.2f}")
        self.scope = scope


def start_of_today_utc() -> datetime:
    tz = ZoneInfo(get_settings().timezone)
    local_midnight = datetime.combine(datetime.now(tz).date(), time.min, tzinfo=tz)
    return local_midnight.astimezone(UTC)


def spent_today(user_id: int | None = None) -> Decimal:
    query = select(func.coalesce(func.sum(LlmCall.cost_usd), 0)).where(
        LlmCall.created_at >= start_of_today_utc()
    )
    if user_id is not None:
        query = query.where(LlmCall.user_id == user_id)
    with SessionLocal() as session:
        return Decimal(session.execute(query).scalar_one())


def check_budget(user_id: int | None) -> None:
    """Raise BudgetExceeded before making an LLM call that would go over budget."""
    settings = get_settings()
    total = spent_today()
    if total >= Decimal(str(settings.daily_budget_usd)):
        raise BudgetExceeded("global", total, settings.daily_budget_usd)
    if user_id is not None:
        mine = spent_today(user_id)
        if mine >= Decimal(str(settings.per_user_daily_budget_usd)):
            raise BudgetExceeded("user", mine, settings.per_user_daily_budget_usd)
```

Call `check_budget(user_id)` at the start of each agent loop (and inside it, before each model call). In the bot,
catch `BudgetExceeded` and reply politely: *"I've hit today's AI budget. I'll be back tomorrow — your tasks are
still available with /list."* Notice the budget is checked *before* the call and calls already in flight can push
you slightly over; that's acceptable — the point is to stop runaway loops quickly.

**Code — daily cost report + spike alert (`organizer/worker/jobs.py`)**

```python
from datetime import timedelta
from decimal import Decimal

import httpx
from sqlalchemy import func, select

from organizer.config import get_settings
from organizer.db import SessionLocal
from organizer.llm.budget import spent_today, start_of_today_utc
from organizer.models import LlmCall


def notify_admin(text: str) -> None:
    settings = get_settings()
    if settings.telegram_admin_chat_id is None:
        return
    token = settings.telegram_bot_token.get_secret_value()
    httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": settings.telegram_admin_chat_id, "text": text},
        timeout=10,
    ).raise_for_status()


def send_cost_report() -> None:
    end = start_of_today_utc()
    start = end - timedelta(days=1)
    with SessionLocal() as session:
        rows = session.execute(
            select(
                LlmCall.purpose,
                LlmCall.model,
                func.count(),
                func.sum(LlmCall.input_tokens),
                func.sum(LlmCall.output_tokens),
                func.sum(LlmCall.cost_usd),
            )
            .where(LlmCall.created_at >= start, LlmCall.created_at < end)
            .group_by(LlmCall.purpose, LlmCall.model)
            .order_by(func.sum(LlmCall.cost_usd).desc())
        ).all()

    total = sum((row[5] or 0 for row in rows), Decimal("0"))
    lines = [f"AI cost report for {start.date()}: ${total:.4f}"]
    for purpose, model, calls, tin, tout, cost in rows:
        lines.append(f"- {purpose} / {model}: {calls} calls, {tin} in / {tout} out tokens, ${cost:.4f}")
    if not rows:
        lines.append("No LLM calls yesterday.")
    notify_admin("\n".join(lines))
```

Add a spike alert that runs every 15 minutes: if `spent_today()` crosses 80% of the daily budget, send one alert
(store "alert sent for <date>" in a small table, or reuse the `briefings_sent` idea, so you're not pinged every 15
minutes).

**Common mistakes**
- Relying only on the provider's monthly limit — by the time it triggers, the month's budget is gone.
- Counting only chat calls in the budget, not background jobs.
- No `max_tokens` and no loop limit — the two most common causes of runaway spend.
- Using the most capable model for everything, including "is this message a task or a question?"

**Exercises**
1. Set `PER_USER_DAILY_BUDGET_USD=0.01` locally and confirm the bot refuses politely after a message or two.
2. Schedule `send_cost_report` and receive one in Telegram.
3. Route `purpose="briefing"` to a cheaper model via settings and compare a week of costs.

**Check yourself**
- Name five independent controls that limit AI spend.
- Why is the budget checked before the call rather than after?

---

### Lesson 19: Updates, Rollbacks and Backups

**Concepts**

**Updates.** Things you must keep updating: your dependencies (Dependabot PRs), the base image (`python:3.12-slim`
gets security patches — rebuild regularly, e.g. a weekly scheduled CI run), the server OS (unattended-upgrades plus
an occasional reboot), Postgres minor versions, and API versions of your integrations.

**Rollbacks.** Because every deploy is an immutable image tagged with its commit, rolling back the *code* is fast:

| Host | Roll back with |
|---|---|
| Render | Events → pick a previous deploy → **Rollback** |
| VPS | `SKIP_MIGRATIONS=1 ./deploy.sh "$(cat .previous_tag)"` |
| Either | `git revert <commit>` → push → CI deploys the revert (the cleanest, fully recorded option) |

The **database doesn't roll back** with the code. That's why migrations are expand/contract (Lesson 12): the old
code still works on the new schema. Don't write "down" migrations you'll run in a panic; roll *forward* with a fix.

**Backups.** The **3-2-1 rule**: 3 copies of your data, on 2 different kinds of storage, 1 of them off-site. A backup
you've never restored is a hope, not a backup.

| Data | How to back it up |
|---|---|
| Postgres | `pg_dump -Fc` nightly, uploaded off-site; managed DBs also have automatic snapshots/PITR |
| SQLite (if still used) | `sqlite3 organizer.db ".backup backup.db"` — **not** `cp` while it's being written |
| Chroma | Tar the volume, or be able to rebuild it from the source documents (re-embed) |
| `.env` / secrets | In your password manager — never in the backup bucket in plain text |
| Caddy certificates | Not needed — Caddy re-issues them |

**Code — `/srv/organizer/backup.sh`**

```bash
#!/usr/bin/env bash
# Nightly backup: Postgres dump + Chroma volume, uploaded off-site with rclone.
set -euo pipefail

cd /srv/organizer
COMPOSE="docker compose -f compose.prod.yaml"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIR=/srv/organizer/backups
HC_URL="$(grep -E '^BACKUP_HEALTHCHECK_URL=' .env | cut -d= -f2- || true)"

trap '[[ -n "$HC_URL" ]] && curl -fsS -m 10 "$HC_URL/fail" > /dev/null' ERR

$COMPOSE exec -T db pg_dump -U organizer -d organizer -Fc > "$DIR/db-$STAMP.dump"

docker run --rm -v organizer_app_data:/data:ro -v "$DIR":/backup busybox \
  tar czf "/backup/chroma-$STAMP.tgz" -C /data .

rclone copy "$DIR" offsite:organizer-backups --include "*-$STAMP.*"

# Keep 7 days locally; the bucket's lifecycle rule keeps 30 days off-site.
find "$DIR" -type f \( -name 'db-*.dump' -o -name 'chroma-*.tgz' \) -mtime +7 -delete

[[ -n "$HC_URL" ]] && curl -fsS -m 10 --retry 3 "$HC_URL" > /dev/null
echo "Backup $STAMP OK"
```

```bash
chmod +x /srv/organizer/backup.sh
```

Set up the off-site remote once with `rclone config` (choose your S3-compatible provider and name the remote
`offsite`). Use a bucket-scoped key that can write but **not delete**, and turn on versioning or object lock, so
an attacker with access to the server can't wipe your backups too.

Schedule it with the `deploy` user's crontab (`crontab -e`):

```text
15 3 * * * /srv/organizer/backup.sh >> /srv/organizer/backups/backup.log 2>&1
```

**Code — restore (practise this!)**

Restore into a scratch database first, so a mistake can't damage production:

```bash
docker compose -f compose.prod.yaml exec db createdb -U organizer restore_test
```

```bash
docker compose -f compose.prod.yaml exec -T db pg_restore -U organizer -d restore_test --no-owner < backups/db-20261104T031500Z.dump
```

```bash
docker compose -f compose.prod.yaml exec db psql -U organizer -d restore_test -c "SELECT count(*) FROM tasks;"
```

For a real restore into production: stop `api`, `bot` and `worker`, run `pg_restore --clean --if-exists -d organizer`,
then start them again.

**Common mistakes**
- Backups stored only on the same server (the disk dies, the backups die with it).
- Never testing a restore, then discovering the dumps were empty because the password changed.
- No alert when the backup job fails — use the heartbeat check.
- Rolling back code across a destructive migration (a dropped column) and finding the old code crashes.

**Exercises**
1. Set up `backup.sh` with an off-site bucket and a heartbeat check. Break it deliberately (wrong remote name) and
   confirm you're alerted.
2. Do a full restore drill into `restore_test` and compare row counts with production. Write down how long it took.
3. Deploy a change, then roll it back with each method in the table above.

**Check yourself**
- What does the 3-2-1 rule say?
- Why shouldn't the server's backup credentials be able to delete backups?
- Why doesn't rolling back the code roll back the database?

---

### Lesson 20: The Production Checklist

Go through this before you call it "production" — and again after every big change.

**Security and secrets**
- [ ] No secrets in Git history, Docker images, logs, or Sentry events
- [ ] Every secret typed as `SecretStr`; `.env` on the server is `chmod 600`
- [ ] Separate keys and Telegram bots for dev and prod; provider spend limits set
- [ ] SSH: keys only, no root login; ufw allows only 22/80/443; database has no public port
- [ ] Containers run as a non-root user
- [ ] `/chat` and webhooks require authentication (only your Telegram user ID / a token)

**Reliability**
- [ ] `restart: unless-stopped` (or the platform equivalent) on every process; survives a reboot
- [ ] Exactly one scheduler; advisory lock and idempotent jobs
- [ ] Migrations run once per deploy, before the new code starts, and are backward-compatible
- [ ] Health checks: `/healthz` (liveness) and `/readyz` (database)
- [ ] Log rotation configured; disk usage below 70%

**Observability**
- [ ] JSON logs with request IDs from all three processes
- [ ] Sentry receiving errors from api, bot and worker, tagged with release and environment
- [ ] Uptime monitor on `/readyz`; heartbeat monitors for the briefing and backups
- [ ] Every LLM call recorded with tokens, cost, latency and trace ID

**Cost**
- [ ] `max_tokens` on every call; agent loop iteration limit
- [ ] Global and per-user daily budgets enforced; daily cost report arrives
- [ ] Spike alert at 80% of the daily budget

**Delivery and recovery**
- [ ] CI runs ruff and pytest on every push; `main` is protected
- [ ] Deploys are automatic from `main`, using immutable SHA-tagged images
- [ ] Rollback tested at least once
- [ ] Nightly off-site backups; a restore has been tested and timed
- [ ] A short `RUNBOOK.md`: how to deploy, roll back, restore, rotate a key, and where logs and dashboards are

**Exercise:** Write your `RUNBOOK.md`. Then ask a friend (or future you, a month from now) to follow it to restore
a backup into a scratch database without asking you any questions.

---

## Capstone Project: Work Organizer in Production

Take the Work Organizer from Section 6 and make it a real, always-on service. Everything you need is in the lessons
above; this project is about putting it together and proving it works.

### Requirements

**Level 1 — containerized**
- One `Dockerfile` (multi-stage, slim base, non-root user, `.dockerignore`) that runs as `api`, `bot` or `worker`
- `compose.yaml` running api + bot + worker + Postgres locally with `docker compose up -d --build`
- All configuration through `organizer/config.py` (pydantic-settings); `.env.example` committed
- Alembic migrations; Postgres replaces SQLite; Chroma on a named volume used only by the API
- The scheduler lives only in the worker, protected by an advisory lock; briefings are idempotent

**Level 2 — deployed**
- GitHub Actions: ruff + pytest on every push; on `main`, build an image tagged `sha-<commit>`, push to GHCR, deploy
- Running on **one** host — a VPS with Compose + Caddy, or Render with a Blueprint
- HTTPS on your own domain (or the platform's subdomain); database not publicly reachable
- Migrations run automatically once per deploy; a failed health check stops (or rolls back) the deploy

**Level 3 — operated**
- JSON logs with request IDs; Sentry on all three processes tagged with `component`, `release` and `environment`
- `/healthz` and `/readyz`; an uptime monitor on `/readyz`; heartbeat checks for the briefing and backups
- Every LLM call recorded in `llm_calls` (tokens, cost, latency, tool uses, trace ID); prompt text purged after 14 days
- Global and per-user daily budgets; a daily cost report delivered to you on Telegram; an 80% spike alert
- Nightly off-site Postgres + Chroma backups and **one documented restore drill**
- `RUNBOOK.md` covering deploy, rollback, restore, key rotation, and where to look when something breaks

### Suggested structure

```
work_organizer/
├── .github/
│   ├── workflows/ci-cd.yml
│   └── dependabot.yml
├── Dockerfile
├── .dockerignore
├── compose.yaml                # local development
├── deploy/                     # copied to /srv/organizer on a VPS
│   ├── compose.prod.yaml
│   ├── Caddyfile
│   ├── deploy.sh
│   └── backup.sh
├── render.yaml                 # if you choose Render instead
├── alembic.ini
├── migrations/
├── requirements.in / requirements.txt / requirements-dev.txt
├── RUNBOOK.md
├── organizer/
│   ├── config.py               # Lesson 6
│   ├── db.py                   # Lesson 12
│   ├── models.py               # + BriefingSent, LlmCall
│   ├── observability.py        # Lessons 14–15
│   ├── metrics.py              # Lesson 16
│   ├── llm/
│   │   ├── pricing.py          # Lesson 17
│   │   ├── tracing.py          # Lesson 17
│   │   └── budget.py           # Lesson 18
│   ├── agent/loop.py           # uses traced_create + check_budget
│   ├── api/main.py             # middleware, /healthz, /readyz, /metrics, /chat
│   ├── bot/main.py
│   └── worker/
│       ├── main.py             # Lesson 11
│       ├── locks.py
│       └── jobs.py             # briefings, cost report, spike alert, purge
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_pricing.py
    ├── test_budget.py
    └── test_health.py
```

### Starter skeleton (fill in the TODOs)

```python
# organizer/agent/loop.py
import logging
from uuid import uuid4

import anthropic

from organizer.config import get_settings
from organizer.llm.budget import check_budget
from organizer.llm.tracing import traced_create

log = logging.getLogger("organizer.agent")


class TooManyToolIterations(Exception):
    pass


async def run_agent(client: anthropic.AsyncAnthropic, user_id: int, conversation_id: str,
                    messages: list[dict], tools: list[dict]) -> str:
    """Run the tool-use loop for one user message and return the final text."""
    settings = get_settings()
    trace_id = uuid4().hex
    for iteration in range(settings.llm_max_tool_iterations):
        check_budget(user_id)
        response = await traced_create(
            client,
            trace_id=trace_id,
            purpose="chat",
            user_id=user_id,
            conversation_id=conversation_id,
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            messages=messages,
            tools=tools,
        )
        if response.stop_reason != "tool_use":
            # TODO: join the text blocks of response.content and return them
            ...
        # TODO: append the assistant turn to messages as plain dicts so it can be stored as JSON:
        #       {"role": "assistant", "content": [b.model_dump() for b in response.content]}
        # TODO: for each tool_use block: run the tool, time it, log a "tool_call" event with
        #       trace_id, tool, duration_ms and ok, increment TOOL_CALLS, and collect a tool_result
        # TODO: append one user turn containing all tool_result blocks
    raise TooManyToolIterations(f"stopped after {settings.llm_max_tool_iterations} iterations")
```

```python
# organizer/bot/main.py
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from organizer.config import get_settings
from organizer.llm.budget import BudgetExceeded
from organizer.observability import setup_logging, setup_sentry

log = logging.getLogger("organizer.bot")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings()
    # TODO: ignore messages from anyone except allowed user IDs (Section 8 goes deeper)
    try:
        # TODO: call your agent (run_agent) and reply with the answer
        ...
    except BudgetExceeded:
        await update.message.reply_text("I've reached today's AI budget. Back tomorrow!")
    except Exception:
        log.exception("bot_message_failed")
        await update.message.reply_text("Sorry, something went wrong. It has been reported.")


def main() -> None:
    settings = get_settings()
    setup_logging(settings)
    setup_sentry(settings, component="bot")
    app = Application.builder().token(settings.telegram_bot_token.get_secret_value()).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    log.info("bot_starting", extra={"environment": settings.environment})
    app.run_polling()          # handles SIGTERM for a clean shutdown


if __name__ == "__main__":
    main()
```

```python
# organizer/worker/jobs.py  (additions)
SPIKE_THRESHOLD = Decimal("0.8")


def check_spend_spike() -> None:
    """Every 15 minutes: alert once per day when spend passes 80% of the daily budget."""
    # TODO: compute spent_today() and compare with SPIKE_THRESHOLD * daily_budget_usd
    # TODO: if over, insert (kind="spend_spike", day=today) into an alerts_sent table with a unique
    #       constraint; only call notify_admin(...) if the insert succeeded
    ...
```

```python
# tests/test_pricing.py
from types import SimpleNamespace
from decimal import Decimal

from organizer.llm.pricing import estimate_cost


def test_known_model_cost():
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=0,
                            cache_creation_input_tokens=0, cache_read_input_tokens=0)
    # TODO: assert the cost equals the input price you put in PRICES_PER_MTOK


def test_unknown_model_costs_zero():
    usage = SimpleNamespace(input_tokens=10, output_tokens=10,
                            cache_creation_input_tokens=None, cache_read_input_tokens=None)
    assert estimate_cost("no-such-model", usage) == Decimal("0")
```

```python
# tests/test_health.py
from fastapi.testclient import TestClient


def test_healthz():
    from organizer.api.main import app      # import after conftest set the env vars
    client = TestClient(app)
    # TODO: assert GET /healthz returns 200 and {"status": "ok", ...}
    # TODO: assert GET /readyz returns 200 against the test SQLite database
```

### Proving it works (your demo)

1. Merge a small change to `main` and show it go live through CI without touching the server.
2. `curl -i https://<your-domain>/readyz` returns 200 with a valid certificate.
3. Send a Telegram message; find its `request_id` in the logs and its `trace_id` rows in `llm_calls`.
4. Trigger a test error and show it in Sentry with the right release.
5. Show the latest daily cost report in Telegram.
6. Show last night's backup in the off-site bucket and your restore drill notes.
7. Reboot the server (or restart all Render services) and show everything comes back on its own.

**Why this matters:** in Section 8 you'll give the assistant permission to send emails and change your calendar.
That's only safe once you can see every action it takes (traces), stop it from running away (budgets and limits),
and recover from mistakes (backups and rollbacks). This capstone builds exactly those foundations.

---

## Weekly Schedule

| Week | Lessons | Mini-project |
|---|---|---|
| 1 | Part 0, Lessons 1–4 | Harden a practice server; build your app's image and run it with `docker run` |
| 2 | Lessons 5–6, 11–12 | Full stack in Compose with Postgres, Alembic, pydantic-settings and a separate worker |
| 3 | Lessons 7–10, 13 | Deploy to Render or a VPS with HTTPS; CI/CD from `main` |
| 4 | Lessons 14–18 | JSON logs, Sentry, health checks, uptime + heartbeats, `llm_calls`, budgets, cost report |
| 5 | Lessons 19–20, Capstone | Backups + restore drill, rollback practice, runbook, final demo |

**Daily routine (1–2 hours):** 15 min reading → 45 min typing configs and code → 30 min breaking things on purpose
and fixing them (that's where ops skills come from) → 5 min adding what you learned to your runbook.

---

## Final Checklist

Before starting Section 8 (Safety and Security), you should be able to do all of this **without looking things up**:

**Linux and servers**
- [ ] SSH into a server with a key; create users; disable password and root login
- [ ] Set file permissions with `chmod`/`chown` and explain `600`, `640` and `755`
- [ ] Open only the ports you need with ufw, and explain why Docker can bypass it
- [ ] Write a systemd unit and read its logs with `journalctl`

**Containers**
- [ ] Explain images, containers, layers, volumes, tags and registries
- [ ] Write a multi-stage Dockerfile for a Python app that runs as non-root
- [ ] Use volumes so data survives container replacement
- [ ] Describe a multi-service app with Compose, healthchecks and `depends_on`

**Configuration and data**
- [ ] Load and validate all config with pydantic-settings, with secrets as `SecretStr`
- [ ] Create, review and apply Alembic migrations, and write backward-compatible ones
- [ ] Run exactly one scheduler and make jobs idempotent

**Hosting and delivery**
- [ ] Compare PaaS, VPS and cloud hosting and justify a choice
- [ ] Deploy to Render with a Blueprint, or to a VPS with Compose + Caddy
- [ ] Point a domain at a server with DNS records and get automatic HTTPS
- [ ] Build a GitHub Actions pipeline: lint, test, build, push, deploy
- [ ] Roll back a bad deploy

**Operations**
- [ ] Emit JSON logs with request IDs and search them
- [ ] Track errors with Sentry; set up uptime and heartbeat monitors
- [ ] Explain counters, gauges and histograms, and avoid high-cardinality labels
- [ ] Record every LLM call with tokens, cost, latency and trace ID
- [ ] Enforce daily budgets, loop limits and `max_tokens`; get a daily cost report
- [ ] Back up Postgres off-site and restore it

---

## Exercise Solutions

Try every exercise yourself first. Look here only after a real attempt (at least 20 minutes).

**Lesson 2, Exercise 2** — `/etc/systemd/system/practice-http.service`

```ini
[Unit]
Description=Practice HTTP server
After=network.target

[Service]
User=deploy
WorkingDirectory=/home/deploy
ExecStart=/usr/bin/python3 -m http.server 9000 --bind 127.0.0.1
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl daemon-reload`, `sudo systemctl enable --now practice-http`, find the PID with
`systemctl status practice-http`, `sudo kill <pid>`, and run `systemctl status` again: a new PID appears ~2 s later.

**Lesson 3, Exercise 1**

```bash
docker run --rm -v practice_data:/data python:3.12-slim python -c "import json; json.dump({'task': 'gym'}, open('/data/t.json', 'w'))"
```

```bash
docker run --rm -v practice_data:/data python:3.12-slim cat /data/t.json
```

**Lesson 4, Exercise 2** — after a code-only change, every step up to and including `RUN pip install` shows
`CACHED`; only the `COPY organizer/` layer and later rebuild. After changing `requirements.txt`, the
`COPY requirements.txt` layer and everything after it rebuild.

**Lesson 5, Exercise 4** — without `init: true`, the scheduler script is PID 1 with no SIGTERM handler, so the
kernel ignores SIGTERM; Docker waits the 10-second grace period and then sends SIGKILL. With `init: true`, the init
process forwards SIGTERM, Python's default action terminates the process, and the stop takes well under a second.
(The `signal.signal(signal.SIGTERM, ...)` line in Lesson 11 also fixes it, by installing a handler.)

**Lesson 6, Exercise 2**

```python
# in Settings
briefing_hour: int = Field(default=7, ge=0, le=23)
```

```python
# in the worker
scheduler.add_job(run_briefings, CronTrigger(hour=settings.briefing_hour, minute=30), id="daily_briefing", **common)
```

`BRIEFING_HOUR=25` fails at startup with `Input should be less than or equal to 23`.

**Lesson 6, Exercise 3**

```python
import pytest

from organizer.config import Settings


@pytest.mark.parametrize("raw", ["postgres://u:p@h/db", "postgresql://u:p@h/db"])
def test_database_url_uses_psycopg3(raw):
    s = Settings(database_url=raw, anthropic_api_key="x", telegram_bot_token="y")
    assert s.database_url == "postgresql+psycopg://u:p@h/db"


def test_sqlite_url_untouched():
    s = Settings(database_url="sqlite:///./x.db", anthropic_api_key="x", telegram_bot_token="y")
    assert s.database_url == "sqlite:///./x.db"
```

**Lesson 9, Exercise 3** — expected `sudo ss -tlnp` output has `0.0.0.0:22` / `[::]:22` (sshd) and
`0.0.0.0:80`, `0.0.0.0:443` (docker-proxy for Caddy). Port 5432 and 8000 must **not** appear on `0.0.0.0`; they
exist only inside Docker's private network.

**Lesson 11, Exercise 2**

```bash
docker compose up -d --scale worker=2
```

```bash
docker compose logs -f worker
```

One container logs `scheduler_starting`; the other logs `scheduler_lock_held_elsewhere; standing by` every 30 s.
Stop the active one with `docker stop organizer-worker-1` (check the name with `docker compose ps`): its connection
closes, Postgres releases the lock, and within 30 s the standby logs `scheduler_starting`.

**Lesson 12, Exercise 2**

```python
# migrations/versions/xxxx_add_user_timezone.py
def upgrade() -> None:
    op.add_column("users", sa.Column("timezone", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "timezone")
```

```python
# migrations/versions/yyyy_backfill_user_timezone.py
def upgrade() -> None:
    op.execute("UPDATE users SET timezone = 'Europe/London' WHERE timezone IS NULL")


def downgrade() -> None:
    pass   # data backfill; nothing to undo
```

Only in a *later* release, once all code writes a timezone, would you make the column `nullable=False`.

**Lesson 14, Exercise 3**

```python
import json
import logging

from organizer.observability import JsonFormatter


def test_json_formatter_includes_extra_fields():
    record = logging.makeLogRecord({"name": "t", "levelname": "INFO", "msg": "tool_call",
                                    "tool": "list_tasks", "duration_ms": 12.5})
    data = json.loads(JsonFormatter().format(record))
    assert data["msg"] == "tool_call"
    assert data["tool"] == "list_tasks"
    assert data["duration_ms"] == 12.5
```

(`makeLogRecord` builds the record directly; with `caplog` you'd format `caplog.records[0]` the same way.)

**Lesson 15, Exercise 2**

```bash
docker compose stop db
```

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/readyz
```

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/healthz
```

Expected: `503` then `200`. Bring the database back with `docker compose start db`.

**Lesson 17, Exercise 2** — inside the agent loop's tool section:

```python
start = time.perf_counter()
ok, result = True, None
try:
    result = TOOLS[block.name](**block.input)
except Exception as exc:
    ok, result = False, f"Error: {exc}"
duration_ms = round((time.perf_counter() - start) * 1000, 1)
TOOL_CALLS.labels(block.name, str(ok).lower()).inc()
log.info("tool_call", extra={
    "trace_id": trace_id, "tool": block.name, "arguments": block.input,
    "ok": ok, "duration_ms": duration_ms, "result_preview": str(result)[:200],
})
```

And a query for one run, in order:

```sql
SELECT created_at, purpose, stop_reason, input_tokens, output_tokens, cost_usd, tool_uses
FROM llm_calls
WHERE trace_id = 'paste-a-trace-id'
ORDER BY id;
```

**Lesson 18, Exercise 3**

```python
# in Settings
llm_model_by_purpose: dict[str, str] = {}      # env: LLM_MODEL_BY_PURPOSE='{"briefing": "a-cheaper-model-id"}'

def model_for(self, purpose: str) -> str:
    return self.llm_model_by_purpose.get(purpose, self.llm_model)
```

pydantic-settings parses JSON for `dict` fields from the environment. Call
`traced_create(..., purpose="briefing", model=settings.model_for("briefing"), ...)`, add the cheaper model to
`PRICES_PER_MTOK`, and after a week compare with:

```sql
SELECT purpose, model, count(*), sum(cost_usd)
FROM llm_calls
WHERE created_at > now() - interval '7 days'
GROUP BY purpose, model;
```

**Capstone — `check_spend_spike`** (`AlertSent` is a small model like `BriefingSent` with a unique `(kind, day)`;
also import `datetime`, `ZoneInfo` and `IntegrityError`)

```python
def check_spend_spike() -> None:
    settings = get_settings()
    spent = spent_today()
    limit = Decimal(str(settings.daily_budget_usd))
    if spent < SPIKE_THRESHOLD * limit:
        return
    today = datetime.now(ZoneInfo(settings.timezone)).date()
    with SessionLocal() as session:
        session.add(AlertSent(kind="spend_spike", day=today))   # unique (kind, day)
        try:
            session.commit()
        except IntegrityError:
            return                                              # already alerted today
    notify_admin(f"Heads up: AI spend today is ${spent:.2f} of ${limit:.2f}.")
```

Schedule it with `scheduler.add_job(check_spend_spike, "interval", minutes=15, id="spend_spike", **common)`.

---

## Recommended Resources

| Resource | Type | Best for |
|---|---|---|
| docs.docker.com — "Get started" and the Dockerfile best-practices guide | Official docs | Images, layers, multi-stage builds, Compose |
| *Docker Deep Dive* (Nigel Poulton) | Book | Understanding containers properly |
| The Twelve-Factor App (12factor.net) | Short essay | The principles behind config, logs and processes |
| DigitalOcean Community Tutorials ("Initial Server Setup with Ubuntu") | Articles | Clear, tested Linux server walkthroughs |
| caddyserver.com/docs | Official docs | Caddyfile syntax and automatic HTTPS |
| render.com/docs (Blueprint spec) / fly.io/docs | Official docs | PaaS deployment details and current plan names |
| docs.github.com/actions | Official docs | Workflow syntax, secrets, environments |
| alembic.sqlalchemy.org | Official docs | Migrations, autogenerate caveats |
| docs.sentry.io/platforms/python | Official docs | Sentry setup and integrations |
| langfuse.com/docs | Official docs | LLM tracing, cost tracking, evaluations |
| *Site Reliability Engineering* (Google, free at sre.google/books) | Book | Monitoring, alerting and on-call thinking — read the "Monitoring Distributed Systems" chapter |
| Healthchecks.io docs | Official docs | Heartbeat monitoring patterns for cron jobs |

**Next:** Section 8 — Safety and Security (permissions, confirmations before risky actions, prompt injection
defences, and sandboxing your assistant's tools).
