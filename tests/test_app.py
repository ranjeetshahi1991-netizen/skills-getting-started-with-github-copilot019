import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Chess Club"
EXISTING_EMAIL = "already-signed-up@example.com"
NEW_EMAIL = "new-student@example.com"


@pytest.fixture
def client(monkeypatch):
    activities = {
        ACTIVITY_NAME: {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 3,
            "participants": [EXISTING_EMAIL],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_participants = [EXISTING_EMAIL]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[ACTIVITY_NAME]["participants"] == expected_participants


def test_signup_adds_participant(client):
    # Arrange
    expected_message = f"Signed up {NEW_EMAIL} for {ACTIVITY_NAME}"

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": NEW_EMAIL}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    participants = client.get("/activities").json()[ACTIVITY_NAME]["participants"]
    assert participants == [EXISTING_EMAIL, NEW_EMAIL]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup", params={"email": NEW_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = EXISTING_EMAIL

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_unregister_removes_participant(client):
    # Arrange
    email = EXISTING_EMAIL

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {ACTIVITY_NAME}"}
    participants = client.get("/activities").json()[ACTIVITY_NAME]["participants"]
    assert participants == []


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    email = NEW_EMAIL

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{unknown_activity}/signup", params={"email": EXISTING_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}