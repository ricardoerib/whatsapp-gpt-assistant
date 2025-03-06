import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

from app.user_profile import UserProfile

@pytest.fixture
def user_profile():
    """Fixture for UserProfile."""
    with patch("app.user_profile.UserProfile._init_db") as mock_init_db:
        profile = UserProfile("TEST")
        
        # Mock the database
        profile.db = MagicMock()
        
        # Setup default user for testing
        profile.default_user = {
            "profile_id": "test_user_123",
            "name": "Test User",
            "phone_number": "5551234567",
            "email": None,
            "accepted_terms": False,
            "language": "en",
            "created_at": "2024-01-01T00:00:00Z",
            "last_interaction": "2024-01-01T00:00:00Z"
        }
        
        # Setup mock database query results
        profile.db.users.find_one.return_value = profile.default_user
        profile.db.users.insert_one.return_value = MagicMock(inserted_id="new_user_id")
        profile.db.interactions.find.return_value = [
            {"question": "Hello", "response": "Hi there", "timestamp": "2024-01-01T01:00:00Z"},
            {"question": "How are you?", "response": "I'm fine, thanks", "timestamp": "2024-01-01T02:00:00Z"}
        ]
        
        yield profile

def test_initialize_database(user_profile):
    """Test database initialization."""
    # Reset mock to test initialization
    user_profile.db = None
    
    # Mock MongoDB client
    with patch("app.user_profile.MongoClient") as mock_mongo:
        mock_client = MagicMock()
        mock_mongo.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        
        # Call the method
        user_profile._init_db()
        
        # Verify MongoDB client was created
        mock_mongo.assert_called_once()
        
        # Verify db reference was set
        assert user_profile.db is not None

def test_get_user(user_profile):
    """Test retrieving a user profile."""
    # Setup the mock
    user_profile.db.users.find_one.return_value = user_profile.default_user
    
    # Call the method
    user = user_profile.get_user("test_user_123")
    
    # Verify the result
    assert user is not None
    assert user["profile_id"] == "test_user_123"
    assert user["name"] == "Test User"
    
    # Verify the mock was called correctly
    user_profile.db.users.find_one.assert_called_once_with({"profile_id": "test_user_123"})

def test_get_user_not_found(user_profile):
    """Test retrieving a non-existent user."""
    # Setup the mock
    user_profile.db.users.find_one.return_value = None
    
    # Call the method
    user = user_profile.get_user("nonexistent_user")
    
    # Verify the result
    assert user is None
    
    # Verify the mock was called correctly
    user_profile.db.users.find_one.assert_called_once_with({"profile_id": "nonexistent_user"})

def test_get_or_create_user_existing(user_profile):
    """Test retrieving an existing user."""
    # Setup the mock
    user_profile.db.users.find_one.return_value = user_profile.default_user
    
    # Call the method
    user = user_profile.get_or_create_user("5551234567", "Test User")
    
    # Verify the result
    assert user is not None
    assert user["profile_id"] == "test_user_123"
    assert user["name"] == "Test User"
    
    # Verify the mock was called correctly
    user_profile.db.users.find_one.assert_called_once_with({"phone_number": "5551234567"})
    user_profile.db.users.insert_one.assert_not_called()

def test_get_or_create_user_new(user_profile):
    """Test creating a new user."""
    # Setup the mock for find_one to return None (user not found)
    user_profile.db.users.find_one.return_value = None
    
    # Mock uuid.uuid4 to return a predictable value
    with patch("uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")):
        # Call the method
        user = user_profile.get_or_create_user("5559876543", "New User")
        
        # Verify the result
        assert user is not None
        assert user["profile_id"] == "12345678-1234-5678-1234-567812345678"
        assert user["name"] == "New User"
        assert user["phone_number"] == "5559876543"
        assert user["accepted_terms"] is False
        assert user["email"] is None
        
        # Verify the mocks were called correctly
        user_profile.db.users.find_one.assert_called_once_with({"phone_number": "5559876543"})
        user_profile.db.users.insert_one.assert_called_once()

