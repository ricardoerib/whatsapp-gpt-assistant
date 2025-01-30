from deep_translator import GoogleTranslator

default_messages = {
    "welcome": "Welcome! Before continuing, we need your consent for GDPR. Do you agree? (Type 'yes' to accept)",
    "terms_required": "You need to accept the GDPR terms to continue. Type 'yes' to accept.",
    "request_email": "Please provide your email to complete your registration.",
    "welcome_back": "Welcome back, user {phone}! How can I assist you today?"
}

def get_translated_message(message_key, language):
    """
    Obtém a mensagem traduzida para o idioma especificado. 
    Se o idioma for 'en', retorna a mensagem padrão sem tradução.
    """
    if language == "en":
        return default_messages.get(message_key, "Message not found")

    try:
        translated_text = GoogleTranslator(source="en", target=language).translate(default_messages[message_key])
        return translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        return default_messages[message_key]
