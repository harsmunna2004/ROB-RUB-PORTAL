# ROB/RUB Mapping Portal

This application reads the RO → PIU → project hierarchy from Supabase and lets a user map one or many ROB/RUB proposal IDs to the selected project. It uses React, FastAPI, Supabase PostgreSQL, and one Vercel deployment. There is intentionally no login or dashboard.

## 1. What is included

- Dependent dropdowns: selecting an RO filters PIUs; selecting a PIU filters projects.
- An **Add another ROB/RUB** button for adding several IDs to one project.
- Validation against `rob_rub_master`.
- Duplicate protection for the same proposal ID and project.
- Per-ID results when part of a multiple-ID request fails.
- SQL schema, CSV templates, automated tests, and Vercel configuration.

## 2. Install the required software

Install these programs before continuing:

1. **Node.js 20 or newer:** <https://nodejs.org/en/download>
2. **Python 3.12:** <https://www.python.org/downloads/>
3. **Git:** <https://git-scm.com/downloads>
4. **VS Code** (recommended editor): <https://code.visualstudio.com/>
5. Create free accounts at <https://supabase.com>, <https://github.com>, and <https://vercel.com>.

During Python installation on Windows, enable **Add python.exe to PATH**.

Verify installation in PowerShell:

```powershell
node --version
npm --version
python --version
git --version
```

## 3. Open the project

Open PowerShell and go to this folder. Replace the example path if you copied the project elsewhere:

```powershell
cd "C:\Users\reddy\Documents\Codex\2026-07-20\ple"
```

Open it in VS Code:

```powershell
code .
```

## 4. Create the Supabase database

1. Sign in at <https://supabase.com/dashboard>.
2. Click **New project**.
3. Enter a project name, create a strong database password, select a nearby region, and click **Create new project**.
4. Wait until the project finishes provisioning.
5. In the left menu, click **SQL Editor** and then **New query**.
6. Open `supabase/schema.sql` from this project, copy all its contents into the query editor, and click **Run**.
7. Open **Table Editor**. You should see `rob_rub_master`, `projects`, and `rob_rub_project_mapping`.

Do not manually import anything into `rob_rub_project_mapping`; the application fills that table.

## 5. Prepare and import your CSV files

Supabase import requires the CSV header names to match the database columns exactly. Compare your files with:

- `sample-data/rob_rub_master_template.csv`
- `sample-data/projects_template.csv`

Your ROB/RUB CSV header must be:

```text
proposal_id,serial_no,proposal_date,name_of_work,division_railway,district,state,associated_road_authority,category_of_road,name_of_road
```

Your projects CSV header must be:

```text
upc,serial_no,ro,piu,project_name
```

Rename the original spreadsheet headings before importing. For example, rename `PROPOSAL_ID(ROB_RUB_ID)` to `proposal_id`, `RO` to `ro`, `PIU` to `piu`, and `PROJECT NAME` to `project_name`.

Import the files:

1. In Supabase, open **Table Editor** → `rob_rub_master`.
2. Click **Insert** → **Import data from CSV**.
3. Select your ROB/RUB CSV, confirm the column mapping, and import it.
4. Open the `projects` table and repeat the process with the projects CSV.
5. Check that every `proposal_id` and every `upc` is unique. Supabase will reject duplicates because they are primary keys.
6. Check that `ro`, `piu`, `project_name`, and `upc` contain no blank cells.

If `proposal_date` contains invalid dates, correct them to `YYYY-MM-DD`, for example `2026-01-15`, or leave the cell empty.

## 6. Obtain the Supabase backend values

In Supabase:

1. Open **Project Settings** → **API**.
2. Copy the **Project URL**. This becomes `SUPABASE_URL`.
3. Copy the **service_role** secret key. This becomes `SUPABASE_SERVICE_ROLE_KEY`.

The service-role key is powerful. Never put it in React, never prefix it with `VITE_`, never paste it into chat, and never commit `.env` to GitHub.

## 7. Configure the local environment

In the project root, copy the example file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace both example values:

```dotenv
SUPABASE_URL=https://abcdefghijk.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-real-service-role-key
```

Save and close Notepad.

## 8. Install the frontend

In PowerShell, from the project root:

```powershell
npm install
```

This creates `node_modules`. It can take several minutes the first time.

## 9. Install the backend

Create a Python virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in the same window and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install backend and test dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## 10. Run locally

You need two PowerShell terminals.

### Terminal 1: FastAPI

```powershell
cd "C:\Users\reddy\Documents\Codex\2026-07-20\ple"
.\.venv\Scripts\Activate.ps1
Get-Content .env | ForEach-Object {
  if ($_ -match '^([^#][^=]*)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
  }
}
uvicorn api.index:app --reload --port 8000
```

