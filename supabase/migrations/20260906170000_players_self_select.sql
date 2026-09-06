-- `stores/auth.ts`'s `loadAuthUser` queries `players` directly with the anon/authenticated
-- client to populate `AuthUser.playerId` (drives `isPal` in AppHeader/MessagesView/etc.), but
-- `players` was left locked to service_role only when RLS was enabled (2.5's `auth_wiring.sql`
-- deferred it to "each Phase 3 feature"). Nobody added it, so that query always returned no rows
-- and every Pal account looked like a plain buyer client-side until a manual patch. Add the
-- missing self-access policy, mirroring `users`' "view their own row" policy.
create policy "Players can view their own row"
  on public.players for select
  to authenticated
  using (auth.uid() = user_id);
