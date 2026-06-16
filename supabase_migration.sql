-- 1. Create the new bots table
create table bots (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  description text,
  created_at  timestamptz default now()
);

-- 2. Modify the existing crawl_jobs table to belong to a bot
-- Note: This will delete existing orphan jobs if you want strict referential integrity.
-- If you want to keep them, remove the `not null`.
alter table crawl_jobs 
add column bot_id uuid references bots(id) on delete cascade;

-- If you don't care about old data, you can clear the table first:
-- delete from crawl_jobs;
-- alter table crawl_jobs alter column bot_id set not null;
