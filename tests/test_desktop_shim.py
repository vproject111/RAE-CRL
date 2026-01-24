import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.crl.run_desktop import main, startup


@pytest.mark.asyncio
async def test_desktop_startup():
    with patch("apps.crl.run_desktop.init_db", new_callable=AsyncMock) as mock_db:
        await startup()
        mock_db.assert_called_once()


def test_desktop_main():
    with patch("apps.crl.run_desktop.ui.run") as mock_run:
        # Just verify main calls ui.run with correct params
        main()
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert kwargs.get("native") is True
        assert kwargs.get("title") == "RAE-CRL Lab Desk"
