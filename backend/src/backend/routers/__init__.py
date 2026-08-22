from . import (
    admin,
    auth,
    bookings,
    feed,
    messages,
    notifications,
    players,
    reviews,
    subscriptions,
    wallet,
)

routers = [
    auth.router,
    players.router,
    bookings.router,
    messages.router,
    reviews.router,
    feed.router,
    wallet.router,
    notifications.router,
    subscriptions.router,
    admin.router,
]
