# ROB/RUB Mapping Portal Design

## Scope

Build an open, login-free mapping portal. A user selects a Regional Office (RO), then a PIU belonging to that RO, then a project belonging to that RO and PIU. The user can add one or more ROB/RUB proposal IDs to the selected project. Dashboard functionality is excluded.

## Architecture

Use one repository and one Vercel project. Vite builds the React frontend as static files. FastAPI is exposed through Vercel's Python serverless runtime under `/api`. Only FastAPI connects to Supabase using the service-role key, so the secret never reaches the browser.

## Database

The user imports their CSV data into these Supabase tables:

- `rob_rub_master`: source records keyed by `proposal_id`, including the state value used when creating a mapping.
- `projects`: organizational hierarchy records containing `ro`, `piu`, `project_name`, and unique `upc`.
- `rob_rub_project_mapping`: mapping records containing `proposal_id`, `upc`, copied project details, state, and creation time.

Database constraints enforce unique proposal IDs in the master table, unique UPCs in the projects table, and one mapping per `(proposal_id, upc)` pair. This permits one project to contain many ROB/RUBs while preventing the same ROB/RUB from being added to the same project twice.

## Frontend

The application contains one mapping form:

1. RO dropdown populated from distinct `projects.ro` values.
2. PIU dropdown populated from records under the selected RO.
3. Project dropdown populated from records under the selected RO and PIU.
4. A list of ROB/RUB proposal-ID inputs.
5. An **Add another ROB/RUB** button that appends another input row.
6. A remove button on additional rows.
7. A submit button that creates the mappings.

Changing an RO clears the PIU, project, and ROB/RUB result state. Changing a PIU clears the project and result state. Dropdowns are disabled until their parent selection exists. At least one non-empty proposal ID is required. Duplicate IDs entered in the same form are rejected before submission.

## API

- `GET /api/ros` returns sorted distinct RO names.
- `GET /api/pius?ro=<ro>` returns sorted distinct PIUs for that RO.
- `GET /api/projects?ro=<ro>&piu=<piu>` returns the matching projects with UPCs.
- `POST /api/mappings` accepts one selected project UPC and a list of proposal IDs.

The mapping endpoint verifies that the UPC exists, checks every proposal ID against `rob_rub_master`, detects existing mappings, and inserts valid mappings. It returns a per-ID result so the frontend can show which IDs were saved, invalid, duplicated in the request, or already mapped. Valid IDs may be saved even when other submitted IDs fail; the response makes partial success explicit.

## Error Handling

The UI shows loading states, disables repeated submission, and displays plain-language errors. FastAPI returns consistent JSON errors for missing query parameters, nonexistent projects, unavailable Supabase service, and malformed requests. Detailed credentials or internal exception messages are never returned to the browser.

## Security

There is no authentication by request. Anyone with the public URL can create mappings. The Supabase URL and service-role key exist only as backend environment variables in local `.env` and Vercel. `.env` is excluded from Git.

## Testing

Backend tests cover hierarchy filtering, invalid IDs, existing mappings, multiple mappings for one project, and partial success. Frontend tests cover dependent dropdown behavior, adding/removing ROB/RUB rows, client-side duplicate detection, request payloads, and result messages. Build and API smoke checks verify the Vercel layout.

## Deployment and Documentation

The repository includes Supabase schema SQL, expected CSV column templates, `.env.example`, local setup commands, Vercel configuration, deployment steps for a beginner, and troubleshooting guidance. Both the React frontend and FastAPI backend deploy together on Vercel.
