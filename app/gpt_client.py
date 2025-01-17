from openai import OpenAI
import os
from app.utils import get_instruction_prompt
from app.csv_processor import csv_data
from app.dynamodb_client import save_interaction, get_user_history

gpt_model = os.getenv("GPT_MODEL")
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
isDatabaseEnabled = os.getenv("DATABASE_ENABLED", "false").lower() == "true"

client = OpenAI()

def get_response_from_gpt(session_id, question):
    instructions = get_instruction_prompt()

    if csv_data is not None:
        insights = csv_data.describe(include="all").to_string()
        context = f"Os seguintes dados estão disponíveis para análise:\n{insights}\n\n"
    else:
        context = ""
    
    if isDatabaseEnabled:
        history = get_user_history(session_id)
        context += "\n".join(history) + "\n" if history else ""
    
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
        if isDatabaseEnabled:
            save_interaction(session_id, question, answer, response)
        return answer
    except Exception as e:
        print(f"Error on calling OpenAI API: {e}")
        return "I'm sorry, I'm having trouble processing your request. Please try again later."