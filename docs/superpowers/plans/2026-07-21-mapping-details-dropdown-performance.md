# Mapping Details, Dropdown, and Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display complete saved ROB/RUB details immediately, replace the Projects page native selects with polished downward-opening searchable dropdowns, and eliminate repeated RO/PIU API delays.

**Architecture:** Extend the existing `/api/projects` function with a hierarchy response and extend `/api/mappings` with `saved_records`, keeping the Vercel function count unchanged. Load and session-cache the hierarchy once in React, filter locally, and render saved/persisted mappings through a focused details-table component.

**Tech Stack:** React 19, React Router, Vitest, Testing Library, FastAPI, Pydantic, Supabase Python client, Vercel Python functions.

## Global Constraints

- Do not add authentication or change the manual certification rules.
- Do not add a Supabase table or restore the removed District field.
- Do not add another physical file under `api/`; Vercel Hobby must remain below 12 serverless functions.
- The RO and PIU option panels must always render below their controls.
- Invalid, duplicate, and already-mapped proposal IDs must not appear as newly saved detail records.

---

### Task 1: Project hierarchy API

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/repository.py`
- Modify: `backend/app.py`
- Modify: `tests/backend/test_api.py`
- Modify: `tests/backend/test_repository.py`

**Interfaces:**
- Produces: `GET /api/projects?hierarchy=true -> {"projects": ProjectSummary[]}`
- Produces: `Repository.list_project_hierarchy() -> list[dict]`
- Consumes: Existing `ProjectSummary` fields and Supabase `projects`/`rob_rub_project_mapping` tables.

- [ ] **Step 1: Write failing hierarchy API and repository tests**

Add an API assertion that one hierarchy request returns all test projects with `mapped_rob_rub_count`. Add a repository test proving it performs one projects read and one mapping read and correctly counts mappings per UPC.

```python
def test_project_hierarchy_returns_all_projects_with_mapping_counts():
    response = client.get("/api/projects", params={"hierarchy": "true"})
    assert response.status_code == 200
    projects = response.json()["projects"]
    assert {row["upc"] for row in projects} == {"UPC-001", "UPC-002", "UPC-003"}
    assert next(row for row in projects if row["upc"] == "UPC-001")["mapped_rob_rub_count"] == 1
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend\test_api.py::test_project_hierarchy_returns_all_projects_with_mapping_counts tests\backend\test_repository.py -q -p no:cacheprovider
```

Expected: failure because the hierarchy query and repository method do not exist.

- [ ] **Step 3: Implement the hierarchy contract**

Add:

```python
class ProjectHierarchy(BaseModel):
    projects: list[ProjectSummary]
```

Implement `list_project_hierarchy()` using one paginated projects query and one paginated mappings query. In `backend/app.py`, give `hierarchy=true` precedence over the RO/PIU listing branch while retaining `upc` project-detail behavior.

- [ ] **Step 4: Run focused and complete backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q -p no:cacheprovider
```

Expected: all backend tests pass.

- [ ] **Step 5: Commit checkpoint**

```powershell
git add backend tests/backend
git commit -m "Add project hierarchy API"
```

### Task 2: Complete saved mapping response

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/repository.py`
- Modify: `backend/app.py`
- Modify: `tests/backend/test_api.py`

**Interfaces:**
- Produces: `MappingResponse.results: MappingResult[]`
- Produces: `MappingResponse.saved_records: MappedRobRub[]`
- Consumes: `Repository.get_master_records(proposal_ids)` returning complete master rows.

- [ ] **Step 1: Write failing mapping-detail tests**

Extend the successful mapping test:

```python
response = client.post(
    "/api/mappings",
    json={"upc": "UPC-003", "proposal_ids": ["ROB-001", "ROB-003"]},
)
saved = response.json()["saved_records"]
assert [row["proposal_id"] for row in saved] == ["ROB-001", "ROB-003"]
assert saved[0]["name_of_work"] == "Delhi ROB"
assert saved[0]["state"] == "Delhi"
assert saved[0]["date_mapped"]
```

Extend the mixed-result test to assert only `status == "saved"` IDs occur in `saved_records`.

- [ ] **Step 2: Run mapping tests and verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend\test_api.py -k "mapping" -q -p no:cacheprovider
```

Expected: failure because `saved_records` is absent.

- [ ] **Step 3: Implement full master lookup and response**

Change the Supabase selection in `get_master_records` from `proposal_id,state` to:

```python
"proposal_id,proposal_date,name_of_work,division_railway,state,associated_road_authority,category_of_road,name_of_road"
```

Add `saved_records: list[MappedRobRub] = []` to `MappingResponse`. Build each saved record from the master row plus the single generated UTC `date_mapped` value used in the inserted mapping row. Return no detail record for invalid, duplicate, or already-mapped results.

