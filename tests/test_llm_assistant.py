import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from app.llm_assistant import GPTAssistantClient

@pytest.fixture
def gpt_client():
    """Fixture para o GPTAssistantClient."""
    with patch("app.llm_assistant.OpenAI") as mock_openai:
        # Setup dos mocks para o OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock para beta.assistants.create
        assistant_mock = MagicMock()
        assistant_mock.id = "assistant_id_123"
        mock_client.beta.assistants.create.return_value = assistant_mock

        # Cria o client
        client = GPTAssistantClient()
        
        # Retorna o client com os mocks configurados
        yield client

@pytest.mark.asyncio
async def test_create_assistant(gpt_client):
    """Testa a criação do assistente."""
    assert gpt_client.assistant == "assistant_id_123"
    assert gpt_client.client.beta.assistants.create.called

@patch("app.llm_assistant.get_instruction_prompt")
def test_create_assistant_with_tools(mock_get_instruction, gpt_client):
    """Testa a criação do assistente com ferramentas."""
    mock_get_instruction.return_value = "Test instructions"
    
    # Chama o método
    assistant_id = gpt_client._create_assistant()
    
    # Verifica se o OpenAI client foi chamado corretamente
    gpt_client.client.beta.assistants.create.assert_called_once()
    call_args = gpt_client.client.beta.assistants.create.call_args[1]
    
    # Verifica se as ferramentas foram configuradas
    assert "tools" in call_args
    assert len(call_args["tools"]) == 3
    
    # Verifica os nomes das funções
    function_names = [t["function"]["name"] for t in call_args["tools"]]
    assert "get_user_history" in function_names
    assert "get_user_profile" in function_names
    assert "handle_audio" in function_names
    
    # Verifica que o resultado é o ID do assistente
    assert assistant_id == "assistant_id_123"

def test_format_history(gpt_client):
    """Testa a formatação do histórico de interações."""
    # Cria dados de teste
    history = [
        {"question": "Hello", "response": "Hi there"},
        {"question": "How are you?", "response": "I'm fine, thanks"}
    ]
    
    # Chama o método
    formatted = gpt_client._format_history(history)
    
    # Verifica o resultado
    assert "Pergunta: Hello\nResposta: Hi there" in formatted
    assert "Pergunta: How are you?\nResposta: I'm fine, thanks" in formatted

@pytest.mark.asyncio
async def test_execute_tool_audio_download(gpt_client):
    """Testa a execução da ferramenta de download de áudio."""
    # Mock para download_whatsapp_audio
    with patch("app.llm_assistant.download_whatsapp_audio") as mock_download:
        mock_download.return_value = AsyncMock(return_value="/tmp/audio.ogg")
        
        # Cria o tool_call
        tool_call = MagicMock()
        tool_call.function.name = "handle_audio"
        tool_call.function.arguments = json.dumps({
            "operation": "download",
            "audio_id": "audio123"
        })
        
        # Chama o método
        result = await gpt_client._execute_tool(tool_call)
        
        # Verifica o resultado
        assert result == "/tmp/audio.ogg"
        mock_download.assert_called_once_with("audio123")

@pytest.mark.asyncio
async def test_execute_tool_audio_transcribe(gpt_client):
    """Testa a execução da ferramenta de transcrição de áudio."""
    # Mock para open
    mock_file = MagicMock()
    mock_open = MagicMock(return_value=mock_file)
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Mock para transcriptions.create
    mock_transcription = MagicMock()
    mock_transcription.text = "Hello, this is a test"
    gpt_client.client.audio.transcriptions.create.return_value = mock_transcription
    
    # Patch para open
    with patch("builtins.open", mock_open):
        # Cria o tool_call
        tool_call = MagicMock()
        tool_call.function.name = "handle_audio"
        tool_call.function.arguments = json.dumps({
            "operation": "transcribe",
            "audio_id": "/tmp/audio.ogg"
        })
        
        # Chama o método
        result = await gpt_client._execute_tool(tool_call)
        
        # Verifica o resultado
        assert result == "Hello, this is a test"
        mock_open.assert_called_once_with("/tmp/audio.ogg", "rb")
        gpt_client.client.audio.transcriptions.create.assert_called_once()

@pytest.mark.asyncio
async def test_execute_tool_get_user_history(gpt_client):
    """Testa a execução da ferramenta de histórico do usuário."""
    # Mock para user_profile.get_user_history
    gpt_client.user_profile.get_user_history = MagicMock(return_value=[
        {"question": "Test Q", "response": "Test R"}
    ])
    
    # Mock para _format_history
    gpt_client._format_history = MagicMock(return_value="Formatted history")
    
    # Cria o tool_call
    tool_call = MagicMock()
    tool_call.function.name = "get_user_history"
    tool_call.function.arguments = json.dumps({
        "profile_id": "user123"
    })
    
    # Chama o método
    result = await gpt_client._execute_tool(tool_call)
    
    # Verifica o resultado
    assert result == "Formatted history"
    gpt_client.user_profile.get_user_history.assert_called_once_with("user123")
    gpt_client._format_history.assert_called_once()

