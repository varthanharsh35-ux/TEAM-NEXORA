# Deployment

Use `Nexora` as the project/build root. The Dockerfile uses Node 24 and Python 3.12. Both deployment options preserve the existing frontend and `/api` routes.

## One persistent service

Deploy the included Dockerfile on a Docker-capable host. `render.yaml` provides a Render blueprint with a persistent disk; a paid disk-capable plan is required. If the repository contains the outer workspace, configure `Nexora` as the service root.

Mount a persistent volume at `/var/lib/gramsahayak`. Set `APP_ENV=production`, `LOCAL_LLM=0`, and `DATA_DIR=/var/lib/gramsahayak`. The host supplies `PORT` (default 8000). The service serves both the frontend and API. Use HTTPS and one service instance/worker with this SQLite architecture. Back up the volume regularly.

`ALLOWED_ORIGINS` is a comma-separated list of exact trusted frontend origins, such as `https://your-site.example`. Include the public domain if the proxy changes the backend Host header. Do not use wildcards.

Local container verification:

```sh
docker build -t gramsahayak .
docker run --rm -p 8000:8000 -e APP_ENV=development -v gramsahayak-data:/var/lib/gramsahayak gramsahayak
```

The development override permits cookies over local HTTP. Keep production mode for HTTPS hosting.

## Vercel frontend with persistent backend

1. Deploy the Docker service and verify its `/api/health` returns status `ok`.
2. Import `Nexora` into Vercel. Select Node 24 and framework preset **Other**. Keep the commands from `vercel.json`. Leave Output Directory unset: the build creates `.vercel/output` using the Build Output API.
3. Set Vercel's `BACKEND_ORIGIN` environment variable to the backend HTTPS origin, without an `/api` suffix. Missing or invalid configuration deliberately fails the build with a clear message.
4. Add the exact Vercel domain and custom frontend domain to the backend's `ALLOWED_ORIGINS`, and restart the backend. Explicitly include preview domains where login is needed.
5. Deploy. The frontend calls same-origin `/api`; Vercel proxies requests to the backend. Cookies stay associated with the frontend domain. No browser CORS setup or client-side API secrets are needed.

SQLite must not live on an ephemeral serverless filesystem: accounts, reports, ledgers, map caches and advice caches need the persistent volume. Horizontal scaling requires migrating storage to a shared database.

In production, generating/reopening reports and accessing financial records requires signing in. Record ownership is derived from the session, not caller-supplied user IDs. Development mode retains the existing guest API behavior. Configure host-level traffic limits and volume backups for public use.

Vercel references: [Build Output API](https://vercel.com/docs/build-output-api) and [routing configuration](https://vercel.com/docs/build-output-api/configuration).

## Data and optional services

Core reports, finance, curated translations and accounts need no AI key. Optional `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` belong only on the backend. Local model weights are excluded from the image; curated guidance remains available when no provider is configured or the provider fails.

New installations start with empty databases. To migrate records, stop writes, back up existing `data/*.sqlite3` files, and copy them to the persistent volume. Do not publish databases or `.env` files. Reference datasets and model files stay separate from writable storage.

Maps depend on external map providers. Speech depends on browser/device voices; Tamil and Hindi voices may need installing. WhatsApp opens a compose window for the user to send the message.

## Verification

```sh
python -m unittest discover -s backend -p 'test_*.py'
cd frontend
npm ci
npm run check:i18n
npm run build
```

After hosting, check `/api/health`, report generation, three language selections, financial/repayment views, WhatsApp, Listen/Stop, account registration/login and workspace saving. Restart the backend and verify saved records persist. Public-domain TLS, proxy and volume behavior require verification on the actual host.
