# Deploying FirstHire (Vercel + Render)

```
Browser ──► Vercel (React app, https://<project>.vercel.app)
               │  /api/*  is proxied (rewrite) ──► Render (FastAPI + SQLite)
```

Why two hosts: the API keeps its data and login sessions in SQLite. Vercel functions are serverless,
so instances don't share a filesystem and SQLite would lose sessions. Render runs the API as one
long-lived process. Because Vercel proxies `/api/*`, the browser only ever talks to the Vercel domain,
so the HttpOnly session cookie works with no CORS setup.

## 0. Push the code to GitHub
```bash
git checkout -b deploy
git add .gitignore README.md DEPLOY.md render.yaml backend frontend
git status        # make sure DEMO_CREDENTIALS.local.md, .env, *.db and node_modules are NOT listed
git commit -m "FirstHire prototype"
git push -u origin deploy      # then merge into main via a PR
```

## 1. Backend on Render (free)
1. Get the demo passwords as one line:
   `cd backend && python -m app.seed --print-env` → copy the JSON after `DEMO_PASSWORDS=`.
2. render.com → **New → Blueprint** → pick the GitHub repo. It reads `render.yaml`.
3. Fill the secret values it asks for:
   - `DEMO_PASSWORDS` = the JSON from step 1 (required, or you get unknown random passwords)
   - `ANTHROPIC_API_KEY` = optional (empty = offline AI mode)
   - `COMPANIES_HOUSE_API_KEY`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` = optional
   - `LINKEDIN_REDIRECT_URI` = `https://<your-vercel-project>.vercel.app/api/auth/linkedin/callback` (only if using real LinkedIn)
4. Deploy, then open `https://<service>.onrender.com/api/health`. It should return `{"ok":true,...}`.

Notes: the free tier sleeps after ~15 min idle (the first request then takes up to a minute), and its disk
is temporary: every restart re-creates the synthetic demo data automatically.

## 2. Frontend on Vercel
1. Edit `frontend/vercel.json`: replace `REPLACE-WITH-YOUR-BACKEND.onrender.com` with your Render host. Commit and push.
2. vercel.com → **Add New → Project** → import the repo.
3. **Root Directory: `frontend`**. Framework preset: **Vite** (build `npm run build`, output `dist`).
4. Deploy and open the URL. The second rewrite in `vercel.json` makes deep links like `/graduate/profile` work.

## 3. Before the demo
- Open `https://<service>.onrender.com/api/health` 2–3 minutes before presenting to wake the API.
- To reset the demo data: Render dashboard → **Manual Deploy → Restart service**.
- Real LinkedIn: in the LinkedIn developer app, add the Vercel callback URL above as an authorized redirect.
