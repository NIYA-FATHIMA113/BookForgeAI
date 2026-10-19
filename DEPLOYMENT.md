# Deploy BookForge AI on Render

This repo is configured as two Render web services plus a managed PostgreSQL database. The `render.yaml` Blueprint creates the services and database.

## Before deploying

1. Put `backend/`, `frontend/`, and the root `render.yaml` together at the root of one GitHub repository. In this local workspace, Git is currently initialized inside `backend/`, so the frontend and Blueprint are not in that Git repository yet; Render needs a repository containing all three.
2. In Render, create a new Blueprint and connect that repository. Review the resources and apply the Blueprint.
3. In the `bookforge-frontend` service environment, set `VITE_API_BASE_URL` to the API service's public URL, for example `https://bookforge-api.onrender.com` (no trailing slash).
4. In the `bookforge-api` service environment, set `CORS_ALLOWED_ORIGINS` to the frontend's public URL, for example `https://bookforge-frontend.onrender.com` (no trailing slash). Add additional comma-separated origins if you use a custom domain.
5. Add at least one AI provider key (`GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`) to the API service if you want live AI features. Keep keys in Render's environment settings; do not commit them.
6. Redeploy both services after setting these values. The API start command applies database migrations before starting Gunicorn.

Render generates `SECRET_KEY` and connects `DATABASE_URL` from the managed database. Django derives its allowed hostname from Render's `RENDER_EXTERNAL_HOSTNAME`, disables debug mode, and serves collected static files through WhiteNoise.

## Local production-like configuration

The Django settings use `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL` (or the `DB_*` fields), and `CORS_ALLOWED_ORIGINS` environment variables. Vite reads `VITE_API_BASE_URL` at build time. Local development keeps the existing localhost defaults.

## Important deployment notes

- Render's free web services may sleep when idle, so the first request after a quiet period can be slow.
- The Blueprint selects a free Postgres database for a temporary preview. Render free Postgres expires after 30 days and has no backups; choose a paid database plan with backups before storing real customer data.
- The API service uses local media storage. If you later add user-uploaded files, configure persistent object storage before relying on uploads in production.
- Rotate any API credentials that were ever committed or exposed in a shared repository.
