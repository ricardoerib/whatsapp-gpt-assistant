from openai import OpenAI
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from functools import lru_cache
from datetime import datetime

from ..config import settings
from ..services.user_profile import UserProfileService
from ..services.csv_processor import CSVProcessor

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GPT_MODEL
        self.user_profile = UserProfileService()
        self.csv_processor = CSVProcessor()
        self._assistant_id = None
        
    @property
    def assistant_id(self):
        """Get or create an assistant ID"""
        if not self._assistant_id:
            self._assistant_id = self._create_assistant()
        return self._assistant_id
        
    def _create_assistant(self):
        """Create an OpenAI assistant"""
        try:
            tools = [
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
                        "name": "analyze_data",
                        "description": "Analyze CSV data based on query",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    }
                }
            ]
            
            # Read instructions from file or use default
            try:
                with open("./data/instructions_prompt.md", "r") as f:
                    instructions = f.read()
            except:
                instructions = "You are a helpful assistant. Answer user questions clearly and concisely."
                
            assistant = self.client.beta.assistants.create(
                name="WhatsApp Support Assistant",
                instructions=instructions,
                model=self.model,
                tools=tools
            )
            
            logger.info(f"Created new assistant with ID: {assistant.id}")
            return assistant.id
            
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            # Return a fallback assistant ID if available, otherwise raise
            if settings.FALLBACK_ASSISTANT_ID:
                return settings.FALLBACK_ASSISTANT_ID
            raise
            
    @lru_cache(maxsize=100)
    def get_common_response(self, query_type: str, language: str = "en") -> Optional[str]:
        """Get cached response for common queries"""
        common_responses = {
            "greeting": {
                "en": "Hello! How can I help you today?",
                "pt": "Olá! Como posso ajudá-lo hoje?",
                "es": "¡Hola! ¿Cómo puedo ayudarte hoy?"
            },
            "thanks": {
                "en": "You're welcome! Is there anything else I can help with?",
                "pt": "De nada! Há mais alguma coisa em que eu possa ajudar?",
                "es": "¡De nada! ¿Hay algo más en lo que pueda ayudar?"
            },
            "help": {
                "en": "I can answer questions, provide information, or help with specific tasks. What do you need assistance with?",
                "pt": "Posso responder perguntas, fornecer informações ou ajudar com tarefas específicas. Com o que você precisa de ajuda?",
                "es": "Puedo responder preguntas, proporcionar información o ayudar con tareas específicas. ¿Con qué necesitas ayuda?"
            }
        }
        
        responses = common_responses.get(query_type, {})
        return responses.get(language, responses.get("en"))
            
    async def process_message(self, profile_id: str, question: str) -> str:
        """Process a user message and return a response"""
        try:
            # Check if this is a common query that can be handled without the LLM
            query_type = self._classify_query(question)
            user = self.user_profile.get_user(profile_id)
            language = user.get("language", "en") if user else "en"
            
            common_response = self.get_common_response(query_type, language)
            if common_response:
                # Save the interaction but return the cached response
                self.user_profile.save_interaction(profile_id, question, common_response)
                return common_response
                
            # Create a thread for this conversation
            thread = self.client.beta.threads.create()
            
            # Add the user's message
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=question
            )
            
            # Add context information
            context = self._get_context(profile_id)
            if context:
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=f"Context information: {context}"
                )
                
            # Create a run to process the messages
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Process the run and handle any tool calls
            response = await self._process_run(thread.id, run.id, profile_id)
            
            # Save the interaction
            self.user_profile.save_interaction(profile_id, question, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return "Sorry, I'm having trouble processing your request. Please try again later."
            
    def _classify_query(self, question: str) -> Optional[str]:
        """Classify the query to check if it's a common type"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["hello", "hi", "hey", "olá", "oi", "hola"]):
            return "greeting"
            
        if any(word in question_lower for word in ["thank", "thanks", "obrigado", "gracias"]):
            return "thanks"
            
        if any(word in question_lower for word in ["help", "ajuda", "ayuda"]):
            return "help"
            
        return None
            
    def _get_context(self, profile_id: str) -> str:
        """Get context for the conversation"""
        context_parts = []
        
        # Get user profile
        user = self.user_profile.get_user(profile_id)
        if user:
            user_dict = dict(user) if hasattr(user, "__dict__") else user
            context_parts.append(f"User information: {json.dumps(user_dict)}")
        
        # Get conversation history
        history = self.user_profile.get_user_history(profile_id)
        if history:
            formatted_history = []
            for interaction in history:
                formatted_history.append(f"User: {interaction['question']}")
                formatted_history.append(f"Assistant: {interaction['response']}")
            context_parts.append("Previous conversation:\n" + "\n".join(formatted_history))
        
        # Get CSV data if available
        csv_data = self.csv_processor.get_csv_data()
        if csv_data is not None:
            context_parts.append(f"Available data for analysis:\n{csv_data.describe(include='all').to_string()}")
            
        return "\n\n".join(context_parts)
            
    async def _process_run(self, thread_id: str, run_id: str, profile_id: str) -> str:
        """Process a run and handle any required actions"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            try:
                # Poll for status
                while True:
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run_id
                    )
                    
                    if run.status == "completed":
                        # Get the final response
                        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                        # The most recent message is the assistant's response
                        return messages.data[0].content[0].text.value
                        
                    elif run.status == "requires_action":
                        # Execute required tools
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        tool_outputs = []
                        
                        for tool_call in tool_calls:
                            output = await self._execute_tool(tool_call, profile_id)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": str(output)
                            })
                            
                        # Submit the outputs
                        self.client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tool_outputs
                        )
                        
                    elif run.status == "failed":
                        logger.error(f"Run failed: {run.last_error}")
                        return "Sorry, I encountered an error while processing your request."
                        
                    elif run.status in ["queued", "in_progress"]:
                        # Wait a bit before checking again
                        await asyncio.sleep(1)
                        
                    else:
                        # Unknown status
                        logger.warning(f"Unknown run status: {run.status}")
                        await asyncio.sleep(1)
                        
            except Exception as e:
                logger.error(f"Error in process_run (attempt {attempt}): {e}", exc_info=True)
                if attempt >= max_attempts:
                    return "Sorry, I'm having trouble processing your request. Please try again later."
                # Wait before retrying
                await asyncio.sleep(2)
                
    async def _execute_tool(self, tool_call, profile_id: str) -> str:
        """Execute a tool call and return the result"""
        try:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if function_name == "get_user_history":
                history = self.user_profile.get_user_history(arguments.get("profile_id", profile_id))
                formatted_history = []
                for interaction in history:
                    formatted_history.append(f"User: {interaction['question']}")
                    formatted_history.append(f"Assistant: {interaction['response']}")
                return "\n".join(formatted_history)
                
            elif function_name == "get_user_profile":
                user = self.user_profile.get_user(arguments.get("profile_id", profile_id))
                return json.dumps(dict(user) if user else {})
                
            elif function_name == "analyze_data":
                query = arguments.get("query", "")
                csv_data = self.csv_processor.get_csv_data()
                if csv_data is None:
                    return "No data available for analysis."
                    
                # Simple analysis based on the query
                try:
                    # Try to find columns that match the query
                    matching_columns = [col for col in csv_data.columns if query.lower() in col.lower()]
                    if matching_columns:
                        results = {}
                        for col in matching_columns:
                            results[col] = csv_data[col].describe().to_dict()
                        return json.dumps(results)
                    else:
                        # Try to find rows that match the query
                        filtered = csv_data[csv_data.apply(
                            lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), 
                            axis=1
                        )]
                        if not filtered.empty:
                            return filtered.describe().to_string()
                        else:
                            return f"No data found matching '{query}'."
                except Exception as e:
                    logger.error(f"Error analyzing data: {e}")
                    return f"Error analyzing data: {str(e)}"
            else:
                return f"Unknown function: {function_name}"
                
        except Exception as e:
            logger.error(f"Error executing tool {function_name if 'function_name' in locals() else 'unknown'}: {e}")
            return f"Error executing tool: {str(e)}"