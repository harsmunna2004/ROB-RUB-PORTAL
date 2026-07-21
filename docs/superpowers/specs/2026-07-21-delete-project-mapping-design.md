# Delete Project Mapping Design

## Objective

Allow a user to correct an incorrectly mapped ROB/RUB by deleting only its row from `rob_rub_project_mapping`. The corresponding `rob_rub_master` record must remain unchanged and become available for mapping again.

## Availability rules

- A Delete action is available for each mapped ROB/RUB while the project has `certification_status = pending`.
- A certified project is read-only and does not display Delete actions.
- After the user clicks Reopen project, the status returns to `pending` and Delete actions become available again.
- The backend independently enforces the pending-status rule so a direct API request cannot modify a certified project.

## API and repository behavior

The existing `/api/mappings` Vercel function will add:

```text
DELETE /api/mappings?upc=<project-upc>&proposal_id=<proposal-id>
```

The endpoint will:

1. Validate that the project exists.
2. Reject the request with HTTP 409 when the project is certified.
3. Delete exactly one mapping matching both `upc` and `proposal_id`.
4. Return HTTP 404 when that mapping does not exist for the selected project.
5. Return a success response containing the deleted Proposal ID.

The repository deletion will target only `rob_rub_project_mapping`. No delete or update operation will be issued against `rob_rub_master`. No Supabase schema change or new Vercel function is required.

## User interface

`MappedRobRubTable` will accept deletion controls from the Certification page. When deletion is allowed, it will display an Action column with a red Delete button on each mapping row.

Clicking Delete will show a confirmation dialog naming the Proposal ID. After confirmation:

- The row button is disabled and displays a deleting state while the request runs.
- A successful response removes the record from local project state immediately.
- `mapped_rob_rub_count` decreases to the remaining number of mappings.
- A success message confirms that the mapping—not the master record—was removed.
- An API failure keeps the row and displays the backend error.

The table remains visible without an Action column when the project is certified. Reopening the project changes its status to pending, causing the Action column and Delete buttons to appear without reloading the page.

## Testing

Backend tests will verify successful deletion, exact UPC/Proposal ID matching, 404 for a missing mapping, rejection for certified projects, and preservation of the master record.

Frontend tests will verify the confirmation dialog, immediate row/count removal, absence of Delete buttons while certified, and reappearance of Delete buttons after reopening.

The complete backend test suite, frontend test suite, production build, Python compilation, and Vercel function-count check must pass before deployment.
