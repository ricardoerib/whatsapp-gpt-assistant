from openai import OpenAI
import logging
import os
from .utils import get_instruction_prompt
from .csv_processor import csv_data
from gtts import gTTS
from .user_profile import UserProfile
from .wpp import download_whatsapp_audio
from dotenv import load_dotenv
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gpt_model = os.getenv("GPT_MODEL")
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
isDatabaseEnabled = os.getenv("DATABASE_ENABLED", "false").lower() == "true"

APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()
user_profile = UserProfile(APP_ENVIRONMENT)

client = OpenAI()

def get_user_profile(profile_id):
    user = user_profile.get_user(profile_id)
    user = dict(user) if user else None 
    name = user.get("name", "user") if user else None
    phone_number = user.get("phone_number", "user") if user else None
    if name:
        user_name = f"O nome do usuário é {name} "
    else:
        user_name = "O nome do usuário não foi informado "

    return {"role": "system", "content": f"The user data (name: {user_name}, phone number: {phone_number}) are available and can be used if necessary."}

def get_user_history(profile_id):
    history = user_profile.get_user_history(profile_id)
    context = "Toda a conversa com o usuário até o momento foi a seguinte:\n"
    for interaction in history:
        context += f"Pergunta: {interaction['question']}\nResposta: {interaction['response']}\n\n"
    return context

def get_survey_data():
    if csv_data is not None:
        insights = csv_data.describe(include="all").to_string()
        response = f"Os seguintes dados estão disponíveis para análise:\n{insights}\n\n"
        logger.info("Survey data retrieved successfully.")
        return response
    else:
        logger.info("Survey data could not be retrieved.")
        return "Não foi possível recuperar os dados da pesquisa VX."

async def download_audio(audio_id: str) -> str:
    audio_file = await download_whatsapp_audio(audio_id)
    return audio_file

def transcribe_audio(audio_file: str) -> str:
    transcription_result = client.Audio.transcribe("whisper-1", audio_file)
    transcription_text = transcription_result.get("text", "")
    return transcription_text

def generate_audio_response(text: str, lang: str = "pt") -> str:
    tts = gTTS(text=text, lang=lang)
    audio_filename = "response_audio.mp3"
    tts.save(audio_filename)
    return audio_filename

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_user_history",
            "description": "Use this tool to get the user interaction history",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_id": {"type": "string", "description": "ID do perfil do usuário"}
                },
                "required": ["profile_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Use this tool to get the user profile",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_id": {"type": "string", "description": "ID do perfil do usuário"}
                },
                "required": ["profile_id"]
            }
        }
    },
    {
       "type": "function",
        "function": {
            "name": "transcribe_audio",
            "description": "Use this tool to transcribe an audio file",
            "parameters": {
                "type": "object",
                "properties": {
                    "audio_file": {"type": "string", "description": "Caminho do arquivo de áudio"}
                },
                "required": ["audio_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_audio_response",
            "description": "Use this tool to generate an audio response",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Texto para transcrever"},
                    "lang": {"type": "string", "description": "Idioma do texto"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_audio",
            "description": "Use this tool to download an audio file",
            "parameters": {
                "type": "object",
                "properties": {
                    "audio_id": {"type": "string", "description": "ID do arquivo de áudio"}
                },
                "required": ["audio_id"]
            }
        }
    }
]

tools_map = {
    "get_user_history": get_user_history,
    "get_user_profile": get_user_profile,
    "transcribe_audio": transcribe_audio,
    "generate_audio_response": generate_audio_response,
    "download_audio": download_audio,
}

def get_response_from_gpt(profile_id, phone_number, question):
    instructions = get_instruction_prompt()
    messages = [{"role": "system", "content": instructions}]

    user_message_data = get_user_profile(profile_id)
    messages.append(user_message_data)

    print("Survey data: ", csv_data)
    if csv_data is not None:
        logger.info("Survey data retrieved successfully.")
        insights = csv_data.describe(include="all").to_string()
        messages.append({"role": "system", "content": f"The folllowing data are available for analysis:\n{insights}\n\n"})
    else:
        messages.append({"role": "system", "content": "It was not possible to recover VX survey data."})
    

    user_history = get_user_history(profile_id)
    messages.append({"role": "system", "content": f"The history of conserversations is:\n{user_history}\n\n"})


    messages.append({"role": "user", "content": f"Pergunta do usuário: {question}"})

    try:
        response = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            temperature=0.5,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        tool_call = None

        if hasattr(message, "tool_calls") and message.tool_calls and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]

        elif message.function_call:
            tool_call = message.function_call

        if tool_call:
            print(f"Tool call detected: {tool_call}")
            if hasattr(tool_call, "function"):
                tool_name = tool_call.function.name
                arguments_str = tool_call.function.arguments
            else:
                tool_name = tool_call["name"]
                arguments_str = tool_call["arguments"]

            try:
                function_args = json.loads(arguments_str)
            except json.JSONDecodeError:
                logger.error("Falha ao converter os argumentos da função para JSON.")
                function_args = {}

            if tool_name in tools_map:
                function_result = tools_map[tool_name](**function_args)
                print(f"Function result: {function_result}")
                #return function_result

        answer = message.content
        print(f"Answer from GPT: {answer}")
        if answer is None:
            logger.error("Empty response from GPT.")
            answer = "I'm sorry, I'm having trouble processing your request. Please try again later."
        user_profile.save_interaction(profile_id, question, answer)
        return answer
    except Exception as e:
        logger.error(f"Error on calling OpenAI API: {e}")
        return "I'm sorry, I'm having trouble processing your request. Please try again later."