@pytest.mark.asyncio
async def test_process_message(gpt_client):
    """Testa o processamento de mensagem."""
    # Mock para beta.threads.create
    thread_mock = MagicMock()
    thread_mock.id = "thread_123"
    gpt_client.client.beta.threads.create.return_value = thread_mock
    
    # Mock para beta.threads.messages.create
    gpt_client.client.beta.threads.messages.create = MagicMock()
    
    # Mock para beta.threads.runs.create
    run_mock = MagicMock()
    run_mock.id = "run_123"
    gpt_client.client.beta.threads.runs.create.return_value = run_mock
    
    # Mock para _process_run
    gpt_client._process_run = AsyncMock(return_value="GPT response")
    
    # Mock para _get_context
    gpt_client._get_context = MagicMock(return_value="User context")
    
    # Mock para user_profile.save_interaction
    gpt_client.user_profile.save_interaction = MagicMock()
    
    # Chama o método
    result = await gpt_client.process_message("user123", "Hello")
    
    # Verifica o resultado
    assert result == "GPT response"
    
    # Verifica as chamadas aos mocks
    gpt_client.client.beta.threads.create.assert_called_once()
    assert gpt_client.client.beta.threads.messages.create.call_count == 2
    gpt_client.client.beta.threads.runs.create.assert_called_once_with(
        thread_id="thread_123",
        assistant_id=gpt_client.assistant
    )
    gpt_client._process_run.assert_called_once_with("thread_123", "run_123")
    gpt_client.user_profile.save_interaction.assert_called_once_with(
        "user123", "Hello", "GPT response"
    )

@pytest.mark.asyncio
async def test_process_run_completed(gpt_client):
    """Testa o processamento de uma execução completa."""
    # Mock para beta.threads.runs.retrieve
    run_mock = MagicMock()
    run_mock.status = "completed"
    gpt_client.client.beta.threads.runs.retrieve.return_value = run_mock
    
    # Mock para beta.threads.messages.list
    message_mock = MagicMock()
    message_content = MagicMock()
    message_content.text.value = "GPT response"
    message_mock.data = [MagicMock(content=[message_content])]
    gpt_client.client.beta.threads.messages.list.return_value = message_mock
    
    # Chama o método
    result = await gpt_client._process_run("thread_123", "run_123")
    
    # Verifica o resultado
    assert result == "GPT response"
    
    # Verifica as chamadas aos mocks
    gpt_client.client.beta.threads.runs.retrieve.assert_called_once_with(
        thread_id="thread_123",
        run_id="run_123"
    )
    gpt_client.client.beta.threads.messages.list.assert_called_once_with(
        thread_id="thread_123"
    )

@pytest.mark.asyncio
async def test_process_run_requires_action(gpt_client):
    """Testa o processamento de uma execução que requer ação."""
    # Setup para ciclo de runs
    run_requires_action = MagicMock()
    run_requires_action.status = "requires_action"
    
    run_completed = MagicMock()
    run_completed.status = "completed"
    
    # Mock para beta.threads.runs.retrieve
    gpt_client.client.beta.threads.runs.retrieve.side_effect = [
        run_requires_action,
        run_completed
    ]
    
    # Setup para tool_calls
    tool_call = MagicMock()
    tool_call.id = "tool_call_123"
    required_action = MagicMock()
    required_action.submit_tool_outputs.tool_calls = [tool_call]
    run_requires_action.required_action = required_action
    
    # Mock para _execute_tool
    gpt_client._execute_tool = AsyncMock(return_value="Tool result")
    
    # Mock para submit_tool_outputs
    gpt_client.client.beta.threads.runs.submit_tool_outputs = MagicMock()
    
    # Mock para beta.threads.messages.list
    message_mock = MagicMock()
    message_content = MagicMock()
    message_content.text.value = "GPT response"
    message_mock.data = [MagicMock(content=[message_content])]
    gpt_client.client.beta.threads.messages.list.return_value = message_mock
    
    # Patch para asyncio.sleep
    with patch("asyncio.sleep", AsyncMock()):
        # Chama o método
        result = await gpt_client._process_run("thread_123", "run_123")
        
        # Verifica o resultado
        assert result == "GPT response"
        
        # Verifica as chamadas aos mocks
        assert gpt_client.client.beta.threads.runs.retrieve.call_count == 2
        gpt_client._execute_tool.assert_called_once_with(tool_call)
        gpt_client.client.beta.threads.runs.submit_tool_outputs.assert_called_once_with(
            thread_id="thread_123",
            run_id="run_123",
            tool_outputs=[{
                "tool_call_id": "tool_call_123",
                "output": "Tool result"
            }]
        )

@pytest.mark.asyncio
async def test_process_run_failed(gpt_client):
    """Testa o processamento de uma execução que falha."""
    # Mock para beta.threads.runs.retrieve
    run_failed = MagicMock()
    run_failed.status = "failed"
    run_failed.last_error = "Test error"
    gpt_client.client.beta.threads.runs.retrieve.return_value = run_failed
    
    # Patch para asyncio.sleep
    with patch("asyncio.sleep", AsyncMock()):
        # Chama o método e verifica se gera exceção
        with pytest.raises(Exception) as excinfo:
            await gpt_client._process_run("thread_123", "run_123")
        
        # Verifica a mensagem de erro
        assert "Run failed: Test error" in str(excinfo.value)
        
        # Verifica as chamadas aos mocks
        gpt_client.client.beta.threads.runs.retrieve.assert_called_once_with(
            thread_id="thread_123",
            run_id="run_123"
        )