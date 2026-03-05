import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the global `activities` dict before/after each test.

    Arrange: copy the initial state, yield control to the test (Act), then
    restore the state (Assert/cleanup).
    """
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


@pytest.fixture
def client():
    """Provide a TestClient tied to the FastAPI app."""
    return TestClient(app)


def test_root_redirect(client):
    # Arrange: nothing special beyond fixture
    # Act (disable auto-following so we can inspect the redirect)
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    # Arrange
    expected = app_module.activities
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_success(client):
    # Arrange
    activity = "Chess Club"
    email = "new@mergington.edu"
    assert email not in activities[activity]["participants"]
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert "Signed up" in response.json()["message"]


def test_signup_duplicate(client):
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 400


def test_signup_nonexistent(client):
    # Arrange
    email = "foo@bar.com"
    # Act
    response = client.post("/activities/Nonexistent/signup", params={"email": email})
    # Assert
    assert response.status_code == 404


def test_unregister_success(client):
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    # Act
    response = client.delete(f"/activities/{activity}/unregister", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]


def test_unregister_not_signed_up(client):
    # Arrange
    activity = "Chess Club"
    email = "absent@mergington.edu"
    # Act
    response = client.delete(f"/activities/{activity}/unregister", params={"email": email})
    # Assert
    assert response.status_code == 404


def test_unregister_nonexistent(client):
    # Arrange
    email = "foo@bar.com"
    # Act
    response = client.delete("/activities/Nonexistent/unregister", params={"email": email})
    # Assert
    assert response.status_code == 404
