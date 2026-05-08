import os
import json
import re
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

user_history = {}
MAX_HISTORY = 2
CHATFLICK_JSON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ChatFlick.json")
)
MAX_KNOWLEDGE_SECTIONS = 4
MAX_SECTION_CHARS = 900


class ChatFlickKnowledge:
    _sections = None

    @classmethod
    def relevant_context(cls, prompt):
        sections = cls._load_sections()
        if not sections:
            return ""

        terms = cls._keywords(prompt)
        app_overview = cls._find_section(sections, "app")
        scored_sections = []

        for section in sections:
            score = cls._score(section, terms)
            if score > 0:
                scored_sections.append((score, section))

        scored_sections.sort(key=lambda item: item[0], reverse=True)

        selected = []
        if app_overview:
            selected.append(app_overview)

        for _, section in scored_sections:
            if len(selected) >= MAX_KNOWLEDGE_SECTIONS:
                break
            if section not in selected:
                selected.append(section)

        if not selected:
            selected = sections[:2]

        lines = []
        for section in selected:
            text = section["text"]
            if len(text) > MAX_SECTION_CHARS:
                text = text[:MAX_SECTION_CHARS].rsplit(" ", 1)[0] + "..."
            lines.append(f"[{section['path']}]\n{text}")

        return "\n\n".join(lines)

    @classmethod
    def _load_sections(cls):
        if cls._sections is not None:
            return cls._sections

        try:
            with open(CHATFLICK_JSON_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            print("ChatFlick knowledge load error:", error)
            cls._sections = []
            return cls._sections

        cls._sections = cls._flatten(data)
        return cls._sections

    @classmethod
    def _flatten(cls, value, path="root"):
        if isinstance(value, dict):
            sections = []
            if path != "root":
                sections.append({"path": path, "text": cls._to_text(value)})
            for key, child in value.items():
                child_path = key if path == "root" else f"{path}.{key}"
                if isinstance(child, (dict, list)):
                    sections.extend(cls._flatten(child, child_path))
            return sections

        if isinstance(value, list):
            return [{"path": path, "text": cls._to_text(value)}]

        return [{"path": path, "text": str(value)}]

    @staticmethod
    def _to_text(value):
        if isinstance(value, dict):
            parts = []
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    child_text = json.dumps(child, ensure_ascii=False)
                else:
                    child_text = str(child)
                parts.append(f"{key}: {child_text}")
            return " | ".join(parts)

        if isinstance(value, list):
            return " | ".join(str(item) for item in value)

        return str(value)

    @staticmethod
    def _keywords(prompt):
        return {
            term
            for term in re.findall(r"[a-zA-Z0-9_/-]{3,}", prompt.lower())
            if term not in {"the", "and", "for", "with", "this", "that", "what", "how", "why", "can", "you"}
        }

    @staticmethod
    def _score(section, terms):
        haystack = f"{section['path']} {section['text']}".lower()
        return sum(haystack.count(term) for term in terms)

    @staticmethod
    def _find_section(sections, path):
        for section in sections:
            if section["path"] == path:
                return section
        return None


class AIService:

    @staticmethod
    def _messages_for_prompt(message, history=None):
        knowledge = ChatFlickKnowledge.relevant_context(message)
        system_prompt = (
            "You are Manzoid-AI, the helpful assistant inside ChatFlick. "
            "Use the ChatFlick app knowledge below when the user asks about this application. "
            "Answer clearly and briefly. If the knowledge does not contain the answer, say what you know "
            "and avoid inventing app behavior."
        )

        if knowledge:
            system_prompt += f"\n\nChatFlick app knowledge:\n{knowledge}"

        messages = [{"role": "system", "content": system_prompt}]

        for user_msg, ai_reply in history or []:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": ai_reply})

        messages.append({"role": "user", "content": message})
        return messages

    @staticmethod
    def chat(user_id, message):

        history = user_history.get(user_id, [])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=AIService._messages_for_prompt(message, history),
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
            messages=AIService._messages_for_prompt(prompt),
            max_tokens=150,
        )

        return response.choices[0].message.content.strip()
