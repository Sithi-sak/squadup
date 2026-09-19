-- 4.28b: withdrawals become an admin-approved queue instead of settling themselves. The enum only
-- had ('paid', 'in_progress'), where `in_progress` doubled as "awaiting review" and nothing ever
-- moved a row off it. `requested` names that state explicitly, `rejected` is the admin's decline
-- (the Pal's coins are credited back), and `in_progress` stays for a payout that has been approved
-- and is with the payment provider.

alter type withdrawal_status add value if not exists 'requested' before 'paid';
alter type withdrawal_status add value if not exists 'rejected';
