import os
import sys

from nicegui import ui

from apps.crl.core.database import init_db
from apps.crl.ui.main import main_page

# Ensure we can find 'apps' module even when frozen
if getattr(sys, "frozen", False):
    sys.path.append(os.path.join(sys._MEIPASS))  # type: ignore


async def startup():
    # Initialize SQLite DB on startup
    await init_db()


def main():
    # Configure nicegui to run in native mode (requires pywebview)
    # If pywebview is missing, it will fallback to browser
    ui.run(
        title="RAE-CRL Lab Desk",
        native=True,
        window_size=(400, 800),  # Mobile-like / Sidebar-like dimensions
        port=native_mode_port(),
        reload=False,
    )


def native_mode_port():
    # Find a free port or fixed one
    return 8503


if __name__ in {"__main__", "__mp_main__"}:
    # Hook startup logic
    ui.timer(0.1, startup, once=True)
    main()
