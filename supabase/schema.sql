create extension if not exists pgcrypto;

create table if not exists public.rob_rub_master (
  proposal_id text primary key,
  serial_no integer,
  proposal_date date,
  name_of_work text,
  division_railway text,
  district text,
  state text,
  associated_road_authority text,
  category_of_road text,
  name_of_road text
);

create table if not exists public.projects (
  upc text primary key,
  serial_no integer,
  ro text not null,
  piu text not null,
  project_name text not null,
  constraint projects_values_not_blank check (
    length(trim(upc)) > 0 and length(trim(ro)) > 0 and
    length(trim(piu)) > 0 and length(trim(project_name)) > 0
  )
);

create table if not exists public.rob_rub_project_mapping (
  mapping_id uuid primary key default gen_random_uuid(),
  proposal_id text not null references public.rob_rub_master(proposal_id),
  upc text not null references public.projects(upc),
  project_name text not null,
  piu text not null,
  regional_office text not null,
  state text,
  date_mapped timestamptz not null default now(),
  constraint one_project_per_proposal unique (proposal_id)
);

create index if not exists projects_ro_piu_idx on public.projects (ro, piu);
create index if not exists mapping_upc_idx on public.rob_rub_project_mapping (upc);
create index if not exists mapping_proposal_id_idx on public.rob_rub_project_mapping (proposal_id);

alter table public.rob_rub_master enable row level security;
alter table public.projects enable row level security;
alter table public.rob_rub_project_mapping enable row level security;

-- No public policies are created. The FastAPI backend uses the server-only
-- service-role key, which bypasses RLS. Never expose that key in React.
