import pytest
from datetime import datetime, timedelta, date
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def test_list_patients_and_envelope():
    """Verify GET /patients returns 200 with standard response envelope."""
    response = client.get("/patients")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert json_data["error"] is None
    assert isinstance(json_data["data"], list)
    assert len(json_data["data"]) >= 1

def test_query_filter_by_last_name():
    """Verify ?last_name query parameter works."""
    response = client.get("/patients?last_name=Doe")
    assert response.status_code == 200
    data = response.json()["data"]
    assert any(p["last_name"] == "Doe" for p in data)

def test_query_filter_by_phone():
    """Verify ?phone_number query parameter works."""
    response = client.get("/patients?phone_number=555-123-4567")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1
    assert data[0]["phone_number"] == "555-123-4567"

def test_create_patient_success():
    """Verify POST /patients creates a valid patient with UUID and 201 status."""
    payload = {
        "first_name": "Michael",
        "last_name": "Jordan",
        "date_of_birth": "02/17/1963",
        "sex": "Male",
        "phone_number": "312-555-0123",
        "email": "mj@bulls.com",
        "address_line_1": "1901 W Madison St",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60612",
        "insurance_provider": "UnitedHealthcare",
        "insurance_member_id": "UHC-232323",
        "preferred_language": "English",
        "emergency_contact_name": "Scottie Pippen",
        "emergency_contact_phone": "312-555-0133"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["error"] is None
    patient = json_data["data"]
    assert "patient_id" in patient
    assert len(patient["patient_id"]) == 36  # UUID length
    assert patient["first_name"] == "Michael"
    assert patient["last_name"] == "Jordan"
    assert patient["phone_number"] == "312-555-0123"

def test_validation_future_dob_rejected():
    """Verify that a future date of birth fails server-side validation with 422."""
    tomorrow = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
    payload = {
        "first_name": "Time",
        "last_name": "Traveler",
        "date_of_birth": tomorrow,
        "sex": "Male",
        "phone_number": "555-019-9999",
        "address_line_1": "1 Future Way",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 422

def test_validation_invalid_phone_rejected():
    """Verify that a 3-digit phone number is rejected with 422."""
    payload = {
        "first_name": "Bad",
        "last_name": "Phone",
        "date_of_birth": "01/01/1990",
        "sex": "Female",
        "phone_number": "123",  # Invalid 3-digit phone
        "address_line_1": "123 Main St",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75001"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 422

def test_validation_invalid_state_rejected():
    """Verify that an invalid 2-letter state code is rejected with 422."""
    payload = {
        "first_name": "Bad",
        "last_name": "State",
        "date_of_birth": "01/01/1990",
        "sex": "Other",
        "phone_number": "555-123-4567",
        "address_line_1": "123 Main St",
        "city": "Nowhere",
        "state": "ZZ",  # Invalid state
        "zip_code": "12345"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 422

def test_validation_invalid_zip_rejected():
    """Verify that a 3-digit zip code is rejected with 422."""
    payload = {
        "first_name": "Bad",
        "last_name": "Zip",
        "date_of_birth": "01/01/1990",
        "sex": "Decline to Answer",
        "phone_number": "555-123-4567",
        "address_line_1": "123 Main St",
        "city": "Boston",
        "state": "MA",
        "zip_code": "123"  # Invalid zip code
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 422

def test_get_patient_by_id_and_not_found():
    """Verify GET /patients/{id} retrieves patient and returns 404 for unknown ID."""
    # First get list
    list_res = client.get("/patients")
    first_patient = list_res.json()["data"][0]
    pid = first_patient["patient_id"]

    res = client.get(f"/patients/{pid}")
    assert res.status_code == 200
    assert res.json()["data"]["patient_id"] == pid

    # Test unknown ID
    unknown_res = client.get("/patients/00000000-0000-0000-0000-000000000000")
    assert unknown_res.status_code == 404

def test_put_partial_update_patient():
    """Verify PUT /patients/{id} updates fields partially."""
    # Create patient to update
    payload = {
        "first_name": "Alice",
        "last_name": "Wonderland",
        "date_of_birth": "04/05/1995",
        "sex": "Female",
        "phone_number": "212-555-7788",
        "address_line_1": "77 Fantasy Ln",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001"
    }
    created = client.post("/patients", json=payload).json()["data"]
    pid = created["patient_id"]

    # Update only phone and address
    update_payload = {
        "phone_number": "212-555-9900",
        "address_line_1": "99 Updated Rd"
    }
    update_res = client.put(f"/patients/{pid}", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()["data"]
    assert updated_data["phone_number"] == "212-555-9900"
    assert updated_data["address_line_1"] == "99 Updated Rd"
    assert updated_data["first_name"] == "Alice"  # Unchanged

def test_soft_delete_patient():
    """Verify DELETE /patients/{id} soft-deletes and excludes patient from listings."""
    payload = {
        "first_name": "Delete",
        "last_name": "Me",
        "date_of_birth": "06/06/1986",
        "sex": "Other",
        "phone_number": "555-000-1122",
        "address_line_1": "100 Temp St",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101"
    }
    created = client.post("/patients", json=payload).json()["data"]
    pid = created["patient_id"]

    # Delete
    del_res = client.delete(f"/patients/{pid}")
    assert del_res.status_code == 200

    # Subsequent GET by ID should be 404
    get_res = client.get(f"/patients/{pid}")
    assert get_res.status_code == 404

    # Patient should not be in list
    list_res = client.get("/patients")
    ids = [p["patient_id"] for p in list_res.json()["data"]]
    assert pid not in ids

def test_voice_agent_tools_with_token():
    """Verify the ElevenLabs webhook tool endpoints work with X-Tool-Token."""
    headers = {"X-Tool-Token": settings.elevenlabs_tool_token}

    # 1. Register Patient Tool
    tool_payload = {
        "first_name": "Sarah",
        "last_name": "Connor",
        "date_of_birth": "02/28/1985",
        "sex": "Female",
        "phone_number": "213-555-4321",
        "address_line_1": "1984 Cyber St",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90001",
        "preferred_language": "English"
    }
    tool_res = client.post("/api/tools/register-patient", json=tool_payload, headers=headers)
    assert tool_res.status_code == 200
    res_data = tool_res.json()
    assert res_data["status"] == "success"
    assert "Sarah" in res_data["message"]

    # 2. Duplicate Detection Lookup Tool (Bonus)
    lookup_res = client.post("/api/tools/lookup-patient-by-phone", json={"phone_number": "213-555-4321"}, headers=headers)
    assert lookup_res.status_code == 200
    lookup_data = lookup_res.json()
    assert lookup_data["found"] is True
    assert "Sarah Connor" in lookup_data["message"]
