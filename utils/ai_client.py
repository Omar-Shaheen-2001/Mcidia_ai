import os
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def llm_chat(system_prompt, user_message, response_format="text"):
    """
    Centralized function to interact with OpenAI API
    
    Args:
        system_prompt: The system role/context for the AI
        user_message: The user's input/question
        response_format: "text" or "json"
    
    Returns:
        AI response as string or JSON
    """
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        kwargs = {
            "model": "gpt-5",
            "messages": messages,
            "max_completion_tokens": 8192
        }
        
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
            messages[0]["content"] += "\n\nRespond with valid JSON format."
        
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        return f"Error: Unable to generate AI response. {str(e)}"

def count_tokens(text):
    """Estimate token count (rough estimation)"""
    return len(text.split()) * 1.3  # Approximate
