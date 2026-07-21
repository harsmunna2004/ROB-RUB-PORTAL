# Delete Project Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users delete an incorrect project mapping before certification or after reopening while permanently preserving the ROB/RUB master record.

**Architecture:** Add a protected DELETE operation to the existing `/api/mappings` FastAPI/Vercel function, targeting a mapping by UPC and Proposal ID. Add row-level deletion to the existing mapping table and update React state immediately after success.

**Tech Stack:** FastAPI, Supabase Python client, Pydantic, React 19, Vitest, Testing Library, Vercel Python functions.

## Global Constraints

- Delete only from `rob_rub_project_mapping`; never delete or update `rob_rub_master`.
- Allow deletion only when the project certification status is `pending`.
- Reopened projects are pending and therefore allow deletion.
- Keep the current Vercel Python entry-file count unchanged.
- Require user confirmation before issuing a deletion request.

---

### Task 1: Protected mapping DELETE API

**Files:**
- Modify: `backend/repository.py`
- Modify: `backend/app.py`
- Modify: `tests/backend/test_api.py`

**Interfaces:**
- Produces: `DELETE /api/mappings?upc=<upc>&proposal_id=<proposal_id>`
- Produces: `Repository.delete_mapping(upc: str, proposal_id: str) -> bool`
- Consumes: `Repository.get_project_detail(upc)` for project status validation.

- [ ] **Step 1: Write failing backend tests**

```python
def test_pending_project_mapping_can_be_deleted_without_touching_master():
    client, repository = make_client()
    before_master = dict(repository.master)
    response = client.delete("/api/mappings", params={"upc": "UPC-001", "proposal_id": "RUB-002"})
    assert response.status_code == 200
    assert response.json() == {"proposal_id": "RUB-002", "message": "Mapping deleted successfully."}
    assert repository.master == before_master
    assert all(row["proposal_id"] != "RUB-002" for row in repository.mappings)

def test_certified_project_mapping_cannot_be_deleted():
    client, repository = make_client()
    repository.projects[0]["certification_status"] = "certified"
    response = client.delete("/api/mappings", params={"upc": "UPC-001", "proposal_id": "RUB-002"})
    assert response.status_code == 409
```

Also test that a mismatched UPC/Proposal ID returns 404 and leaves the mapping in place.

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend\test_api.py -k "deleted or delete" -q -p no:cacheprovider
```

Expected: failure because DELETE `/api/mappings` is not implemented.

- [ ] **Step 3: Implement the repository deletion**

Add the protocol method and Supabase implementation:

```python
def delete_mapping(self, upc: str, proposal_id: str) -> bool:
    rows = (
        self.client.table("rob_rub_project_mapping")
        .delete()
        .eq("upc", upc)
        .eq("proposal_id", proposal_id)
        .execute()
        .data
    )
    return bool(rows)
```

This method must not access `rob_rub_master`.

- [ ] **Step 4: Implement the protected endpoint**

Add `DELETE` to CORS methods and add an endpoint that loads the project detail, returns 404 when the project is missing, returns 409 when `certification_status != "pending"`, calls `delete_mapping`, and returns 404 when no exact mapping is deleted.

- [ ] **Step 5: Run the complete backend suite**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q -p no:cacheprovider
```

Expected: all backend tests pass.

### Task 2: Row-level deletion interface

**Files:**
- Modify: `src/api.js`
- Modify: `src/components/MappedRobRubTable.jsx`
- Modify: `src/components/MappedRobRubTable.css`
- Modify: `src/pages/CertificationPage.jsx`
- Modify: `src/App.test.jsx`

**Interfaces:**
- Produces: `api.deleteMapping(upc, proposalId) -> Promise<{proposal_id,message}>`
- Produces: `<MappedRobRubTable records canDelete deletingId onDelete />`
- Consumes: Project `certification_status` and existing `project.mappings`.

- [ ] **Step 1: Write failing frontend tests**

Test a pending project with a mapping, confirm deletion, and assert the row and count disappear immediately. Test a certified project has no Delete button. Reopen it and assert the Delete button appears.

```jsx
expect(screen.getByRole('button', {name:'Delete mapping ROB-001'})).toBeVisible()
await user.click(screen.getByRole('button', {name:'Delete mapping ROB-001'}))
expect(window.confirm).toHaveBeenCalledWith('Delete mapping ROB-001 from this project?')
expect(await screen.findByText('Mapping ROB-001 deleted. The master record is unchanged.')).toBeVisible()
expect(screen.queryByText('Delhi ROB')).not.toBeInTheDocument()
```

- [ ] **Step 2: Run the focused test and verify RED**

```powershell
npm test -- --run src/App.test.jsx -t "deletes a mapping"
```

Expected: failure because no Delete action exists.

- [ ] **Step 3: Add API client and table action**

Implement:

```javascript
deleteMapping: (upc, proposalId) => request(`/api/mappings?${query({upc, proposal_id:proposalId})}`, {method:'DELETE'})
```

Add an Action heading and red Delete buttons only when `canDelete` is true. Disable only the record matching `deletingId` and label it `Deleting…` while awaiting the response.

- [ ] **Step 4: Update Certification page state**

Confirm using the exact Proposal ID. On success, filter that ID from `project.mappings`, set `mapped_rob_rub_count` to the remaining length, and show `Mapping <ID> deleted. The master record is unchanged.` On failure, retain the row and display the API error.

- [ ] **Step 5: Run complete verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q -p no:cacheprovider
npm test -- --run
npm run build
.\.venv\Scripts\python.exe -m compileall -q api backend
(Get-ChildItem api -Recurse -Filter *.py | Where-Object Name -ne '__init__.py').Count
```

Expected: all tests pass, the build succeeds, Python compilation produces no error, and the API entry count remains 9.
