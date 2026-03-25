import pytest
from fastapi.testclient import TestClient
from nicegui import app
from apps.crl.ui.main import main_page

@pytest.fixture
def client():
    # NiceGUI needs some setup to work with TestClient
    # We just need to make sure the app is initialized
    return TestClient(app)

def test_ui_root_smoke(client):
    """
    [SMOKE TEST] Verify the UI root page returns 200 OK.
    This covers the layout definition and basic rendering.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Check if some key UI strings are in the HTML response
    assert "RAE-CRL" in response.text
    assert "Lab Desk" in response.text

def test_ui_traces_rendering(client):
    """Verify that the page can be loaded even if it attempts to call load_traces."""
    # Since we are not using a full browser, we just check if the 
    # initial FastAPI response (which contains the JS/HTML shell) is correct.
    response = client.get("/")
    assert response.status_code == 200
