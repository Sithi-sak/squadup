-- 4.40: "Take action" on a flagged player can now send that Pal a warning, which arrives as a
-- notification. None of the existing types fit (it isn't a booking, message, review or payout),
-- so moderation gets its own.

alter type notification_type add value if not exists 'moderation';
