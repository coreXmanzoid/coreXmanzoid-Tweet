import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

user_history = {}
MAX_HISTORY = 2


class AIService:

    @staticmethod
    def chat(user_id, message):

        history = user_history.get(user_id, [])

        context_prompt = ""
        for user_msg, ai_reply in history:
            context_prompt += f"User: {user_msg}\nAI: {ai_reply}\n"

        context_prompt += f"User: {message}\nAI:"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": context_prompt}],
            max_tokens=180,
        )

        answer = response.choices[0].message.content.strip()

        history.append((message, answer))

        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

        user_history[user_id] = history

        return answer


    @staticmethod
    def simple_chat(prompt):

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )

        return response.choices[0].message.content.strip()