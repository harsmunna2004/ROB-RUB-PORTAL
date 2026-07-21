alter table public.projects
  add column if not exists certification_status text not null default 'pending',
  add column if not exists certified_at timestamptz;

alter table public.projects
  drop constraint if exists projects_certification_status_check;

alter table public.projects
  add constraint projects_certification_status_check
  check (certification_status in ('pending', 'certified'));

create index if not exists projects_ro_piu_certification_idx
  on public.projects (ro, piu, certification_status);
