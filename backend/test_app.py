import pytest
from fastapi.testclient import TestClient
from backend.app import app, sessions_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear sessions before each test"""
    sessions_db.clear()
    yield
    sessions_db.clear()


def test_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_create_session():
    """Test creating a new negotiation session"""
    response = client.post(
        "/api/sessions/new",
        json={"student_id": "TEST123"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert data["student_id"] == "TEST123"
    assert "initial_message" in data
    assert "deal_parameters" in data
    
    # Check deal parameters are present
    params = data["deal_parameters"]
    assert "base_price" in params
    assert "target_quantity" in params
    assert "delivery_days" in params
    assert "quality_grade" in params
    assert "warranty_months" in params


def test_seedable_parameters():
    """Test that same student ID produces same parameters"""
    response1 = client.post(
        "/api/sessions/new",
        json={"student_id": "SEED123"}
    )
    params1 = response1.json()["deal_parameters"]
    
    # Clear and create again with same student ID
    sessions_db.clear()
    
    response2 = client.post(
        "/api/sessions/new",
        json={"student_id": "SEED123"}
    )
    params2 = response2.json()["deal_parameters"]
    
    # Should produce identical parameters
    assert params1 == params2


def test_chat_message():
    """Test sending a chat message"""
    # First create a session
    session_response = client.post(
        "/api/sessions/new",
        json={"student_id": "CHAT123"}
    )
    session_id = session_response.json()["session_id"]
    
    # Send a message
    chat_response = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "What is your best price?"
        }
    )
    
    assert chat_response.status_code == 200
    data = chat_response.json()
    
    assert "alex_response" in data
    assert "turn_count" in data
    assert data["turn_count"] == 1
    assert "status" in data


def test_chat_invalid_session():
    """Test chat with invalid session ID"""
    response = client.post(
        "/api/chat",
        json={
            "session_id": "invalid-id",
            "message": "Hello"
        }
    )
    assert response.status_code == 404


def test_get_session():
    """Test retrieving session details"""
    # Create a session
    session_response = client.post(
        "/api/sessions/new",
        json={"student_id": "GET123"}
    )
    session_id = session_response.json()["session_id"]
    
    # Get session details
    get_response = client.get(f"/api/sessions/{session_id}")
    
    assert get_response.status_code == 200
    data = get_response.json()
    
    assert data["session_id"] == session_id
    assert data["student_id"] == "GET123"
    assert "messages" in data
    assert "status" in data


def test_get_invalid_session():
    """Test getting non-existent session"""
    response = client.get("/api/sessions/invalid-id")
    assert response.status_code == 404


def test_negotiation_flow():
    """Test a complete negotiation flow"""
    # Create session
    session_response = client.post(
        "/api/sessions/new",
        json={"student_id": "FLOW123"}
    )
    session_id = session_response.json()["session_id"]
    base_price = session_response.json()["deal_parameters"]["base_price"]
    
    # Negotiate price
    chat1 = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": f"Can you do ${base_price - 5} per unit?"
        }
    )
    assert chat1.status_code == 200
    
    # Accept deal
    chat2 = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "I accept the deal"
        }
    )
    assert chat2.status_code == 200
    data = chat2.json()
    
    # Check if deal is closed
    if data["deal_closed"]:
        assert "evaluation" in data
        assert data["evaluation"] is not None
        assert "overall_score" in data["evaluation"]
        assert "metrics" in data["evaluation"]


def test_evaluation_metrics():
    """Test that evaluation contains all required metrics"""
    # Create and complete a negotiation
    session_response = client.post(
        "/api/sessions/new",
        json={"student_id": "EVAL123"}
    )
    session_id = session_response.json()["session_id"]
    
    # Quick acceptance to trigger evaluation
    chat = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "I accept your offer"
        }
    )
    
    data = chat.json()
    if data["deal_closed"] and data["evaluation"]:
        eval_data = data["evaluation"]
        
        # Check all 5 metrics are present
        assert "metrics" in eval_data
        metrics = eval_data["metrics"]
        
        assert "price_achievement" in metrics
        assert "efficiency" in metrics
        assert "relationship_building" in metrics
        assert "value_creation" in metrics
        assert "strategic_negotiation" in metrics
        
        # All metrics should be 0-100
        for metric_value in metrics.values():
            assert 0 <= metric_value <= 100
