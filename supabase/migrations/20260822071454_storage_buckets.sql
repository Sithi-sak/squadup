-- Storage buckets for SquadUp (CHECKPOINT.md 2.4).
-- `public` only controls anonymous read via the public URL endpoint; writes to storage.objects
-- still go through RLS, which — same as the 2.3 schema — is enabled with no policies yet, so
-- only the backend's service_role client can upload/delete. Per-user upload policies (a Pal can
-- only write their own avatar, a buyer can only attach files to their own dispute, etc.) land
-- alongside real Supabase Auth (2.5) and each Phase 3 feature.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('avatars', 'avatars', true, 5242880, array['image/png', 'image/jpeg', 'image/webp']),
  ('service-covers', 'service-covers', true, 8388608, array['image/png', 'image/jpeg', 'image/webp']),
  ('rank-verification', 'rank-verification', false, 10485760, array['image/png', 'image/jpeg', 'application/pdf']),
  ('id-documents', 'id-documents', false, 10485760, array['image/png', 'image/jpeg', 'application/pdf']),
  ('dispute-attachments', 'dispute-attachments', false, 20971520, array['image/png', 'image/jpeg', 'image/webp', 'video/mp4', 'video/quicktime'])
on conflict (id) do nothing;

-- Backs Create Service's cover image upload (`CreateServiceView.vue`), storing the path in the
-- `service-covers` bucket. Missed in the 2.3 migration since the mock's `PlayerServiceListing`/
-- `PlayerServiceDetail` shapes don't carry an image field, only the create-service UI does.
alter table public.services add column cover_image_url text;

-- Backs the ID front/back uploads in the Become a Pal wizard's Verify step (`StepVerify.vue`,
-- `VerifyStepData`). Paths, not raw files, live in `id-documents` and are never exposed on the
-- public profile.
alter table public.players add column id_front_url text;
alter table public.players add column id_back_url text;

-- Rank verification has no upload UI yet (`StepGames.vue`'s "Highest rank" is plain text), but
-- the bucket is explicitly scoped in CHECKPOINT.md 2.4, so the column is provisioned ahead of
-- that UI landing.
alter table public.players add column rank_verification_url text;

-- Backs `RefundModal`'s "Add screenshots or a clip" evidence upload on the Order Detail report
-- flow, into `dispute-attachments`. `order_disputes.attachment_urls` (added in 2.3) already
-- holds the resulting paths, so no column change needed here.
