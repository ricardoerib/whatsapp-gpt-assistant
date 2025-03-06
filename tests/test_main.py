import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app

client = TestClient(app)

@pytest.mark.parametrize(
    "query_params,expected_status,expected_response",
    [
        (
            {"hub.mode": "subscribe", "hub.verify_token": "teste", "hub.challenge": "challenge123"},
            200,
            "challenge123",
        ),
        (
            {"hub.mode": "subscribe", "hub.verify_token": "wrong_token", "hub.challenge": "challenge123"},
            403,
            {"detail": "Verification token invalid"},
        ),
    ],
)
def test_webhook_verification(query_params, expected_status, expected_response):
    """Test webhook verification endpoint."""
    response = client.get("/webhook", params=query_params)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.text == expected_response
    else:
        assert response.json() == expected_response


@patch("app.messages.process_webhook")
@patch("app.main.send_whatsapp_message")
def test_webhook_text_message(mock_send_message, mock_process_webhook, text_message_payload):
    """Test webhook with text message."""
    # Setup mock return values
    mock_process_webhook.return_value = AsyncMock(
        return_value=[{"recipient": "1234567890", "message": "Test response"}]
    )
    
    # Call endpoint
    response = client.post(
        "/webhook",
        json=text_message_payload,
    )
    
    # Verify response
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    
    # Verify mocks were called correctly
    mock_process_webhook.assert_called_once_with(text_message_payload)
    

@patch("app.messages.process_webhook")
@patch("app.main.send_whatsapp_message")
def test_webhook_audio_message(mock_send_message, mock_process_webhook, audio_message_payload):
    """Test webhook with audio message."""
    # Setup mock return values
    mock_process_webhook.return_value = AsyncMock(
        return_value=[{"recipient": "1234567890", "message": "Audio response"}]
    )
    
    # Call endpoint
    response = client.post(
        "/webhook",
        json=audio_message_payload,
    )
    
    # Verify response
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    
    # Verify mocks were called correctly
    mock_process_webhook.assert_called_once_with(audio_message_payload)


@patch("app.messages.process_webhook")
def test_webhook_error_handling(mock_process_webhook):
    """Test webhook error handling."""
    # Setup mock to raise exception
    mock_process_webhook.side_effect = Exception("Test error")
    
    # Call endpoint
    response = client.post(
        "/webhook",
        json={"invalid": "payload"},
    )
    
    # Verify response contains error
    assert response.status_code == 200  # We're returning 200 even on errors
    assert response.json() == {"status": "error", "message": "Test error"}
    

@pytest.fixture
def text_message_payload():
    """Fixture for a text message payload."""
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
def audio_message_payload():
    """Fixture for an audio message payload."""
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
                                    "id": "wamid.audio123",
                                    "timestamp": "1677771234",
                                    "audio": {
                                        "id": "audio123",
                                        "mime_type": "audio/ogg; codecs=opus"
                                    },
                                    "type": "audio"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }