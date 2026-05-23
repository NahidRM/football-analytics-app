# Railway Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the app as a single Railway service — Next.js frontend built to static files and served by the FastAPI backend.

**Architecture:** `npm run build` compiles the React frontend into plain HTML/CSS/JS files in `frontend/out/`. FastAPI serves those files alongside the API using a path-based catch-all route. A `nixpacks.toml` at the repo root tells Railway to install both Node.js and Python dependencies, build the frontend, then start the Python server.

**Tech Stack:** FastAPI (Python), Next.js 14 static export, Railway (Nixpacks build system)

---

## File Map

| File | Change |
|------|--------|
| `frontend/next.config.mjs` | Add `output: 'export'` |
| `frontend/app/analysis/[id]/page.tsx` | Add `generateStaticParams` export |
| `frontend/lib/api.ts` | Change fallback URL from `"http://localhost:8000"` to `""` |
| `backend/main.py` | Import Path + FileResponse, add `_FRONTEND_OUT`, catch-all route, remove Vercel CORS regex |
| `nixpacks.toml` | New file — Railway build + start config |

---

### Task 1: Enable Next.js static export

**Files:**
- Modify: `frontend/next.config.mjs`
- Modify: `frontend/app/analysis/[id]/page.tsx`

The `output: 'export'` config tells Next.js to produce a folder of plain files instead of running a Node server. Dynamic routes (like `/analysis/[id]`) require a `generateStaticParams` export under static export — returning an empty array means "handle all IDs client-side at runtime, don't pre-render any."

- [ ] **Step 1: Update next.config.mjs**

Replace the full file contents:

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
};

export default nextConfig;
```

- [ ] **Step 2: Add generateStaticParams to the analysis page**

Open `frontend/app/analysis/[id]/page.tsx`. Add this export immediately before the `export default function AnalysisPage` line (currently line 211):

```typescript
// Required by Next.js static export for dynamic routes.
// Empty array = no pages pre-rendered; all IDs are handled client-side.
export function generateStaticParams() {
  return [];
}
```

- [ ] **Step 3: Run the build and verify the output directory is created**

```bash
cd frontend && npm run build
```

Expected: build completes without errors. You should see a new `frontend/out/` directory containing `index.html` and an `_next/` folder.

If the build fails with "Page ... is missing generateStaticParams()", make sure Step 2 was applied to the correct file.

- [ ] **Step 4: Commit**

```bash
git add frontend/next.config.mjs "frontend/app/analysis/[id]/page.tsx"
git commit -m "feat: enable Next.js static export for Railway deployment"
```

---

### Task 2: Fix API base URL for production

**Files:**
- Modify: `frontend/lib/api.ts` (line 1)

In production, the frontend is served from the same domain as the API. API calls should use relative paths (`/matches`, `/analyze`, etc.) so they automatically go to the right server. The current fallback `"http://localhost:8000"` would be baked into the production build and break all API calls.

- [ ] **Step 1: Change the fallback URL**

In `frontend/lib/api.ts`, change line 1 from:

```typescript
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
```

to:

```typescript
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
```

In production, `NEXT_PUBLIC_API_URL` is not set, so `BASE` becomes `""`. A fetch to `""  + "/matches"` resolves to `/matches` on the current domain — which is the FastAPI server. Locally, `frontend/.env.local` still sets `NEXT_PUBLIC_API_URL=http://localhost:8000`, so nothing changes for local development.

- [ ] **Step 2: Rebuild and verify localhost:8000 is not in the output**

```bash
cd frontend && npm run build && grep -r "localhost:8000" out/ | head -5
```

Expected: no output (the string `localhost:8000` should not appear in the built files).

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/api.ts
git commit -m "fix: use relative API URL in production build"
```

---

### Task 3: Serve frontend from FastAPI

**Files:**
- Modify: `backend/main.py`

FastAPI needs to serve the built frontend files. The approach:
1. Compute the path to `frontend/out/` relative to `main.py` using `Path(__file__)` — this works regardless of what directory uvicorn is started from.
2. Add a catch-all route `/{full_path:path}` at the **end** of `main.py` (after all API routes). FastAPI evaluates routes in registration order, so explicit routes like `/matches` and `/analyze` match first; this catch-all only fires for unknown paths.
3. The catch-all serves the file if it exists (JS, CSS, images), or falls back to `index.html` (for all app routes like `/analysis/apf:1234`).
4. The whole block is conditional on the `out/` directory existing — so local dev without a build is unaffected.

- [ ] **Step 1: Add the imports and path constant**

At the top of `backend/main.py`, add `Path` and `FileResponse` to the existing imports. Find this line:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
```

Replace with:

```python
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Absolute path to the Next.js static export output directory.
# Path(__file__) is backend/main.py, so .parent.parent is the repo root.
_FRONTEND_OUT = Path(__file__).parent.parent / "frontend" / "out"
```

