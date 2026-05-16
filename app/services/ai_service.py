import os
import json
import re
from groq import Groq

from app.extensions import db
from app.models.support_requests import Support

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

user_history = {}
DEFAULT_MAX_HISTORY = 2
CHATFLICK_JSON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ChatFlick.json")
)
MAX_KNOWLEDGE_SECTIONS = 4
MAX_SECTION_CHARS = 900
MAX_SUPPORT_EXAMPLES = 3


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
    def _messages_for_prompt(message, history=None, mode="chat", extra_context=None):
        knowledge = ChatFlickKnowledge.relevant_context(message)
        if mode == "support":
            system_prompt = (
                "You are Manzoid-AI, the support assistant for ChatFlick. "
                "Answer support requests with a clear, helpful, ready-to-send reply. "
                "Use ChatFlick app knowledge and prior support examples when relevant. "
                "If the request needs account-specific admin action, explain the likely next step and ask for the "
                "needed details without pretending the action was completed. "
                "Do not invent policies, charges, or account changes. Keep the answer friendly and concise."
            )
        else:
            system_prompt = (
                "You are Manzoid-AI, the helpful assistant inside ChatFlick. "
                "Answer the user's question clearly and briefly. "
                "Use ChatFlick app knowledge when the user asks about this application. "
                "If the knowledge does not contain an exact app detail, provide the safest helpful answer and say "
                "when the user should contact support."
            )

        if knowledge:
            system_prompt += f"\n\nChatFlick app knowledge:\n{knowledge}"

        if extra_context:
            system_prompt += f"\n\nSupport context:\n{extra_context}"

        messages = [{"role": "system", "content": system_prompt}]

        for user_msg, ai_reply in history or []:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": ai_reply})

        messages.append({"role": "user", "content": message})
        return messages

    @staticmethod
    def _support_context(category, message):
        examples = AIService._support_examples(category, message)
        if not examples:
            return f"Current category: {category or 'General'}"

        lines = [f"Current category: {category or 'General'}", "Prior answered support examples:"]
        for item in examples:
            lines.append(
                f"- Category: {item.category}\n"
                f"  User asked: {item.message}\n"
                f"  Admin replied: {item.admin_reply}"
            )
        return "\n".join(lines)

    @staticmethod
    def _support_examples(category, message):
        terms = ChatFlickKnowledge._keywords(f"{category or ''} {message or ''}")
        query = (
            db.select(Support)
            .where(Support.admin_reply.is_not(None))
            .order_by(Support.updated_at.desc().nullslast(), Support.created_at.desc())
            .limit(25)
        )

        try:
            answered_requests = db.session.scalars(query).all()
        except Exception as error:
            print("Support examples load error:", error)
            return []

        scored = []
        category_text = (category or "").lower()
        for item in answered_requests:
            haystack = f"{item.category} {item.message} {item.admin_reply}".lower()
            score = sum(haystack.count(term) for term in terms)
            if category_text and category_text == (item.category or "").lower():
                score += 3
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda value: value[0], reverse=True)
        return [item for _, item in scored[:MAX_SUPPORT_EXAMPLES]]

    @staticmethod
    def chat(user_id, message, max_history=DEFAULT_MAX_HISTORY):

        history = user_history.get(user_id, [])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=AIService._messages_for_prompt(message, history),
            max_tokens=320,
        )

        answer = response.choices[0].message.content.strip()

        history.append((message, answer))

        if max_history == 0:
            history = []
        elif max_history > 0 and len(history) > max_history:
            history = history[-max_history:]

        user_history[user_id] = history

        return answer


    @staticmethod
    def simple_chat(prompt):

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=AIService._messages_for_prompt(prompt),
            max_tokens=260,
        )

        return response.choices[0].message.content.strip()

    @staticmethod
    def answer_support_request(category, message):
        prompt = (
            f"Support request category: {category or 'General'}\n"
            f"User question/request: {message}\n\n"
            "Write the support answer only."
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=AIService._messages_for_prompt(
                prompt,
                mode="support",
                extra_context=AIService._support_context(category, message),
            ),
            max_tokens=360,
        )

        return response.choices[0].message.content.strip()
