# Financial Chatbot Project

## Overview

This project implements a financial chatbot using Python, FastAPI, and OpenAI's GPT-4. The chatbot processes user questions, analyzes a CSV file containing financial data, and provides personalized investment insights. It also integrates with Amazon DynamoDB to store user interactions, maintaining conversational context for each user session.

---

## Features

1. **Virtual Assistant Functionality**
   - Answers user questions with personalized insights based on the user's session context and a financial dataset.

2. **GPT-4 Integration**
   - Leverages OpenAI's GPT-4 model to generate insightful and context-aware responses.

3. **Memory Support**
   - Tracks user sessions using `sessionId` to maintain context across interactions.

4. **DynamoDB Integration**
   - Stores questions, responses, and session history.
   - Provides data retention policies to clean up data older than 12 months.

5. **Filesystem Watcher**
   - Monitors updates to the CSV file and reloads data dynamically.

6. **Secure JWT Authentication**
   - Ensures secure access to the API endpoints.

7. **AWS SES Notifications**
   - Sends email notifications when the CSV is updated or duplicates are detected.

8. **Extensible Architecture**
   - Modular codebase designed for scalability and maintainability.

---

## Requirements

- Python 3.9+
- Node.js (for WhatsApp integration)
- AWS Account (for DynamoDB and SES)
- OpenAI API Key

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ricardoerib/bot-assistant-open-api.git
cd bot-assistant-open-api
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=<your_openai_api_key>
AWS_ACCESS_KEY_ID=<your_aws_access_key>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
AWS_REGION=<your_aws_region>
JWT_SECRET_KEY=<your_jwt_secret_key>
GPT_MODEL="gpt-4o-mini"
AWS_REGION=us-east-1
DATABASE_ENABLED=false
```

---

## Usage

### 1. Start the FastAPI Server
```bash
uvicorn app.main:app --reload
```

### 2. Test API Endpoints
Use Postman or a similar tool to send requests:

**Endpoint:** `/ask`
- **Method:** `POST`
- **Headers:**
  - `Authorization: Bearer <JWT_TOKEN>`
- **Body:**
```json
{
  "question": "What are the investment trends for 2025?",
  "overrideConfig": {
    "sessionId": "1234567890"
  }
}
```

### 3. Example Response
```json
{
  "response": "Based on current trends, sectors like renewable energy, AI, and healthcare show great potential for 2025."
}
```

---

## Architecture

### Key Components
1. **FastAPI:** Provides API endpoints for user interactions.
2. **GPT-4 Integration:** Processes questions and generates responses.
3. **DynamoDB:** Stores user interactions with `sessionId` as the primary key.
4. **CSV Processor:** Loads and monitors financial data for insights.
5. **JWT Authentication:** Secures API access.

### Directory Structure
```
bot-assistant-open-api/
├── app/
│   ├── main.py               # FastAPI application entry point
│   ├── csv_processor.py      # Processes CSV data and monitors updates
│   ├── gpt_client.py         # Handles GPT-4 API requests
│   ├── auth.py               # JWT authentication
│   ├── dynamodb_client.py    # DynamoDB interactions
│   ├── email_notifier.py     # Sends notifications via AWS SES
│   ├── scheduler.py          # Cron jobs for data cleanup
│   └── utils.py              # Helper functions
├── data/
│   └── data.csv              # Financial data file
├── tests/
│   └── test_main.py          # Unit tests
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
```

---

## Future Enhancements

- Add support for multi-language responses.
- Integrate with additional data sources (e.g., APIs for live market data).
- Expand analytics with visual dashboards.
- Introduce advanced error monitoring and observability tools.
- Implement a CI/CD pipeline for automated testing and deployment.
- Enhance security with rate limiting and input validation.