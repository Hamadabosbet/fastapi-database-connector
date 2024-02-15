from fastapi.testclient import TestClient
from fastapi import status
from main import app
import json
import pytest
from unittest.mock import patch, MagicMock

client = TestClient(app=app)

@pytest.fixture
def customers_data():
    with open('./files/customers.json', 'r') as file:
        return json.load(file)

def test_index_return_string():
    response = client.get('/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "Ahalan! You can fetch some json by navigating to '/json'"

def test_create_saint():
    saint_data = {
        "id": 1,  
        "name": "hhhh John",
        "age": 30,
        "occupation": {  
            "id": 1,
            "name": "FATHER",
            "isSaint": True  
        }
    }
    
    with patch('main.db_connection') as mock_connection:
        with patch.object(mock_connection, 'cursor') as mock_cursor:
            mock_execute = MagicMock()
            mock_cursor.return_value.execute = mock_execute
            mock_connection.return_value.commit.return_value = None
            response = client.post("/saints/", json=saint_data)

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == saint_data

def test_get_json(customers_data):
    response = client.get("/json")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == customers_data

def test_saints_in_age_range_invalid_min_max_age():
    response = client.get("/admin/saint/age/40/20")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Minimum age must be less than maximum age."}

def test_saints_in_age_range_invalid_negative_age():
    response = client.get("/admin/saint/age/-10/20")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "Input should be greater than or equal to 0"

mock_db_cursor = MagicMock()

def test_saints_in_age_range_valid():
    with patch('main.db_cursor', mock_db_cursor):
        mock_db_cursor.fetchall.return_value = [("John", 30), ("Mary", 35)]  # Sample data
        response = client.get("/admin/saint/age/20/40")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [["John", 30], ["Mary", 35]]
