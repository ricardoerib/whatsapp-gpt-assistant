import os
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock das variáveis de ambiente necessárias para os testes."""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_key",
        "GPT_MODEL": "gpt-4-turbo-preview",
        "APP_ENVIRONMENT": "TEST",
        "WHATSAPP_VERIFY_TOKEN": "teste"
    }):
        yield

@pytest.fixture
def mock_user_profile():
    """Mock para UserProfile."""
    with patch("app.user_profile.UserProfile") as mock:
        profile_instance = MagicMock()
        mock.return_value = profile_instance
        
        # Configure métodos do mock
        profile_instance.get_user.return_value = {
            "profile_id": "user123",
            "name": "Test User",
            "phone_number": "5551234567",
            "email": "user@example.com",
            "language": "en",
            "accepted_terms": True
        }
        
        profile_instance.get_user_history.return_value = [
            {"question": "Hello", "response": "Hi there"},
            {"question": "How are you?", "response": "I'm fine, thanks"}
        ]
        
        yield profile_instance

@pytest.fixture
def mock_openai():
    """Mock para o cliente OpenAI."""
    with patch("app.llm_assistant.OpenAI") as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        
        # Configure beta.assistants
        assistant_mock = MagicMock()
        assistant_mock.id = "assistant_id_123"
        client_instance.beta.assistants.create.return_value = assistant_mock
        
        # Configure beta.threads
        thread_mock = MagicMock()
        thread_mock.id = "thread_123"
        client_instance.beta.threads.create.return_value = thread_mock
        
        # Configure audio transcription
        transcription_mock = MagicMock()
        transcription_mock.text = "Transcribed audio text"
        client_instance.audio.transcriptions.create.return_value = transcription_mock
        
        yield client_instance

@pytest.fixture
def sample_processed_message():
    """Fixture com uma mensagem processada de exemplo."""
    from app.messages import ProcessedMessage, MessageType
    
    return ProcessedMessage(
        message_id="wamid.test123",
        phone_number="5551234567",
        timestamp="1677771234",
        type=MessageType.TEXT,
        text_body="Hello, world!",
        contact_name="Test User"
    )