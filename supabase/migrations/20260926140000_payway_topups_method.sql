-- 4.58: "QR Scan" top-ups now go through PayWay's real KHQR (`generate-qr`) too, so a
-- `payway_topups` row records which method it was paid with. Existing rows are all card.

alter table public.payway_topups
  add column method text not null default 'card' check (method in ('card', 'khqr'));
