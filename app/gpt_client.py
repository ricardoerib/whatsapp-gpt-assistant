from openai import OpenAI
import logging
import os
from .utils import get_instruction_prompt
from .csv_processor import csv_data
from .user_profile import UserProfile
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gpt_model = os.getenv("GPT_MODEL")
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
isDatabaseEnabled = os.getenv("DATABASE_ENABLED", "false").lower() == "true"

APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()
user_profile = UserProfile(APP_ENVIRONMENT)

client = OpenAI()

def get_response_from_gpt(profile_id, phone_number, question):
    instructions = get_instruction_prompt()
    user = user_profile.get_user(profile_id)
    user = dict(user) if user else None 
    language = user.get("language", "en") if user else "en"
    name = user.get("name", "user") if user else None
    if name:
        user_name = f"O nome do usuário é {name} "
    else:
        user_name = "O nome do usuário não foi informado "

    if csv_data is not None:
        insights = csv_data.describe(include="all").to_string()
        context = f"Os seguintes dados estão disponíveis para análise:\n{insights}\n\n"
    else:
        context = ""
    
    history = user_profile.get_user_history(profile_id)
    context += f"{user_name} e seu número de telefone é {phone_number}.\nE toda a conversa com o usuário até o momento foi a seguinte:\n"
    for interaction in history:
        context += f"Pergunta: {interaction['question']}\nResposta: {interaction['response']}\n\n"
    
    
    prompt = context + f"Pergunta do usuário: {question}"

    try:
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        answer = response.choices[0].message.content
        user_profile.save_interaction(profile_id, question, answer)
        return answer
    except Exception as e:
        print(f"Error on calling OpenAI API: {e}")
        return "I'm sorry, I'm having trouble processing your request. Please try again later."