- [ ] **Step 4: Run complete backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q -p no:cacheprovider
```

Expected: all backend tests pass.

- [ ] **Step 5: Commit checkpoint**

```powershell
git add backend tests/backend
git commit -m "Return saved ROB RUB details"
```

### Task 3: Searchable downward-opening dropdown and cached hierarchy

**Files:**
- Create: `src/components/SearchableSelect.jsx`
- Create: `src/components/SearchableSelect.test.jsx`
- Modify: `src/pages/ProjectsPage.jsx`
- Modify: `src/api.js`
- Modify: `src/styles.css`
- Modify: `tests/frontend/App.test.jsx`

**Interfaces:**
- Produces: `<SearchableSelect label value options onChange placeholder disabled loading />`
- Produces: `api.getProjectHierarchy() -> Promise<{projects: ProjectSummary[]}>`
- Consumes: `sessionStorage` key `rob-rub-project-hierarchy-v1`.

- [ ] **Step 1: Write failing dropdown tests**

Test that the option panel is a child of a positioned dropdown wrapper, opens after clicking the trigger, filters by typed search, selects using click and keyboard, and closes on Escape.

```jsx
render(<SearchableSelect label="Regional Office (RO)" value="" options={['Delhi','Mumbai']} onChange={onChange} placeholder="Select an RO" />)
await user.click(screen.getByRole('button', {name:/select an ro/i}))
expect(screen.getByRole('listbox')).toHaveClass('select-menu')
await user.type(screen.getByPlaceholderText(/search regional office/i), 'del')
expect(screen.getByRole('option', {name:'Delhi'})).toBeVisible()
expect(screen.queryByRole('option', {name:'Mumbai'})).not.toBeInTheDocument()
```

- [ ] **Step 2: Run the component test and verify RED**

Run:

```powershell
npm test -- --run src/components/SearchableSelect.test.jsx
```

Expected: failure because `SearchableSelect` does not exist.

- [ ] **Step 3: Implement `SearchableSelect` and its styles**

Use a `position: relative` wrapper and the following menu geometry:

```css
.searchable-select{position:relative}
.select-menu{position:absolute;top:calc(100% + 8px);left:0;right:0;z-index:40;max-height:280px;overflow:auto}
```

Implement outside-click cleanup, Escape, Arrow Up/Down, Enter, option search, disabled/loading appearance, selected checkmark, and `aria-expanded`, `role="listbox"`, and `role="option"` semantics.

- [ ] **Step 4: Write a failing Projects page performance test**

Mock `api.getProjectHierarchy` once, select an RO and PIU, then assert no `getRos`, `getPius`, or filtered `getProjects` call occurs and the correct project row appears.

```jsx
expect(api.getProjectHierarchy).toHaveBeenCalledTimes(1)
expect(api.getPius).not.toHaveBeenCalled()
expect(api.getProjects).not.toHaveBeenCalled()
expect(await screen.findByText('Example Project')).toBeVisible()
```

- [ ] **Step 5: Run the Projects page test and verify RED**

Run:

```powershell
npm test -- --run tests/frontend/App.test.jsx
```

Expected: failure because the page still calls separate endpoints.

- [ ] **Step 6: Implement one-request hierarchy loading and session cache**

Add `getProjectHierarchy()` to `src/api.js`. In `ProjectsPage`, initialize from `sessionStorage`, request the hierarchy once, replace the cache after success, derive sorted ROs and PIUs with `Set`, and filter projects in memory. If cached data exists, keep it visible if background refresh fails.

- [ ] **Step 7: Run all frontend tests**

Run:

```powershell
npm test -- --run
```

Expected: all frontend tests pass.

- [ ] **Step 8: Commit checkpoint**

```powershell
git add src tests/frontend
git commit -m "Improve project dropdown speed and design"
```

### Task 4: Immediate and persisted mapping details table

**Files:**
- Create: `src/components/MappedRobRubTable.jsx`
- Modify: `src/pages/CertificationPage.jsx`
- Modify: `src/styles.css`
- Modify: `tests/frontend/App.test.jsx`

**Interfaces:**
- Produces: `<MappedRobRubTable records />`
- Consumes: `project.mappings` from project detail and `response.saved_records` from mapping creation.

- [ ] **Step 1: Write failing frontend tests**

Mock `api.createMappings` with one result and one complete saved record. Submit an ID and assert the table immediately shows its proposal ID, name of work, state, and proposal date without a second `api.getProject` call. Add a load test where `api.getProject` already contains a mapping and assert it renders.

```jsx
expect(await screen.findByRole('heading', {name:/mapped robs\/rubs/i})).toBeVisible()
expect(screen.getByText('ROB-001')).toBeVisible()
expect(screen.getByText('Delhi ROB')).toBeVisible()
expect(api.getProject).toHaveBeenCalledTimes(1)
```

- [ ] **Step 2: Run the mapping-page tests and verify RED**

Run:

```powershell
npm test -- --run tests/frontend/App.test.jsx
```

Expected: failure because the detail table and immediate merge are absent.

- [ ] **Step 3: Implement details table and immediate merge**

Render the nine approved columns in a horizontally scrollable table. On save success, update project state with unique records keyed by `proposal_id`, increase `mapped_rob_rub_count`, keep existing status messages, clear successfully saved input rows, and disable the Save button while the request is active.

- [ ] **Step 4: Run all frontend tests and production build**

Run:

```powershell
npm test -- --run
npm run build
```

Expected: all frontend tests pass and Vite reports a successful production build.

- [ ] **Step 5: Commit checkpoint**

```powershell
git add src tests/frontend
git commit -m "Display mapped ROB RUB details"
```

### Task 5: Final verification and deployment handoff

**Files:**
- Verify: `api/`
- Verify: `backend/`
- Verify: `src/`
- Verify: `tests/`

**Interfaces:**
- Consumes all outputs from Tasks 1–4.
- Produces a tested Vercel-ready commit with fewer than 12 Python entry functions.

- [ ] **Step 1: Run complete verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q -p no:cacheprovider
npm test -- --run
npm run build
.\.venv\Scripts\python.exe -m compileall -q api backend
(Get-ChildItem api -Recurse -Filter *.py | Where-Object Name -ne '__init__.py').Count
```

Expected: all backend and frontend tests pass, build succeeds, compile exits without output, and the API entry-file count is no more than 12.

- [ ] **Step 2: Review the final diff**

```powershell
git status --short
git diff --check
```

Expected: only intended files are modified and `git diff --check` reports no whitespace errors.

- [ ] **Step 3: Push deployment commit**

```powershell
git add .
git commit -m "Improve mapping details and project selectors"
git push origin main
```

Expected: GitHub accepts the push and Vercel starts the connected production deployment.