def test_update_email(user_profile):
    """Test updating a user's email."""
    # Call the method
    user_profile.update_email("test_user_123", "user@example.com")
    
    # Verify the mock was called correctly
    user_profile.db.users.update_one.assert_called_once_with(
        {"profile_id": "test_user_123"},
        {"$set": {"email": "user@example.com"}}
    )

def test_accept_terms(user_profile):
    """Test accepting terms of service."""
    # Call the method
    user_profile.accept_terms("test_user_123")
    
    # Verify the mock was called correctly
    user_profile.db.users.update_one.assert_called_once_with(
        {"profile_id": "test_user_123"},
        {"$set": {"accepted_terms": True}}
    )

def test_save_interaction(user_profile):
    """Test saving an interaction."""
    # Setup mock for datetime
    with patch("app.user_profile.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2024-01-02T12:00:00Z"
        mock_datetime.now.return_value = mock_now
        
        # Call the method
        user_profile.save_interaction("test_user_123", "What is the weather?", "It's sunny today.")
        
        # Verify the mocks were called correctly
        user_profile.db.interactions.insert_one.assert_called_once()
        call_args = user_profile.db.interactions.insert_one.call_args[0][0]
        assert call_args["profile_id"] == "test_user_123"
        assert call_args["question"] == "What is the weather?"
        assert call_args["response"] == "It's sunny today."
        assert call_args["timestamp"] == "2024-01-02T12:00:00Z"
        
        user_profile.db.users.update_one.assert_called_once_with(
            {"profile_id": "test_user_123"},
            {"$set": {"last_interaction": "2024-01-02T12:00:00Z"}}
        )

def test_get_user_history(user_profile):
    """Test retrieving user interaction history."""
    # Setup the mock
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value.limit.return_value = [
        {"question": "Hello", "response": "Hi there", "timestamp": "2024-01-01T01:00:00Z"},
        {"question": "How are you?", "response": "I'm fine, thanks", "timestamp": "2024-01-01T02:00:00Z"}
    ]
    user_profile.db.interactions.find.return_value = mock_cursor
    
    # Call the method
    history = user_profile.get_user_history("test_user_123", limit=10)
    
    # Verify the result
    assert len(history) == 2
    assert history[0]["question"] == "Hello"
    assert history[1]["response"] == "I'm fine, thanks"
    
    # Verify the mocks were called correctly
    user_profile.db.interactions.find.assert_called_once_with({"profile_id": "test_user_123"})
    mock_cursor.sort.assert_called_once_with("timestamp", -1)
    mock_cursor.sort.return_value.limit.assert_called_once_with(10)

def test_get_user_no_database(user_profile):
    """Test getting a user when database is disabled."""
    # Simulate disabled database
    user_profile.is_database_enabled = False
    user_profile.db = None
    
    # Call the method
    user = user_profile.get_user("test_user_123")
    
    # Verify the result is None
    assert user is None

def test_get_or_create_user_no_database(user_profile):
    """Test creating a user when database is disabled."""
    # Simulate disabled database
    user_profile.is_database_enabled = False
    user_profile.db = None
    
    # Mock uuid.uuid4 to return a predictable value
    with patch("uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")):
        # Call the method
        user = user_profile.get_or_create_user("5559876543", "New User")
        
        # Verify a default user is returned
        assert user is not None
        assert user["profile_id"] == "12345678-1234-5678-1234-567812345678"
        assert user["name"] == "New User"
        assert user["phone_number"] == "5559876543"
        assert user["accepted_terms"] is False
        assert user["email"] is None

def test_get_user_history_no_database(user_profile):
    """Test getting history when database is disabled."""
    # Simulate disabled database
    user_profile.is_database_enabled = False
    user_profile.db = None
    
    # Call the method
    history = user_profile.get_user_history("test_user_123")
    
    # Verify empty list is returned
    assert history == []