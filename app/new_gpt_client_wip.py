import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

from .utils import get_instruction_prompt
from .user_profile import UserProfile
from .csv_processor import csv_data  # Pesquisa VX
from .wpp import send_whatsapp_message  # WhatsApp message sender

load_dotenv()

gpt_model = os.getenv("GPT_MODEL")
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()

user_profile = UserProfile(APP_ENVIRONMENT)

client = OpenAI()

functions = [
    {
        "name": "get_user_history",
        "description": "Recupera o histórico de interações do usuário",
        "parameters": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string", "description": "ID do perfil do usuário"}
            },
            "required": ["profile_id"]
        }
    },
    {
        "name": "get_user_history",
        "description": "Recupera o perfil do usuário",
        "parameters": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string", "description": "ID do perfil do usuário"}
            },
            "required": ["profile_id"]
        }
    },
    {
        "name": "query_csv_data",
        "description": "Consulta insights da pesquisa VX",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Palavras-chave para buscar insights na pesquisa"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_csv_insights",
        "description": "Gera insights baseados na pesquisa VX",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "description": "Métrica a ser analisada nos dados da pesquisa"}
            },
            "required": ["metric"]
        }
    }
]

def query_csv_data(query):
    try:
        results = csv_data[csv_data.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
        if results.empty:
            return "Nenhum dado relevante encontrado para essa consulta."

        insights = results.describe().to_dict()
        return f"Insights agregados para '{query}': {insights}"
    except Exception as e:
        return f"Erro ao consultar a pesquisa: {e}"

def generate_csv_insights(metric):
    try:
        if metric not in csv_data.columns:
            return f"A métrica '{metric}' não foi encontrada na pesquisa."

        summary = csv_data[metric].describe().to_dict()
        return f"Resumo estatístico de '{metric}': {summary}"
    except Exception as e:
        return f"Erro ao gerar insights: {e}"

function_map = {
    "get_user_history": user_profile.get_user_history,
    "get_user_profile": user_profile.get_user,
    "query_csv_data": query_csv_data,
    "generate_csv_insights": generate_csv_insights,
}

def get_response_from_gpt(session_id, question):
    try:
        instructions = get_instruction_prompt()
        messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": question}
        ]

        if any(term in question.lower() for term in ["investimento", "t+1", "automação", "fundos", "gestores"]):
            messages.append({"role": "system", "content": "Considere a pesquisa VX como referência para responder a esta questão."})

        response = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            temperature=0.5,
            functions=functions 
        )

        if response.choices[0].message.get("function_call"):
            function_call = response.choices[0].message["function_call"]
            function_name = function_call["name"]
            function_args = function_call["arguments"]

            if function_name in function_map:
                function_result = function_map[function_name](**function_args)
                return function_result

        answer = response.choices[0].message.content

        user_profile.save_interaction(session_id, question, answer)

        return answer

    except Exception as e:
        print(f"Erro ao chamar a API do OpenAI: {e}")
        return "Desculpe, estou com dificuldades para processar sua solicitação. Tente novamente mais tarde."
