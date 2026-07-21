# Project Certification and Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add project certification, an RO/PIU project grid, a searchable ROB/RUB register, management summaries, and CSV export to the existing open portal.

**Architecture:** Keep one FastAPI application and the existing Supabase repository boundary, extending both with typed certification, register, and dashboard interfaces. Replace the single React screen with React Router pages inside a shared shell; explicit Vercel entry modules expose every new API path.

**Tech Stack:** React 19, React Router DOM, Vite, FastAPI, Pydantic, Supabase/PostgreSQL, Vitest/Testing Library, Pytest, Vercel.

## Global Constraints

- No authentication. Certification is manual and may be completed with zero mappings.
- Ask whether a project has ROBs/RUBs before mapping or certification.
- One proposal maps to at most one project; one project has zero or many proposals.
- Use State and District; do not add City. Downloads are CSV only.
- Search all displayed ROB/RUB fields and filter State, District, Category, Division/Railway, and Mapping Status.
- Never expose `SUPABASE_SERVICE_ROLE_KEY` to React.

## File Map

- Database: create `supabase/003_add_project_certification.sql`; modify `supabase/schema.sql`.
- Backend: modify `api/models.py`, `api/repository.py`, `api/index.py`; create `api/rob_rubs.py`, `api/dashboard.py`.
- Backend tests: modify all three files under `tests/backend/`.
- Routing/shared UI: modify `package.json`, `pnpm-lock.yaml`, `src/App.jsx`, `src/main.jsx`, `src/api.js`, `src/styles.css`; create `src/components/AppShell.jsx`, `Breadcrumbs.jsx`, `StatusBadge.jsx`, `Pagination.jsx`.
- Pages: create `src/pages/ProjectsPage.jsx`, `CertificationPage.jsx`, `RobRubDatabasePage.jsx`, `DashboardPage.jsx` and focused tests for each.

---

### Task 1: Certification Schema

**Files:** Create `supabase/003_add_project_certification.sql`; modify `supabase/schema.sql`.

**Produces:** `projects.certification_status` and `projects.certified_at`.

- [ ] Add this idempotent migration:

```sql
alter table public.projects
  add column if not exists certification_status text not null default 'pending',
  add column if not exists certified_at timestamptz;
alter table public.projects drop constraint if exists projects_certification_status_check;
alter table public.projects add constraint projects_certification_status_check
  check (certification_status in ('pending', 'certified'));
create index if not exists projects_ro_piu_certification_idx
  on public.projects (ro, piu, certification_status);
```

- [ ] Add the same two columns, check constraint, and index to `schema.sql`.
- [ ] Run `rg -n "certification_status|certified_at" supabase` and confirm both files contain both fields.
- [ ] Commit with `git add supabase && git commit -m "Add project certification schema"`.

---

### Task 2: Project Grid and Certification API

**Files:** Modify `api/models.py`, `api/repository.py`, `api/index.py`, `tests/backend/test_api.py`, `tests/backend/test_repository.py`.

**Produces:** enriched project summaries, project detail, and certification update.

- [ ] Add failing tests asserting project rows include `certification_status`, `certified_at`, and `mapped_rob_rub_count`; detail includes current mappings; PATCH can certify with zero mappings and reopen without deleting mappings.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/backend -q -p no:cacheprovider`; expect failures for missing fields/routes.
- [ ] Add these contracts:

```python
class ProjectSummary(Project):
    certification_status: Literal["pending", "certified"]
    certified_at: datetime | None = None
    mapped_rob_rub_count: int = 0

class MappedRobRub(BaseModel):
    proposal_id: str
    name_of_work: str | None = None
    district: str | None = None
    state: str | None = None
    date_mapped: datetime

class ProjectDetail(ProjectSummary):
    mappings: list[MappedRobRub]

class CertificationRequest(BaseModel):
    status: Literal["pending", "certified"]
