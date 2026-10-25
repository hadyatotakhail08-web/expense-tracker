import pytest
from app import app


@pytest.fixture()
def client():
	app.config["TESTING"] = True
	with app.test_client() as client:
		yield client


def test_health(client):
	response = client.get("/health")
	assert response.status_code == 200
	assert response.get_json()["status"] == "ok"


def test_add_and_list_expense(client):
	response = client.post(
		"/expenses",
		json={"item": "test", "amount": 1.5, "category": "ci"},
	)
	assert response.status_code == 201

	listing = client.get("/expenses")
	assert any(expense["item"] == "test" for expense in listing.get_json())
