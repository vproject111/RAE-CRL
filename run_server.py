import os
import sys
from nicegui import ui
from apps.crl.core.database import init_db
from apps.crl.ui.main import main_page

async def startup():
    await init_db()

ui.timer(0.1, startup, once=True)

if __name__ in {"__main__", "__mp_main__"}:
    port = int(os.getenv("PORT", "8503"))
    host = os.getenv("HOST", "0.0.0.0")
    ui.run(
        title="RAE-CRL Lab Desk (Cognitive Research Loop)",
        host=host,
        port=port,
        reload=False,
        show=False,
    )