```

- [ ] Extend `Repository` with `get_project_detail(upc: str) -> dict | None` and `set_certification(upc: str, status: str) -> bool`. Enrich `list_projects` by counting mapping rows for returned UPCs.
- [ ] Implement certification timestamps with `datetime.now(timezone.utc).isoformat()` for certified and `None` for pending.
- [ ] Add `GET /api/projects/{upc}` returning 404 when absent and `PATCH /api/projects/{upc}/certification` accepting `CertificationRequest`.
- [ ] Run the backend suite; expect all tests to pass.
- [ ] Commit with message `Add project certification API`.

---

### Task 3: ROB/RUB Register API

**Files:** Modify backend models/repository/index/tests; create `api/rob_rubs.py`.

**Produces:** `GET /api/rob-rubs` and `GET /api/rob-rubs/filters`.

- [ ] Add failing tests for search by proposal/work/district/state/railway/authority/category/road name, every exact filter, mapped/pending status, combined filters, and page boundaries.
- [ ] Run the backend suite and confirm 404 failures.
- [ ] Add `RobRubRecord`, `RobRubPage`, and `RobRubFilters` models. `RobRubRecord` contains every master-table display field plus `mapping_status`, `mapped_upc`, and `mapped_project_name`.
- [ ] Implement this repository signature:

```python
def list_rob_rubs(self, page: int, page_size: int, search: str,
                  state: str, district: str, category: str,
                  division: str, mapping_status: str) -> dict: ...
