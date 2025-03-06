from openai import OpenAI
import logging
import os
import json
import asyncio
from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from datetime import datetime
from .utils import get_instruction_prompt
from .csv_processor import csv_data
from gtts import gTTS
from .user_profile import UserProfile
from .wpp import download_whatsapp_audio
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gpt_client():
    return GPTAssistantClient()

class UserData(BaseModel):
    profile_id: str
    name: Optional[str]
    phone_number: Optional[str]

class GPTAssistantClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("GPT_MODEL", "gpt-4-turbo-preview")
        self.environment = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()
        self.user_profile = UserProfile(self.environment)
        self.assistant = self._create_assistant()

    def _create_assistant(self) -> str:
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_user_history",
                    "description": "Retrieve user interaction history",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "profile_id": {"type": "string"}
                        },
                        "required": ["profile_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_user_profile",
                    "description": "Retrieve user profile information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "profile_id": {"type": "string"}
                        },
                        "required": ["profile_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "handle_audio",
                    "description": "Process audio operations (download, transcribe, generate)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["download", "transcribe", "generate"]},
                            "audio_id": {"type": "string"},
                            "text": {"type": "string"},
                            "lang": {"type": "string", "default": "pt"}
                        },
                        "required": ["operation"]
                    }
                }
            }
        ]

        assistant = self.client.beta.assistants.create(
            name="Customer Support Assistant",
            instructions=get_instruction_prompt(),
            model=self.model,
            tools=available_tools
        )
        return assistant.id

    def _format_history(self, history: List[Dict]) -> str:
        """Format history into a string representation."""
        formatted_history = []
        for interaction in history:
            formatted_history.append(
                f"Question: {interaction['question']}\n"
                f"Response: {interaction['response']}"
            )
        return "\n\n".join(formatted_history)

    async def _execute_tool(self, tool_call) -> str:
        """Execute a tool call and return the result."""
        try:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name == "handle_audio":
                operation = arguments["operation"]
                
                if operation == "download":
                    audio_file = await download_whatsapp_audio(arguments["audio_id"])
                    return str(audio_file)
                    
                elif operation == "transcribe":
                    audio_path = arguments["audio_id"]
                    with open(audio_path, "rb") as audio_file:
                        transcription = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                    return str(transcription.text)
                    
                elif operation == "generate":
                    tts = gTTS(text=arguments["text"], lang=arguments.get("lang", "pt"))
                    filename = f"response_{datetime.now().timestamp()}.mp3"
                    tts.save(filename)
                    return str(filename)
                    
                else:
                    raise ValueError(f"Unknown audio operation: {operation}")

            elif function_name == "get_user_history":
                history = self.user_profile.get_user_history(arguments["profile_id"])
                return self._format_history(history)

            elif function_name == "get_user_profile":
                user = self.user_profile.get_user(arguments["profile_id"])
                return json.dumps(dict(user) if user else {})

            else:
                raise ValueError(f"Unknown function: {function_name}")

        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}", exc_info=True)
            raise ValueError(f"Tool execution failed: {str(e)}")

    async def process_message(self, profile_id: str, question: str) -> str:
        """Process a user message and return the assistant's response."""
        try:
            thread = self.client.beta.threads.create()

            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=question
            )

            context = self._get_context(profile_id)
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=context
            )

            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant
            )

            response = await self._process_run(thread.id, run.id)
            self.user_profile.save_interaction(profile_id, question, response)
            
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I'm having trouble processing your request. Please try again later."

    async def _process_run(self, thread_id: str, run_id: str) -> str:
        """Process a run and handle any tool calls."""
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )

            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                return messages.data[0].content[0].text.value

            elif run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    output = await self._execute_tool(tool_call)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": str(output)  # Ensure output is always a string
                    })

                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs
                )

            elif run.status == "failed":
                raise Exception(f"Run failed: {run.last_error}")

            await asyncio.sleep(1)

    def _get_context(self, profile_id: str) -> str:
        """Get context information about the user and available data."""
        context_parts = []
        
        user = self.user_profile.get_user(profile_id)
        if user:
            context_parts.append(f"Informações do usuário: {json.dumps(dict(user))}")

        if csv_data is not None:
            insights = csv_data.describe(include="all").to_string()
            context_parts.append(f"Available data for analysis: {insights}")

        return "\n\n".join(context_parts)