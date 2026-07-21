# Mapping Details, Dropdown, and Performance Design

## Objective

Improve the project certification workflow in three connected areas:

1. After a user saves one or more proposal IDs, show the corresponding ROB/RUB master details on the same page.
2. Replace the RO and PIU native selects with polished custom dropdowns that always open below their controls.
3. Remove the repeated 4–5 second waits when choosing an RO and PIU by loading the project hierarchy once and filtering it locally.

## Project hierarchy data flow

The Projects page will make one request to a new hierarchy mode on the existing `/api/projects` serverless function. Reusing the existing function avoids increasing the Vercel Hobby function count.

The response will contain the project rows required by the page: `ro`, `piu`, `upc`, `project_name`, `certification_status`, `certified_at`, and `mapped_rob_rub_count`. The frontend will derive unique sorted RO and PIU options from this response and filter projects in memory.

The response will be cached in `sessionStorage`. Returning to the Projects page in the same browser tab will render existing options immediately while a background refresh obtains current data. Selecting an RO or PIU will not make another API request.

The backend will obtain project rows and mapping counts with a bounded number of Supabase queries rather than one query per RO or PIU. Empty or null organization values will be excluded from dropdown choices.

## Custom dropdown component

A reusable `SearchableSelect` component will replace the native RO and PIU `<select>` controls on the Projects page.

The component will:

- Render its option panel below the control with an explicit positioned popover.
- Provide an internal search input when opened.
- Use the portal’s navy, green, and neutral colors, with hover and selected states.
- Display a chevron, selected value, empty state, and loading state.
- Close on outside click or Escape.
- Support keyboard navigation with Arrow Up, Arrow Down, Enter, and Escape.
- Keep the PIU control disabled until an RO is selected.
- Reset PIU and the project grid when RO changes.

The panel will have a maximum height and vertical scrolling, so a long list will remain usable without opening upward.

## Saved mapping details

The mapping operation will return full ROB/RUB master details for every successfully saved proposal ID. The backend master lookup will select all available master fields needed by the UI instead of only `proposal_id` and `state`.

The mapping response will retain its per-ID status results and add a `saved_records` collection. Each saved record will contain:

- Proposal ID
- Proposal date
- Name of work
- Division/Railway
- State
- Associated road authority
- Category of road
- Name of road
- Date mapped

After a successful save, the Certification page will immediately merge `saved_records` into the project’s existing mappings and render one “Mapped ROBs/RUBs” table. This avoids a second network request and provides immediate confirmation.

When the page is opened later, `GET /api/projects?upc=...` will continue loading all previously mapped records from the mapping and master tables, so the same table remains persistent after refresh.

Invalid, duplicate-in-request, and already-mapped IDs will remain in the per-ID results area with their existing explanatory messages. They will not be inserted into the details table.

## Error and loading behavior

- The Projects page will show dropdown skeleton/loading text only during the initial hierarchy request when no cached data exists.
- A failed background refresh will keep cached options visible and show a retryable warning.
- A failed initial request will show the existing error alert and retry action.
- The Save mappings button will be disabled while saving to prevent duplicate submissions.
- If some IDs save and others fail validation, successful records will still appear in the details table and failed records will show their individual messages.

## Testing

Backend tests will verify:

- The hierarchy response includes projects and mapped counts in one request contract.
- Mapping creation returns complete details for successfully saved records.
- Invalid, duplicate, and previously mapped IDs are excluded from `saved_records`.
- Project detail still returns persisted master details after reload.

Frontend tests will verify:

- RO and PIU selection uses the preloaded hierarchy without additional API calls.
- The custom dropdown opens below its control and supports selection.
- Saved ROB/RUB details appear immediately after Save mappings.
- Existing mapped details render when the Certification page loads.

The complete backend test suite, frontend test suite, production build, and Python compile check must pass before deployment instructions are provided.

## Scope boundaries

This update does not add authentication, change certification rules, add new Supabase tables, or change dashboard behavior. It does not restore the removed District field or filter.