def get_rob_rub_filters(self) -> dict: ...
```

- [ ] Enrich master rows from a proposal-to-mapping dictionary, case-fold search across every displayed value, apply filters, calculate `total`, then slice with `start = (page - 1) * page_size`.
- [ ] Add FastAPI query validation: `page >= 1`, `1 <= page_size <= 100`, and mapping status limited to `all|mapped|pending`.
- [ ] Create `api/rob_rubs.py` containing `from api.index import app` and `__all__ = ["app"]`; add `rob_rubs` to the Vercel-entrypoint test.
- [ ] Run all backend tests and commit with message `Add searchable ROB RUB register API`.

---

### Task 4: Dashboard and CSV API

**Files:** Modify backend models/repository/index/tests; create `api/dashboard.py`.

**Produces:** `GET /api/dashboard` and `GET /api/dashboard.csv`.

- [ ] Add failing tests for overall totals, RO grouping, PIU grouping, optional RO/PIU filters, and CSV headers/content disposition.
- [ ] Add models `DashboardTotals`, `DashboardRow`, and `DashboardResponse` with project total/certified/pending and ROB/RUB total/mapped/pending counts.
- [ ] Implement `get_dashboard(ro: str = "", piu: str = "") -> dict`; count mapped proposals only when their project belongs to the selected organizational scope.
- [ ] Add JSON route and CSV route. Generate CSV using `csv.writer(StringIO())` with columns `RO, PIU, Projects Total, Projects Certified, Projects Pending, ROBs/RUBs Total, ROBs/RUBs Mapped, ROBs/RUBs Pending`.
- [ ] Return CSV via `StreamingResponse` with `Content-Disposition: attachment; filename=rob-rub-dashboard.csv`.
- [ ] Create `api/dashboard.py` re-exporting `app`; update entrypoint test.
- [ ] Run all backend tests and commit with message `Add dashboard summary and CSV API`.

---

### Task 5: Router Shell and Project Grid

**Files:** Modify package/lockfile and core frontend files; create shared components and `ProjectsPage.jsx`.

**Produces:** `/projects`, `/projects/:upc/certify`, `/rob-rubs`, `/dashboard` routes.

- [ ] Run `pnpm add react-router-dom`.
- [ ] Add failing tests proving `/` redirects to `/projects`, header links exist, RO/PIU selection loads a table, and Manage navigates to the UPC certification route.
- [ ] Replace `App.jsx` with `BrowserRouter`, one `AppShell` layout route, redirect index, and the four page routes.
- [ ] Implement `AppShell` with persistent Projects, ROB/RUB Database, and Dashboard NavLinks plus `<Outlet />`.
- [ ] Implement `Breadcrumbs` from `{ label, to? }[]` items and `StatusBadge` for pending/certified.
- [ ] Move RO/PIU selection into `ProjectsPage`; render UPC, Project Name, Certification Status, mapped count, and Manage/View Link.
- [ ] Keep hierarchy requests in `src/api.js`; ensure changing RO clears PIU and projects, and changing PIU clears stale projects.
- [ ] Run `npm test -- --run`; expect all frontend tests to pass. Commit with message `Add routed project certification grid`.

---

### Task 6: Certification Decision Page

**Files:** Create `src/pages/CertificationPage.jsx` and test; modify `src/api.js`, `src/styles.css`.

**Consumes:** project detail, mapping POST, certification PATCH.

- [ ] Add failing tests for breadcrumbs/back, Yes showing mapping inputs, No hiding inputs and permitting zero-mapping certification, mapping results, confirmation, certified state, and reopen.
- [ ] Add API methods:

```javascript
getProject: (upc) => request(`/api/projects/${encodeURIComponent(upc)}`),
setCertification: (upc, status) => request(`/api/projects/${encodeURIComponent(upc)}/certification`, {
  method: 'PATCH', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status }),
}),
```

- [ ] Implement decision state `'' | 'yes' | 'no'`. Yes renders dynamic proposal inputs and Save Mappings; No explains zero mappings and renders Certify Project.
- [ ] After Yes, show certification only when at least one mapping is saved or project detail already has mappings. Use `window.confirm` for certify/reopen.
- [ ] Add breadcrumb `Projects / RO / PIU / UPC / Certification`, Back button using `navigate(-1)`, and Link to `/rob-rubs`.
- [ ] Run all frontend tests and commit with message `Add certification decision and mapping flow`.

---

### Task 7: ROB/RUB Database Page

**Files:** Create `Pagination.jsx`, `RobRubDatabasePage.jsx`, and test; modify API/styles.

- [ ] Add failing tests for all columns, 300ms debounced search, filters, filter reset to page 1, Previous/Next boundaries, loading, retryable error, and empty state.
- [ ] Add `getRobRubs(params)` and `getRobRubFilters()` using `URLSearchParams`.
- [ ] Fetch filter options once; refetch page data when search/filter/page/page-size changes. Render all approved fields inside `.table-scroll`.
- [ ] Implement `Pagination({ page, pageSize, total, onPageChange })`; display `Page X of Y` and correctly disable boundary buttons.
- [ ] Use empty copy `No ROB/RUB records match these filters.` and an inline Retry button on errors.
- [ ] Run frontend tests and commit with message `Add searchable ROB RUB database page`.

---

### Task 8: Dashboard Page and CSV Link

**Files:** Create `DashboardPage.jsx` and test; modify API/styles.

- [ ] Add failing tests for five cards, RO/PIU tables, hierarchy filters, loading/error states, and a CSV link containing current filters.
- [ ] Add `getDashboard(params)` and `dashboardCsvUrl(params)` using `URLSearchParams`.
- [ ] Render cards: Projects Certified, Projects Pending, Total ROBs/RUBs, Mapped ROBs/RUBs, Pending ROBs/RUBs.
- [ ] Render RO-wise and PIU-wise tables; filter changes refetch JSON and update the CSV anchor URL.
- [ ] Run frontend tests and commit with message `Add certification dashboard and CSV download`.

---

### Task 9: Responsive Polish and Full Verification

**Files:** Modify `src/styles.css`, `README.md`.

- [ ] Keep the navy/green identity. Add responsive header, breadcrumbs, tables, badges, metric cards, filters, certification branches, buttons, and pagination. Below 760px, stack forms and scroll only table wrappers horizontally.
- [ ] Document deployment order: run migration, push code, wait for Vercel, test APIs, then test direct frontend routes and refreshes.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/backend -q -p no:cacheprovider`; expect all backend tests to pass.
- [ ] Run `npm test -- --run`; expect all frontend tests to pass without unhandled errors.
- [ ] Run `npm run build`; expect Vite exit 0 with hashed assets in `dist/`.
- [ ] Run `git diff --check` and `rg -n "sb_secret_|service_role" --glob "!.env"`; confirm no whitespace errors or real secrets.
- [ ] Commit final polish/docs, run the Supabase migration, push, and smoke-test `/api/health`, `/api/projects`, `/api/rob-rubs`, `/api/dashboard`, `/projects`, `/rob-rubs`, and `/dashboard`.

