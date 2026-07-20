-- Run the duplicate-report query first. If it returns rows, decide which
-- mapping to keep and delete the unwanted rows in Table Editor before running
-- the ALTER TABLE statements below.

select
  proposal_id,
  count(*) as mapping_count,
  array_agg(project_name order by date_mapped) as mapped_projects
from public.rob_rub_project_mapping
group by proposal_id
having count(*) > 1
order by proposal_id;

-- Run these statements only after the query above returns no rows.
alter table public.rob_rub_project_mapping
  drop constraint if exists one_mapping_per_project;

alter table public.rob_rub_project_mapping
  drop constraint if exists one_project_per_proposal;

alter table public.rob_rub_project_mapping
  add constraint one_project_per_proposal unique (proposal_id);
