# MyPage48 — Agent Instructions

Monorepo: `src/` (FastAPI backend), `frontend/` (SvelteKit 2 + Svelte 5 + TailwindCSS v4), `scraper/` (Python CLI).

## Agent workflows (`.agent/workflows/`)

These define standard procedures — follow them when applicable:

- `backend_test_runner.md` — how to run pytest
- `frontend_quality_check.md` — order: `npm run check && npm run format && npm run lint`
- `backend_service_template.md` — blueprint for new FastAPI services (Repository pattern)

## Commands

| Goal | Command |
|------|---------|
| Install all | `make install` |
| Run dev (both) | `make dev` |
| Run backend only | `make dev-be` (uvicorn reload, port 8000) |
| Run frontend only | `make dev-fe` (Vite dev, port 5173) |
| Full quality gate | `make check` |
| Backend checks | `scripts/lint-format.sh` → `pytest` |
| Frontend checks | `npm run check && npm run format && npm run lint` (from `frontend/`) |
| Create DB indexes | `make db-index` |

## Backend

- Entrypoint: `src/main.py` → FastAPI `app` with lifespan (DB connect, live monitor loop)
- Routes registered in `src/api.py` with prefix `/api`
- DI wiring in `src/dependencies.py`
- Config: pydantic-settings in `src/config.py` (reads `.env`)
- Service pattern per module: `constants.py`, `exceptions.py`, `http_exceptions.py`, `schemas.py`, `repository.py`, `service.py`, `route.py`
- Style (both `src/` and `scraper/`): `autoflake --exclude=__init__.py,_example` → `isort --profile black` → `black`; `flake8` (88 cols, ignore E203/W503, exclude `__init__.py,alembic/*,temp_*,_example`)
- Dev port: 8000; prod port: 8080
- Docker: `PYTHONPATH=/app/src`, production via `scripts/start-prod.sh`
- API key prefix: `ffk_`

## Frontend

- Dev: Vite proxies `/api` → localhost:8000
- Prettier: tabs, single quotes, no trailing commas, 100 width, `prettier-plugin-svelte`
- Build args: `PUBLIC_CLIENT_SIDE_API_BASE_URL`, `PUBLIC_SERVER_SIDE_API_BASE_URL`
- If npm fails, init NVM: `source ~/.nvm/nvm.sh && nvm use default`
- Production: `@sveltejs/adapter-node`, runs on port 5050 via `node build/index.js`
- `.npmrc` has `engine-strict=true` — Node version must match range

## Scraper (`scraper/`)

- Standalone CLI: `python jkt48scraper.py --members --news [PAGE|range|all] --schedule [YEAR|all|current] [--sync] [--merge]`
- Self-chdirs to `scraper/` on startup
- Uses `curl_cffi` + FlareSolverr for Cloudflare bypass
- Cookies: `data/cookies.json`; member ref: `src/active.members.json`

## Testing

- **Prerequisites**: MongoDB and MinIO must be running locally
- Docker Compose maps MongoDB to host port **27018** (not 27017). CI uses `localhost:27018`. Local `.env` defaults to `localhost:27017` — if running tests directly (not via Docker), use `27017`.
- Run: `.venv/bin/python -m pytest`
- Test DB: `mypage48_test` — auto-dropped per function
- Key fixtures in `tests/conftest.py`: `client` (httpx AsyncClient), `db`, `create_user`, `create_ticket`
- conftest monkeypatches bcrypt, mocks Resend emails, overrides CSRF to always pass
- pytest config: `asyncio_mode=auto`, `log_cli=INFO`

## Production

- **Troubleshooting** → consult `docs/DEPLOYMENT.md` first (nginx management, 502/503 debugging, SSL certs, health checks, log locations)
- Deploy on `v*` tag via GitHub Actions: SSH → `git pull` → `docker compose -f docker-compose.prod.yml up -d --build`
- Production config validation: HTTPS-only origins, no localhost URLs, SECRET_KEY ≥ 32 chars
- `OAUTHLIB_INSECURE_TRANSPORT=1` in dev for OAuth
