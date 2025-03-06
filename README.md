# WhatsApp GPT Assistant

A powerful integration between WhatsApp Business API and OpenAI's GPT models, allowing businesses to provide intelligent automated responses to customer inquiries through WhatsApp.

![WhatsApp GPT Assistant](https://img.shields.io/badge/WhatsApp-GPT-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai&logoColor=white)

## 🌟 Features

- 💬 **WhatsApp Integration**: Seamless integration with WhatsApp Business API
- 🤖 **GPT-Powered Responses**: Intelligent, contextual responses using OpenAI's latest models
- 🔊 **Audio Processing**: Transcribe and respond to voice messages
- 👤 **User Profiles**: Track user details and interaction history
- 🌐 **Multi-language Support**: Framework for handling multiple languages
- 💾 **Persistence**: Optional database integration for storing user profiles and interactions
- 🔒 **User Consent Flow**: Built-in flow for terms acceptance and email collection

## 📋 Requirements

- Python 3.11+
- WhatsApp Business API access
- OpenAI API key
- Docker (optional, for containerized deployment)

## 🚀 Quick Start

### Using Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/whatsapp-gpt-assistant.git
   cd whatsapp-gpt-assistant
   ```

2. Create a `.env` file with your configuration:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GPT_MODEL=gpt-4-turbo-preview
   APP_ENVIRONMENT=DEV
   WHATSAPP_VERIFY_TOKEN=your_verification_token
   DATABASE_ENABLED=false
   ```

3. Build and run the Docker container:
   ```bash
   docker-compose up -d
   ```

4. The API will be accessible at `http://localhost:8000`

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/whatsapp-gpt-assistant.git
   cd whatsapp-gpt-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration (see Docker section)

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## 🔌 WhatsApp Business API Setup

1. Create a Meta developer account at [developers.facebook.com](https://developers.facebook.com/)
2. Set up a WhatsApp Business account
3. Configure a webhook with the following:
   - URL: `https://your-domain.com/webhook`
   - Verification Token: Same as your `WHATSAPP_VERIFY_TOKEN`
   - Subscribe to `messages` events
4. Test the connection by sending a message to your WhatsApp number

## 🏗️ Architecture

The application follows a modular architecture:

```
WhatsApp Cloud API → FastAPI Application → GPT Assistant Client → OpenAI API
                      ↓                     ↓
                      Webhook Processor  →  User Profile Manager
```

- **FastAPI Application**: Manages endpoints and async processes
- **Webhook Processor**: Processes WhatsApp message payloads
- **GPT Assistant Client**: Interfaces with OpenAI's API
- **User Profile Manager**: Handles user data and conversation history

## 📝 API Endpoints

- `GET /webhook`: Handles WhatsApp webhook verification
- `POST /webhook`: Processes incoming WhatsApp messages
- `GET /healthcheck`: Health check endpoint for monitoring
- `POST /ask`: Direct API endpoint for testing responses without WhatsApp

## 🔧 Configuration

Environment variables:

| Variable | Description | Default Value |
|----------|-------------|--------------|
| OPENAI_API_KEY | OpenAI API key | - |
| GPT_MODEL | GPT model to use | gpt-4-turbo-preview |
| APP_ENVIRONMENT | Execution environment (LOCAL, DEV, PROD) | LOCAL |
| WHATSAPP_VERIFY_TOKEN | WhatsApp webhook verification token | teste |
| DATABASE_ENABLED | Enables data persistence | false |

## 🧪 Testing

The project includes comprehensive tests for all components:

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
pytest tests/test_messages.py
```

## 🛠️ Development

Useful commands:

```bash
# Format code
make format

# Lint code
make lint

# Clean temporary files
make clean

# Build Docker image
make docker-build

# Run Docker container
make docker-run
```

## 💡 Supported Message Types

| Type | Support Level | Description |
|------|---------------|-------------|
| Text | ✅ Full | Process and respond to text messages |
| Audio | ✅ Full | Transcribe voice messages and respond |
| Image | ⚠️ Partial | Detect but cannot process content |
| Document | ⚠️ Partial | Detect but cannot process content |
| Video | ⚠️ Partial | Detect but cannot process content |
| Location | ❌ None | Not supported yet |
| Contacts | ❌ None | Not supported yet |
| Interactive | ❌ None | Not supported yet |

## 🔍 Debugging

### Local Testing with curl

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[{"id":"123456789","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"5551234567","phone_number_id":"1234567890"},"contacts":[{"profile":{"name":"Test User"},"wa_id":"5551234567"}],"messages":[{"from":"5551234567","id":"wamid.abcdefghijklmnopqrstuvwxyz","timestamp":"1234567890","text":{"body":"Hello!"},"type":"text"}]},"field":"messages"}]}]}'
```

### Logs

The application uses Python's logging module. To increase log verbosity, modify the log level in `app/main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📊 Project Structure

```
whatsapp-gpt-assistant/
├── app/                       # Application code
│   ├── main.py                # FastAPI application entry point
│   ├── messages.py            # WhatsApp message processor
│   ├── llm_assistant.py       # GPT client implementation
│   ├── user_profile.py        # User profile management
│   └── ...                    # Other modules
├── tests/                     # Test suite
│   ├── conftest.py            # Shared test fixtures
│   ├── test_main.py           # Tests for FastAPI endpoints
│   └── ...                    # Other test modules
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker configuration
├── Makefile                   # Development commands
└── ...                        # Other project files
```

## 🚧 Future Improvements

- Image processing with Vision API
- Support for interactive buttons and menus
- Local audio file processing
- Enhanced multi-language support
- Response caching for performance
- Integration with analytics platforms

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📬 Contact

If you have any questions, please reach out to [ricardo@ribeiro.solutions](mailto:ricardo@ribeiro.solutions)

---

Made with ❤️ by Ricardo Ribeiro