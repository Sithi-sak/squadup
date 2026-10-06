-- Lets a "booking" notification deep-link to its order (CHECKPOINT.md 4.69a): the Pal lands on
-- their Orders page with that order open, the buyer on Order Detail. Same shape as `thread_id`
-- (20260913060000_notification_thread_id.sql): nullable, and `on delete set null` so a
-- notification outlives its booking.

alter table public.notifications
  add column booking_id uuid references public.bookings (id) on delete set null;
