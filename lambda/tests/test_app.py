import io
import pytest
from ..app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    rv = client.get('/')
    assert rv.status_code == 200


def test_clear_session(client):
    rv = client.post('/api/clear_session')  # Adjusted to POST request
    assert rv.status_code == 200
    assert 'Session cleared successfully' in rv.get_json().get('message', '')  # Updated expected message