- [ ] **Step 2: Remove the stale Vercel CORS regex**

Find the CORS middleware block:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Replace with:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # local dev only; production is same-origin
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 3: Add the catch-all route at the very end of main.py**

Append these lines after the final `raise HTTPException(...)` line at the bottom of `main.py`:

```python

# ── Static frontend (production only) ────────────────────────────────────────
# Only registered when the Next.js build output exists.
# API routes above are registered first, so they always take priority.
if _FRONTEND_OUT.exists():
    app.mount("/_next", StaticFiles(directory=str(_FRONTEND_OUT / "_next")), name="next-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve built frontend files; fall back to index.html for SPA routing."""
        file_path = _FRONTEND_OUT / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_FRONTEND_OUT / "index.html"))
```

- [ ] **Step 4: Test locally — serve the built frontend from FastAPI**

Make sure the frontend is already built (Task 1 Step 3). Then start only the backend:

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app" && uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000 in a browser. Expected: the app loads (the match selector page). Open http://localhost:8000/matches in a browser. Expected: JSON response (the API route still works).

- [ ] **Step 5: Commit**

```bash
git add backend/main.py
git commit -m "feat: serve Next.js static export from FastAPI for single-server deployment"
```

---

### Task 4: Add Railway build config

**Files:**
- Create: `nixpacks.toml` (repo root)

Railway uses a build system called Nixpacks to automatically detect languages and build apps. By default it would try to start the app as either Python or Node.js, not both. The `nixpacks.toml` overrides this: install both runtimes, build the frontend during the build phase, then start only the Python server.

- [ ] **Step 1: Create nixpacks.toml at the repo root**

```toml
# Railway build config.
# Installs Node.js (for frontend build) and Python (for backend).
# Builds the Next.js frontend first, then starts the FastAPI server.

[phases.setup]
nixPkgs = ["nodejs_20"]

[phases.install]
cmds = [
  "pip install -r backend/requirements.txt",
  "cd frontend && npm ci"
]

[phases.build]
cmds = ["cd frontend && npm run build"]

[start]
cmd = "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
```

**Why `$PORT`?** Railway dynamically assigns a port and passes it as an environment variable. Using `--port $PORT` tells uvicorn to listen on that port.

**Why `npm ci` instead of `npm install`?** `npm ci` installs exact versions from `package-lock.json` and is faster/more reliable in CI environments.

- [ ] **Step 2: Verify the file is at the repo root (not inside backend/ or frontend/)**

```bash
ls "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app/nixpacks.toml"
```

Expected: the file exists.

- [ ] **Step 3: Commit**

```bash
git add nixpacks.toml
git commit -m "chore: add nixpacks.toml for Railway single-service deployment"
```

---

### Task 5: Deploy to Railway

**No code changes** — this task connects the repo to Railway and triggers the first deploy.

- [ ] **Step 1: Push all commits to the remote**

```bash
git push
```

- [ ] **Step 2: Create a new Railway project**

1. Go to https://railway.app and sign in
2. Click **New Project**
3. Choose **Deploy from GitHub repo**
4. Select the `Analysis app` repository
5. Railway will immediately start a deployment

- [ ] **Step 3: Share the environment variables with the service**

The API keys were added as Shared Variables in the previous session. They now need to be linked to the service:

1. In the Railway project, click on the service that was created
2. Go to **Variables** tab
3. Click **Shared Variable** → select `ANTHROPIC_API_KEY` → click **Add**
4. Repeat for `API_FOOTBALL_KEY`

- [ ] **Step 4: Watch the first deployment build log**

In the Railway dashboard, click on the active deployment to see the build log. The log should show:

```
==> Installing Node.js
==> pip install -r backend/requirements.txt   ← Python deps
==> npm ci                                     ← Node deps
==> npm run build                              ← Frontend build
==> uvicorn backend.main:app ...               ← Server starts
```

If the build fails, read the error in the log — it will tell you exactly what went wrong (most likely a missing package or path issue in nixpacks.toml).

- [ ] **Step 5: Open the deployed app**

Once the deployment shows as **Active** (green), click the **Generate Domain** button in Railway to get a public URL (e.g. `https://analysis-app-production.up.railway.app`).

Open the URL in a browser. Expected: the match selector loads and matches appear.

Open `<your-url>/matches` directly. Expected: JSON list of matches.

- [ ] **Step 6: Verify the API keys are working**

In the app, click a match and run a **Match Stats** analysis. Expected: chart renders. This confirms `API_FOOTBALL_KEY` is wired up correctly.

Click **Generate Content** on the result. Expected: newsletter and Twitter draft appear. This confirms `ANTHROPIC_API_KEY` is wired up correctly.
