-- Auth wiring for SquadUp (CHECKPOINT.md 2.5).
-- Google OAuth (and any future provider) creates the `auth.users` row directly, with no app
-- code in between, so `public.users` needs a trigger to stay populated rather than relying on a
-- signup endpoint. `security definer` lets it write despite `public.users` RLS being enabled.

create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.users (id, email, display_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- First real RLS policies (the 2.3/2.4 tables were left policy-less on purpose, deferred to
-- here). Frontend now talks to Supabase directly with the anon/publishable key for Auth and its
-- own profile row, so `users` needs a self-access policy; every other table stays locked to
-- service_role only until each Phase 3 feature adds its own policies.
create policy "Users can view their own row"
  on public.users for select
  to authenticated
  using (auth.uid() = id);

create policy "Users can update their own row"
  on public.users for update
  to authenticated
  using (auth.uid() = id)
  with check (auth.uid() = id);