Keep this terminal open. Test the health endpoint in a browser: <http://127.0.0.1:8000/api/health>. You should see `{"status":"ok"}`.

### Terminal 2: React

```powershell
cd "C:\Users\reddy\Documents\Codex\2026-07-20\ple"
npm run dev
```

Open <http://localhost:5173>. The Vite development server automatically forwards `/api` requests to FastAPI on port 8000.

## 11. Use the application

1. Select an RO. The PIU dropdown becomes active and displays only PIUs under that RO.
2. Select a PIU. The project dropdown displays only projects under that RO and PIU.
3. Select a project.
4. Enter the first ROB/RUB proposal ID exactly as it appears in `rob_rub_master`.
5. To add another ID to the same project, click **Add another ROB/RUB**.
6. Add as many rows as needed, up to 100 per request. Use **Remove** to delete an extra row.
7. Click **Save mappings**.
8. Read the result shown beside every ID. Valid IDs can be saved even if another ID in the same request is invalid.

## 12. Run automated checks

Activate the Python environment and run backend tests:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest tests/backend -v
```

Run frontend tests:

```powershell
npm test -- --run
```

Create the production frontend build:

```powershell
npm run build
```

## 13. Upload the code to GitHub

Do not continue until `.env` is listed inside `.gitignore`.

Create an empty repository on GitHub without adding a README. Then run these commands, replacing the URL:

```powershell
git init
git add .
git commit -m "Build ROB RUB mapping portal"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rob-rub-mapping-portal.git
git push -u origin main
```

Confirm on GitHub that `.env`, `.venv`, and `node_modules` are absent.

## 14. Deploy React and FastAPI together on Vercel

The project uses `api/index.py`, a Vercel-recognized FastAPI entrypoint. The `vercel.json` file sends non-API browser routes to React while leaving `/api/*` for FastAPI.

1. Sign in to Vercel using GitHub.
2. Click **Add New** → **Project**.
3. Import the GitHub repository you created.
4. Keep the framework preset as **Vite** if Vercel detects it.
5. Confirm:
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`
6. Expand **Environment Variables**.
7. Add `SUPABASE_URL` with your Supabase project URL.
8. Add `SUPABASE_SERVICE_ROLE_KEY` with your Supabase service-role key.
9. Apply both variables to Production, Preview, and Development.
10. Click **Deploy**.
11. When deployment finishes, open the provided URL.
12. Test `https://YOUR-VERCEL-DOMAIN.vercel.app/api/health` first.
13. Then open the main domain and test the full dropdown and mapping workflow.

Vercel currently supports FastAPI applications exported as `app` from `api/index.py`, and installs Python dependencies from root `requirements.txt`. If the Vercel dashboard auto-fills a Python-only preset instead of Vite, explicitly set the build command and output directory shown above.

## 15. Updating the deployed app

After changing code:

```powershell
git add .
git commit -m "Describe the change"
git push
```

Vercel automatically creates a new deployment from the pushed commit.

## 16. Troubleshooting

### RO dropdown is empty

- Confirm the `projects` table contains rows.
- Confirm its columns are exactly `ro`, `piu`, `project_name`, and `upc`.
- Open the browser developer tools with F12, select **Network**, and inspect `/api/ros`.
- Confirm both Vercel environment variables are present, then redeploy.

### “Database service is not configured or is unavailable”

- Check spelling: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
- Do not use the anon/publishable key in place of the service-role key.
- After changing Vercel variables, open **Deployments**, select the latest deployment menu, and click **Redeploy**.

### An ID is reported as invalid

- Search the Supabase `rob_rub_master` table for the exact `proposal_id`.
- Check spaces, capitalization, hyphens, and leading zeroes in the imported CSV.

### An ID is already mapped

The proposal ID already belongs to a project. Each proposal ID can be mapped only once across the entire system. A project may still contain many different proposal IDs.

### Vercel `/api/health` returns 404

- Confirm `api/index.py` is present on GitHub.
- Confirm `requirements.txt` is in the repository root.
- Remove any catch-all rewrite that includes `/api/`; the supplied negative-lookahead rule intentionally excludes API paths.
- Review the Vercel build log for Python dependency errors.

### Local React page reports a network error

- Confirm FastAPI is still running on port 8000.
- Confirm React is running on port 5173.
- Do not open `index.html` directly; use <http://localhost:5173>.

## API reference

- `GET /api/health`
- `GET /api/ros`
- `GET /api/pius?ro=Delhi`
- `GET /api/projects?ro=Delhi&piu=Dwarka`
- `POST /api/mappings`

Example POST body:

```json
{
  "upc": "UPC-001",
  "proposal_ids": ["ROB-001", "RUB-002"]
}
```

The backend keeps the project name, PIU, RO, and state in the mapping row as a historical snapshot. The authoritative selection still comes from the `projects` table, and the state comes from `rob_rub_master`.
