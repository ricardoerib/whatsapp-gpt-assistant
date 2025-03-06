import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.messages import (
    WebhookProcessor, 
    MessageType, 
    ProcessedMessage
)

@pytest.fixture
def webhook_processor():
    """Fixture para o WebhookProcessor."""
    return WebhookProcessor()

@pytest.fixture
def sample_payload():
    """Fixture com um payload de webhook de exemplo."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "12345",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "5551234567",
                                "phone_number_id": "1234567890"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Test User"},
                                    "wa_id": "5551234567"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "5551234567",
                                    "id": "wamid.test123",
                                    "timestamp": "1677771234",
                                    "text": {"body": "Hello, world!"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

@pytest.fixture
def text_message():
    """Fixture com uma mensagem de texto."""
    return {
        "from": "5551234567",
        "id": "wamid.test123",
        "timestamp": "1677771234",
        "text": {"body": "Hello, world!"},
        "type": "text"
    }

@pytest.fixture
def audio_message():
    """Fixture com uma mensagem de áudio."""
    return {
        "from": "5551234567",
        "id": "wamid.audio123",
        "timestamp": "1677771234",
        "audio": {"id": "audio123"},
        "type": "audio"
    }

@pytest.fixture
def contacts():
    """Fixture com dados de contato."""
    return [
        {
            "profile": {"name": "Test User"},
            "wa_id": "5551234567"
        }
    ]

def test_extract_webhook_data(webhook_processor, sample_payload):
    """Testa a extração de dados do webhook."""
    result = webhook_processor.extract_webhook_data(sample_payload)
    
    assert "messages" in result
    assert "contacts" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["id"] == "wamid.test123"
    assert len(result["contacts"]) == 1
    assert result["contacts"][0]["profile"]["name"] == "Test User"

def test_process_text_message(webhook_processor, text_message, contacts):
    """Testa o processamento de mensagem de texto."""
    processed = webhook_processor.process_message(text_message, contacts)
    
    assert processed is not None
    assert processed.message_id == "wamid.test123"
    assert processed.phone_number == "5551234567"
    assert processed.timestamp == "1677771234"
    assert processed.type == MessageType.TEXT
    assert processed.text_body == "Hello, world!"
    assert processed.contact_name == "Test User"

def test_process_audio_message(webhook_processor, audio_message, contacts):
    """Testa o processamento de mensagem de áudio."""
    processed = webhook_processor.process_message(audio_message, contacts)
    
    assert processed is not None
    assert processed.message_id == "wamid.audio123"
    assert processed.phone_number == "5551234567"
    assert processed.type == MessageType.AUDIO
    assert processed.media_id == "audio123"

@patch("app.messages.WebhookProcessor.handle_message")
@pytest.mark.asyncio
async def test_handle_webhook(mock_handle_message, webhook_processor, sample_payload):
    """Testa o processamento completo de um webhook."""
    # Setup do mock
    mock_handle_message.return_value = "Test response"
    
    # Executa o teste
    responses = await webhook_processor.handle_webhook(sample_payload)
    
    # Verifica o resultado
    assert len(responses) == 1
    assert responses[0]["recipient"] == "5551234567"
    assert responses[0]["message"] == "Test response"
    
    # Verifica se o mock foi chamado
    mock_handle_message.assert_called_once()

@patch("app.messages.WebhookProcessor.handle_terms_flow")
@pytest.mark.asyncio
async def test_handle_message_terms_flow(mock_terms_flow, webhook_processor):
    """Testa o fluxo de termos no processamento de mensagens."""
    # Setup do mock para user_profile
    webhook_processor.user_profile.get_or_create_user = MagicMock(return_value={
        "profile_id": "user123",
        "accepted_terms": False,
        "language": "en"
    })
    
    # Setup do mock para handle_terms_flow
    mock_terms_flow.return_value = "Please accept the terms"
    
    # Cria mensagem de teste
    test_message = ProcessedMessage(
        message_id="test123",
        phone_number="5551234567",
        timestamp="1677771234",
        type=MessageType.TEXT,
        text_body="Hello",
        contact_name="Test User"
    )
    
    # Executa o teste
    response = await webhook_processor.handle_message(test_message)
    
    # Verifica o resultado
    assert response == "Please accept the terms"
    
    # Verifica se o mock foi chamado corretamente
    mock_terms_flow.assert_called_once_with("user123", test_message, "en")

@patch("app.messages.WebhookProcessor.handle_email_flow")
@pytest.mark.asyncio
async def test_handle_message_email_flow(mock_email_flow, webhook_processor):
    """Testa o fluxo de coleta de email no processamento de mensagens."""
    # Setup do mock para user_profile
    webhook_processor.user_profile.get_or_create_user = MagicMock(return_value={
        "profile_id": "user123",
        "accepted_terms": True,
        "email": None,
        "language": "en"
    })
    
    # Setup do mock para handle_email_flow
    mock_email_flow.return_value = "Please provide your email"
    
    # Cria mensagem de teste
    test_message = ProcessedMessage(
        message_id="test123",
        phone_number="5551234567",
        timestamp="1677771234",
        type=MessageType.TEXT,
        text_body="Hello",
        contact_name="Test User"
    )
    
    # Executa o teste
    response = await webhook_processor.handle_message(test_message)
    
    # Verifica o resultado
    assert response == "Please provide your email"
    
    # Verifica se o mock foi chamado corretamente
    mock_email_flow.assert_called_once_with("user123", test_message, "en")

@patch("app.messages.WebhookProcessor.handle_text")
@pytest.mark.asyncio
async def test_handle_message_text(mock_handle_text, webhook_processor):
    """Testa o processamento de mensagens de texto."""
    # Setup do mock para user_profile
    webhook_processor.user_profile.get_or_create_user = MagicMock(return_value={
        "profile_id": "user123",
        "accepted_terms": True,
        "email": "user@example.com",
        "language": "en"
    })
    
    # Setup do mock para handle_text
    mock_handle_text.return_value = "Text response"
    
    # Cria mensagem de teste
    test_message = ProcessedMessage(
        message_id="test123",
        phone_number="5551234567",
        timestamp="1677771234",
        type=MessageType.TEXT,
        text_body="Hello",
        contact_name="Test User"
    )
    
    # Executa o teste
    response = await webhook_processor.handle_message(test_message)
    
    # Verifica o resultado
    assert response == "Text response"
    
    # Verifica se o mock foi chamado corretamente
    mock_handle_text.assert_called_once_with("user123", test_message)

@patch("app.messages.WebhookProcessor.handle_audio")
@pytest.mark.asyncio
async def test_handle_message_audio(mock_handle_audio, webhook_processor):
    """Testa o processamento de mensagens de áudio."""
    # Setup do mock para user_profile
    webhook_processor.user_profile.get_or_create_user = MagicMock(return_value={
        "profile_id": "user123",
        "accepted_terms": True,
        "email": "user@example.com",
        "language": "en"
    })
    
    # Setup do mock para handle_audio
    mock_handle_audio.return_value = "Audio response"
    
    # Cria mensagem de teste
    test_message = ProcessedMessage(
        message_id="test123",
        phone_number="5551234567",
        timestamp="1677771234",
        type=MessageType.AUDIO,
        media_id="audio123",
        contact_name="Test User"
    )
    
    # Executa o teste
    response = await webhook_processor.handle_message(test_message)
    
    # Verifica o resultado
    assert response == "Audio response"
    
    # Verifica se o mock foi chamado corretamente
    mock_handle_audio.assert_called_once_with("user123", test_message)

@patch("app.messages.is_email_valid")
@pytest.mark.asyncio
async def test_handle_email_flow_valid(mock_is_email_valid, webhook_processor):
    """Testa o fluxo de email com email válido."""
    # Setup do mock
    mock_is_email_valid.return_value = True
    webhook_processor.user_profile.update_email = MagicMock()
    
    # Cria mensagem de teste
    test_message = ProcessedMessage(
        message_id="test123",
        phone_number="5551234567",
        timestamp="1677771234",
        type=MessageType.TEXT,
        text_body="user@example.com",
        contact_name="Test User"
    )
    
    # Setup do mock para get_translated_message
    with patch("app.messages.get_translated_message", return_value="Email saved"):
        # Executa o teste
        response = await webhook_processor.handle_email_flow("user123", test_message, "en")
        
        # Verifica o resultado
        assert response == "Email saved"
        
        # Verifica se os mocks foram chamados corretamente
        mock_is_email_valid.assert_called_once_with("user@example.com")
        webhook_processor.user_profile.update_email.assert_called_once_with("user123", "user@example.com")

@pytest.mark.asyncio
async def test_handle_terms_flow_accept(webhook_processor):
    """Testa a aceitação de termos."""
    # Setup mock
    webhook_processor.user_profile.accept_terms = MagicMock()
    
    # Cria mensagem de teste
    test_message = ProcessedMessage(
        message_id="test123",
        phone_number="5551234567",
        timestamp="1677771234",
        type=MessageType.TEXT,
        text_body="accept",
        contact_name="Test User"
    )
    
    # Setup do mock para get_translated_message
    with patch("app.messages.get_translated_message", return_value="Terms accepted"):
        # Executa o teste
        response = await webhook_processor.handle_terms_flow("user123", test_message, "en")
        
        # Verifica o resultado
        assert response == "Terms accepted"
        
        # Verifica se o mock foi chamado corretamente
        webhook_processor.user_profile.accept_terms.assert_called_once_with("user123")