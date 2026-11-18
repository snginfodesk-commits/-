-- תקציב הבית: טבלה אחת, שורה לכל מסמך של כל משתמש.
-- doc_id = 'main' (קטגוריות ותכנון) או 'm-YYYY-MM' (תנועות של חודש).
create table if not exists public.budget_docs (
  user_id    uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  doc_id     text        not null check (char_length(doc_id) <= 20),
  data       jsonb       not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, doc_id)
);

alter table public.budget_docs enable row level security;

-- כל משתמש רואה ומשנה רק את השורות של עצמו.
drop policy if exists "own rows" on public.budget_docs;
create policy "own rows" on public.budget_docs
  for all to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
