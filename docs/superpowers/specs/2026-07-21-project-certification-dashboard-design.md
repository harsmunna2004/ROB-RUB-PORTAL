# Project Certification, ROB/RUB Register, and Dashboard Design

## Objective

Expand the open ROB/RUB Mapping Portal into a four-page workflow for project certification, ROB/RUB mapping, master-register browsing, and management reporting. No login or admin authentication is required.

## Navigation and Pages

Use React Router so browser navigation, direct URLs, breadcrumbs, and Back actions work correctly.

The persistent header contains links to:

- Projects
- ROB/RUB Database
- Dashboard

Routes:

- `/projects`: select an RO and PIU, then view the project certification grid.
- `/projects/:upc/certify`: review one project, decide whether it contains ROBs/RUBs, map records when necessary, and certify it.
- `/rob-rubs`: browse and filter the complete ROB/RUB master register.
- `/dashboard`: view overall, RO-wise, and PIU-wise summaries and download them as CSV.

Every detail page includes breadcrumbs and a Back button.

## Project Certification Grid

The Projects page first loads the existing RO and PIU selectors. After the user selects a PIU, show a grid with:

- UPC
- Project Name
- Certification Status
- Number of mapped ROBs/RUBs
- Action

The Action button opens `/projects/:upc/certify`.

Certification status is independent of mapping count. A project can be certified with zero mappings.

## Certification Workflow

The certification page displays project identity, current status, and mapped-count summary. Before allowing certification, ask:

> Are there any ROBs/RUBs in this project?

If the user chooses **Yes**:

1. Display one proposal-ID input.
2. Allow additional inputs with an Add button.
3. Validate and save mappings using the existing global proposal-ID uniqueness rule.
4. Show per-ID results.
5. After successful mapping, allow the user to confirm project certification.

If the user chooses **No**:

1. Do not display mapping inputs.
2. Explain that the project will be certified with zero mappings.
3. Show a confirmation action.
4. Certify the project without requiring any mapping.

Certification is manual. Clicking Certify Project requires confirmation and sets the status to `certified` with a timestamp. A Reopen Project action returns the status to `pending` and clears the certification timestamp without deleting mappings.

The page contains a button leading to the complete ROB/RUB Database.

## ROB/RUB Database

Display all records from `rob_rub_master` using server-side pagination so large tables do not overload the browser or Vercel function.

Displayed fields:

- Proposal ID
- Proposal date
- Name of work
- Division/Railway
- District
- State
- Associated road authority
- Category of road
- Name of road
- Mapping status
- Mapped UPC and project name when mapped

Search operates across every displayed textual field. Filters include:

- State
- District
- Category of road
- Division/Railway
- Mapping status: All, Mapped, Pending

The page provides clear loading, empty-result, and error states. Filters reset pagination to the first page.

No city field or City filter will be added because the source table does not contain city data.

## Dashboard

Overall summary cards:

- Projects certified: projects with `certification_status = 'certified'`
- Projects pending: projects with `certification_status = 'pending'`
- Total ROBs/RUBs: all records in `rob_rub_master`
- Mapped ROBs/RUBs: master records present in `rob_rub_project_mapping`
- Pending ROBs/RUBs: master records absent from `rob_rub_project_mapping`

Summary tables show the same metrics grouped:

- RO-wise
- PIU-wise within each RO

Dashboard filters allow selection of RO and PIU. A Download CSV button exports the currently filtered summary. The CSV contains the filter context, overall totals, RO rows, and PIU rows in a spreadsheet-friendly format.

## Database Changes

Add these columns to `projects`:

```sql
certification_status text not null default 'pending'
certified_at timestamptz null
```

Add a check constraint limiting status to `pending` or `certified`. Add an index on `(ro, piu, certification_status)` for grid and dashboard queries.

The existing mapping model remains unchanged:

- One proposal ID can belong to only one project.
- One project can have zero, one, or many proposal IDs.

Provide an idempotent Supabase migration for existing databases and update the complete schema for new databases.

## Backend Design

Keep FastAPI and the existing repository boundary. Add typed models and repository methods for:

- Project grid rows with status and mapped count
- Project detail with existing mappings
- Certify/reopen status updates
- Paginated ROB/RUB register queries and filter options
- Dashboard totals and grouped summaries
- CSV response generation

New API operations:

- `GET /api/projects?ro=&piu=` returns enriched project grid rows.
- `GET /api/projects/{upc}` returns project detail and mappings.
- `PATCH /api/projects/{upc}/certification` accepts `pending` or `certified`.
- `GET /api/rob-rubs` accepts page, page size, search, and filter parameters.
- `GET /api/rob-rubs/filters` returns distinct filter values.
- `GET /api/dashboard` accepts optional RO and PIU filters.
- `GET /api/dashboard.csv` returns the current summary as CSV.

Because this Vite deployment requires explicit Vercel Python entrypoints, add physical entry modules for every new top-level API path while reusing the same FastAPI `app`.

## Frontend Structure

Split the current large component into focused units:

- `AppShell`: header, navigation, and route outlet
- `Breadcrumbs`: shared breadcrumbs
- `ProjectsPage`: RO/PIU selection and certification grid
- `CertificationPage`: decision, mapping, and certification workflow
- `RobRubDatabasePage`: search, filters, paginated table
- `DashboardPage`: summary cards, grouped tables, and CSV action
- Reusable loading, error, status badge, and pagination components

API calls remain centralized in `src/api.js`. Preserve the current visual identity while extending it to responsive tables and mobile layouts.

## Error Handling

- Backend configuration or Supabase failures return a stable user-facing 503 message and log the original server error.
- Missing projects return 404.
- Invalid certification statuses and malformed query parameters return 422.
- Mapping conflicts continue returning per-proposal results rather than failing the whole batch.
- Frontend pages show inline retryable errors and never render stale data after hierarchy or filter changes.
- CSV download failures show an inline dashboard error.

## Testing and Verification

Backend tests cover:

- Grid counts and certification status
- Certifying a project with zero mappings
- Certifying after mappings
- Reopening without deleting mappings
- Search across all register fields
- Each filter and combined filters
- Pagination boundaries
- Dashboard overall calculations
- RO/PIU grouping
- CSV content and headers
- Vercel entrypoint availability

Frontend tests cover:

- Route navigation, breadcrumbs, and Back actions
- RO/PIU grid loading
- Yes and No certification branches
- Mapping and certification actions
- Search/filter/pagination behavior
- Dashboard rendering and CSV download
- Loading, empty, and error states

Verification includes the full backend suite, frontend suite, production Vite build, SQL migration review, and deployed smoke tests for every new API and page route.

## Deployment Sequence

1. Run the Supabase migration.
2. Commit and push application changes.
3. Let Vercel deploy with the existing environment variables.
4. Verify API health, grid, certification, register, dashboard, and CSV endpoints.
5. Verify all frontend routes on the deployed URL, including direct navigation and browser refresh.

